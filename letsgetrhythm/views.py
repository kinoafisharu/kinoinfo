#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
from random import randrange

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.core.mail import get_connection, EmailMultiAlternatives
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits, resize_image
from user_registration.views import get_usercard
from user_registration.func import *
from news.views import cut_description, create_news
from vladaalfimov.forms import *
from organizations.func import is_editor_func
from organizations.views import org, search_func
from organizations.ajax import xss_strip2
from organizations.forms import OrganizationImageSlideUploadForm, OrganizationInviteTextForm, OrganizationImageUploadForm
from kinoinfo_folder.func import low, del_separator, uppercase
from release_parser.clickatell import clickatell_send_sms, clickatell_get_sms_status
from letsgetrhythm.forms import LetsGetNewsForm
from articles.views import pagination as pagi


LETS_PRICES = {
    '1': 150, 
    '2': 250, 
    '3': 100, 
    '4': 150,
}

def get_org_menu(slug, request, profile=False):
    if profile:
        filter = {'orgmenu__profile__user__id': slug}
    else:
        filter = {'orgmenu__organization__uni_slug': slug}
    
    language = None
    if request.current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    menu_data = {}
    
    menu = list(OrgSubMenu.objects.filter(**filter).values('name', 'id', 'orgmenu__name', 'orgmenu', 'page_type', 'orgmenu__orgmenulang__name', 'orgmenu__orgmenulang__language', 'orgmenu__private'))

    for i in menu:
        key = 'about' if i['orgmenu__name'] == 'About Us' else i['orgmenu']

        title = i['orgmenu__name']
        title_lang = ''
        if language:
            if i['orgmenu__orgmenulang__name'] and i['orgmenu__orgmenulang__language'] == language.id:
                title_lang = i['orgmenu__orgmenulang__name']

        if menu_data.get(key):
            menu_data[key]['sub'].append({'id': i['id'], 'name': i['name'], 'type': i['page_type']})
            if title_lang:
                menu_data[key]['title'] = title_lang
        else:
            if title_lang:
                title = title_lang
            menu_data[key] = {'title': title, 'private': i['orgmenu__private'], 'sub': [{'id': i['id'], 'name': i['name'], 'type': i['page_type']}]}

    return menu_data
    

def get_org_left_menu(slug, vid, request):
    orgmenu = None
    left_menu = {}

    language = None
    if request.current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    filter = {'submenu__id': vid, 'organization__uni_slug': slug}
    org_title = ''
    orgmenu_tmp = None
    if language:
        try:
            orgmenu_tmp = list(OrgMenu.objects.filter(**filter).filter(orgmenulang__language=language).values('id', 'name', 'orgmenulang__name', 'orgmenulang__language', 'private'))[0]
            if orgmenu_tmp['orgmenulang__name'] and orgmenu_tmp['orgmenulang__language'] == language.id:
                org_title = orgmenu_tmp['orgmenulang__name']
                org_id = orgmenu_tmp['id']
        except IndexError: pass

    if not orgmenu_tmp:
        try:
            orgmenu_tmp = OrgMenu.objects.get(**filter)
            org_title = orgmenu_tmp.name
            org_id = orgmenu_tmp.id
        except OrgMenu.DoesNotExist: pass
        
    
    if orgmenu_tmp:
        orgmenu = {'id': org_id, 'name': org_title}

        for i in list(OrgSubMenu.objects.filter(orgmenu__pk=org_id).values('name', 'id', 'orgmenu__name', 'orgmenu', 'page_type', 'orgsubmenulang__language', 'orgsubmenulang__name')):
            if not left_menu.get(i['id']):
                left_menu[i['id']] = i
        
            left_name_lang = ''
            if language and i['orgsubmenulang__name'] and i['orgsubmenulang__language'] == language.id:
                left_name_lang = i['orgsubmenulang__name']
                left_menu[i['id']]['name'] = left_name_lang

    left_menu = left_menu.values()
    if request.current_site.domain == 'imiagroup.com.au' and 'WEB-DEVELOPMENT' in org_title:
        t = _(u'Управление проектами')
        left_menu.insert(0, {
            'orgsubmenulang__name': None, 
            'name': t, 
            'orgmenu__name': u'', 
            'orgmenu': 20L, 
            'orgsubmenulang__language': None, 
            'page_type': u'1', 
            'id': None,
        })


    return orgmenu, left_menu


@never_cache
def index(request):
    from organizations.views import org
    current_site = request.current_site

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
    elif current_site.domain == 'vsetiinter.net':
        slug = request.subdomain
        
    data = org(request, slug, offers=False)

    if data == 'redirect':
        return HttpResponseRedirect(reverse('main'))
    else:
        data['title'] = 'About Us'
        data['current_site'] = current_site
        data['site_name'] = current_site.name
        if current_site.domain == 'vsetiinter.net':
            data['site_name'] = slug
        
        return render_to_response('letsget/main.html', data, context_instance=RequestContext(request))


@never_cache
def view_post_del(request, vid, id, type, org=None):
    if request.POST:
        if request.user.is_superuser or request.is_admin:
            next = request.GET.get('next')

            current_site = request.current_site
            subdomain = request.subdomain
            if not subdomain:
                subdomain = 0
            
            menu = OrgSubMenu.objects.select_related('news').get(pk=vid)

            filter = {'pk': id}
            if type == 'org':
                filter['site'] = current_site
                filter['subdomain'] = subdomain

            news = News.objects.get(**filter)
            if news in menu.news.all():
                menu.news.remove(news)
                
            ActionsLog.objects.create(
                profile = request.profile,
                object = '6',
                action = '3',
                object_id = news.id,
                attributes = news.title,
                site = current_site,
            )
            
            author = news.autor

            news.delete()

            if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):

                if type == 'spec':
                    return HttpResponseRedirect(reverse('get_spec', kwargs={'url': next}))
                else:
                    if author:
                        return HttpResponseRedirect(reverse('profile_view', kwargs={'user_id': author.user_id, 'vid': vid}))
            else:
                return HttpResponseRedirect(reverse('letsget_view', kwargs={'vid': vid}))
            
    raise Http404

@never_cache
def view_ipost_del(request, id, itype):
    if request.POST:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            if not subdomain:
                subdomain = 0

            news = News.objects.get(pk=id, site=current_site, subdomain=subdomain).delete()

            return HttpResponseRedirect(reverse('letsget_%s_template' % itype))
            
    raise Http404


@never_cache
def searching_text(request):
    current_site = request.current_site
    site_name = current_site.name
    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        
    data = search_func(request, current_site, None)
    
    news_ids = []
    news_data = []
    for i in data['objs']:
        description = cut_description(i['text'], True, 250)
        news_data.append({'id': i['id'], 'news_title': i['title'], 'dtime': i['dtime'], 'description': description, 'video': False, 'vid': i['orgsubmenu'], 'sub_title': i['orgsubmenu__name']})
    
    data['news_data'] = news_data
    data['slug'] = slug
    data['current_site'] = current_site
    data['site_name'] = site_name
    data['title'] = 'Searching'
    
    return render_to_response('letsget/search.html', data, context_instance=RequestContext(request))


def view_func(request, vid, id, type, access, slug=None):
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain

    inv_t = {
        'invite': '15',
        'invoice': '16',
    }

    is_my_profile = False
    user_id = None
    is_blog = False
    check_domain = True

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        if request.domain == '0.0.1:8000':
            if vid == 53:
                is_blog = True
        else:
            if vid == 29:
                is_blog = True
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
    elif current_site.domain == 'vsetiinter.net':
        if not slug:
            slug = subdomain
            site_name = subdomain
    elif current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
        check_domain = False

    if not subdomain:
        subdomain = 0

    if vid:
        if type == 'org':
            filter_1 = {'orgmenu__organization__uni_slug': slug}
            
            filter_2 = {'pk': vid, 'orgmenu__organization__uni_slug': slug}
        elif type == 'user':
            user_id = request.GET.get('u')
            if user_id:
                if int(request.profile.user_id) == int(user_id):
                    is_my_profile = True
            else:
                user_id = request.profile.user_id
                is_my_profile = True
                
            filter_1 = {'orgmenu__profile__user__id': user_id}
            filter_2 = {'pk': vid}

            slug = user_id
        elif type in ('spec', 'booking'):
            filter_2 = {'pk': vid}
            slug = ''

        
        try:
            menu = OrgSubMenu.objects.select_related('news').get(**filter_2)
        except OrgSubMenu.DoesNotExist:
            raise Http404
    
    language = None
    if current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    
    if request.POST:
        if access:
            name = request.POST.get('news_title', ' ')
            text = request.POST.get('text','')
            visible = request.POST.get('visible', False)
            edit = int(request.POST.get('edit'))

            if not name.strip() and (not vid or type == 'booking'):
                name_clear = BeautifulSoup(text, from_encoding='utf-8').text.strip()
                name = name_clear[0:70]
                
            lact = None
            
            if text: 
                #if type == 'user':
                #    text = xss_strip2(text)

                if edit:
                    edit_filter = {'pk': edit}
                    if check_domain:
                        edit_filter['site'] = current_site
                        edit_filter['subdomain'] = subdomain
                    news = News.objects.get(**edit_filter)
                    news.title = name
                    news.text = text
                    news.visible = visible
                    news.language = language
                    news.save()
                    lact, lobj, lattr = ('2', news.id, news.title)
                else:
                    type_obj = inv_t.get(type)
                    news = create_news(request, [], name, text, type_obj, 0, None, visible)
                    if vid:
                        menu.news.add(news)
                        
                    lact, lobj, lattr = ('1', news.id, news.title)
                    
                    if type == 'user':
                        # Создается объект в очередь на рассылку юзерам
                        SubscriberObjects.objects.create(
                            type = '1',
                            obj = vid,
                            end_obj = news.id,
                        )

                        # Создается подписка автора статьи на новые комменты
                        from user_registration.func import sha1_string_generate
                        unsubscribe = sha1_string_generate().replace('_','')
                        SubscriberUser.objects.get_or_create(
                            type = '3',
                            obj = news.id,
                            profile = request.profile,
                            defaults = {
                                'type': '3',
                                'obj': news.id,
                                'profile': request.profile,
                                'unsubscribe': unsubscribe,
                            })
                    

            if lact:
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '6',
                    action = lact,
                    object_id = lobj,
                    attributes = lattr,
                    site = current_site,
                )
                
            return 'redirect'
            
                
    title = ''
    page_type = None
    page_types = ()
    posts = []
    if vid:
        if id:
            filter = {'reader_type': None, 'pk': id, 'language': language}
        else:
            filter = {'reader_type': None, 'language': language}
        if not access:
            filter['visible'] = True
        if check_domain:
            filter['site'] = current_site
            filter['subdomain'] = subdomain
        posts = menu.news.filter(**filter).order_by('-dtime')

        if type in ('user', 'spec') and posts:
            if id or posts.count() == 1:
                posts[0].views += 1
                posts[0].save()
    else:
        type_obj = inv_t.get(type)
        if type_obj:
            inv_filter = {'reader_type': type_obj, 'language': language}
            if id:
                inv_filter['id'] = id
            if check_domain:
                inv_filter['site'] = current_site
                inv_filter['subdomain'] = subdomain
            posts = News.objects.filter(**inv_filter)
        title = '%s templates' % type.capitalize()
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    p, page = pagi(page, posts, 15)

    news_ids = []
    news_data = []
    for ind, i in enumerate(p.object_list):
        description = cut_description(i.text, True, 250)
        video = True if i.video else False
        news_data.append({'obj': i, 'description': description, 'video': video, 'date': i.dtime})

    count = len(news_data)

    if vid:
        page_type = menu.page_type
        if count == 0:
            page_types = PAGE_TYPES_CHOICES
        title = menu.name

    report = {'is_report': False, 'send': False, 'calendar_id': 0}
    if request.user.is_superuser and is_blog and count == 1:
        try:
            report_obj = LetsGetCalendar.objects.get(report=news_data[0]['obj'].id)
            report['is_report'] = True
            report['send'] = report_obj.report_send
            report['calendar_id'] = report_obj.id
        except LetsGetCalendar.DoesNotExist: pass
            

    news_data = sorted(news_data, key=operator.itemgetter('date'), reverse=True)
    return {'news_data': news_data, 'title': title, 'site_name': site_name, 'current_site': current_site, 'slug': slug, 'count': count, 'vid': vid, 'id': id, 'access': access, 'is_my_profile': is_my_profile, 'user_id': user_id, 'page_types': page_types, 'page_type': page_type, 'is_blog': is_blog, 'report': report, 'p': p, 'page': page}


@never_cache
def view(request, vid, id=None, type='org'):
    access = True if request.user.is_superuser or request.is_admin else False

    data = view_func(request, int(vid), id, type, access)

    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())

    comments_list = []
    if id:
        current_site = request.current_site
        subdomain = request.subdomain
        if not subdomain:
            subdomain = 0
        
        comments = News.objects.filter(site=current_site, subdomain=subdomain, reader_type='10', extra__istartswith='%s;' % id).order_by('dtime')
        
        comments_dict = {}
        authors = {}
        for i in comments:
            extra = i.extra.split(';')
            comment, answer = extra if len(extra) == 2 else (extra[0], None)

            autor = org_peoples([i.autor])[0]
            
            if i.autor_nick == 1:
                if i.autor.user.first_name:
                    autor['fio'] = i.autor.user.first_name
                    autor['show'] = '2'
            elif i.autor_nick == 2:
                autor['fio'] = ''
                autor['short_name'] = ''
            
            if autor['fio']:
                user = autor['fio']
            else:
                user = autor['short_name']

            authors[i.id] = user

            ans = None
            if answer:
                ans = authors.get(int(answer))
            
            comment_cut = ''
            if len(i.text) > 250:
                comment_cut = cut_description(i.text, True, 250)
            
            comments_list.append({'comment': i.text, 'comment_cut': comment_cut, 'date': str(i.dtime), 'user': user, 'id': i.id, 'answer': ans})
            
    
    extend_template = 'base.html'
    
    current_site = request.current_site
    if type == 'org':
        if current_site.domain == 'letsgetrhythm.com.au':
            template = 'vladaalfimov/main.html'
        elif current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
            template = 'vladaalfimov/main_new.html'
            extend_template = 'base_vlada.html'
        elif current_site.domain == 'vsetiinter.net':
            template = 'vladaalfimov/main.html'

    elif type == 'user':
        template = 'user/view.html'

    data['extend_template'] = extend_template
    data['comments_list'] = comments_list
    
    
    return render_to_response(template, data, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def change_page_type(request, vid):
    if request.POST:
        if request.user.is_superuser or request.is_admin:
            menu = get_object_or_404(OrgSubMenu, pk=vid)
            menu.page_type = request.POST.get('page_type')
            menu.save()
            current_site = request.current_site

            if menu.page_type == '1':
                if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
                    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
                    return HttpResponseRedirect(ref)
                else:
                    ref = 'letsget_view'
                    return HttpResponseRedirect(reverse(ref, kwargs={'vid': vid}))
            elif menu.page_type == '2':
                if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
                    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
                    return HttpResponseRedirect(ref)
                else:
                    ref = 'gallery'
                    return HttpResponseRedirect(reverse(ref, kwargs={'vid': vid}))
            
    raise Http404
    

@only_superuser_or_admin
@never_cache
def clients_add(request):
    if request.POST:
        current_site = request.current_site
        subdomain = request.subdomain
        user = request.POST.get('user_id')
        LetsGetClients.objects.get_or_create(
            profile_id = user,
            site = current_site,
            subdomain = subdomain,
            defaults = {
                'profile_id': user,
                'site': current_site,
                'subdomain': subdomain,
            })

    return HttpResponseRedirect(reverse('letsget_clients'))


@only_superuser_or_admin
@never_cache
def clients_del(request):
    if request.POST:
        current_site = request.current_site
        subdomain = request.subdomain
        checker = request.POST.getlist('checker')
        if checker:
            clients = LetsGetClients.objects.filter(id__in=checker, site=current_site, subdomain=subdomain)
            
            for i in clients:
                attr = ''
                if i.organization_id:
                    attr = u'Org: %s' % i.organization.name
                elif i.profile_id:
                    attr = u'Profile: %s' % i.profile.user_id
                    
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '10',
                    action = '3',
                    object_id = i.id,
                    attributes = attr,
                    site = current_site,
                )
            
            clients.delete()
            
    return HttpResponseRedirect(reverse('letsget_clients'))
        
        
@only_superuser_or_admin
@never_cache
def clients(request):
    title = 'Clients List'
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name
    char = None
    date_from = ''
    date_to = ''
    note_srch = ''
    code = ''
    agree = 0
    tag = None
    
    agree_filter = {
        0: ('* all', ''),
        1: ('Confirmed', 'True'),
        2: ('Failure', 'False'),
        3: ('Paid', 'Paid'),
        4: ('No Reply', 'None'),
    }
    
    filter = {'site': current_site, 'subdomain': subdomain}
    if request.POST:
        if 'note_filter' in request.POST:
            note_srch = request.POST.get('note_srch','')
            if note_srch:
                filter['organization__extra__icontains'] = note_srch
        elif 'date_filter' in request.POST:
            date_from = request.POST.get('date_from','')
            date_to = request.POST.get('date_to','')
            
            if date_from:
                f_year, f_month, f_day = date_from.split('-')
                date_from = datetime.datetime(int(f_year), int(f_month), int(f_day))
            if date_to:
                t_year, t_month, t_day = date_to.split('-')
                date_to = datetime.datetime(int(t_year), int(t_month), int(t_day))
        else:
            char = request.POST.get('char')
            if char and char != '* all':
                filter['organization__name__istartswith'] = char
                
            code = request.POST.get('code')
            if code and code != '* all':
                filter['organization__source_id'] = code
                
            agree = int(request.POST.get('status', 0))
            if agree and agree != 0:
                agreee = agree_filter.get(agree)
                filter['organization__extra__icontains'] = agreee[1]
    
            if 'tags' in request.POST:
                tag = request.POST.get('tags')
                if tag != '* all':
                    filter['tag'] = tag

    
    alphabet_filter = ['* all',]
    codes = ['* all',]
    orgs = []
    tags = ['* all',]
    notified_data = {}
    
    now = datetime.datetime.now()

    for i in list(LetsGetClients.objects.select_related('organization').filter(site=current_site, subdomain=subdomain).exclude(organization=None).values('id', 'organization', 'tag', 'organization__name', 'organization__source_id', 'letsgetcalendar__letsgetcalendarnotified', 'letsgetcalendar__letsgetcalendarnotified__invite_notified', 'letsgetcalendarclientnotified', 'letsgetcalendarclientnotified__invite_notified', 'letsgetcalendarclientnotified__invite_dtime', 'letsgetcalendar__letsgetcalendarnotified__invite_dtime')):
    
        alphabet_filter.append(low(del_separator(i['organization__name'].encode('utf-8'))).decode('utf-8')[0])
        codes.append(i['organization__source_id'])
        orgs.append(i['organization'])
        tags.append(i['tag'])
        
        
        notify = i['letsgetcalendarclientnotified']
        if i['letsgetcalendar__letsgetcalendarnotified']:
            notify = i['letsgetcalendar__letsgetcalendarnotified']
        
        notified = i['letsgetcalendarclientnotified__invite_notified']
        if i['letsgetcalendar__letsgetcalendarnotified__invite_notified']:
            notified = i['letsgetcalendar__letsgetcalendarnotified__invite_notified']
        
        notify_date = i['letsgetcalendarclientnotified__invite_dtime']
        if i['letsgetcalendar__letsgetcalendarnotified__invite_dtime']:
            notify_date = i['letsgetcalendar__letsgetcalendarnotified__invite_dtime']
        
        
        one_week_ago = now - datetime.timedelta(days=7)
        two_week_ago = now - datetime.timedelta(days=14)
        three_week_ago = now - datetime.timedelta(days=21)
        
        notify_color = ''
        
        if notify_date:
            if notify_date <= now and notify_date >= one_week_ago:
                notify_color = '#7CA6D1'
            elif notify_date <= one_week_ago and notify_date >= two_week_ago:
                notify_color = '#EECD4D'
            elif notify_date <= three_week_ago:
                notify_color = '#DCAF82'
        
        notify_enable = True if notified != now.date() else False

        notified_data[i['id']] = {
            'notify': notify, 
            'notified': notified,
            'dtime': notify_date,
            'color': notify_color,
            'enable': notify_enable,
        }
        
    alphabet_filter = sorted(set(alphabet_filter))
    codes = sorted(set(codes))
    tags = sorted(set(tags))
    
    profiles_tmp = list(Profile.objects.filter(staff_organization__pk__in=orgs).values('staff_organization', 'user'))
    org_prof = {}
    for i in profiles_tmp:
        org_prof[i['staff_organization']] = i['user']
    
    users = list(User.objects.filter(pk__in=org_prof.values()))
    usercards_dict = get_usercard(users, ucity=False)

    clients = LetsGetClients.objects.select_related('organization','profile').filter(**filter)

    profiles = [i.profile for i in clients if i.profile]
    pclients = org_peoples(profiles, dic=True)
    
    clients_list = []
    
    for i in clients:
        notify = notified_data.get(i.id)
        
        if i.profile:
            if not date_from and not date_to:
                person = pclients.get(i.profile.user_id)
                clients_list.append({'id': i.id, 'name': person['name'], 'obj_id': i.profile.user_id, 'type': 'person', 'extra': '', 'tag': i.tag, 'notify': notify})
        else:
            prof = org_prof.get(long(i.organization_id))
            card = usercards_dict.get(prof)
        
            email = None
            contact = ''
            extra = ['', '', '', '']
            if card:
                if card['email']:
                    email = card['email']
                elif not card['email'] and card['emails']:
                    card['profile'].user.email = card['emails'][0]
                    card['profile'].user.save()
                    card['email'] = card['emails'][0]
                    email = card['email']
                if not card['email'] and card['emails_not_auth']:
                    email = card['emails_not_auth'][0]
            
                contact = card['name']
                if card['profile'].phone:
                    contact += u'\n%s' % card['profile'].phone
                if email:
                    contact += u'\n%s' % email

            name = i.organization.name
            obj_id = i.organization.uni_slug
            if i.organization.extra:
                extra = i.organization.extra.replace(' 00:00:00','').split(';')
                
            append = True
            
            ev_date = None
            if extra[0]:
                try:
                    e_year, e_month, e_day = extra[0].split('-')
                    ev_date = datetime.datetime(int(e_year), int(e_month), int(e_day))
                except ValueError: pass
            
            if date_from or date_to:
                append = False
                if extra[0]:
                    e_year, e_month, e_day = extra[0].split('-')
                    ev_date = datetime.datetime(int(e_year), int(e_month), int(e_day))
                    
                    if date_from and date_to:
                        if ev_date >= date_from and ev_date <= date_to:
                            append = True
                    elif date_from:
                        if ev_date >= date_from:
                            append = True
                    else:
                        if ev_date <= date_to:
                            append = True
                    
            if append:
                clients_list.append({'id': i.id, 'name': name, 'obj_id': obj_id, 'type': 'org', 'extra': extra, 'date': ev_date, 'contact': contact, 'tag': i.tag, 'notify': notify})
    
    clients = sorted(clients_list, key=operator.itemgetter('name'))
    
    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        template = 'letsget/clients.html'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
        template = 'vladaalfimov/clients.html'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        template = 'vladaalfimov/clients.html'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain
        site_name = slug
        template = 'letsget/clients.html'
    
    return render_to_response(template, {'title': title, 'site_name': site_name, 'clients': clients, 'current_site': current_site, 'alphabet_filter': alphabet_filter, 'char': char, 'date_from': str(date_from).replace(' 00:00:00', ''), 'date_to': str(date_to).replace(' 00:00:00', ''), 'note_srch': note_srch, 'codes': codes, 'code': code, 'agree_filter': agree_filter, 'agree': agree, 'slug': slug, 'tags': tags, 'tag': tag}, context_instance=RequestContext(request))


def ahead_time(ahead, dtime):
    times = {
        1: 5,
        2: 15,
        3: 30,
        4: 60,
        5: 120,
        6: 180,
        7: 240,
        8: 300,
        9: 1440,
    }
    t = times.get(int(ahead))
    dtime = dtime - datetime.timedelta(minutes=t)
    return dtime


def create_pdf(**kwargs):
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import A4
    
    to = kwargs['to']
    event = kwargs['event']
    today = kwargs['today']
    general_price = kwargs['general_price']
    offer = kwargs['offer']
    domain = kwargs['domain']
    bank = kwargs['bank']
    note = kwargs['note']
    bcr = kwargs['bcr']
    bcr_code = kwargs['bcr_code']
    numsess = kwargs['numsess']
    forwhat = kwargs.get('forwhat', 'per session')
    times = kwargs.get('times', True)
    subtotal = kwargs.get('subtotal', True)

    def draw(lines, p, x, y):
        for line in lines:
            p.setFont("Helvetica", line['size'])
            for l in line['txt'].split('\n'):
                p.drawString(x, y, l)
                y = y-line['size']*1.3
        return y

    code = md5_string_generate(to)[:8]
    file_name = 'invoice_%s.pdf' % code
    file_path = '%s/%s' % (settings.INVOICES_TMP, file_name)
    
    with open('%s/%s_invoice_data.json' % (settings.API_EX_PATH, domain), 'r') as f:
        data = json.loads(f.read())
    
    bcr = str(bcr) if bcr else '01'
    
    p = canvas.Canvas(file_path, A4)
    
    y = 788
    line_1 = {'txt': '%s\n%s\nABN %s' % (data['name'], data['company'], data['abn']), 'size': 14}
    line_2 = {'txt': '%s\n%s\nTel. %s\n%s' % (data['address1'], data['address2'], data['tel'], data['email']), 'size': 12}
    y = draw([line_1, line_2], p, 330, y)

    y = y-12*1.3
    lines = [{'txt': 'Bill to: %s' % to['name'], 'size': 12}]
    if to['address']:
        lines.append({'txt': to['address'], 'size': 12})
    y = draw(lines, p, 78, y)
    
    x = 260
    y = y-12*2.6
    line_1 = {'txt': 'Tax invoice', 'size': 16}
    y = draw([line_1], p, x, y)
    
    y = y+12/0.7
    p.line(x, y, x + p.stringWidth('Tax invoice'), y)

    y = y-12*2.6
    line_1 = {'txt': 'Invoice Number: %s-%s\nDate: %s' % (bcr_code, bcr, today), 'size': 12}
    y = draw([line_1], p, 330, y)
    
    y = y-12*1.3
    line_1 = {'txt': '%s\nAccount number %s' % (bank.name.encode('utf-8'), bank.account.encode('utf-8')), 'size': 12}
    y = draw([line_1], p, 78, y)
    
    if subtotal:
        y = y-12*1.3
        lines = [{'txt': 'Rating: $%s.00 %s' % (general_price, forwhat), 'size': 12}]
        if offer:
            lines.append({'txt': 'Special offer: $%s.00 %s' % (offer, forwhat), 'size': 12})
        y = draw(lines, p, 78, y)
    
    
    y = y-12*1.3

    if times:
        line_1 = {'txt': 'Number of sessions: %s' % numsess, 'size': 12}
        y = draw([line_1], p, 78, y)
    
        y = y-12*2.6
        line_1 = {'txt': 'Time', 'size': 12}
        y = draw([line_1], p, 330, y)
    
    y = y+12/0.8
    line_1 = {'txt': 'Amount', 'size': 12}
    y = draw([line_1], p, 420, y)
    
    line_1 = {'txt': event, 'size': 12}
    draw([line_1], p, 78, y)
    
    if times:
        line_1 = {'txt': '45-60 min', 'size': 12}
        draw([line_1], p, 330, y)
    
    if not offer:
        offer = general_price
        
    line_1 = {'txt': '$%s.00' % offer, 'size': 12}
    y = draw([line_1], p, 420, y)
    
    line_1 = {'txt': 'Total', 'size': 12}
    draw([line_1], p, 78, y)
    
    line_1 = {'txt': '$%s.00' % (offer * numsess), 'size': 12}
    y = draw([line_1], p, 420, y)
    
    if subtotal:
        y = y-12*1.3
        line_1 = {'txt': 'Balance from last time', 'size': 12}
        draw([line_1], p, 78, y)
        
        line_1 = {'txt': '$0.00', 'size': 12}
        y = draw([line_1], p, 420, y)
        
        line_1 = {'txt': 'Subtotal', 'size': 12}
        draw([line_1], p, 78, y)
        
        line_1 = {'txt': '$%s.00' % (offer * numsess), 'size': 12}
        y = draw([line_1], p, 420, y)
    
    y = y-12*2.6
    line_1 = {'txt': 'Please use invoice number as a reference if you pay direct debit.', 'size': 12}
    y = draw([line_1], p, 78, y)
    
    
    if note:
        chars = 70
        note_words = note.split()

        y = y-12*1.3
        line_1 = {'txt': 'Note:', 'size': 12}
        y = draw([line_1], p, 78, y)
        
        words_line = ''
        words_lines = []
        for word in note_words:
            words_line += word + ' '
            if len(words_line) >= 70:
                words_lines.append({'txt': words_line, 'size': 12})
                words_line = ''
    
        if words_line:
            words_lines.append({'txt': words_line, 'size': 12})
            
        y = draw(words_lines, p, 78, y)
            
    p.save()
    
    # 595.27 на 841.89 типографских пункта (1 типографский пункт равен 1/72 дюйма)
    #p.drawString(100,100,"Hello World")

    return file_name


def send_invite_invoice(current_site, checker, invite, invoice, validate, clients, files, tmpl, txt, invrel):
    from letsgetrhythm.ajax import get_bcr_and_bcr_code
    
    log = []
    files_path = []
    
    now = datetime.datetime.now()
    
    froms = {
        'letsgetrhythm.com.au': 'letsgetrhythm@gmail.com',
        'vladaalfimovdesign.com.au': 'vladaalfimov@gmail.com',
        'imiagroup.com.au': 'info@imiagroup.com.au',
    }
    
    efrom = froms.get(current_site.domain, '')
    
    orgs_dict = {}
    orgs = Organization.objects.select_related('domain').filter(uni_slug__in=('vlada-alfimov-design', 'lets-get-rhythm', 'imia-group'))
    for i in orgs:
        orgs_dict[i.domain.domain] = i.email

    if clients:
        data = LetsGetClients.objects.select_related('organization').filter(pk__in=checker)
    else:
        data = LetsGetCalendar.objects.select_related('client', 'client__organization', 'bank').filter(pk__in=checker)
    
    data_count = []
    for i in data:
        client_tag = i.tag if clients else i.client.tag
        data_count.append(client_tag)
    data_count = len(set(data_count))
    
    for i in data:
        org = i.organization if clients else i.client.organization
        client_tag = i.tag if clients else i.client.tag
        client_obj = i if clients else i.client

        if org:
            profile = org.staff.all()
            if profile:
                profile = profile[0]
            org_name = org.name
            org_slug = org.uni_slug
            
        else:
            profile = i.profile if clients else i.client.profile
            org_name = ''
            org_slug = ''
        
        if profile:
            if not clients:
                notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                if notify:
                    notify = notify[0]
                else:
                    notify = LetsGetCalendarNotified.objects.create(event=i, profile=profile)
            
            card = get_usercard(profile.user_id, ucity=False)
            email = None
            if card['email']:
                email = card['email']
            elif not card['email'] and card['emails']:
                profile.user.email = card['emails'][0]
                profile.user.save()
                card['email'] = card['emails'][0]
                email = card['email']
            if not card['email'] and card['emails_not_auth']:
                email = card['emails_not_auth'][0]
            
            client_link = '<a href="/user/profile/%s/" target="_blank">%s</a>' % (card['profile'].user_id, card['name'])
        else:
            if not clients:
                notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                if notify:
                    notify = notify[0]
                else:
                    notify = LetsGetCalendarNotified.objects.create(event=i, organization=org)

        
        use_org_email = False
        if (org and not profile) or (org and profile and not email):
            email = org.email if org.email else None
            client_link = u'<a href="/org/%s/" target="_blank">%s</a>' % (org.uni_slug, org.name)
            use_org_email = True

        if not email:
            log_msg = "Client Does Not Have E-mail Address"
            log.append({'link': client_link, 'email': '', 'status': False, 'msg': log_msg, 'file_name': '', 'org_name': org_name, 'org_slug': org_slug})
            
            LetsGetCalendarClientNotified.objects.get_or_create(
                client = client_obj,
                defaults = {
                    'client': client_obj,
                    'invite_notified': False,
                    'invite_status': log_msg,
                })
                            
            if not clients:
                if invite:
                    notify.invite_notified = False
                    notify.invite_status = log_msg
                    
                else:
                    notify.invoice_notified = False
                    notify.invoice_status = log_msg

        else:
            if '@' not in email:
                log_msg = "Client Has Incorrect E-mail Address"
                log.append({'link': client_link, 'email': email, 'status': False, 'msg': log_msg, 'file_name': '', 'org_name': org_name, 'org_slug': org_slug})
                
                LetsGetCalendarClientNotified.objects.get_or_create(
                    client = client_obj,
                    defaults = {
                        'client': client_obj,
                        'invite_notified': False,
                        'invite_status': log_msg,
                    })
                            
                if not clients:
                    if invite:
                        notify.invite_notified = False
                        notify.invite_status = log_msg
                        notify.invite_dtime = now
                    else:
                        notify.invoice_notified = False
                        notify.invoice_status = log_msg
                        notify.invoice_dtime = now
            else:
                if invite:
                    
                    code = md5_string_generate(email)
                    subject = u'"%s" Invite' % current_site.name
                    
                    if use_org_email:
                        add_to_msg = ''
                        add_to_msgh = ''
                    else:
                        auth_link = u'http://%s/user/login/email/%s/' % (current_site.domain, code) 
                        add_to_msg = u'TO CONFIRM ACCOUNT CLICK HERE: \n%s\n' % auth_link
                        add_to_msgh = u'<h3>To confirm account click here: </h3>\
                        <a href="%s" target="_blank">%s</a><br />' % (auth_link, auth_link)

                        
                    if current_site.domain == 'letsgetrhythm.com.au':
                        file_name = 'letsget'
                    if current_site.domain == 'vladaalfimovdesign.com.au':
                        file_name = 'vlada'
                    elif current_site.domain == 'imiagroup.com.au':
                        file_name = 'imiagroup'
                    
                    
                    if current_site.domain == 'letsgetrhythm.com.au' and client_tag in (u'SCH', u'NH'):
                        tmpl = invrel.get(client_tag)
                        
                        
                    try:
                        text = News.objects.get(pk=tmpl, site=current_site)
                        if text.text != txt and data_count == 1:
                            text.text = txt
                            text.save()
                        text = text.text
                    except News.DoesNotExist:
                        text = ''
                   
                    
                    msg = u"%s\n\n%s" % (text, add_to_msg)
                    
                    msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                        %s <br /><br />%s</div>' % (text, add_to_msgh)
                    
                    mail = EmailMultiAlternatives(subject, msg, efrom, [email.strip()])
                    mail.attach_alternative(msg_html, "text/html")
                    if files:
                        all_files, fpath = getfiles_func(current_site.domain, '', 'private')
                        for i in files:
                            file_data = all_files[int(i)]
                            mail.attach_file(file_data[0])
                            
                    mail.send()
                    
                    log_msg = "Message Has Been Sent Successfully"
                    log.append({'link': client_link, 'email': email, 'status': True, 'msg': log_msg, 'file_name': '', 'org_name': org_name, 'org_slug': org_slug, 'client_id': client_obj.id})
                    
                    LetsGetCalendarClientNotified.objects.get_or_create(
                            client = client_obj,
                            defaults = {
                                'client': client_obj,
                                'invite_notified': True,
                                'invite_status': log_msg,
                            })
                    
                    if not clients:
                        notify.invite_notified = True
                        notify.invite_status = log_msg
                        notify.invite_dtime = now
                    
                    # ------------------------------
                    # копия для Алфимова
                    admin_email = orgs_dict.get(current_site.domain)
                    if admin_email:
                        mail = EmailMultiAlternatives(subject, msg, efrom, [admin_email])
                        mail.attach_alternative(msg_html, "text/html")
                        if files:
                            all_files, fpath = getfiles_func(current_site.domain, '', 'private')
                            for i in files:
                                file_data = all_files[int(i)]
                                mail.attach_file(file_data[0])
                        mail.send()
                    
                    # копия для Иванова
                    mail = EmailMultiAlternatives(subject, msg, efrom, ['kinoafisharu@gmail.com'])
                    mail.attach_alternative(msg_html, "text/html")
                    if files:
                        all_files, fpath = getfiles_func(current_site.domain, '', 'private')
                        for i in files:
                            file_data = all_files[int(i)]
                            mail.attach_file(file_data[0])
                    mail.send()
                    
                    '''
                    # копия для Юры
                    mail = EmailMultiAlternatives(subject, msg, efrom, ['twohothearts@gmail.com'])
                    mail.attach_alternative(msg_html, "text/html")
                    if files:
                        all_files, fpath = getfiles_func(current_site.domain, '', 'private')
                        for i in files:
                            file_data = all_files[int(i)]
                            mail.attach_file(file_data[0])
                    mail.send()
                    '''

                if invoice:
                    if current_site.domain == 'letsgetrhythm.com.au':
                        subject = u'"%s" Invoice' % current_site.name
                        
                        if i.invoice_template:
                            msg = i.invoice_template.text
                        else:
                            msg = News.objects.filter(site=current_site, reader_type='16')
                            msg = msg[0].text if msg else ''

                        msg_clear = BeautifulSoup(msg, from_encoding='utf-8').text.strip()
                        
                        #msg = u'Invoice PDF file has been attached to this e-mail message'
                        msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                            %s <br /><br /></div>' % msg
                        
                        address = ''
                        try:
                            b_all = org.buildings.all()
                            if b_all:
                                building = Building.objects.select_related('city', 'street', 'street__area').get(pk=b_all[0].id)
                                if building.street:
                                    address = u'%s %s %s' % (building.number, building.street.name, building.street.get_type_display())
                                    if building.street.area:
                                        address = u'%s, %s' % (address, building.street.area.name)
                        except Building.DoesNotExist: pass
                        
                        bill_to = {'name': org.name, 'address': address.strip()}
                        event = i.event_name if i.event_name else 'Group Drumming Circle'
                        today = datetime.datetime.today().strftime('%d.%m.%Y')
                        
                        prices = LETS_PRICES
                        price = int(i.price.replace('$','').strip())
                        
                        general_price = prices.get(i.type)
                        offer = general_price
                        
                        if price != general_price:
                            if price > general_price:
                                general_price = price
                            offer = price
                        
                        bcr = str(i.bcr)
                        if len(bcr) == 1:
                            bcr = '0%s' % bcr
                        bcr_code = i.bcr_code
                        
                        file_name = create_pdf(to=bill_to, event=event, today=today, general_price=general_price, offer=offer, domain=current_site.domain, bank=i.bank, note=i.note, bcr=bcr, bcr_code=bcr_code, numsess=i.num_sessions)

                        if validate:
                            log_msg = 'Invoice Ready To Send'
                        else:
                            # отправка письма клиенту
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, [email.strip()])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                            mail.send()

                            log_msg = 'Message Has Been Sent Successfully'

                            notify.invoice_notified = True
                            notify.invoice_status = log_msg
                            notify.invoice_dtime = now
                            
                            i.pdf = file_name
                            i.save()

                            # ----------------------------------
                            # копия Алфимову
                            admin_email = orgs_dict.get(current_site.domain)
                            if admin_email:
                                mail = EmailMultiAlternatives(subject, msg_clear, efrom, [admin_email])
                                mail.attach_alternative(msg_html, "text/html")
                                mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                                mail.send()
                            # копия Иванову
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, ['kinoafisharu@gmail.com'])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                            mail.send()
                            '''
                            # копия Юре
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, ['twohothearts@gmail.com'])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                            mail.send()
                            '''
                        #документация по функции mail.attach_file
                        #import pydoc
                        #open('ddd2.txt', 'a').write(str(pydoc.render_doc(mail.attach_file)))

                        log.append({'link': client_link, 'email': email, 'status': True, 'msg': log_msg, 'file_name': file_name, 'org_name': org_name, 'org_slug': org_slug})
                    else:
                        log_msg = "Invoices Function Is Not Available"
                        log.append({'link': client_link, 'email': email, 'status': True, 'msg': log_msg, 'file_name': '', 'org_name': org_name, 'org_slug': org_slug})
        if not clients:
            notify.save()
    '''
    if not validate:
        for i in os.listdir(settings.INVOICES_TMP):
            try:
                os.remove('%s/%s' % (settings.INVOICES_TMP, i))
            except OSError: pass
    '''
    return log
    

@only_superuser_or_admin
@never_cache
def invoices_list(request):
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    
    if request.POST:
        if 'paid_btn' in request.POST or 'not_paid_btn' in request.POST:
            inv = request.POST.getlist('checker')
            if inv:
                paid = True if 'paid_btn' in request.POST else False 
                LetsGetCalendar.objects.filter(pk__in=inv, site=current_site, subdomain=subdomain).update(paid=paid)
        
            return HttpResponseRedirect(reverse('letsget_invoices_list'))
        else:
            paid_select = request.POST.get('paid_filter')
            if paid_select:
                paid_select = int(paid_select)
            request.session['invoice_list_paid_filter'] = paid_select

    paid_select = request.session.get('invoice_list_paid_filter', 0)

    filter = {'site': current_site}
    if subdomain:
        filter = {'subdomain': subdomain}
    if len(str(paid_select)):
        filter['paid'] = paid_select

    events = []
    for i in LetsGetCalendar.objects.exclude(pdf=None).filter(**filter).order_by('-dtime'):
        prices = LETS_PRICES
        price = int(i.price.replace('$','').strip())
        
        general_price = prices.get(i.type)
        offer = general_price
        
        if price != general_price:
            if price > general_price:
                general_price = price
            offer = price
    
        if not offer:
            offer = general_price

        total = offer * i.num_sessions
    
        events.append({'obj': i, 'total': total})
    
    
    
    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'vsetiinter.net':
        slug = request.subdomain
        site_name = slug
        
    paid_filter = {
        '': 'All',
        0: 'Unpaid',
        1: 'Paid'
    }

    return render_to_response('letsget/invoices_list.html', {'title': 'Invoices List', 'site_name': site_name, 'events': events, 'current_site': current_site, 'slug': slug, 'invoices_path': settings.INVOICES_TMP, 'paid_filter': paid_filter, 'paid_select': paid_select}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def invoice(request):
    import json
    
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    
    if subdomain:
        fname = '%s%s_invoice_data.json' % (subdomain, request.current_site.domain) 
    else:
        fname = '%s_invoice_data.json' % request.current_site.domain
    
    bank_warning = ''
    if request.POST:
        #"bsb": request.POST.get('bsb'),
        #"account_number": request.POST.get('account_number')
        if 'save' in request.POST:
            data = {
                "name": request.POST.get('name'),
                "company": request.POST.get('company'),
                "abn": request.POST.get('abn'),
                "address1": request.POST.get('address1'),
                "address2": request.POST.get('address2'),
                "tel": request.POST.get('tel'),
                "email": request.POST.get('email'),
            }
            with open('%s/%s' % (settings.API_EX_PATH, fname), 'w') as f:
                json.dump(data, f)
                
            return HttpResponseRedirect(request.get_full_path())
        else:
            bank = request.POST.get('bank')
            events = LetsGetCalendar.objects.filter(bank__pk=bank).count()
            if events:
                bank_warning = u'%s Events Have Relationships With The Bank!' % events
            else:
                try:
                    LetsGetBank.objects.get(id=bank, site=current_site, subdomain=subdomain).delete()
                except LetsGetBank.DoesNotExist: pass
            
                return HttpResponseRedirect(request.get_full_path())
    
    banks = LetsGetBank.objects.filter(site=current_site, subdomain=subdomain)

    try:
        with open('%s/%s' % (settings.API_EX_PATH, fname), 'r') as f:
            data = json.loads(f.read())
    except IOError:
        with open('%s/%s' % (settings.API_EX_PATH, fname), 'w') as f:
            data = {
                "tel": "", 
                "name": "", 
                "address1": "", 
                "company": "", 
                "abn": "", 
                "email": "", 
                "address2": "",
                }
            json.dump(data, f)
    
    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain
        site_name = slug
    return render_to_response('letsget/invoice.html', {'title': 'Invoice Data Editor', 'site_name': site_name, 'data': data, 'current_site': current_site, 'slug': slug, 'banks': banks, 'bank_warning': bank_warning}, context_instance=RequestContext(request))
    
    
@only_superuser_or_admin
@never_cache
def calendar_add(request):
    current_site = request.current_site
    subdomain = request.subdomain
    
    
    if request.POST:
        edit = int(request.POST.get('edit'))
        e_name = request.POST.get('event_name')
        e_place = request.POST.get('event_place')
        e_date = request.POST.get('event_date')
        e_time = request.POST.get('event_time')
        e_sms = int(request.POST.get('event_sms', 0))
        e_email = int(request.POST.get('event_email', 0))
        e_ahead_sms = request.POST.get('time_msg_sms')
        e_ahead_email = request.POST.get('time_msg_email')
        e_price = request.POST.get('event_price')
        e_type = request.POST.get('event_type')
        e_bank = request.POST.get('event_bank', 1)
        e_note = request.POST.get('event_invoice_note').strip()
        e_bcr = request.POST.get('event_bcr')
        e_code = request.POST.get('event_code').strip()
        e_numsess = request.POST.get('event_numsess').strip()
        e_invoice_tmpl = request.POST.get('event_invoice_tmpl')
        
        e_bcr = int(e_bcr) if e_bcr else 1
        e_code = e_code if e_code else 'BCR'
        e_numsess = e_numsess if e_numsess else 1

        int(e_price.replace('$',''))

        year, month, day = e_date.split('-')
        try:
            hour, minute = e_time.split(':')
        except ValueError:
            hour, minute = (e_time.replace(':', ''), 0)
        
        dtime = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))

        sms_dtime = ahead_time(e_ahead_sms, dtime)
        email_dtime = ahead_time(e_ahead_email, dtime)

        client = get_object_or_404(LetsGetClients, pk=e_place, site=current_site, subdomain=subdomain)

        bank = LetsGetBank.objects.get(pk=e_bank, site=current_site, subdomain=subdomain)
        
        nsub = subdomain if subdomain else 0
        news = News.objects.get(pk=e_invoice_tmpl, site=current_site, subdomain=nsub)
        
        if edit:
            obj = LetsGetCalendar.objects.get(pk=edit, site=current_site, subdomain=subdomain)
            
            # проверка, есть ли уже такое событие
            try:
                exist_obj = LetsGetCalendar.objects.get(
                    event_name = e_name,
                    site = current_site,
                    subdomain = subdomain,
                    client = client,
                    dtime = dtime,
                    type = e_type,
                )
                if obj == exist_obj:
                    request.session['calendar_event_double'] = False
                    next = True
                else:
                    request.session['calendar_event_double'] = True
                    next = False
            except LetsGetCalendar.DoesNotExist:
                request.session['calendar_event_double'] = False
                next = True
            except LetsGetCalendar.MultipleObjectsReturned:
                request.session['calendar_event_double'] = True
                next = False
            
            if next:
                # проверка, есть ли уже событие с таким же кодом и номером инвойса
                try:
                    obj_tmp = LetsGetCalendar.objects.get(bcr=e_bcr, bcr_code=e_code, site=current_site, subdomain=subdomain, dtime__lte=dtime)
                    if obj == obj_tmp:
                        inv_number_fail = False
                    else:
                        inv_number_fail = True
                except LetsGetCalendar.DoesNotExist:
                    inv_number_fail = False
                except LetsGetCalendar.MultipleObjectsReturned:
                    inv_number_fail = True
                request.session['calendar_inv_number_fail'] = inv_number_fail
                
                if not inv_number_fail:
                    obj.event_name = e_name
                    obj.dtime = dtime
                    obj.sms = e_sms
                    obj.email = e_email
                    obj.start_notify_sms = e_ahead_sms
                    obj.start_notify_email = e_ahead_email
                    obj.start_notify_sms_dtime = sms_dtime
                    obj.start_notify_email_dtime = email_dtime
                    obj.price = e_price
                    obj.type = e_type
                    obj.client = client
                    obj.bank = bank
                    obj.note = e_note
                    obj.bcr = e_bcr
                    obj.bcr_code = e_code
                    obj.num_sessions = e_numsess
                    obj.invoice_template = news
                    obj.auto = False
                    obj.save()
                    
                    
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '9',
                        action = '2',
                        object_id = obj.id,
                        attributes = '',
                        site = current_site,
                    )
        else:
            # проверка, есть ли уже событие с таким же кодом и номером инвойса
            try:
                LetsGetCalendar.objects.get(bcr=e_bcr, bcr_code=e_code, site=current_site, subdomain=subdomain, dtime__lte=dtime)
                inv_number_fail = True
            except LetsGetCalendar.DoesNotExist:
                inv_number_fail = False
            except LetsGetCalendar.MultipleObjectsReturned:
                inv_number_fail = True
            request.session['calendar_inv_number_fail'] = inv_number_fail
            
            if not inv_number_fail:
                obj, obj_created = LetsGetCalendar.objects.get_or_create(
                    event_name = e_name,
                    site = current_site,
                    subdomain = subdomain,
                    client = client,
                    dtime = dtime,
                    type = e_type,
                    defaults = {
                        'event_name': e_name,
                        'dtime': dtime,
                        'sms': e_sms,
                        'email': e_email,
                        'start_notify_sms': e_ahead_sms,
                        'start_notify_email': e_ahead_email,
                        'start_notify_sms_dtime': sms_dtime,
                        'start_notify_email_dtime': email_dtime,
                        'price': e_price,
                        'type': e_type,
                        'site': current_site,
                        'subdomain': subdomain,
                        'client': client,
                        'bank': bank,
                        'note': e_note,
                        'bcr': e_bcr,
                        'bcr_code': e_code,
                        'num_sessions': e_numsess,
                        'invoice_template': news,
                        'auto': False,
                    })
                
                if obj_created:
                    request.session['calendar_event_double'] = False
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '9',
                        action = '1',
                        object_id = obj.id,
                        attributes = '',
                        site = current_site,
                    )
                    
                    org = client.organization
                    if org:
                        profile = client.organization.staff.all()
                        if profile:
                            profile = profile[0]
                    else:
                        profile = client.profile
                    
                    if profile:
                        notify = LetsGetCalendarNotified.objects.filter(event=obj).order_by('-id')
                        if not notify:
                            LetsGetCalendarNotified.objects.create(event=obj, profile=profile)
                    else:
                        notify = LetsGetCalendarNotified.objects.filter(event=obj).order_by('-id')
                        if not notify:
                            LetsGetCalendarNotified.objects.create(event=obj, organization=org)
                else:
                    request.session['calendar_event_double'] = True
                    

                            
        if not inv_number_fail:
            ev = LetsGetCalendar.objects.filter(client=obj.client, dtime__gt=obj.dtime, site=current_site, subdomain=subdomain).exclude(pk=obj.id).order_by('dtime')
            
            cur_bcr = e_bcr
            for i in ev:
                cur_bcr += 1
                i.bcr = cur_bcr
                i.bcr_code = e_code
                i.auto = True
                i.save()
        
    return HttpResponseRedirect(reverse('letsget_calendar'))


@only_superuser_or_admin
@never_cache
def calendar(request):
    title = 'Calendar'
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    
    now = datetime.datetime.now()

    go_to_event = None
    
    if request.POST:
        ev = request.POST.getlist('checker')
        if ev:
            calendar = LetsGetCalendar.objects.select_related('client').filter(pk__in=ev, site=current_site, subdomain=subdomain).order_by('dtime')
            if 'create_copy' in request.POST:
                copies = int(request.POST.get('copies'))
                crange = int(request.POST.get('range'))
                if copies > 0:
                    codes = {}
                    first_date = None
                    for i in calendar:
                        if not first_date:
                            first_date = i.dtime
                            
                        if not codes.get(i.bcr_code):
                            codes[i.bcr_code] = i
                        
                        dtime = None

                        for j in range(copies):
                            if not dtime:
                                dtime = i.dtime
                                
                            dtime = dtime + datetime.timedelta(days=crange)
                            client = i.client
                    
                            try:
                                exist_obj = LetsGetCalendar.objects.get(
                                    site = current_site,
                                    subdomain = subdomain,
                                    dtime = dtime,
                                    type = i.type,
                                    client = client,
                                )
                            except LetsGetCalendar.DoesNotExist:

                                i.pk = None
                                i.dtime = dtime
                                i.pdf = None
                                i.paid = False
                                i.save()

                                ActionsLog.objects.create(
                                    profile = request.profile,
                                    object = '9',
                                    action = '1',
                                    object_id = i.id,
                                    attributes = 'copy',
                                    site = current_site,
                                )
                                
                                org = client.organization
                                if org:
                                    profile = client.organization.staff.all()[0]
                                else:
                                    profile = client.profile
                                
                                notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                                if not notify:
                                    LetsGetCalendarNotified.objects.create(event=i, profile=profile)
                    
                    
                    for k, v in codes.iteritems():

                        cur_bcr = v.bcr
                        
                        for l in LetsGetCalendar.objects.filter(bcr_code=k, dtime__gt=first_date, site=current_site, subdomain=subdomain).order_by('dtime'):
                            cur_bcr += 1
                            l.bcr = cur_bcr
                            l.auto = True
                            l.save()
            
            else:
                codes = {}
                first_date = None
                
                for i in calendar:
                    if not first_date:
                        first_date = i.dtime
                        
                    if not codes.get(i.bcr_code):
                        codes[i.bcr_code] = i.bcr
        
                
                for i in calendar:
                    LetsGetCalendarNotified.objects.filter(event=i).delete()
                    
                    attr_cl = ''
                    if i.client.organization_id:
                        attr_cl = u'Org: %s' % i.client.organization.name
                    elif i.client.profile_id:
                        attr_cl = u'Profile: %s' % i.client.profile.user_id
                        
                    attr = u'%s (%s), %s' % (i.event_name, i.dtime, attr_cl)
                    
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '9',
                        action = '3',
                        object_id = i.id,
                        attributes = attr,
                        site = current_site,
                    )
                    
                    i.delete()
                
                
                for i in codes.keys():
                    prev = LetsGetCalendar.objects.filter(bcr_code=i, dtime__lt=first_date, site=current_site, subdomain=subdomain).order_by('-dtime')
                    cur_bcr = 0
                    if prev and prev[0].bcr:
                        cur_bcr = int(prev[0].bcr)
                    
                    for l in LetsGetCalendar.objects.filter(bcr_code=i, dtime__gt=first_date, site=current_site, subdomain=subdomain).order_by('dtime'):
                        cur_bcr += 1
                        l.bcr = cur_bcr
                        l.auto = True
                        l.save()

            return HttpResponseRedirect(reverse('letsget_calendar'))
            
        else:
            if 'past_filter' in request.POST:
                past_select = request.POST.get('past_filter')
                request.session['calendar_past_filter'] = int(past_select)
    else:
        go_to_event = request.GET.get('ev')
        if go_to_event:
            past_select = 2
            request.session['calendar_past_filter'] = past_select

    past_select = request.session.get('calendar_past_filter', 1)

    if past_select == 1:
        filter = {'site': current_site, 'subdomain': subdomain, 'dtime__gte': now}
        order = 'dtime'
    else:
        filter = {'site': current_site, 'subdomain': subdomain, 'dtime__lt': now}
        order = '-dtime'
    
    all_clients = LetsGetClients.objects.select_related('organization').exclude(organization=None).filter(site=current_site, subdomain=subdomain)

    profiles_tmp = list(Profile.objects.filter(staff_organization__domain=current_site).values('staff_organization', 'user'))
    org_prof = {}
    for i in profiles_tmp:
        org_prof[i['staff_organization']] = i['user']

    users = list(User.objects.filter(pk__in=org_prof.values()))
    profiles_dict = get_usercard(users, ucity=False)
    
    clients_dict = {}
    for i in all_clients:
        name = i.organization.name
        obj_id = i.organization.uni_slug
        prof = org_prof.get(long(i.organization_id))
        card = profiles_dict.get(prof)

        email = None
        contact = ''
        contact_id = ''
        contact_name = ''
        
        if card:
            if card['email']:
                email = card['email']
            elif not card['email'] and card['emails']:
                card['profile'].user.email = card['emails'][0]
                card['profile'].user.save()
                card['email'] = card['emails'][0]
                email = card['email']
            if not card['email'] and card['emails_not_auth']:
                email = card['emails_not_auth'][0]
    
            if card['profile'].phone:
                contact += card['profile'].phone
                
            if email:
                if contact:
                     contact += '\n'
                contact += email
            
            contact_name = card['name']
            
            contact_id = card['profile'].user_id
        
        clients_dict[i.id] = {'id': i.id, 'name': name, 'obj_id': obj_id, 'type': 'org', 'contact': contact_name, 'contact_id': contact_id, 'contact_info': contact, 'org_email': i.organization.email}
    
    events_list = []
    for i in LetsGetCalendar.objects.select_related('client', 'client__organization').filter(**filter).order_by(order):
        past = True if i.dtime < now else False
        client = clients_dict.get(i.client_id)
        
        prices = LETS_PRICES
        price = int(i.price.replace('$','').strip())
        
        general_price = prices.get(i.type)
        offer = general_price
        
        if price != general_price:
            if price > general_price:
                general_price = price
            offer = price
        
        events_list.append({'obj': i, 'member': client, 'past': past, 'price': i.price, 'total_price': '$%s' % (offer * i.num_sessions)})
    
    all_clients = sorted(clients_dict.values(), key=operator.itemgetter('name'))

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        template = 'letsget/calendar.html'
    elif current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
        slug = 'vlada-alfimov-design'
        template = 'vladaalfimov/calendar.html'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain
        site_name = slug
        template = 'letsget/calendar.html'
    
    past_filter = {
        1: 'Future Events',
        2: 'Previous Events',
    }

    banks = LetsGetBank.objects.filter(site=current_site, subdomain=subdomain)

    event_double = request.session.get('calendar_event_double')
    if event_double:
        request.session['calendar_event_double'] = False

    inv_number_fail = request.session.get('calendar_inv_number_fail')
    if inv_number_fail:
        request.session['calendar_inv_number_fail'] = False

    invoice_tmp = []
    if not subdomain:
        subdomain = 0
    for i in News.objects.filter(site=current_site, subdomain=subdomain, reader_type='16'):
        invoice_tmp.append({'id': i.id, 'title': i.title})

    return render_to_response(template, {'title': title, 'site_name': site_name, 'events': events_list, 'all_clients': all_clients, 'time_msg': TIME_MSG_CHOICES, 'events_type': LETSGET_EVENTS_TYPE, 'current_site': current_site, 'slug': slug, 'past_filter': past_filter, 'past_select': past_select, 'banks': banks, 'event_double': event_double, 'invoice_tmp': invoice_tmp, 'go_to_event': go_to_event, 'inv_number_fail': inv_number_fail}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def upload_images(request):
    title = 'Upload Images'
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name
    
    if current_site.domain == 'vladaalfimovdesign.com.au':
        folder = 'vlada_imgs'
    elif current_site.domain == 'letsgetrhythm.com.au':
        folder = 'letsget'
    elif current_site.domain == 'imiagroup.com.au':
        folder = 'imiagroup'
    elif current_site.domain == 'vsetiinter.net':
        folder = subdomain
        site_name = subdomain
    
    
    files = []
    try:
        for f in os.listdir('%s/%s' % (settings.GALLERY_PATH, folder)):
            if os.path.isfile('%s/%s/%s' % (settings.GALLERY_PATH, folder, f)):
                files.append(('%s/%s/%s' % (settings.GALLERY_FOLDER, folder, f), f, f.split('.')[0][:10]))
    except OSError: pass
    
    if request.POST:
        if 'slides' in request.FILES:
            img_path = '%s/%s' % (settings.GALLERY_PATH, folder)
            try: os.makedirs(img_path)
            except OSError: pass

            try:
                if 'slides' in request.FILES:
                    form = OrganizationImageSlideUploadForm(request.POST, request.FILES)
                    
                    if form.is_valid():
                        files = request.FILES.getlist('slides')

                        for i in files:
                            file_format = low(i.name)
                            img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif)$', file_format)
                            if img_format:
                                img_obj = i.read()
                                img_name = '%s.%s' % (md5_string_generate(randrange(9999)), img_format[0])
                                img_path_tmp = '%s/%s' % (img_path, img_name)

                                with open(img_path_tmp, 'wb') as f:
                                    f.write(img_obj)

                                resized = resize_image(1000, None, img_obj, 1500)
                                if resized:
                                    resized.save(img_path_tmp)

                                img_name_tmp = '%s/%s/%s' % (settings.GALLERY_FOLDER, folder, img_name)
                                img_object = Images.objects.create(file=img_name_tmp, status=1)

                        return HttpResponseRedirect(reverse("letsget_upload_images"))
            except IOError:
                open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write('*** ' + str(request.FILES.getlist('slides')) + '\n')
    
    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        template = 'letsget/upload_images.html'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
        template = 'vladaalfimov/upload_images.html'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        template = 'vladaalfimov/upload_images.html'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain
        template = 'letsget/upload_images.html'
        
    return render_to_response(template, {'title': title, 'site_name': site_name, 'files': files, 'current_site': current_site, 'slug': slug}, context_instance=RequestContext(request))


def getfiles_func(domain, subdomain, folder):
    if subdomain:
        domain = '%s.%s' % (subdomain, domain)
    tmp = u'%s/%s' % (settings.MEDIA_ROOT, domain)
    try: os.makedirs(tmp)
    except OSError: pass
    
    path = u'%s/%s' % (tmp, folder)
    try: os.makedirs(path)
    except OSError: pass
    
    files = []
    for f in os.listdir(path):
        if os.path.isfile(u'%s/%s' % (path, f)):
            files.append((u'%s/%s' % (path, f), f))
    
    return files, path

@only_superuser_or_admin
@never_cache
def upload_files(request):
    title = 'Upload Files'
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name

    files, path_private = getfiles_func(current_site.domain, subdomain, 'private')
    
    if request.POST:
        if 'file_add' in request.POST:
            files = request.FILES.getlist('files')
            for i in files:
                obj = i.read()
                name = unidecode(i.name).split()
                name = '_'.join(name)
                with open(u'%s/%s' % (path_private, name), 'wb') as f:
                    f.write(obj)
        
        if 'delfile' in request.POST:
            checker = request.POST.getlist('checker')
            for i in checker:
                file_data = files[int(i)]
                try: os.remove(file_data[0])
                except OSError: pass

        
        return HttpResponseRedirect(reverse("letsget_upload_files"))


    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        template = 'letsget/upload_files.html'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain
        site_name = subdomain
        template = 'letsget/upload_files.html'
    '''
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
        template = 'vladaalfimov/upload_images.html'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        template = 'vladaalfimov/upload_images.html'
    '''
    return render_to_response(template, {'title': title, 'site_name': site_name, 'files': files, 'current_site': current_site, 'slug': slug}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def letsget_inv_templates(request, itype, id=None):
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    
    if current_site.domain == 'letsgetrhythm.com.au':
        template = 'vladaalfimov/main.html'
        extend_template = 'base.html'
    elif current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
        template = 'vladaalfimov/main_new.html'
        extend_template = 'base_vlada.html'
    elif current_site.domain == 'vsetiinter.net':
        template = 'vladaalfimov/main.html'
        extend_template = 'base.html'
    
    access = True if request.user.is_superuser or request.is_admin else False
    
    data = view_func(request, None, id, itype, access)
    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())

    data['extend_template'] = extend_template
    data['itype'] = itype
    
    return render_to_response(template, data, context_instance=RequestContext(request))

@never_cache
def view_inv_del(request, id, itype):
    if request.POST:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            if not subdomain:
                subdomain = 0
            
            inv_t = {
                'invite': '15',
                'invoice': '16',
            }
            type_obj = inv_t.get(type)
            news = News.objects.get(pk=id, reader_type=type_obj, site=current_site, subdomain=subdomain).delete()
            return HttpResponseRedirect(reverse('letsget_%s_template' % type))
    raise Http404



@only_superuser_or_admin
@never_cache
def letsget_inv_template(request, itype):
    title = 'Template %s Message' % itype.capitalize()
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        fname = 'letsget'
        template = 'letsget/invite.html'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
        fname = 'vlada'
        template = 'vladaalfimov/invite.html'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        fname = 'imiagroup'
        template = 'vladaalfimov/invite.html'
    if current_site.domain == 'vsetiinter.net':
        site_name = subdomain
        slug = subdomain
        fname = '%s%s' % (subdomain, current_site.domain)
        template = 'letsget/invite.html'
        
        
    try:
        with open('%s/%s_%s_text.txt' % (settings.API_EX_PATH, fname, itype),'r') as f:
            content = f.read()
    except IOError:
        open('%s/%s_%s_text.txt' % (settings.API_EX_PATH, fname, itype),'w')
        content = ''
        
    if request.POST:
        form = OrganizationInviteTextForm(request.POST)
        if form.is_valid():
            content = request.POST['text'].encode('utf-8')
            with open('%s/%s_%s_text.txt' % (settings.API_EX_PATH, fname, itype),'w') as f:
                f.write(content)
            return HttpResponseRedirect(reverse('letsget_%s_template' % itype))

    return render_to_response(template, {'title': title, 'site_name': site_name, 'clients': clients, 'content': content, 'example': content, 'current_site': current_site, 'slug': slug, 'itype': itype}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def orgs(request, id):
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name
    
    if current_site.domain == 'vsetiinter.net':
        site_name = subdomain
    
    data = org(request, id, offers=True, area=True)
    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())
    else:
        data['title'] = data['org'].name
        data['current_site'] = current_site
        data['site_name'] = site_name
        return render_to_response('letsget/orgs.html', data, context_instance=RequestContext(request))

@only_superuser_or_admin
@never_cache
def org_staff(request, id):
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name
    
    if current_site.domain == 'vsetiinter.net':
        site_name = subdomain
        
    org = get_object_or_404(Organization, uni_slug=id)
    staff = org_peoples(org.staff.all())
    is_editor = is_editor_func(request, org)

    return render_to_response('letsget/org_staff.html', {'org': org, 'site_name': site_name, 'current_site': current_site, 'staff': staff, 'is_editor': is_editor}, context_instance=RequestContext(request))
        


def off_and_adv(request, id, slug, flag):
    current_site = request.current_site
    subdomain = request.subdomain
    site_name = current_site.name
    
    
    if current_site.domain == 'vsetiinter.net':
        site_name = subdomain
    
    tag_rel = get_object_or_404(Organization_Tags, pk=id, organization__uni_slug=slug, organizationtags__group_flag=flag)
    
    if flag == '4':
        reader_type = '12'
        tag = 'спрос'
        title = "I'm Looking For"
    else:
        reader_type = '11'
        tag = 'предложение'
        title = "My Offers"
        
    try:
        org_news = OrganizationNews.objects.select_related('news').get(tag=tag_rel)
        post = org_news.news
        init = {
            'title': post.title,
            'text': post.text,
            'visible': post.visible,
        }
    except OrganizationNews.DoesNotExist:
        post = None
        init={}
        
    if request.POST:
        org = Organization.objects.get(uni_slug=slug)
        is_editor = is_editor_func(request, org)
        if request.user.is_superuser or request.is_admin or is_editor:
            form = LetsGetNewsForm(request.POST)
            if form.is_valid():
                title = form.cleaned_data['title']
                text = form.cleaned_data['text']
                if post:
                    post.title = title
                    post.text = text
                    post.visible = form.cleaned_data['visible']
                    post.reader_type = reader_type
                    post.save()
                else:
                    post = create_news(request, [tag], title, text, reader_type)
                    OrganizationNews.objects.create(organization=org, news=post, tag=tag_rel)
                    
                return 'redirect'
            
    form = LetsGetNewsForm(initial=init)
    return {'title': title, 'site_name': site_name, 'form': form, 'post': post, 'current_site': current_site}
    

@never_cache
def org_offers_and_adv(request, id, iid, flag):
    org = get_object_or_404(Organization, uni_slug=id)
    data = off_and_adv(request, iid, org.uni_slug, flag)
    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())
    is_editor = is_editor_func(request, org)
    data['org'] = org
    data['is_editor'] = is_editor
    data['title'] = u'%s - %s' % (org.name, data['title'])
    return render_to_response('letsget/seek.html', data, context_instance=RequestContext(request))


@never_cache
def offers_and_adv(request, id, slug, flag):
    data = off_and_adv(request, id, slug, flag)
    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())
    return render_to_response('letsget/seek.html', data, context_instance=RequestContext(request))
 


def event_email_send(event, email, efrom, data):

    if event.subdomain:
        title = u'"%s.%s" Event' % (event.subdomain, event.site.domain)
    else:
        title = u'"%s" Event' % event.site.name

    org = event.client.organization
    place = org.name if org else ''
    
    event_time = event.dtime.strftime('%d/%m/%Y at %I:%M %p')

    msg = u'Dear customer! This is just a reminder about "%s" entertainment %s\n\nKind Regards,\n%s\n%s\nMob.%s\n%s\n%s\
    ' % (event.site.name, event_time, data['name'], data['company'], data['tel'], data['email'], data['site'])
            
    msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
        Dear customer! This is just a reminder about "%s" entertainment %s<br /><br />Kind Regards,<br />%s<br />%s<br />Mob.%s<br />%s<br />%s\
        </div>' % (event.site.name, event_time, data['name'], data['company'], data['tel'], data['email'], data['site'])

    mail = EmailMultiAlternatives(title, msg, efrom, [email.strip()])
    mail.attach_alternative(msg_html, "text/html")
    mail.send()
    

#@only_superuser_or_admin
#@never_cache
def events_msg_sender():
        
    now = datetime.datetime.now()
    now_date = now.date()
    now = now.replace(microsecond=0).replace(second=0)
    past = now - datetime.timedelta(minutes=3)

    events = LetsGetCalendar.objects.select_related('site', 'client', 'client__organization', 'client__profile').filter(start_notify_email_dtime__gte=past, start_notify_email_dtime__lte=now)
    
    froms = {
        'letsgetrhythm.com.au': 'letsgetrhythm@gmail.com',
        'vladaalfimovdesign.com.au': 'vladaalfimov@gmail.com',
        'imiagroup.com.au': 'info@imiagroup.com.au',
    }
    
    orgs_dict = {}
    if events:
        orgs = Organization.objects.select_related('domain').filter(uni_slug__in=('vlada-alfimov-design', 'lets-get-rhythm', 'imia-group'))
        for i in orgs:
            orgs_dict[i.domain.domain] = i.email

    for i in events:
        if i.email:
            profile = None
            org = i.client.organization
            if org:
                profile = org.staff.all()
                if profile:
                    profile = profile[0]
            else:
                profile = i.client.profile
            
            if profile:
                card = get_usercard(profile.user)
                
                email = None
                
                if card['email']:
                    email = card['email']
                elif not card['email'] and card['emails']:
                    profile.user.email = card['emails'][0]
                    profile.user.save()
                    card['email'] = card['emails'][0]
                    email = card['email']
                
                if not card['email'] and card['emails_not_auth']:
                    email = card['emails_not_auth'][0]
                

                notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                if notify:
                    notify = notify[0]
                else:
                    notify = LetsGetCalendarNotified.objects.create(event=i, profile=profile)

            else:
                if org:
                    notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                    if notify:
                        notify = notify[0]
                    else:
                        notify = LetsGetCalendarNotified.objects.create(event=i, organization=org)

                    
            if (org and not profile) or (org and profile and not email):
                email = org.email if org.email else None
            
            if email:
                if '@' in email:
                    efrom = froms.get(i.site.domain, '')
                
                    with open('%s/%s_invoice_data.json' % (settings.API_EX_PATH, i.site.domain), 'r') as f:
                        data = json.loads(f.read())
                
                    data['site'] = i.site.domain
                    
                    # отправляем письмо клиенту
                    event_email_send(i, email, efrom, data)
                    notify.email_notified = True
                    notify.email_status = "Message Has Been Sent Successfully"
                    
                    # -----------------------------------------
                    # копия для Алфимова
                    admin_email = orgs_dict.get(i.site.domain)
                    if admin_email:
                        event_email_send(i, admin_email, efrom, data)
                        
                    # копия для Иванова
                    event_email_send(i, 'kinoafisharu@gmail.com', efrom, data)
                    
                    # копия для Юры
                    #event_email_send(i, 'twohothearts@gmail.com', efrom, data)

                else:
                    notify.email_status = "Client Had An Incorrect E-mail Address"
            else:
                notify.email_status = "Client Didn't Have E-mail Address"
            
            notify.email_dtime = datetime.datetime.now()
            notify.save()
        
        
        if i.sms:
            for j in i.client.organization.staff.all():
                phone = j.phone
                
                notify = LetsGetCalendarNotified.objects.filter(event=i).order_by('-id')
                if notify:
                    notify = notify[0]
                else:
                    notify = LetsGetCalendarNotified.objects.create(event=i, profile=j)

                
                if phone:
                    phone = phone.replace(' ','').replace('(','').replace(')','').replace('-','')
                    phone = phone.replace('+610','61') # для австралийских номеров
                    phone = phone.replace('+', '')
                    
                    sms_text = u'%s - %s' % (i.dtime, i.client.organization.name)
                    
                    result = clickatell_send_sms(phone, sms_text)

                    notify.sms_id = None
                    if 'ID:' in result:
                        notify.sms_id = result.replace('ID: ','')
                    else:
                        notify.sms_status = result  
                else:
                    notify.sms_status = "Client Didn't Have Phone Number"
                
                notify.sms_dtime = datetime.datetime.now()
                notify.save()
    
    return HttpResponse(str())


def letsget_report_create(event_obj, org, address, event_name, efrom, admin_email):
    
    if not event_obj.report:
    
        blog_submenu = OrgSubMenu.objects.get(orgmenu__organization__uni_slug='lets-get-rhythm', orgmenu__name='About Us', name='My Blog', page_type='1')
        
        dtime = event_obj.dtime
        dtime_txt = dtime.strftime('%d/%m/%Y at %I:%M %p')
        
        title = u'%s. %s' % (event_name, org)
        post_txt = u'<p>%s passed "%s" event. </p><p>Place: %s %s</p>' % (dtime_txt, event_name, org, address)
        

        subdomain = event_obj.subdomain if event_obj.subdomain else 0
    
        report = News.objects.create(
            title = title, 
            autor = None,
            site = event_obj.site,
            subdomain = 0,
            text = post_txt,
            visible = True,
            reader_type = None,
        )
        
        report.dtime = dtime
        report.save()

        event_obj.report = report
        event_obj.save()
        
        blog_submenu.news.add(report)
        
        
        if admin_email:
            if event_obj.subdomain:
                site = u'%s.%s' % (event_obj.subdomain, event_obj.site.domain)
            else:
                site = event_obj.site.domain
        
            url = u'http://%s/view/%s/post/%s/' % (site, blog_submenu.id, report.id)
        
            subject = u'Create Event Report'
            msg_txt = u'%s passed "%s" event. Follow this link to create a report about it' % (dtime_txt, event_name)
            
            msg_clear = u'%s %s' % (msg_txt, url)
            msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">%s <a href="%s">%s</a><br /><br /></div>' % (msg_txt, url, url)
        
            mail = EmailMultiAlternatives(subject, msg_clear, efrom, [admin_email])
            mail.attach_alternative(msg_html, "text/html")
            mail.send()
            
            # копия Иванову
            subject = u'%s [COPY]' % subject
            mail = EmailMultiAlternatives(subject, msg_clear, efrom, ['kinoafisharu@gmail.com'])
            mail.attach_alternative(msg_html, "text/html")
            mail.send()



def invoice_msg_sender():
        
    now = datetime.datetime.now()
    now_date = now.date()
    now = now.replace(microsecond=0).replace(second=0)
    past = now - datetime.timedelta(days=3)
    
    events = LetsGetCalendarNotified.objects.select_related('event', 'event__site', 'event__client', 'event__client__organization', 'event__client__profile').filter(event__dtime__gte=past, event__dtime__lte=now, invoice_notified=False)
    
    froms = {
        'letsgetrhythm.com.au': 'letsgetrhythm@gmail.com',
        'vladaalfimovdesign.com.au': 'vladaalfimov@gmail.com',
        'imiagroup.com.au': 'info@imiagroup.com.au',
    }
    
    orgs_dict = {}
    if events:
        orgs = Organization.objects.select_related('domain').filter(uni_slug__in=('vlada-alfimov-design', 'lets-get-rhythm', 'imia-group'))
        for i in orgs:
            orgs_dict[i.domain.domain] = i.email

    for i in events:
        
        profile = None
        org = i.event.client.organization
        if org:
            profile = org.staff.all()
            if profile:
                profile = profile[0]
        else:
            profile = i.event.client.profile
        
        if profile:
            card = get_usercard(profile.user)
            
            email = None
            
            if card['email']:
                email = card['email']
            elif not card['email'] and card['emails']:
                profile.user.email = card['emails'][0]
                profile.user.save()
                card['email'] = card['emails'][0]
                email = card['email']
            
            if not card['email'] and card['emails_not_auth']:
                email = card['emails_not_auth'][0]

                
        if (org and not profile) or (org and profile and not email):
            email = org.email if org.email else None
        
        current_site = i.event.site
        if current_site.domain == 'letsgetrhythm.com.au':
        
            if email:
                
                if '@' in email:

                    efrom = froms.get(current_site.domain, '')

                    subject = u'"%s" Invoice' % current_site.name
                     
                    msg = i.event.invoice_template.text if i.event.invoice_template else ''
                    
                    if i.event.invoice_template:
                        msg = i.event.invoice_template.text
                    else:
                        msg = News.objects.filter(site=current_site, reader_type='16')
                        msg = msg[0].text if msg else ''
                            
                    msg_clear = BeautifulSoup(msg, from_encoding='utf-8').text.strip()

                    msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                        %s <br /><br /></div>' % msg
                    
                    address = ''
                    try:
                        b_all = org.buildings.all()
                        if b_all:
                            building = Building.objects.select_related('city', 'street', 'street__area').get(pk=b_all[0].id)
                            if building.street:
                                address = u'%s %s %s' % (building.number, building.street.name, building.street.get_type_display())
                                if building.street.area:
                                    address = u'%s, %s' % (address, building.street.area.name)
                    except Building.DoesNotExist: pass
                    
                    bill_to = {'name': org.name, 'address': address.strip()}
                    event = i.event.event_name if i.event.event_name else 'Group Drumming Circle'
                    
                    admin_email = orgs_dict.get(current_site.domain)
                    
                    letsget_report_create(i.event, org.name, address.strip(), event, efrom, admin_email)
                    
                    
                    today = datetime.datetime.today().strftime('%d.%m.%Y')
                    
                    prices = LETS_PRICES
                    price = int(i.event.price.replace('$','').strip())
                    
                    general_price = prices.get(i.event.type)
                    offer = general_price
                    
                    if price != general_price:
                        if price > general_price:
                            general_price = price
                        offer = price
                    
                    bcr = str(i.event.bcr)
                    if len(bcr) == 1:
                        bcr = '0%s' % bcr
                    bcr_code = i.event.bcr_code
                    
                    file_name = create_pdf(to=bill_to, event=event, today=today, general_price=general_price, offer=offer, domain=current_site.domain, bank=i.event.bank, note=i.event.note, bcr=bcr, bcr_code=bcr_code, numsess=i.event.num_sessions)

                    # отправка письма клиенту
                    mail = EmailMultiAlternatives(subject, msg_clear, efrom, [email.strip()])
                    mail.attach_alternative(msg_html, "text/html")
                    mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                    mail.send()

                    log_msg = 'Message Has Been Sent Successfully'

                    i.invoice_notified = True
                    i.invoice_status = log_msg
                    i.invoice_dtime = datetime.datetime.now()
                    
                    i.event.pdf = file_name
                    i.event.save()

                    # ------------------------------------------------
                    
                    msg_clear_copy = u'ЭТО КОПИЯ ПИСЬМА ИЗ АВТОРАССЫЛКИ! %s' % msg_clear
                    msg_html_copy = u'<b>Это копия письма из авторассылки!</b><br />. %s' % msg_html
                    # копия Алфимову
                    if admin_email:
                        mail = EmailMultiAlternatives(subject, msg_clear_copy, efrom, [admin_email])
                        mail.attach_alternative(msg_html_copy, "text/html")
                        mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                        mail.send()
                    # копия Иванову
                    mail = EmailMultiAlternatives(subject, msg_clear_copy, efrom, ['kinoafisharu@gmail.com'])
                    mail.attach_alternative(msg_html_copy, "text/html")
                    mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                    mail.send()
                    '''
                    # копия Юре
                    mail = EmailMultiAlternatives(subject, msg_clear_copy, efrom, ['twohothearts@gmail.com'])
                    mail.attach_alternative(msg_html_copy, "text/html")
                    mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
                    mail.send()
                    '''
                else:
                    i.invoice_status = "Client Had An Incorrect E-mail Address"
            else:
                i.invoice_status = "Client Didn't Have E-mail Address"

        i.save()
    #return HttpResponse(str())


@only_superuser_or_admin
@never_cache
def comment_delete(request):
    if request.POST:
        current_site = request.current_site
        subdomain = request.subdomain
        if not subdomain:
            subdomain = 0
        comment = request.POST.get('comment_id')
        News.objects.filter(pk=comment, site=current_site, subdomain=subdomain, reader_type='10').delete()
        ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
        return HttpResponseRedirect(ref)
    raise Http404



@only_superuser_or_admin
@never_cache
def admin_actions(request):
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    title = 'Actions List'

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
    elif current_site.domain == 'vsetiinter.net':
        slug = subdomain

    groups = []
    for i in ACTION_OBJ_CHOICES:
        if i[0] not in ['0', '2', '3']:
            groups.append(i)
    
    group = None
    if request.POST:
        group = request.POST.get('group')
        
    if not group:
        group = request.session.get('filter_admin_actions__group', '1')
        
    request.session['filter_admin_actions__group'] = group

    actions = ActionsLog.objects.select_related('profile').filter(object=group, site=current_site)

    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, actions, 50)

    objs_ids = set([i.object_id for i in p.object_list])
    
    objs = {}
    if group == '1':
        for i in Organization.objects.filter(pk__in=objs_ids):
            objs[i.id] = {'name': i.name, 'slug': i.uni_slug}
    elif group == '4':
        for i in OrgMenu.objects.filter(pk__in=objs_ids):
            objs[i.id] = {'name': i.name, 'slug': ''}
    elif group == '5':
        for i in OrgSubMenu.objects.filter(pk__in=objs_ids):
            objs[i.id] = {'name': i.name, 'slug': ''}
    elif group == '6':
        for i in News.objects.filter(pk__in=objs_ids):
            objs[i.id] = {'name': i.title, 'slug': ''}
    elif group == '7':
        pass
    elif group == '9':
        for i in LetsGetCalendar.objects.filter(pk__in=objs_ids):
            objs[i.id] = {'name': u'%s (%s)' % (i.event_name, i.dtime), 'slug': ''}
    elif group == '10':
        for i in LetsGetClients.objects.filter(pk__in=objs_ids):
            attr_cl = ''
            if i.organization_id:
                attr_cl = u'Org: %s' % i.organization.name
            elif i.profile_id:
                attr_cl = u'Profile: %s' % i.profile.user_id
            objs[i.id] = {'name': attr_cl, 'slug': ''}
            
    log = []
    for i in p.object_list:
        obj_data = objs.get(i.object_id)
        if obj_data:
            log.append({'obj': i, 'dtime': i.dtime, 'name': obj_data['name'], 'slug': obj_data['slug']})
        else:
            log.append({'obj': i, 'dtime': i.dtime, 'name': i.attributes, 'slug': ''})
        
    if log:
        log = sorted(log, key=operator.itemgetter('dtime'), reverse=True)
    
    return render_to_response('letsget/admin_actions.html', {'p': p, 'page': page, 'groups': groups, 'group': group, 'site_name': site_name, 'title': title, 'slug': slug, 'log': log}, context_instance=RequestContext(request))



######################
@only_superuser_or_admin
@never_cache
def lets_img_auto_size(request):
    folders = ('vlada_imgs', 'vlada', 'letsget', 'letsget_gallery', 'imiagroup')

    for folder in folders:
        try:
            for f in os.listdir('%s/%s' % (settings.GALLERY_PATH, folder)):
                if os.path.isfile('%s/%s/%s' % (settings.GALLERY_PATH, folder, f)):
                    path = '%s%s/%s/%s' % (settings.MEDIA_ROOT, settings.GALLERY_FOLDER, folder, f)
                    
                    with open(path, 'r') as img_obj:
                        img_obj = img_obj.read() 

                    resized = resize_image(1000, None, img_obj, 1500)
                    if resized:
                        resized.save(path)
                    
        except OSError: pass

    
    return HttpResponse(str('OK'))



@only_superuser_or_admin
@never_cache
def test_pdf(request):
    to = {'name': 'Test Org', 'address': ''}
    event = 'Event Name'
    today = datetime.datetime.today()
    general_price = '150'
    offer = False
    create_pdf(to, event, today, general_price, offer)
    return HttpResponse(str())



