#-*- coding: utf-8 -*-
import re
import os
import datetime
import time
import operator
import random

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models_dic import *
from base.models_choices import *
from base.models import *
from organizations.forms import OrganizationImageUploadForm, OrganizationImageSlideUploadForm
from kinoinfo_folder.func import low, capit, del_separator
from user_registration.func import only_superuser_or_admin, md5_string_generate, org_peoples
from articles.views import pagination as pagi
from organizations.ajax import tags_save
from organizations.func import *
from news.views import news
from api.func import resize_image


DOMAIN_CITIES = [
    {'name': 'Ялта', 'sub': 'yalta2'},
    {'name': 'Орск', 'sub': 'orsk'}
]


def search_func(request, current_site, subdomain):
    city = None
    if subdomain in ('yalta', 'yalta2'):
        city = 'Ялта'
    elif subdomain == 'orsk':
        city = 'Орск'
    
    query = request.GET.get('query', '')
    category = request.GET.get('filter', '')
    
    msg = ''
    element = ''
    count = 0
    objs = []
    if query:
        query = low(query)
        if len(query) > 2:
            filter = {'tags__name__icontains': query}

            # организации
            if category == '1':
                element = 'организаций'
                objs = Organization.objects.filter(
                    Q(name__icontains=query) | Q(**filter), 
                    buildings__city__name__name=city
                ).order_by('name').distinct('id')
                count = objs.count()
            # новости
            elif category == '2':
                element = _(u'новостей')
                if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                    objs = list(News.objects.filter(Q(title__icontains=query) | Q(text__icontains=query), site=current_site, visible=True).order_by('title').distinct('id').values('id', 'orgsubmenu', 'dtime', 'text', 'title', 'orgsubmenu__name'))
                    count = len(objs)
                else:
                    objs = News.objects.filter(
                        Q(title__icontains=query) | Q(**filter), 
                        site=current_site, subdomain=subdomain, visible=True
                    ).order_by('title').distinct('id')
            
                    count = objs.count()
                
            # люди
            elif category == '3':
                element = 'людей'
                
                objs = Profile.objects.select_related('user').filter(Q(accounts__nickname__icontains=query) | Q(accounts__fullname__icontains=query), person__city__name__name=city, show_profile=1).distinct('user__id').order_by('user__id')

                count = objs.count()
                
                users = []
                for i in objs:
                    acc = []
                    for j in i.accounts.all():
                        if j.fullname:
                            if query in low(j.fullname):
                                acc.append(j.fullname)
                        if j.nickname:
                            if query in low(j.nickname):
                                acc.append(j.nickname)
                            
                    acc = set(sorted(acc, reverse=True))
                    users.append({'acc': acc, 'id': i.user_id})
                objs = users
        else:
            msg = _(u'Слишком короткий запрос')
            
    return {'count': count,  'msg': msg, 'query': query, 'objs': objs, 'category': category, 'element': element}


@never_cache
def organization_search(request):
    current_site = request.current_site
    subdomain = request.subdomain
    data = search_func(request, current_site, subdomain)
    return render_to_response('organizations/search.html', data, context_instance=RequestContext(request))


@never_cache
def organization_list(request, char):
    current_site = request.current_site
    subdomain = request.subdomain
    
    filter = {}
    city_name = None
    city_names = ''
    if subdomain in ('yalta', 'yalta2'):
        filter = {'buildings__city__name__name': 'Ялта'}
        city_names = 'Ялты'
    elif subdomain == 'orsk':
        filter = {'buildings__city__name__name': 'Орск'}
        city_names = 'Орска'
        
    org_names = list(Organization.objects.filter(**filter).values_list('slug', flat=True).distinct('name'))

    alphabet = []
    for i in org_names:
        try:
            alphabet.append(i[0])
        except IndexError: pass
    alphabet = sorted(set(alphabet))
    
    if char not in alphabet:
        char = alphabet[0]
    
    filter['slug__istartswith'] = char
    orgs = Organization.objects.select_related('tags').filter(**filter).distinct('id').order_by('name')
    
    return render_to_response('organizations/list.html', {'orgs': orgs, 'alphabet': alphabet, 'city_names': city_names}, context_instance=RequestContext(request))


@never_cache
def organization_lists(request):
    tags = set(list(Organization.objects.all().values_list('tags', flat=True)))
    tags = OrganizationTags.objects.filter(pk__in=tags).order_by('name')

    if request.POST:
        tag = int(request.POST['tags'])
    else:
        tag = request.session.get('filter_organizations_show__tag', tags[0].id)

    orgs = Organization.objects.filter(tags__id=tag)
    count = Organization.objects.all().count()
    cat_count = orgs.count()

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, orgs, 12)

    request.session['filter_organizations_show__tag'] = tag
    return render_to_response('organizations/lists.html', {'p': p, 'page': page, 'count': count, 'cat_count': cat_count, 'tags': tags, 'tag': tag}, context_instance=RequestContext(request))


@never_cache
def change_org_branding(request, id):
    if request.POST:
    
        org = get_object_or_404(Organization, pk=id)
        is_editor = is_editor_func(request, org)
        if is_editor or request.user.is_superuser or request.is_admin:
            import shutil

            img_path = '%s/%s' % (settings.BACKGROUND_PATH, org.id)
            
            try: shutil.rmtree(img_path)
            except OSError: pass

            if 'save' in request.POST and request.FILES:
                try: os.makedirs(img_path)
                except OSError: pass
                
                file_format = low(request.FILES['file'].name.encode('utf-8'))
                img_format = re.findall(r'\.(jpg|png|jpeg)$', file_format)[0]
                if img_format:
                    img_obj = request.FILES['file'].read()
                    img_name = '%s.%s' % (md5_string_generate(org.id), img_format)
                    img_path_tmp = '%s/%s' % (img_path, img_name)

                    with open(img_path_tmp, 'wb') as f:
                        f.write(img_obj)
                    
                    org.branding = img_name
                    org.save()
                    
            elif 'delete' in request.POST:
                org.branding = None
                org.save()
        
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404


def organization_save_data(request, org):
    from film.views import get_youtube_video_player
    
    cache.delete('organization__%s__data' % org.uni_slug)

    profile = request.profile
    
    language = None
    if request.current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    if 'note' in request.POST:
        note = request.POST.get('note', False)
        if note != False:

            action = '2' if note else '3'
            if not org.note:
                action = '1'

            org.note = note
            org.note_accept = True if request.user.is_superuser or request.is_admin else False
            org.save()


            if language:
                org_lang, org_lang_created = OrganizationLang.objects.get_or_create(
                    organization = org,
                    language = language,
                    defaults = {
                        'organization': org,
                        'language': language,
                        'note': note,
                    })
                if not org_lang_created:
                    org_lang.note = note
                    org_lang.save()


            ActionsLog.objects.create(
                profile = profile,
                object = '1',
                action = action,
                object_id = org.id,
                attributes = 'Заметка',
                site = request.current_site,
            )


    if 'file' in request.FILES or 'slides' in request.FILES:
        img_path = '%s/%s' % (settings.ORGANIZATIONS_PATH, org.id)
        try: os.makedirs(img_path)
        except OSError: pass

        if 'file' in request.FILES:
            form = OrganizationImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                file_format = low(request.FILES['file'].name)
                img_format = re.findall(r'\.(jpg|png|jpeg)$', file_format)
                if img_format:
                    img_obj = request.FILES['file'].read()
                    img_name = '%s.%s' % (md5_string_generate(org.id), img_format[0])
                    img_path_tmp = '%s/%s' % (img_path, img_name)

                    with open(img_path_tmp, 'wb') as f:
                        f.write(img_obj)

                    resized = resize_image(1000, None, img_obj, 1500)
                    if resized:
                        resized.save(img_path_tmp)

                    img_name_tmp = '%s/%s/%s' % (settings.ORGANIZATIONS_FOLDER, org.id, img_name)

                    img_all = org.images.all()
                    if img_all:
                        img_del = None
                        img_flag = False
                        for i in img_all:
                            if i.status == 1:
                                img_flag = True
                                img_del = i.img.replace(settings.ORGANIZATIONS_FOLDER, settings.ORGANIZATIONS_PATH)
                                i.img = img_name_tmp
                                i.save()

                        if img_del:
                            os.remove(img_del)

                        if not img_flag:
                            org_img = OrganizationImages.objects.create(img=img_name_tmp, status=1)
                            org.images.add(org_img)
                    else:
                        org_img = OrganizationImages.objects.create(img=img_name_tmp, status=1)
                        org.images.add(org_img)

                    ActionsLog.objects.create(
                        profile = profile,
                        object = '1',
                        action = '2',
                        object_id = org.id,
                        attributes = 'Постер',
                        site = request.current_site,
                    )

        if 'slides' in request.FILES:
            form = OrganizationImageSlideUploadForm(request.POST, request.FILES)
            if form.is_valid():
                org_slides = len([i for i in org.images.all() if i.status == 2])
                empty = 3 - org_slides

                files = request.FILES.getlist('slides')[:empty]

                for i in files:

                    file_format = low(i.name)
                    img_format = re.findall(r'\.(jpg|png|jpeg)$', file_format)
                    if img_format:
                        img_obj = i.read()
                        img_name = '%s.%s' % (md5_string_generate(org.id), img_format[0])
                        img_path_tmp = '%s/%s' % (img_path, img_name)

                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)

                        resized = resize_image(1000, None, img_obj, 1500)
                        if resized:
                            resized.save(img_path_tmp)

                        img_name_tmp = '%s/%s/%s' % (settings.ORGANIZATIONS_FOLDER, org.id, img_name)

                        org_img = OrganizationImages.objects.create(img=img_name_tmp, status=2)
                        org.images.add(org_img)

                if files:
                    ActionsLog.objects.create(
                        profile = profile,
                        object = '1',
                        action = '2',
                        object_id = org.id,
                        attributes = 'Слайды',
                        site = request.current_site,
                    )

    if 'trailer' in request.POST:
        video = request.POST.get('trailer')

        code = get_youtube_video_player(video, width=560, height=315)

        action = ''
        if not org.trailer and code:
            action = '1'
        if org.trailer and code:
            action = '2'
        if org.trailer and not code:
            action = '3'

        org.trailer = code
        org.save()

        if action:
            ActionsLog.objects.create(
                profile = profile,
                object = '1',
                action = action,
                object_id = org.id,
                attributes = 'Видео',
                site = request.current_site,
            )

    return org
    
    
def org(request, id, offers=True, area=False, afisha=False):
    timer = time.time()

    tags_objs = {}
    ownership = ()
    street_types = ()
    streets = []
    editors = []
    staff = []
    areas = []
    source = None
    city_names = ''

    im_simple_user = True if 'simple' in request.GET else False

    domain = request.current_site.domain
    subdomain = request.subdomain
    profile = request.profile

    form = OrganizationImageUploadForm()

    street_type = [i for i in STREET_TYPE_CHOICES if int(i[0]) < 70]
    
    filter = {'uni_slug': id, 'visible': True, 'buildings__city__name__status': 1}
    filter2 = {'city__name__status': 1}
    if subdomain in ('yalta', 'yalta2'):
        filter['buildings__city__name__name'] = 'Ялта'
        filter2['city__name__name'] = 'Ялта'
        city_names = 'Ялты'
    elif subdomain == 'orsk':
        filter['buildings__city__name__name'] = 'Орск'
        filter2['city__name__name'] = 'Орска'
        city_names = 'Орска'
    

    unislug = ''
    if domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au', 'vsetiinter.net', 'pm-prepare.com'):
        if domain == 'letsgetrhythm.com.au':
            unislug = 'lets-get-rhythm'
        elif domain == 'vladaalfimovdesign.com.au':
            unislug = 'vlada-alfimov-design'
        elif domain == 'imiagroup.com.au':
            unislug = 'imia-group'
        elif domain == 'pm-prepare.com':
            unislug = 'pmprepare'
        else:
            if subdomain not in ('yalta', 'yalta2', 'orsk'):
                unislug = subdomain
    elif domain in ('kinoinfo.ru', 'kinoafisha.ru') and afisha:
        filter = {'uni_slug': id, 'visible': True, 'buildings__city__name__status': 1}
        filter2['organization__kid__gt'] = 0
        city_names = ''
    
    
    if unislug:
        filter2['city__name__name'] = 'Melbourne'
        if id == unislug:
            filter = {'uni_slug': id}
        else:
            filter['buildings__city__name__name'] = 'Melbourne'
    
        street_type = [i for i in STREET_TYPE_CHOICES if int(i[0]) >= 70]
    
    
    try:
        org = Organization.objects.select_related('source_obj', 'creator').get(**filter)
    except Organization.DoesNotExist:
        raise Http404

    is_editor = is_editor_func(request, org)
    
    ka_movies = []
    org_ka = None
    org_schedules = {}
    rates = {}
    countries = []
    cities_names = []
    org_country = None
    
    kinohod_tickets = ''
    rambler_tickets = ''

    if request.user.is_superuser or is_editor or request.is_admin and not im_simple_user:
        if request.POST:
            organization_save_data(request, org)
            return 'redirect'

        tags = OrganizationTags.objects.exclude(group_flag__in=('2','3','4'))
        for i in tags:
            tags_objs[i.name] = i

        builds = Building.objects.select_related('street').filter(**filter2).exclude(street=None).order_by('street__name')

        streets = sorted(set([i.street.name for i in builds if i.street]))

        if area:
            areas = sorted(set([i.street.area.name for i in builds if i.street and i.street.area]))

        '''
        source = org.source_id
        if org.source_obj:
            if org.source_obj.url == 'http://m.0654.com.ua/':
                source = "http://www.0654.com.ua/catalog/full/%s" % source
            elif org.source_obj.url == 'http://www.bigyalta.info/':
                source = "http://www.bigyalta.info/business/index.php?show=%s" % source
            elif org.source_obj.url == 'http://www.orgpage.ru/':
                source = "http://www.orgpage.ru/орск_и_городской_округ_орск/%s" % source.encode('utf-8')
            elif org.source_obj.url == 'http://www.kinoafisha.ru/':
                source = "http://www.kinoafisha.ru/index.php3?id2=%s&status=2" % source.encode('utf-8')
        '''
        
        editors = org_peoples(org.editors.all())
        
        if org.kid:
            try:
                org_ka = Movie.objects.using('afisha').get(pk=org.kid)
            except Movie.DoesNotExist: pass
        

            today = datetime.date.today()
            day7 = today + datetime.timedelta(days=7)
            
            sch = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lte=day7, cinema__cinema__code=org.kid).exclude(film__source_id=0).values('dtime', 'film__kid', 'film__source_id', 'cinema__name', 'cinema__city__name', 'source_obj__url', 'cinema__source_id', 'sale'))
            
            for i in sch:
                if not org_schedules.get(i['film__kid']):
                    org_schedules[i['film__kid']] = {'dtime': [], 'name': ''}
                org_schedules[i['film__kid']]['dtime'].append(i['dtime'])

                if domain in ('kinoafisha.ru', 'kinoinfo.ru'):

                    if i['source_obj__url'] in ('http://kinohod.ru/', 'http://www.rambler.ru/') and i['sale'] == True:
                        if i['source_obj__url'] == 'http://kinohod.ru/':
                            #kinohod_tickets = u'<a href="http://kinohod.ru/" class="kh_boxoffice" ticket cinema="%s" city=""></a>' % i['cinema__name']
                            kinohod_tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % (
                                i['film__source_id'], i['film__source_id'], i['cinema__city__name'])
                        else:
                            rambler_tickets = u'<rb:place key="%s" placeName="" cityName="" placeID="%s" cityID="" xmlns:rb="http://kassa.rambler.ru"></rb:place>' % (settings.RAMBLER_TICKET_KEY, i['cinema__source_id'])

            for i in FilmsName.objects.using('afisha').only('name', 'film_id').filter(film_id__id__in=org_schedules.keys(), status=1, type=2):
                org_schedules[i.film_id_id]['name'] = i.name
                org_schedules[i.film_id_id]['dtime'] = sorted(set(org_schedules[i.film_id_id]['dtime']))
            
            try:
                rates = AfishaCinemaRate.objects.get(organization=org)
                rates = {'rate': '%5.1f' % rates.rate, 'vnum': rates.vnum}
            except AfishaCinemaRate.DoesNotExist: pass
                

        for i in Movie.objects.using('afisha').select_related('city').only('city', 'id', 'name').all().order_by('name'):
            if org.kid == i.id:
                org_ka = i
            ka_movie_city = i.city.name if i.city else None
            ka_movies.append({'id': i.id, 'name': i.name, 'city': ka_movie_city})
        
        ka_movies = sorted(ka_movies, key=operator.itemgetter('city'))
    

    if not request.user.is_anonymous():
        current_user_is_creator = True if org.creator == profile else False
    else:
        current_user_is_creator = False


    if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
        cache.delete('organization__%s__data' % id)

    is_cached = cache.get('organization__%s__data' % id, 'nocaсhed')

    if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
        cached_page = False

        name_tags = []
        guide_tags = []
        for i in org.tags.filter(group_flag__in=('1', '2')):
            if i.group_flag == '1':
                name_tags.append(i)
            elif i.group_flag == '2':
                guide_tags.append(i)


        offers_tags = []
        advert_tags = []
        if offers:
            offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')
            
            for i in offers_tag:
                if i.organizationtags.group_flag == '3':
                    offers_tags.append(i)
                elif i.organizationtags.group_flag == '4':
                    advert_tags.append(i)


        # СЛАЙДЫ И ПОСТЕР
        images = {'main': '', 'slides': []}
        for i in org.images.all():
            if i.status == 1:
                images['main'] = i.img
            else:
                images['slides'].append({'img': i.img, 'id': i.id})
                
        # УЛИЦА
        street = None
        try:
            b_all = org.buildings.all()
            if b_all:
                street = Building.objects.select_related('city', 'street', 'street__area').get(pk=b_all[0].id)
        except Building.DoesNotExist: pass

        # ТЕЛЕФОНЫ
        phones = []
        phone_pre = ''
        for i in org.phones.all():
            ph_code = ''
            num = i.phone
            num_format = num
            phones.append({'pre': phone_pre, 'code': ph_code, 'num': num, 'format': num_format})
        phones = sorted(phones, key=operator.itemgetter('num'))

        site = org.site if org.site else ''
        
        # ПУСТЫЕ СЛАЙДЫ
        range_to = 3 - len(images['slides'])
        for i in range(range_to):
            images['slides'].append({})

        # ТРЕЙЛЕР
        trailer_code = org.trailer if org.trailer else ''
        trailer_url = ''
        if trailer_code:
            trailer = BeautifulSoup(trailer_code, from_encoding='utf-8')
            trailer = trailer.find('iframe')
            if trailer:
                trailer_url = 'http:%s' % trailer['src']
                trailer_code = trailer
                trailer_code['width'] = 250
                trailer_code['height'] = 150
            else:
                trailer_code = ''
        trailer = str(trailer_code)

        relations = org.relations.count()

        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)

        data = {
            'guide_tags': guide_tags, 
            'name_tags': name_tags, 
            'offers_tags': offers_tags, 
            'advert_tags': advert_tags,  
            'street': street, 
            'phones': phones, 
            'phone_pre': phone_pre,
            'site': site, 
            'trailer': trailer,
            'trailer_url': trailer_url,
            'images': images, 
            'relations': relations,
            'branding': branding,
        }

        cache.set('organization__%s__data' % id, data, 60*60*4)
    else:
        data = is_cached
        cached_page = True


    language = None
    note_lang = ''
    if request.current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
        
        if language:
            try: note_lang = OrganizationLang.objects.get(organization=org, language=language).note
            except OrganizationLang.DoesNotExist: pass
        

    read_more = False
    # если описание проверено или не проверенно и автор - это текущий юзер
    if org.note_accept or not org.note_accept and current_user_is_creator:
        org_note = note_lang if language and note_lang else org.note

        note_all = org_note if org_note else ''
        note_cut = BeautifulSoup(note_all, from_encoding='utf-8').text.strip()

        if len(note_cut) > 200:
            note_cut = note_cut[:200]
            read_more = True
    else:
        note_all = ''
        note_cut = ''


    if request.user.is_superuser or is_editor or request.is_admin and not im_simple_user:
        if afisha:
            city_filter = {'status': 1, 'city__country__id': 2}
            if data['street'].city:
                org_country = data['street'].city.country_id
                city_filter['city__country__id'] = org_country

            countries = Country.objects.filter(city__name__status=1).distinct('pk').order_by('name')
            cities_names = list(NameCity.objects.filter(**city_filter).order_by('name').values('id', 'city__id', 'name'))
        
    kinohod_key = settings.KINOHOD_APIKEY_CLIENT if domain in ('kinoafisha.ru', 'kinoinfo.ru') else ''

    data.update({
        'org': org, 
        'note_all': note_all, 
        'note_cut': note_cut, 
        'tags': tags_objs, 
        'read_more': read_more, 
        'ownership': OWNERSHIP_CHOICES, 
        'street_types': street_type, 
        'streets': streets, 
        'form': form, 
        'source': source, 
        'creator': current_user_is_creator, 
        'city_names': city_names, 
        'editors': editors, 
        'is_editor': is_editor, 
        'areas': areas,
        'DOMAIN_CITIES': DOMAIN_CITIES,
        'org_ka': org_ka,
        'ka_movies': ka_movies,
        'org_schedules': org_schedules,
        'im_simple_user': im_simple_user,
        'rates': rates,
        'afisha': afisha,
        'countries': countries,
        'cities_names': cities_names,
        'org_country': org_country,
        'timer': '%5.2f' % (time.time()-timer),
        'cached_page': cached_page,
        'kinohod_tickets': kinohod_tickets,
        'kinohod_key': kinohod_key,
        'rambler_tickets': rambler_tickets,
    })

    return data



@never_cache
def organization_show_new(request, id):
    data = org(request, id)
    if data == 'redirect':
        return HttpResponseRedirect(reverse('organization_show_new', kwargs={'id': id}))
    else:
        return render_to_response('organizations/show.html', data, context_instance=RequestContext(request))


@never_cache
def organization_cinema(request, id):
    data = org(request, id, afisha=True)
    if data == 'redirect':
        return HttpResponseRedirect(reverse('organization_cinema', kwargs={'id': id}))
    else:
        tmplt = 'organizations/show.html'
        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            tmplt = 'mobile/organizations/show.html'
        return render_to_response(tmplt, data, context_instance=RequestContext(request))


@never_cache
def organization_cinema_list(request, id):
    try:
        city = City.objects.get(kid=id)
    except City.DoesNotExist:
        raise Http404
    else:
        city_name = NameCity.objects.get(city__pk=city.id, status=1).name
        buildings = list(Building.objects.filter(organization__kid__gt=0).values('city__kid', 'organization', 'organization__name', 'organization__uni_slug'))

        cities_kids = set([i['city__kid'] for i in buildings])

        countries = {}
        for i in list(NameCity.objects.filter(city__kid__in=cities_kids, status=1).values('city', 'city__kid', 'name', 'city__country', 'city__country__name')):
            if not countries.get(i['city__country']):
                countries[i['city__country']] = {'id': i['city__country'], 'name': i['city__country__name'], 'cities': []}
            countries[i['city__country']]['cities'].append({'kid': i['city__kid'], 'name': i['name']})

        countries = sorted(countries.values(), key=operator.itemgetter('name'))
        for i in countries:
            i['cities'] = sorted(i['cities'], key=operator.itemgetter('name'))

        none = []
        cinemas = {}
        for i in buildings:
            if not cinemas.get(i['city__kid']):
                cinemas[i['city__kid']] = []
            name = i['organization__name'] if i['organization__name'] else 'None'
            cinemas[i['city__kid']].append({
                'name': name, 
                'slug': i['organization__uni_slug'],
            })


        cinemas = cinemas.get(long(id))
        cinemas = sorted(cinemas, key=operator.itemgetter('name'))

        return render_to_response('organizations/cinema_list.html', {'countries': countries, 'city': city, 'city_name': city_name, 'cinemas': cinemas}, context_instance=RequestContext(request))


@never_cache
def organization_schedules(request, id):
    from slideblok.views import releasedata

    org = get_object_or_404(Organization, uni_slug=id)
    
    data = {}
    
    if org.kid:

        today = datetime.date.today()
        day7 = today + datetime.timedelta(days=7)
        
        sch = SourceSchedules.objects.select_related('film').only('dtime', 'film').filter(dtime__gte=today, dtime__lte=day7, cinema__cinema__code=org.kid).exclude(film__source_id=0)
        
        for i in sch:
            if not data.get(i.film.kid):
                data[i.film.kid] = {'dtime': [], 'data': {}}
            data[i.film.kid]['dtime'].append(i.dtime)

        films = releasedata(data, {}, persons=False, likes=True, trailers=True)
        
        for i in films:
            data[i['id']]['data'] = i
            data[i['id']]['dtime'] = sorted(set(data[i['id']]['dtime']))

    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    is_editor = is_editor_func(request, org)
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
    tmplt = 'organizations/schedules.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/organizations/schedules.html'

    return render_to_response(tmplt, {'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'data': data, 'org_ka': True}, context_instance=RequestContext(request))


@never_cache
def organization_staff(request, id):
    org = get_object_or_404(Organization, uni_slug=id)
    staff = org_peoples(org.staff.all())
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    is_editor = is_editor_func(request, org)
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
    return render_to_response('organizations/staff.html', {'staff': staff, 'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES}, context_instance=RequestContext(request))


@never_cache
def organization_relations(request, id):
    org = get_object_or_404(Organization, uni_slug=id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    is_editor = is_editor_func(request, org)
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
    
    return render_to_response('organizations/relations.html', {'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES}, context_instance=RequestContext(request))


@never_cache
def organization_offers(request, id, offer_id):
    org = get_object_or_404(Organization, uni_slug=id)
    tag_rel = get_object_or_404(Organization_Tags, pk=offer_id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    offer = None
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
            if i.id == int(offer_id):
                offer = i
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    if offer:
        is_editor = is_editor_func(request, org)
        
        filter = {'organization': org, 'tag': tag_rel, 'news__reader_type': 11}
        if not request.user.is_superuser and not is_editor and not request.is_admin:
            filter['news__visible'] = True
        
        org_news = list(OrganizationNews.objects.filter(**filter).values_list('news', flat=True))

        news = News.objects.filter(pk__in = org_news).order_by('-dtime')
        
        page = request.GET.get('page')
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        
        p, page = pagi(page, news, 8)
        
        news_data = []
        for ind, i in enumerate(p.object_list):
            description_orig = BeautifulSoup(i.text, from_encoding='utf-8').text.strip()
            description = description_orig[:130]
            try:
                last_word = description_orig[130:]
                if last_word[0] == ' ':
                    last_word = ' ' + last_word.split()[0]
                else:
                    last_word = last_word.split()[0]
            except IndexError:
                last_word = ''
                
            description = '%s%s ...' % (description, last_word)
            
            even = True if ind % 2 == 0 else False
            video = True if i.video else False
            autor = org_peoples([i.autor])
            news_data.append({'obj': i, 'description': description, 'even': even, 'video': video, 'autor': autor})
        
        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
        if len(news_data) == 1:
            item_id = news_data[0]['obj'].id
            return HttpResponseRedirect(reverse('organization_offers_news', kwargs={'id': id, 'offer_id': offer_id, 'item_id': item_id}))
        
        tmplt = 'organizations/offers.html'
        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            tmplt = 'mobile/organizations/offers.html'

        return render_to_response('organizations/offers.html', {'org': org, 'offers_tags': offers_tags, 'offer': offer, 'advert_tags': advert_tags, 'is_editor': is_editor, 'news_data': news_data, 'p': p, 'page': page, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'org_ka': True}, context_instance=RequestContext(request))
    else:
        raise Http404


@never_cache
def organization_offers_news(request, id, offer_id, item_id):
    org = get_object_or_404(Organization, uni_slug=id)
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')
    
    offers_tags = []
    advert_tags = []
    offer = None
    
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
            if i.id == int(offer_id):
                offer = i
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    if offer:
        is_editor = is_editor_func(request, org)
        
        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
        data = {
            'status': 11, 
            'org': org, 
            'is_editor': is_editor, 
            'offers_tags': offers_tags, 
            'advert_tags': advert_tags,
            'offer': offer,
            'branding': branding,
            'DOMAIN_CITIES': DOMAIN_CITIES
        }

        return news(request, item_id, data)
    else:
        raise Http404
    

@never_cache
def organization_adverts_news(request, id, advert_id, item_id):
    org = get_object_or_404(Organization, uni_slug=id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org,      organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    offer = None
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
            if i.id == int(advert_id):
                advert = i

    if advert:
        is_editor = is_editor_func(request, org)
        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
        data = {
            'status': 12, 
            'org': org, 
            'is_editor': is_editor, 
            'offers_tags': offers_tags, 
            'advert_tags': advert_tags,
            'offer': advert,
            'branding': branding,
            'DOMAIN_CITIES': DOMAIN_CITIES
        }
        return news(request, item_id, data)
        
    else:
        raise Http404


@never_cache
def organization_adverts(request, id, advert_id):
    org = get_object_or_404(Organization, uni_slug=id)
    tag_rel = get_object_or_404(Organization_Tags, pk=advert_id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    advert = None
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
            if i.id == int(advert_id):
                advert = i
    
    if advert:
        is_editor = is_editor_func(request, org)
        
        filter = {'organization': org, 'tag': tag_rel, 'news__reader_type': 12}
        if not request.user.is_superuser and not is_editor and not request.is_admin:
            filter['news__visible'] = True
        
        org_news = list(OrganizationNews.objects.filter(**filter).values_list('news', flat=True))

        news = News.objects.filter(pk__in = org_news).order_by('-dtime')
        
        page = request.GET.get('page')
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        
        p, page = pagi(page, news, 8)
        
        news_data = []
        for ind, i in enumerate(p.object_list):
            description_orig = BeautifulSoup(i.text, from_encoding='utf-8').text.strip()
            description = description_orig[:130]
            try:
                last_word = description_orig[130:]
                if last_word[0] == ' ':
                    last_word = ' ' + last_word.split()[0]
                else:
                    last_word = last_word.split()[0]
            except IndexError:
                last_word = ''
                
            description = '%s%s ...' % (description, last_word)
            
            even = True if ind % 2 == 0 else False
            video = True if i.video else False
            autor = org_peoples([i.autor])
            news_data.append({'obj': i, 'description': description, 'even': even, 'video': video, 'autor': autor})
        
        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
        
        tmplt = 'organizations/adverts.html'
        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            tmplt = 'mobile/organizations/adverts.html'

        return render_to_response(tmplt, {'org': org, 'offers_tags': offers_tags, 'offer': advert, 'advert_tags': advert_tags, 'is_editor': is_editor, 'news_data': news_data, 'p': p, 'page': page, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'org_ka': True}, context_instance=RequestContext(request))
    else:
        raise Http404

    
@never_cache
def organization_offers_and_advert(request, id):
    if request.POST:
        org = get_object_or_404(Organization, uni_slug=id)
        
        profile = request.profile
        is_editor = is_editor_func(request, org)

        if request.user.is_superuser or is_editor or request.is_admin:
            tags = []
            tags_del = []
            tags_new = []
            
            st = request.POST.get('status')
            
            if st == '3':
                url_type = u'offers'
            elif st == '4':
                url_type = u'advert'
            
            arr = request.POST.getlist('organization_menu_field')
            
            vals = []
            for i in arr:
                val, oid = i.split('~%~')
                val = val.strip()
                if val not in vals:
                    vals.append(val)
                    oid = int(oid)
                    if val:
                        tag = tags_save(request.current_site, profile, org, st, [val])[0]
                        tags.append({'id': oid, 'tag': tag})
                        tags_new.append(tag)
                    else:
                        tags_del.append(oid)
            
            offers_tags = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag=st)

            tags_exist = [i.organizationtags for i in offers_tags]

            tags_back = []

            for i in offers_tags:
                if i.organizationtags_id in tags_del:
                    i.delete()
                
                for t in tags:
                    if t['id'] == i.organizationtags_id:
                        if t['tag'] not in tags_exist:
                            i.organizationtags = t['tag']
                            i.save()
                            while i.organizationtags in tags_new: tags_new.remove(i.organizationtags)
            
            new = None
            for i in tags_new:
                if i not in tags_exist:
                    new = Organization_Tags.objects.create(organizationtags=i, organization=org)
                    
            if new:
                if request.current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
                    return HttpResponseRedirect(ref)
                else:
                    if st == '3':
                        return HttpResponseRedirect(reverse('organization_offers', kwargs={'id': org.uni_slug, 'offer_id': new.id}))
                    elif st == '4':
                        return HttpResponseRedirect(reverse('organization_adverts', kwargs={'id': org.uni_slug, 'advert_id': new.id}))
        if request.current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
            ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
            return HttpResponseRedirect(ref)
        else:
            return HttpResponseRedirect(reverse('organization_show_new', kwargs={'id': org.uni_slug}))
    else:
        raise Http404
        


@never_cache
def organization_reviews_and_questions(request, id, type=None):
    org = get_object_or_404(Organization, uni_slug=id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    if type == 'reviews':
        reader = 8
        title = 'Отзывы'
    elif type == 'questions':
        reader = 9
        title = 'Вопросы'
    elif type == 'comments':
        reader = 10
        title = 'Комментарии'
    
    is_editor = is_editor_func(request, org)
    
    org_news = list(OrganizationNews.objects.filter(organization=org, news__reader_type=reader).values_list('news', flat=True))
    
    news = News.objects.select_related('autor').filter(pk__in=org_news, reader_type=reader).order_by('-dtime')
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    p, page = pagi(page, news, 6)
    
    news_data = []
    for ind, i in enumerate(p.object_list):
        description_orig = BeautifulSoup(i.text, from_encoding='utf-8').text.strip()
        description = description_orig[:130]
        try:
            last_word = description_orig[130:]
            if last_word[0] == ' ':
                last_word = ' ' + last_word.split()[0]
            else:
                last_word = last_word.split()[0]
        except IndexError:
            last_word = ''
            
        description = '%s%s ...' % (description, last_word)
        
        even = True if ind % 2 == 0 else False
        video = True if i.video else False
        autor = org_peoples([i.autor])[0]
        
        if i.autor_nick == 1:
            if i.autor.user.first_name:
                autor['fio'] = i.autor.user.first_name
                autor['show'] = '2'
        elif i.autor_nick == 2:
            autor['fio'] = ''
            autor['short_name'] = ''
        
        news_data.append({'obj': i, 'description': description, 'even': even, 'video': video, 'autor': autor})
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)

        
    spam_msg = request.session.get('news_antispam')
    if spam_msg:
        request.session['news_antispam'] = ''
    banned = request.session.get('banned')

    tmplt = 'organizations/reviews_and_questions.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/organizations/reviews_and_questions.html'

    return render_to_response(tmplt, {'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'news_data': news_data, 'status': reader, 'p': p, 'page': page, 'title': title, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'spam_msg': spam_msg, 'banned': banned, 'org_ka': True}, context_instance=RequestContext(request))




@never_cache
def organization_reviews_and_questions_news(request, id, item_id, type):
    org = get_object_or_404(Organization, uni_slug=id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org,      organizationtags__group_flag__in=('3','4')).order_by('id')

    offers_tags = []
    advert_tags = []
    offer = None
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)

    if type == 'reviews':
        type = 8
    elif type == 'questions':
        type = 9
    elif type == 'comments':
        type = 10
        
    is_editor = is_editor_func(request, org)
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)

    data = {
        'status': type, 
        'org': org, 
        'is_editor': is_editor, 
        'offers_tags': offers_tags, 
        'advert_tags': advert_tags,
        'offer': None,
        'branding': branding,
        'DOMAIN_CITIES': DOMAIN_CITIES
    }
    return news(request, item_id, data)
        
   

def organizations_add_func(request, name, tag, org_city, ncinema):
    org, id = (None, None)
    if name and tag:
        profile = request.profile
            
        current_site = request.current_site
        subdomain = request.subdomain
        city = None
        if subdomain in ('yalta', 'yalta2'):
            city = 'Ялта'
        elif subdomain == 'orsk':
            city = 'Орск'
        
        city_obj = None
        if subdomain:
            city_obj = City.objects.get(name__name=city, name__status=1)
        else:
            if org_city:
                city_obj = City.objects.select_related('country').get(name__pk=org_city)
        
        if city_obj:
            tag = tag.strip()
            t_list = (tag, capit(tag), low(tag))
            tag_obj = None
            for t in t_list:
                try:
                    tag_obj = OrganizationTags.objects.get(name=t, group_flag='1')
                    break
                except OrganizationTags.DoesNotExist: pass

            if not tag_obj:
                tag_obj = OrganizationTags.objects.create(name=t_list[0], group_flag='1')
                
            if name:
                try:
                    org = Organization.objects.get(name=name, tags=tag_obj, buildings__city=city_obj)
                    id = None
                except Organization.DoesNotExist:
                    build, bcreated = Building.objects.get_or_create(
                        number=None, 
                        street=None, 
                        city=city_obj,
                        defaults = {
                            'number': None, 
                            'street': None, 
                            'city': city_obj,
                        })
                        
                    slug = low(del_separator(name.encode('utf-8')))
                    org = Organization.objects.create(
                        name = name, 
                        slug = slug,
                        creator = request.user.get_profile(), 
                    )

                    uni = unidecode(name)
                    uni = re.findall(ur'[a-z0-9]+', low(uni))
                    uni = '-'.join(uni) if uni else ''
                    uni_slug = '%s-%s' % (uni, org.id)
                    org.uni_slug = uni_slug
                    org.save()
                    
                    Organization_Tags.objects.create(organizationtags=tag_obj, organization=org)

                    org.buildings.add(build)

                    if ncinema == '1':
                        unique_list = list(Movie.objects.using('afisha').all().values_list('random', flat=True))
                                            
                        randm = random.randint(100000000, 999999999)
                        while randm in unique_list:
                            randm = random.randint(100000000, 999999999)

                        new_id = Movie.objects.using('afisha').latest('id').id + 1

                        afisha_cinema = Movie.objects.using('afisha').create(
                            id = new_id,
                            name = name,
                            city_id = city_obj.kid,
                            idterr_id = city_obj.country.kid,
                            random = randm,
                            ind = '',
                            address = '',
                            phones = '',
                            fax = '',
                            mail = '',
                            director = '',
                            kontakt1 = '',
                            kontakt2 = '',
                            path = '',
                            site = '',
                            techinfo = '',
                            workingtime = '',
                            set_field_id = 0,
                            metro_id = 0,
                            comment = '',
                            access = 0,
                            tech_comment = '',
                            longitude = 0,
                            latitude = 0,
                        )
                        MovieExtData.objects.using('afisha').create(
                            id = new_id,
                            rate1 = 0,
                            rate2 = 0,
                            rate3 = 0,
                            rate = 0,
                            vnum = 0.0,
                            opinions = '',
                        )
                        org.kid = new_id
                        org.save()

                        cinema, cinema_created = Cinema.objects.get_or_create(
                            code = org.kid,
                            defaults = {
                                'code': org.kid,
                                'city': city_obj,
                            })

                        if cinema_created:
                            try:
                                slug = low(del_separator(name))
                            except UnicodeDecodeError:
                                slug = low(del_separator(name.encode('utf-8')))

                            names = [
                                {'name': name.encode('utf-8'), 'status': 1},
                                {'name': slug, 'status': 2}
                            ]

                            for n in names:
                                name_obj, name_obj_created = NameCinema.objects.get_or_create(
                                    name = n['name'], 
                                    status = n['status'], 
                                    defaults = {
                                        'name': n['name'], 
                                        'status': n['status'],
                                    })
                                cinema.name.add(name_obj)


                    id = org.id

                    ActionsLog.objects.create(
                        profile = profile,
                        object = '1',
                        action = '1',
                        object_id = id,
                        attributes = 'Организация'
                    )

                    OrganizationTags.objects.filter(organization=None).delete()
    return org, id


@only_superuser_or_admin
@never_cache
def organizations_add(request):
    if request.POST:
        name = request.POST.get('organization_name')
        tag = request.POST.get('tag')
        org_city = request.POST.get('org_city')
        ncinema = request.POST.get('ncinema')

        current_site = request.current_site

        org, id = organizations_add_func(request, name, tag, org_city, ncinema)

        if not id:
            id = org.id if org.creator == request.profile else None

        if id:
            if current_site.domain == 'vsetiinter.net':
                return HttpResponseRedirect(reverse('organization_show_new', kwargs={'id': org.uni_slug}))
            if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
                return HttpResponseRedirect(reverse('organization_cinema', kwargs={'id': org.uni_slug}))
            else:
                return HttpResponseRedirect(reverse('organizations_show', kwargs={'id': id}))

    ref = request.META.get('HTTP_REFERER', '/')
    return HttpResponseRedirect(ref)


@only_superuser_or_admin
@never_cache
def organizations_delete(request, id):
    if request.POST:
        org = get_object_or_404(Organization, pk=id)
        profile = request.profile
        if org.creator == profile and not request.user.is_superuser and not request.is_admin:
            org.visible = False
            org.save()

            ActionsLog.objects.create(
                profile=profile,
                object='1',
                action='3',
                object_id=id,
                attributes='Организация'
            )

        elif request.user.is_superuser or request.is_admin:
            ActionsLog.objects.filter(object=1, object_id=org.id).delete()
            org_news = OrganizationNews.objects.select_related('news').filter(organization=org)

            for i in org_news:
                i.news.delete()

            org_news.delete()

            org.delete()
            OrganizationTags.objects.filter(organization=None).delete()

        return HttpResponseRedirect(reverse('main'))
    else:
        raise Http404


@only_superuser_or_admin
@never_cache
def org_tags_upd(request):
    for i in OrganizationTags.objects.all():
        if i.group_flag == '2':
            i.group_flag = '3'
            '''
            elif i.group_flag == 'org_about':
                i.group_flag = '2'
            elif i.group_flag == 'org_offers_tag':
                i.group_flag = '3'
            elif i.group_flag == 'org_needs_tag':
                i.group_flag = '4'
            '''
            i.save()

    return HttpResponse(str())


@only_superuser_or_admin
@never_cache
def organizations_show(request, id):
    # отображает организацию через админку киноинфо

    tags_objs = {}
    o_tags_list = []
    ownership = ()
    street_types = ()
    streets = []
    source = None

    try:
        org = Organization.objects.select_related('source_obj', 'creator').get(pk=id, visible=True)
    except Organization.DoesNotExist:
        raise Http404

    form = OrganizationImageUploadForm()

    if request.user.is_superuser or request.is_admin:
        if request.POST:

            if 'note' in request.POST:
                note = request.POST.get('note', False)
                if note is not False:

                    action = '2' if note else '3'
                    if not org.note:
                        action = '1'

                    org.note = note
                    org.note_accept = True if request.user.is_superuser or request.is_admin else False
                    org.save()

                    ActionsLog.objects.create(
                        profile = request.user.get_profile(),
                        object = '1',
                        action = action,
                        object_id = org.id,
                        attributes = 'Заметка'
                    )

            if 'file' in request.FILES or 'slides' in request.FILES:
                img_path = '%s/%s' % (settings.ORGANIZATIONS_PATH, org.id)
                try: os.makedirs(img_path)
                except OSError: pass

                if 'file' in request.FILES:
                    form = OrganizationImageUploadForm(request.POST, request.FILES)
                    if form.is_valid():
                        img_format = re.findall(r'\.(jpg|JPG|png|PNG)$', request.FILES['file'].name)[0]
                        if img_format:
                            img_obj = request.FILES['file'].read()
                            img_name = '%s.%s' % (md5_string_generate(org.id), img_format)
                            img_path_tmp = '%s/%s' % (img_path, img_name)

                            with open(img_path_tmp, 'wb') as f:
                                f.write(img_obj)

                            resized = resize_image(1000, None, img_obj, 1500)
                            if resized:
                                resized.save(img_path_tmp)

                            img_name_tmp = '%s/%s/%s' % (settings.ORGANIZATIONS_FOLDER, org.id, img_name)

                            img_all = org.images.all()
                            if img_all:
                                img_del = None
                                img_flag = False
                                for i in img_all:
                                    if i.status == 1:
                                        img_flag = True
                                        img_del = i.img.replace(settings.ORGANIZATIONS_FOLDER, settings.ORGANIZATIONS_PATH)
                                        i.img = img_name_tmp
                                        i.save()

                                if img_del:
                                    os.remove(img_del)

                                if not img_flag:
                                    org_img = OrganizationImages.objects.create(img=img_name_tmp, status=1)
                                    org.images.add(org_img)
                            else:
                                org_img = OrganizationImages.objects.create(img=img_name_tmp, status=1)
                                org.images.add(org_img)

                            ActionsLog.objects.create(
                                profile = request.user.get_profile(),
                                object = '1',
                                action = '2',
                                object_id = org.id,
                                attributes = 'Постер'
                            )

                if 'slides' in request.FILES:
                    form = OrganizationImageSlideUploadForm(request.POST, request.FILES)
                    if form.is_valid():
                        org_slides = len([i for i in org.images.all() if i.status == 2])
                        empty = 3 - org_slides

                        files = request.FILES.getlist('slides')[:empty]

                        for i in files:

                            img_format = re.findall(r'\.(jpg|JPG|png|PNG)$', i.name)[0]
                            if img_format:
                                img_obj = i.read()
                                img_name = '%s.%s' % (md5_string_generate(org.id), img_format)
                                img_path_tmp = '%s/%s' % (img_path, img_name)

                                with open(img_path_tmp, 'wb') as f:
                                    f.write(img_obj)

                                resized = resize_image(1000, None, img_obj, 1500)
                                if resized:
                                    resized.save(img_path_tmp)

                                img_name_tmp = '%s/%s/%s' % (settings.ORGANIZATIONS_FOLDER, org.id, img_name)

                                org_img = OrganizationImages.objects.create(img=img_name_tmp, status=2)
                                org.images.add(org_img)

                        if files:
                            ActionsLog.objects.create(
                                profile = request.user.get_profile(),
                                object = '1',
                                action = '2',
                                object_id = org.id,
                                attributes = 'Слайды'
                            )

            if 'trailer' in request.POST:
                video = request.POST.get('trailer')

                video_id = ''
                code = None

                if video and 'youtu' in video:
                    video = strip_tags(video)

                    if 'youtu.be' in video:
                        video_id = video.split('http://youtu.be/')[1]
                    elif 'www.youtube.com' in video:
                        try:
                            video_id = video.split('?v=')[1]
                        except IndexError:
                            video_id = video.split('&v=')[1]

                        video_id = video_id.split('&')[0]

                if video_id:
                    video_id = video_id.replace("'", '').replace('"', '').replace('=', '')
                    code = '<iframe width="560" height="315" src="//www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % video_id

                action = '2' if code else '3'
                if not org.trailer:
                    action = '1'

                org.trailer = code
                org.save()

                ActionsLog.objects.create(
                    profile = request.user.get_profile(),
                    object = '1',
                    action = action,
                    object_id = org.id,
                    attributes = 'Видео'
                )

            return HttpResponseRedirect(reverse('organizations_show', kwargs={'id': id}))

        # словарь всех меток передается в шабло для использование в функции ява скрипта
        tags = OrganizationTags.objects.all()
        for i in tags:
            tags_objs[i.name] = i

        builds = Building.objects.select_related('street').filter(city__name__name="Ялта", city__name__status=1).exclude(street=None).order_by('street__name')

        streets = sorted(set([i.street.name for i in builds]))

        # список имеющихся меток преобразовывается для выдачи форм полей в интерфейсе
        o_tags = org.tags.all()
        empty_tags = 6 - o_tags.count()
        o_tags_list = [{'id': i.id, 'name': i.name, 'alter_name': i.alter_name, 'group_flag': i.group_flag } for i in o_tags]
        o_tags_list = sorted(o_tags_list, key=operator.itemgetter('name'))
        for i in range(empty_tags):
            o_tags_list.append({'id': 99999999 + i + 1, 'name': ''})

        ownership = OWNERSHIP_CHOICES
        street_types = STREET_TYPE_CHOICES

        source = org.source_id
        if source and org.source_obj:
            if org.source_obj.url == 'http://m.0654.com.ua/':
                source = "http://www.0654.com.ua/catalog/full/%s" % source
            elif org.source_obj.url == 'http://www.bigyalta.info/':
                source = "http://www.bigyalta.info/business/index.php?show=%s" % source

        actions = ActionsLog.objects.select_related('profile').filter(object=1, object_id=org.id).order_by('-dtime')
        actions = actions[0] if actions else None


    images = {'main': '', 'slides': []}
    for i in org.images.all():
        if i.status == 1:
            images['main'] = i.img
        else:
            images['slides'].append({'img': i.img, 'id': i.id})

    street = Building.objects.select_related('city', 'street').get(pk = org.buildings.all()[0].id)

    for i in street.city.name.all():
        #return HttpResponse(str(i.status))
        if i.status == 1:
            if i.name == u'Ялта':
                return HttpResponseRedirect('http://yalta2.vsetiinter.net/%s/' % org.uni_slug)
            elif i.name == u'Орск':
                return HttpResponseRedirect('http://orsk.vsetiinter.net/%s/' % org.uni_slug)   

    phones = []
    for i in org.phones.all():
        if re.findall(r'^654', i.phone):
            ph_code = '654'
            num = i.phone.replace('654', '')
            num_temp = [num[i:i+2] for i in range(0, len(num), 2)]
            num_format = '-'.join(num_temp)
        else:
            ph_code = ''
            num = i.phone
            num_format = num

        phones.append({'pre': '+380', 'code': ph_code, 'num': num, 'format': num_format})

    phones = sorted(phones, key=operator.itemgetter('num'))

    site = org.site if org.site else ''

    range_to = 3 - len(images['slides'])
    for i in range(range_to):
        images['slides'].append({})

    trailer_code = org.trailer if org.trailer else ''
    trailer_url = ''

    if trailer_code:
        trailer = BeautifulSoup(trailer_code, from_encoding='utf-8')
        trailer = trailer.find('iframe')
        if trailer:
            trailer_url = 'http:%s' % trailer['src']
            trailer_code = trailer
            trailer_code['width'] = 250
            trailer_code['height'] = 150
        else:
            trailer_code = ''

    trailer = str(trailer_code)

    current_user_is_creator = True if org.creator == request.user.get_profile() else False

    read_more = False
    # если описание проверено или не проверенно и автор - это текущий юзер
    if org.note_accept or not org.note_accept and current_user_is_creator:
        note_all = org.note if org.note else ''
        note_cut = BeautifulSoup(note_all, from_encoding='utf-8').text.strip()

        if len(note_cut) > 200:
            note_cut = note_cut[:200]
            read_more = True
    else:
        note_all = ''
        note_cut = ''


    # список меток для вывода на страницу организации
    org_tags = sorted([i.name for i in org.tags.all()])

    org_meta_tag_list = OrganizationTags.objects.filter(organization__id=id)

    org_offers_tag = []
    org_needs_tag = []
    org_about_tag = []
    org_name_tag = []

    return render_to_response('organizations/show.html', { 'org': org, 'trailer': trailer, 'note_all': note_all, 'note_cut': note_cut, 'tags': tags_objs, 'o_tags_list': o_tags_list, 'org_tags': org_tags, 'phones': phones, 'read_more': read_more, 'ownership': ownership, 'street_types': street_types, 'street': street, 'streets': streets, 'trailer_url': trailer_url, 'form': form, 'images': images, 'site': site, 'source': source, 'actions': actions, 'creator': current_user_is_creator, }, context_instance=RequestContext(request))



@never_cache
def view(request, id, vid, pid=None):
    from letsgetrhythm.views import view_func

    org = get_object_or_404(Organization, uni_slug=id)
    
    offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')
    
    offers_tags = []
    advert_tags = []
    for i in offers_tag:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
    
    is_editor = is_editor_func(request, org)
    
    branding = None
    if org.branding:
        branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)

    access = True if request.user.is_superuser or request.is_admin or is_editor else False

    data = view_func(request, vid, pid, 'org', access, id)

    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())

    data.update({'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'org_ka': None})

    tmplt = 'organizations/view.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/organizations/view.html'

    return render_to_response(tmplt, data, context_instance=RequestContext(request))
    


@never_cache
def org_change_page_type(request, id, vid):
    if request.POST:
        org = get_object_or_404(Organization, uni_slug=id)
        
        is_editor = is_editor_func(request, org)
        
        if request.user.is_superuser or request.is_admin or is_editor:
        
            menu = get_object_or_404(OrgSubMenu, pk=vid)
            
            try:
                OrgMenu.objects.get(organization=org, submenu=menu)
            except OrgMenu.DoesNotExist:
                pass
            else:
                menu.page_type = request.POST.get('page_type')
                menu.save()
                
                if menu.page_type == '1':
                    ref = 'org_view'
                elif menu.page_type == '2':
                    ref = 'org_gallery'
            
            
                return HttpResponseRedirect(reverse(ref, kwargs={'id': id, 'vid': vid}))
            
    raise Http404
    
    
@never_cache
def org_view_post_del(request, id, vid, pid):
    if request.POST:
        org = get_object_or_404(Organization, uni_slug=id)
        
        is_editor = is_editor_func(request, org)
        
        if request.user.is_superuser or request.is_admin or is_editor:
        
            try:
                menu = OrgSubMenu.objects.select_related('news').get(pk=vid)
            except OrgSubMenu.DoesNotExist:
                raise Http404
            
            try:
                OrgMenu.objects.get(organization=org, submenu=menu)
            except OrgMenu.DoesNotExist:
                pass
            else:
                news = News.objects.get(pk=pid)
                if news in menu.news.all():
                    menu.news.remove(news)

                news.delete()

                return HttpResponseRedirect(reverse('org_view', kwargs={'id': id, 'vid': vid}))
            
    raise Http404
    
    
@never_cache
def org_gallery(request, id, vid):
    from vladaalfimov.views import gallery_func
    
    org = get_object_or_404(Organization, uni_slug=id)
    
    try:
        menu = OrgSubMenu.objects.select_related('news').get(pk=vid)
    except OrgSubMenu.DoesNotExist:
        raise Http404
    
    try:
        OrgMenu.objects.get(organization=org, submenu=menu)
    except OrgMenu.DoesNotExist:
        raise Http404
    else:
        is_editor = is_editor_func(request, org)
        
        access = True if request.user.is_superuser or request.is_admin or is_editor else False
        
        data = gallery_func(request, vid, menu, access, id)
        if data == 'redirect':
            return HttpResponseRedirect(reverse("org_gallery", kwargs={'id': id, 'vid': vid}))
        
        offers_tag = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag__in=('3','4')).order_by('id')

        offers_tags = []
        advert_tags = []
        for i in offers_tag:
            if i.organizationtags.group_flag == '3':
                offers_tags.append(i)
            elif i.organizationtags.group_flag == '4':
                advert_tags.append(i)

        
        branding = None
        if org.branding:
            branding = '%sbg/%s/%s' % (settings.MEDIA_URL, org.id, org.branding)
            
        data.update({'org': org, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'branding': branding, 'DOMAIN_CITIES': DOMAIN_CITIES, 'org_ka': None})
    
    tmplt = 'organizations/gallery.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/organizations/gallery.html'

    return render_to_response(tmplt, data, context_instance=RequestContext(request))
    
