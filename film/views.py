#-*- coding: utf-8 -*- 
import re
import datetime
import time
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import date as tmp_date
from django.db.models import Q
from django import db

from bs4 import BeautifulSoup

from api.models import *
from api.views import film_poster, film_poster2, get_film_data
from api.func import age_limits, get_client_ip, get_country_by_ip
from base.models import *
from kinoinfo_folder.func import low, del_separator

from release_parser.func import get_imdb_id, actions_logger
from release_parser.decors import timer
from user_registration.func import *
from user_registration.views import get_usercard
from user_registration.ajax import bpost_comments_gen
from movie_online.IR import check_int_rates
from release_parser.kinoafisha_admin import identification_info
from news.views import cut_description, create_news


def get_youtube_video_player(video, width, height):
    video_id = ''
    code = None

    if video and 'youtu' in video:
        video = strip_tags(video)

    if 'www.youtube.com' in video:
        if 'www.youtube.com/embed/' in video:
            video_id = video.split('/embed/')[1]
        else:
            try:
                video_id = video.split('?v=')[1]
                video_id = video_id.split('&')[0]
            except IndexError:
                try:
                    video_id = video.split('/v/')[1]
                    video_id = video_id.split('?')[0]
                except IndexError:
                    try:
                        video_id = video.split('&v=')[1]
                        video_id = video_id.split('&')[0]
                    except IndexError: pass
    elif 'youtu.be/' in video:
        video_id = video.split('//youtu.be/')[1]

    if video_id:
        video_id = video_id.replace("'", '').replace('"', '').replace('=', '')
        code = '<iframe width="%s" height="%s" src="//www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % (width, height, video_id)

    return code


def films_name_create(film_obj, name, ntype, status, slug):
    name_obj, name_created = FilmsName.objects.using('afisha').get_or_create(
        film_id=film_obj,
        name=name.strip(),
        type=ntype,
        status=status,
        slug=slug,
        defaults={
            'film_id': film_obj,
            'name': name.strip(),
            'type': ntype,
            'status': status,
            'slug': slug,
            'hide': '',
        })
    return name_obj, name_created

def film_menu(film):
    #film_ext = FilmExtData.objects.using('afisha').only('rate', 'vnum').get(pk=film.id)
    #frate = film_ext.rate if film_ext.rate else '0,0'
    #fnum = film_ext.vnum

    #reviews = AfishaNews.objects.using('afisha').filter(type=2, object_type=1, obj__id=film.id).count()
    
    opinions = NewsFilms.objects.filter(kid=film.id, message__visible=True).exclude(Q(message__text=None) | Q(message__text='')).count()

    topics = SourceFilms.objects.filter(source_obj__url="http://rutracker.org/").count()

    data = {
        #'rating': {'fvotes': fnum, 'frate': frate, 'imdb_rate': film.imdb, 'imdb_votes': film.imdb_votes},
        #'reviews': {'count': reviews},
        'opinions': {'count': opinions},
        #'web': {'nowru': nowru, 'megogo':  megogo, 'codes': codes},
        'download': {'count': topics},
    }
    
    return data
    

def get_names_and_film_obj(id):
    try:
        film = Film.objects.using('afisha').only("id", "idalldvd", "year", "imdb", "imdb_votes").get(pk=id)
    except Film.DoesNotExist:
        return False, False, False
    
    # названия фильма
    name_ru = ''
    name_en = ''
    for i in film.filmsname_set.all():
        if i.status == 1:
            if i.type == 1:
                name_en = i.name.strip()
            elif i.type == 2:
                name_ru = i.name.strip()
    if not name_ru:
        name_ru = name_en
    if not name_en:
        name_en = name_ru
        
    return film, name_ru, name_en


def get_film_func(request, id):
    timer = time.time()

    from release_parser.ajax import get_film_likes
    from user_registration.ajax import get_subscription_status

    
    if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
        cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])


    is_cached = cache.get('get_film__%s' % id, 'nocaсhed')

    if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
        cached_page = False
        film = get_film_data(id)
        if not film:
            raise Http404
        cache.set('get_film__%s' % id, film, 60*60*24)
    else:
        film = is_cached
        cached_page = True

    film_editor = is_film_editor(request)
    
        
    if request.POST:
        if film_editor:
            if 'note' in request.POST:
                note = request.POST.get('note', False)
                if note != False:
                    note = note.replace('<br />','\n').replace('<br >','\n').replace('<br>','\n')
                    note = BeautifulSoup(note, from_encoding='utf-8').text.strip()
                    
                    act = None
                    if film['object'].description:
                        if note != film['object'].description:
                            act = '2' if note else '3'
                    else:
                        if note:
                            act = '1'
                    
                    actions_logger(7, id, request.profile, act) # фильм Описание
                    
                    film['object'].description = note
                    film['object'].save()
            
            if 'note2' in request.POST:
                note2 = request.POST.get('note2', False)
                if note2 != False:
                    note2 = BeautifulSoup(note2, from_encoding='utf-8').text.strip()
                    
                    act = None
                    if film['object'].comment:
                        if note2 != film['object'].comment:
                            act = '2' if note2 else '3'
                    else:
                        if note2:
                            act = '1'
                            
                    actions_logger(27, id, request.profile, act) # фильм Примечание
                    
                    film['object'].comment = note2
                    film['object'].save()
            
            if 'trailer' in request.POST:
                video = request.POST.get('trailer')
                video_kid = request.POST.get('trailer_id')
                act = None
                
                code = get_youtube_video_player(video, width=560, height=349)

                #if video_kid == u'None':
                if code:
                    trailer_date = datetime.datetime.now().date()
                    last_trailer = TrailerInfo.objects.using('afisha').all().order_by('-trailer_id')[0]
                    next_trailer = last_trailer.trailer_id + 1
                    trailer_obj = TrailerInfo.objects.using('afisha').create(
                        trailer_id = next_trailer,
                        group_id = 1,
                        date = trailer_date,
                        size_w = 560,
                        size_h = 349,
                        runtime = 0,
                        cmt = '',
                        cmt_group = 'Трейлер',
                        file_ext = '',
                        code = code,
                    )
                    
                    Objxres.objects.using('afisha').create(
                        objtypeid = 3, 
                        objpkvalue = id,
                        extresid_id = trailer_obj.trailer_id,
                    )

                    act = '1'
                #else:
                #    if code:
                #        trailer = TrailerInfo.objects.using('afisha').get(trailer_id=video_kid) 
                #        trailer.code = code
                #        trailer.save()
                #        act = '2'
                #    else:
                #        act = '3'
                        
                actions_logger(11, id, request.profile, act) # фильм Трейлер

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

            return HttpResponseRedirect(reverse('get_film', kwargs={'id': id}))
    

    fdata_is_cached = cache.get('film__%s__fdata' % id, 'nocaсhed')

    if fdata_is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
        description = ''
        poster = ''
        
        name = ''

        if not poster:
            poster = film['posters'].replace('_small','') if film['posters'] else ''
        
        slides = []
        for ind, i in enumerate(film['slides']):
            slides.append((i.replace('_small',''), i))
            #if ind == 2: break

        slides_count = len(slides)
        trailers_count = len(film['trailers'])
        
        range_to = 3 - slides_count
        for i in range(range_to):
            slides.append(('', ''))
            
        trailer_url = ''
        trailer_code = ''
        trailer_id = None
        if film['trailers']:
            trailer_last = sorted(film['trailers'], key=operator.itemgetter('id'), reverse=True)[0]
            trailer_id = trailer_last['id']

            trailer = BeautifulSoup(trailer_last['code'], from_encoding='utf-8')
            
            for i in trailer.findAll(['iframe', 'object', 'embed']):
                if i.get('src'):
                    trailer_url = 'http:%s' % i.get('src')
                    
                i['width'] = 250
                i['height'] = 150
            trailer_code = str(trailer).replace('<html><head></head><body>', '').replace('</body></html>', '')
        trailer = trailer_code

        imdb_rate = film['imdb_rate'] if film['imdb_num'] else 0
        imdb_vote = film['imdb_num'] if film['imdb_num'] else 0
        afisha_rate_tag = u'<b>Оценки посетителей Киноафиши:</b> %s (%s голоса)' % (film['afisha_rate'], film['afisha_num']) if film['afisha_num'] else ''
        comment_tag = film['comment'].replace('&#034;', '"') if film['comment'] else ''

        if not description:
            description = u'%s' % film['description'] if film['description'] else ''

        description = description.replace('\n', '<br />')
        description_cut = ''
        
        if description:
            description_cut = BeautifulSoup(description, from_encoding='utf-8').text.strip().split()[:30]
            description_cut = ' '.join(description_cut)
            description_cut = '%s ...' % description_cut.rstrip(u'…').rstrip(u'...')
            
        limit = age_limits(film['limits']) if film['limits'] else ''
        runtime_tag = u'%s' % film['runtime'] if film['runtime'] else ''

        person_ids = []
        directors = []
        for v in film['directors']:
            try:
                director_imdb = get_imdb_id(v['imdb'])
                director_imdb_link = u'http://www.imdb.com/name/nm%s/' % director_imdb
                imdb_link = director_imdb_link
                imdb_name = v['name'][1]['name']
            except IndexError:
                imdb_link = ''
                imdb_name = ''
            
            parental_name = NamePerson.objects.filter(person__kid=v['id'], status=3, language__id=1).order_by('-id')[:1]
            parental_name = parental_name[0] if parental_name else None
            
            person_ids.append(v['id'])
            directors.append({
                'afisha_link': u'/person/%s/' % v['id'], 
                'afisha_name': v['name'][0]['name'],
                'imdb_link': imdb_link,
                'imdb_name': imdb_name,
                'parental_name': parental_name,
                'id': v['id'],
            })
        
        voices = [int(i['id']) for i in film['other_person'] if int(i['type'] == 5)]
        
        actors = []
        for v in film['actors']:
            if v['id'] not in voices:
                actor_imdb = get_imdb_id(v['imdb'])
                actor_imdb_link = u'http://www.imdb.com/name/nm%s/' % actor_imdb
                imdb_link = actor_imdb_link
                imdb_name = ''
                name_person = ''
                for n in v['name']:
                    if n['flag'] == 2:
                        imdb_name = n['name']
                    else:
                        name_person = n['name']
                        
                person_ids.append(v['id'])
                actors.append({
                    'afisha_link': u'/person/%s/' % v['id'], 
                    'afisha_name': name_person,
                    'imdb_link': imdb_link,
                    'imdb_name': imdb_name,
                    'id': v['id'],
                })
        
        other_person = []
        for v in film['other_person']:
            name_person = v['name'][0]['name']
            
            try:
                actor_imdb = get_imdb_id(v['imdb'])
                actor_imdb_link = u'http://www.imdb.com/name/nm%s/' % actor_imdb
                imdb_link = actor_imdb_link
                imdb_name = v['name'][1]['name']
            except IndexError:
                imdb_link = ''
                imdb_name = ''
                
            other_person.append({
                'afisha_link': u'/person/%s/' % v['id'], 
                'afisha_name': name_person,
                'imdb_link': imdb_link,
                'imdb_name': imdb_name,
                'type': v['type_name']
            })
        
        extresids = {}
        extresid = Objxres.objects.using('afisha').filter(objtypeid=302, objpkvalue__in=set(person_ids)).only('extresid', 'objpkvalue')
        for i in extresid:
            extresids[int(i.extresid_id)] = int(i.objpkvalue)
        
        person_photos = {}
        photos = Extres.objects.using('afisha').only('extresid', 'filename').filter(extresid__in=extresids.keys(), filename__icontains='small', info__icontains='*t')

        for i in photos:
            pkid = extresids.get(i.extresid)
            if pkid:
                person_photos[pkid] = 'http://persons.nodomain.kinoafisha.ru/%s' % i.filename

        for p in [directors, actors]:
            for i in p:
                ph = person_photos.get(int(i['id']))
                i['photo'] = ph
        
        name_ru = film.get('name_ru')
        name_en, name_en_imdb = (film['name_en'], int(film['idimdb'])) if film['idimdb'] else ('', '')
#by OFC076
        imdb_link = get_imdb_id(name_en_imdb)

        int_rate, show_ir, show_imdb, rotten = check_int_rates(id)
        rating = {'rate': int_rate, 'show_ir': show_ir, 'show_imdb': show_imdb, 'rotten': rotten}
        
        films_sound_copy = []
        films_copy = []
        films_sound = []
        films_sounds = FilmSound.objects.using('afisha').select_related('type_sound').filter(film_id=id)
        for i in films_sounds:
            films_copy.append(i.num)
            films_sound.append(i.type_sound.sound_type)
            films_sound_copy.append({
                'id': i.type_sound_id, 
                'name': i.type_sound.sound_type,
                'num': i.num,
            })
        
        
        kinoinfo_film_vote = FilmsVotes.objects.filter(kid=id)
        kinoinfo_film_vote_dict = {}
        for i in kinoinfo_film_vote:
            kinoinfo_film_vote_dict[i.user] = i.rate_1 + i.rate_2 + i.rate_3
            
        reviews_dict = []
        kinoinfo_reviews = News.objects.select_related('autor').filter(visible=True, reader_type='14', extra=id)
        authors = [i.autor for i in kinoinfo_reviews]
        authors_dict = org_peoples(authors, dic=True)
        
        for i in kinoinfo_reviews:
            v = kinoinfo_film_vote_dict.get(i.autor)

            autor = authors_dict.get(i.autor.user_id)
            if autor:
                if i.autor_nick == 1:
                    if i.autor.user.first_name:
                        autor['fio'] = i.autor.user.first_name
                        autor['show'] = '2'
                elif i.autor_nick == 2:
                    autor['fio'] = ''
                    autor['short_name'] = ''
            else:
                autor = {'fio': '', 'short_name': ''}
                
            aut = autor['fio'] if autor['fio'] else autor['short_name']
            
            reviews_dict.append({'title': i.title.replace('"','&#034;'), 'user': aut, 'rate': v, 'date': i.dtime})
        
        try:
            budget = FilmsBudget.objects.get(kid=id).budget
        except FilmsBudget.DoesNotExist:
            budget = None


        money = {'ru':  None, 'usa': None}
        '''
        gathering = Gathering.objects.using('afisha').only('country', 'total_gathering').filter(film=id, country__id__in=(1, 2)).order_by('sunday_date')

        for i in gathering:
            key = 'usa' if i.country_id == 1 else 'ru'
            total = '%s $\n' % intcomma(int(i.total_gathering)).replace(',', ' ')
            money[key] = total
        '''
        gathering = BoxOffice.objects.select_related('country').filter(kid=id, country__name__in=('США', 'Россия')).order_by('date_to')
        for i in gathering:
            key = 'usa' if i.country.name == u'США' else 'ru'
            total = '%s $\n' % intcomma(i.all_sum).replace(',', ' ')
            money[key] = total


        name_ru_query = name_ru.encode('utf-8').replace("'", '').replace("(", '').replace(")", '').strip()
        name_en_query = name_en.encode('utf-8').replace("'", '').replace("(", '').replace(")", '').strip()

        release_clear = ''
        if film['release']:
            release_clear = str(film['release']).replace(' 00:00:00','')
            year, month, day = release_clear.split('-')
            release_clear = '%s%s%s' % (day, month, year)

        try:
            release_ua = UkrainianReleases.objects.get(kid=id).release
            year_ua, month_ua, day_ua = str(release_ua).split('-')
            release_ua_clear = '%s%s%s' % (day_ua, month_ua, year_ua)
        except UkrainianReleases.DoesNotExist:
            release_ua = None
            release_ua_clear = ''

        fdata = {
            'name_ru': name_ru, 
            'name_en': name_en,
            'name_ru_query': name_ru_query,
            'name_en_query': name_en_query,
            'name_en_imdb': name_en_imdb,
            'year': film['year'],
            'afisha_rate': afisha_rate_tag,
            'imdb_rate': imdb_rate,
            'imdb_vote': imdb_vote,
            'comment': comment_tag,
            'description': description,
            'description_cut': description_cut,
            'limits': limit,
            'runtime': runtime_tag,
            'directors': directors,
            'actors': actors,
            'other_person': other_person,
            'posters': poster,
            'slides': slides,
            'slides_count': slides_count,
            'trailers': trailer,
            'trailer_id': trailer_id,
            'trailer_url': trailer_url,
            'trailers_count': trailers_count,
            'runtime': runtime_tag,
            'countries': film['countries'],
            'genres': film['genres'],
            'distributors': film['distributors'],
            'rating': rating,
            'release': film['release'],
            'release_clear': release_clear,
            'release_ua': release_ua,
            'release_ua_clear': release_ua_clear,
            'copies': films_copy,
            'sound': films_sound,
            'sound_copy': films_sound_copy,
            'money': money,
            'reviews': sorted(reviews_dict, key=operator.itemgetter('date'), reverse=True),
            'budget': budget,
            'id': id,
            'kinohod_key': settings.KINOHOD_APIKEY_CLIENT,
            'imdb_link': imdb_link,
        }
        cache.set('film__%s__fdata' % id, fdata, 60*60*24)
    else:
        fdata = fdata_is_cached


    likes = get_film_likes(id)
    
    fdata.update(likes)

    
    menu = film_menu(film['object'])
    fdata['menu'] = menu
    
    if film_editor:
        genres = list(AfishaGenre.objects.using('afisha').all().values_list('name', flat=True))
        fdata['admin_genres'] = genres
        countries = list(AfishaCountry.objects.using('afisha').all().values_list('name', flat=True))
        fdata['admin_countries'] = countries
        fdata['select_limits'] = (0, 6, 12, 16, 18, 21)
        fdata['select_countries'] = Country.objects.all().order_by('name')
        fdata['prokat'] = Prokat.objects.using('afisha').only('id', 'name').order_by('name')
        fdata['film_sound'] = FilmSoundType.objects.using('afisha').all().order_by('id')
        subscribe_me = u'<br />Ссылка для подписки "Хочу смотреть в кино":\
        <br />http://kinoinfo.ru/releases/%s/?subscribe' % id
        fdata['subscribe_me'] = subscribe_me

    current_user_city_id = request.current_user_city_id
    sch = []
    country = None
    city_name = None
    countries = []
    if current_user_city_id:
        city_name = request.current_user_city
        today = datetime.date.today()
        next_month = today + datetime.timedelta(days=30)
        
        sch = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lte=next_month, cinema__cinema__name__status=1, cinema__city__city__id=current_user_city_id, film__kid=id).exclude(film__source_id=0).values('cinema__cinema', 'cinema__cinema__name__name').distinct('cinema__cinema__city'))
        sch = sorted(sch, key=operator.itemgetter('cinema__cinema__name__name'))
    else:
        # получаю страну по IP
        ip = get_client_ip(request)
        if ip == '127.0.0.1':
            ip = '91.224.86.255' # для локальной машины
        country = get_country_by_ip(ip)
        country = country.id if country else 2
    
        countries = Country.objects.filter(city__name__status=1).distinct('pk')
    
    fdata.update({
        'countries_list': countries,
        'country': country,
        'city_name': city_name,
        'schedule_cinemas': sch,
        'subr': get_subscription_status(id, request.profile),
        'film_editor': film_editor,
        'cached_page': cached_page,
        'status': 'True',
    })

    if sch:
        fdata['cinema_load'] = sch[0]['cinema__cinema']
    
    fdata['timer'] = '%5.2f' % (time.time()-timer)

    tmplt = 'film/film.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film.html'

    return render_to_response(tmplt, fdata, context_instance=RequestContext(request))

@never_cache
def get_film(request, id):
    return get_film_func(request, id)


@never_cache
def get_film_rating(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    film_ext = FilmExtData.objects.using('afisha').only('rate', 'vnum').get(pk=id)

    frate = film_ext.rate
    fnum = film_ext.vnum
    
    rotten_data = SourceFilms.objects.filter(source_obj__url='http://www.rottentomatoes.com/', kid=id)
    rotten_rate = 0
    rotten_votes = 0
    if rotten_data:
        average, reviews, fresh, rotten = rotten_data[0].extra.split(';')
        try:
            rotten_rate = float(average.replace('/10',''))
            rotten_votes = reviews
        except ValueError: pass


    reviews_len = []
    for i in FilmsVotes.objects.filter(kid=id):
        reviews_sum = i.rate_1 + i.rate_2 + i.rate_3
        reviews_len.append(reviews_sum)

    reviewers_votes = len(reviews_len)
    reviewers_rate = 0
    if reviewers_votes:
        reviewers_rate = float(sum(reviews_len)) / float(reviewers_votes)
    

    opinions = list(NewsFilms.objects.filter(kid=id, rate__gt=0).values_list('rate', flat=True))
    opinions_votes = len(opinions)
    opinions_rate = 0
    if opinions_votes:
        opinions_rate = float(sum(opinions)) / float(opinions_votes)

    imdb_id = get_imdb_id(film.idalldvd)


    menu = film_menu(film)
    film_editor = is_film_editor(request)
    
    tmplt = 'film/film_rating.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_rating.html'

    return render_to_response(tmplt, {'imdb_rate': film.imdb, 'imdb_votes': film.imdb_votes, 'imdb_id': imdb_id, 'afisha_rate': frate, 'afisha_votes': fnum, 'id': id, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'menu': menu, 'film_editor': film_editor, 'rotten_rate': rotten_rate, 'rotten_votes': rotten_votes, 'reviewers_votes': reviewers_votes, 'reviewers_rate': reviewers_rate, 'opinions_votes': opinions_votes, 'opinions_rate': opinions_rate}, context_instance=RequestContext(request))


@never_cache
def get_film_boxoffice(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    gathering = BoxOffice.objects.select_related('country').filter(kid=id, country__name__in=('США', 'Россия')).order_by('date_to')

    money = {
        'ru': {'all': [], 'places': [], 'total': None}, 
        'usa': {'all': [], 'places': [], 'total': None}
    }
    
    for i in gathering:
        key = 'usa' if i.country.name == u'США' else 'ru'
        
        friday_date = tmp_date(i.date_from, "d")
        sunday_date = tmp_date(i.date_to, "d b")
        
        dates = '%s - %s' % (friday_date, sunday_date)

        total = intcomma(i.all_sum).replace(',', ' ')
        
        money[key]['all'].append([dates, i.week_sum, i.screens])
        money[key]['total'] = total

    money['usa']['all'] = money['usa']['all'][:30]
    money['ru']['all'] = money['ru']['all'][:30]
    
    menu = film_menu(film)
    
    film_editor = is_film_editor(request)

    tmplt = 'film/film_boxoffice.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_boxoffice.html'

    return render_to_response(tmplt, {'money': money, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor}, context_instance=RequestContext(request))
    

def delete_film_review(request, id):
    film_editor = is_film_editor(request)
    if film_editor:
        n = get_object_or_404(News, pk=id)
        
        actions_logger(4, n.extra, request.profile, '3', n.title) # рецензия
        
        try:
            afisha_obj = AfishaNews.objects.using('afisha').get(pk=n.kid)
            FilmsVotes.objects.filter(kid=afisha_obj.obj_id, user=n.autor).delete()
            FilmVotes.objects.using('afisha').filter(pk=afisha_obj.id).delete()
            afisha_obj.delete()
        except AfishaNews.DoesNotExist:
            pass
            
        n.delete()
        News.objects.filter(reader_type='10', extra__istartswith='%s;' % id).delete()
        NewsTags.objects.filter(news=None).delete()
        
    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
    return HttpResponseRedirect(ref)


def add_film_review(request, id):
    from news.views import create_news

    profile = request.profile

    type = '14'
    if request.POST:
        film_editor = is_film_editor(request)

        if film_editor:
            id = request.POST.get('film_id')
            rate1 = request.POST.get('eye')
            rate2 = request.POST.get('mind')
            rate3 = request.POST.get('heart')

            if id:
                text = request.POST.get('note')
                title = request.POST.get('title', 'Рецензия на фильм')
                review_id = request.POST.get('review_id')
                profile_id = request.POST.get('profile_id')

                act = None

                if review_id:
                    obj = News.objects.get(id=review_id)
                    obj.title = title
                    obj.text = text
                    obj.save()

                    # обновление на Киноафише
                    AfishaNews.objects.using('afisha').filter(pk=obj.kid).update(
                        name=obj.title,
                        content=obj.text,
                    )

                    if rate1 and rate2 and rate3:
                        votes, votes_created = FilmsVotes.objects.get_or_create(
                            kid=id,
                            user_id=profile_id,
                            defaults={
                                'kid': id,
                                'user_id': profile_id,
                                'rate_1': rate1,
                                'rate_2': rate2,
                                'rate_3': rate3,
                            })
                        if not votes_created:
                            votes.rate_1 = rate1
                            votes.rate_2 = rate2
                            votes.rate_3 = rate3
                            votes.save()

                        # обновление на Киноафише
                        FilmVotes.objects.using('afisha').filter(pk=obj.kid).update(
                            rate_1=rate1,
                            rate_2=rate2,
                            rate_3=rate3,
                        )
                    act = '2'
                else:
                    author_nick = request.POST.get('author_nick', 0)

                    news = create_news(request, [], title, text, type, author_nick, id)

                    # Создается подписка автора статьи на новые комменты
                    from user_registration.func import sha1_string_generate
                    unsubscribe = sha1_string_generate().replace('_', '')
                    SubscriberUser.objects.get_or_create(
                        type='3',
                        obj=news.id,
                        profile=request.profile,
                        defaults={
                            'type': '3',
                            'obj': news.id,
                            'profile': request.profile,
                            'unsubscribe': unsubscribe,
                        })

                    FilmsVotes.objects.get_or_create(
                        kid=id,
                        user=profile,
                        defaults={
                            'kid': id,
                            'user': profile,
                            'rate_1': rate1,
                            'rate_2': rate2,
                            'rate_3': rate3,
                        })
                    act = '1'

                    # запиь на Киноафишу
                    if profile.kid:
                        afisha_obj = AfishaNews.objects.using('afisha').create(
                            name=news.title,
                            content=news.text,
                            type=2,
                            object_type=1,
                            obj_id=id,
                            user_id=profile.kid,
                        )

                        FilmVotes.objects.using('afisha').create(
                            pk=afisha_obj.id,
                            rate_1=rate1,
                            rate_2=rate2,
                            rate_3=rate3,
                        )

                        news.kid = afisha_obj.id
                        news.save()

                actions_logger(4, id, profile, act, title) # рецензия

    return HttpResponseRedirect(reverse('get_film_reviews', kwargs={'id': id}))


@never_cache
def get_film_reviews(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    reviews_back_link = False
    original_ref = request.META.get('HTTP_REFERER', '')
    ref = original_ref.split('?')[0]
    if ref == 'http://www.kinoafisha.ru/reviews/' or ref == 'http://127.0.0.1:8000/reviews/':
        reviews_back_link = True


    rate_text = {
        9: 'превосходно',
        8: 'отлично',
        7: 'хорошо',
        6: 'неплохо',
        5: 'плохо',
        4: 'совсем плохо',
        3: 'полный провал',
    }


    first_load = request.GET.get('r')

    reviews_dict = []

    kinoinfo_film_vote = FilmsVotes.objects.filter(kid=id)
    kinoinfo_film_vote_dict = {}
    for i in kinoinfo_film_vote:
        sum_rate = i.rate_1 + i.rate_2 + i.rate_3
        rate_txt = rate_text.get(sum_rate)
        kinoinfo_film_vote_dict[i.user] = {'sum': sum_rate, 'r1': i.rate_1, 'r2': i.rate_2, 'r3': i.rate_3, 'rate_txt': rate_txt, 'user_id': i.user_id}
    
    kinoinfo_reviews = News.objects.select_related('autor').filter(visible=True, reader_type='14', extra=id)

    authors = [i.autor for i in kinoinfo_reviews]
    authors_dict = org_peoples(authors, dic=True)
    
    for i in kinoinfo_reviews:
        v = kinoinfo_film_vote_dict.get(i.autor)

        txt_cut = BeautifulSoup(i.text, from_encoding='utf-8').text.strip()
        if len(txt_cut) > 400:
            txt_cut = txt_cut[:400]
            
        autor = authors_dict.get(i.autor.user_id)
        
        if i.autor_nick == 1:
            if i.autor.user.first_name:
                autor['fio'] = i.autor.user.first_name
                autor['show'] = '2'
        elif i.autor_nick == 2:
            autor['fio'] = ''
            autor['short_name'] = ''
        
        #comments = News.objects.filter(reader_type='10', extra__istartswith='%s;' % i.id).count()
        
        avatar = None
        if i.autor.kid == 3354:
            avatar = 'http://slides.kinoafisha.ru/7/6890-004.jpg'
        elif i.autor.kid == 2:
            avatar = 'http://slides.kinoafisha.ru/7/6890-003.jpg'
        elif i.autor.kid == 3043:
            avatar = 'http://slides.kinoafisha.ru/7/6890-002.jpg'
        else:
            avatar = 'http://slides.kinoafisha.ru/7/6890-005.jpg'


        comments = bpost_comments_gen(i.id, request.current_site, request.user.is_superuser)

        try:
            comments_subscribed = SubscriberUser.objects.get(profile=request.profile, type='2', obj=i.id).id
        except SubscriberUser.DoesNotExist:
            comments_subscribed = None

        reviews_dict.append({'title': i.title, 'user': autor, 'uid': i.autor.user_id, 'avatar': avatar, 'rate': v, 'txt': i.text, 'txt_cut': txt_cut, 'date': i.dtime, 'kinoinfo': True, 'id': i.id, 'comments': comments, 'comments_subscribed': comments_subscribed})


    # poster
    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid__in=[301, 300], objpkvalue=id)
    posters = []
    slides = []
    for p in poster_obj:
        if p.objtypeid == 301:
            posters.append(p)
        else:
            slides.append(p)


    poster_path = ''
    if posters:
        poster_path = film_poster2(posters, 'big')

    slides_tmp = []
    if slides:
        slides_tmp = film_poster2(slides, 'small', True)
        
    slides = []
    for ind, s in enumerate(slides_tmp):
        slides.append((s.replace('_small',''), s))
        if ind == 14: break



    # trailers
    trailers_rel = Objxres.objects.using('afisha').filter(objtypeid=3, objpkvalue=id)
    trailers_ids = [i.extresid_id for i in trailers_rel]
    
    trailers_objs = TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=trailers_ids)

    trailers = []
    
    for i in trailers_objs:

        trailer_code = ''
        trailer_img = ''
        trailer_id = ''
        if i:
            trailer = BeautifulSoup(i.code.replace('&#034;', '"'), from_encoding='utf-8')
            if 'youtu' in str(trailer):
                for tr in trailer.findAll(['iframe', 'object', 'embed', 'frame']):
                    tr['width'] = 250
                    tr['height'] = 150
                    src = tr.get('src')
                    if src:
                        try:
                            trailer_id = src.split('/embed/')[1].split('?')[0].replace('/','')
                        except IndexError:
                            trailer_id = src.split('/v/')[1].split('?')[0].replace('/','')
                    else:
                        src = tr.findAll('param', limit=1)[0].get('value')
                        trailer_id = src.split('/v/')[1].split('?')[0].replace('/','')

                    trailer_img = u'http://img.youtube.com/vi/%s/mqdefault.jpg' % trailer_id
                trailer_code = str(trailer).replace('<html><head></head><body>', '').replace('</body></html>', '')

                if trailer_id:
                    trailers.append({'code': trailer_code,  'id': trailer_id, 'img': trailer_img})

    trailers = sorted(trailers, key=operator.itemgetter('id'))

    menu = film_menu(film)
    
    reviews_dict = sorted(reviews_dict, key=operator.itemgetter('date'), reverse=True)
    
    reviews_count = len(reviews_dict)

    film_editor = is_film_editor(request)
    
    spam_msg = request.session.get('news_antispam')
    if spam_msg:
        request.session['news_antispam'] = ''
    banned = request.session.get('banned')


    tmplt = 'film/film_reviews.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_reviews.html'

    email_exist = False
    if request.user.is_authenticated():
        main_email = request.user.email
        if main_email:
            email_exist = True
        else:
            emails = [i.email.strip() for i in request.profile.accounts.all() if i.email and i.email.strip()]
            if emails:
                email_exist = True

    
    return render_to_response(tmplt, {'data': reviews_dict, 'reviews_back_link': reviews_back_link, 'original_ref': original_ref, 'trailers': trailers, 'slides': slides, 'poster_path': poster_path, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'first_load': first_load, 'film_editor': film_editor, 'spam_msg': spam_msg, 'banned': banned, 'reviews_count': reviews_count, 'email_exist': email_exist}, context_instance=RequestContext(request))



@never_cache
def get_film_relations(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    if request.POST and request.user.is_superuser or request.is_admin:
        film_kid = request.POST.get('film')
        source_id = request.POST.get('source_id')
        source_type = request.POST.get('source_type')
        
        now = datetime.datetime.now()
        
        if 'kid_sid' in request.POST:
            if source_type == 'sourcefilms':
                SourceFilms.objects.filter(pk=source_id).update(kid=film_kid, rel_dtime=now, rel_profile=request.profile)
            if source_type == 'relfilms':
                ReleasesRelations.objects.filter(pk=source_id).update(film_kid=film_kid, rel_dtime=now, rel_profile=request.profile)
        elif 'del_rel' in request.POST:
            if source_type == 'sourcefilms':
                SourceFilms.objects.filter(pk=source_id).delete()
            if source_type == 'relfilms':
                ReleasesRelations.objects.filter(pk=source_id).delete()
                
    world = {'world': [], 'cis': [], 'russia': []}
    
    films = SourceFilms.objects.select_related('source_obj', 'rel_profile').filter(kid=id)
    
    films_rel = ReleasesRelations.objects.select_related('release', 'rel_profile').filter(film_kid=id, rel_double=False, rel_ignore=False)
    
    film_rel_dict = {}
    for i in films_rel:
        uid = '%s%s' % (i.film_kid, i.release_id)
        if not film_rel_dict.get(uid):
            film_rel_dict[uid] = i
    
    imdb_id = get_imdb_id(film.idalldvd)
    
    official_site = None
    if film.site:
        official_site = film.site.lstrip('#').rstrip('#').strip()

    kinoafisha_rel = None

    for i in films:
        url = ''
        if i.source_obj.url == 'http://yaltakino.com/Oreanda/':
            url = 'http://yaltakino.com/Oreanda/?filmid=%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://yaltakino.com/Spartak/':
            url = 'http://yaltakino.com/Spartak/?filmid=%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://ktmir.ru/':
            url = '%s/' % i.source_id.replace('http:ktmir.rufilms', 'http://ktmir.ru/films/')
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://kt-russia.ru/':
            url = '%s/' % i.source_id.replace('http:kt-russia.rufilms', 'http://kt-russia.ru/films/')
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://megamag.by/':
            url = 'http://kinoteatr.megamag.by/newsdesk_info.php?newsdesk_id=%s' % i.source_id
            world['cis'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://kino-teatr.ua/':
            url = 'http://kino-teatr.ua/film/%s.phtml' % i.source_id
            world['cis'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://etaj.mega74.ru/':
            url = 'http://etaj.mega74.ru/kino/list/films_%s.html' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://www.rambler.ru/':
            url = 'http://kassa.rambler.ru/movie/%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://kinohod.ru/':
            url = 'http://kinohod.ru/movie/%s/' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://surkino.ru/':
            url = 'http://surkino.ru/?film=%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://cinemaarthall.ru/':
            url = 'http://cinemaarthall.ru/page/kino/films/%s/' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://www.zlat74.ru/':
            url = 'http://www.zlat74.ru/movies/%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://kino-bklass.ru/':
            url = 'http://kino-bklass.ru/films/%s/' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://www.michurinsk-film.ru/':
            url = 'http://www.michurinsk-film.ru/film/item/%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://luxor.chuvashia.com/':
            url = 'http://luxor.chuvashia.com/films.aspx?id=%s' % i.source_id
            world['russia'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://vkino.com.ua/':
            url = 'http://vkino.com.ua/show/%s/about' % i.source_id
            world['cis'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://www.rottentomatoes.com/':
            url = 'http://www.rottentomatoes.com/%s' % i.source_id
            world['world'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://www.yo-video.net/':
            url = 'http://www.yo-video.net%s' % i.source_id
            world['world'].append({'obj': i, 'url': url})
        elif i.source_obj.url == 'http://rutracker.org/':
            if request.user.is_superuser:
                url = 'http://rutracker.org/forum/viewtopic.php?t=%s' % i.source_id
                world['russia'].append({'obj': i, 'url': url, 'admin': True})
        elif i.source_obj.url == 'http://www.tvzavr.ru/':
            world['russia'].append({'obj': i, 'url': i.extra})
        elif i.source_obj.url == 'http://cinemaplex.ru/':
            world['russia'].append({'obj': i, 'url': None})
    
    not_found = None
    alt_names = None
    sources = []
    if request.user.is_superuser:
        sources = ImportSources.objects.exclude(url__in=("http://www.imdb.com/", "http://www.kinoafisha.ru/", "http://www.kinobusiness.com/", "http://megogo.net/", "http://www.maxmind.com", "http://m.0654.com.ua/", "http://www.bigyalta.info/", "http://www.orgpage.ru/", "http://top250.info/", "http://www.now.ru/", "http://распиши.рф/"))
        not_found = NotFoundFilmsRelations.objects.filter(kid=film.id)
        alt_names = NameFilms.objects.filter(kifilmrelations__kid=film.id)
        
    if not kinoafisha_rel:
        kinoafisha_rel = 'http://www.kinoafisha.ru/index.php3?id1=%s&status=1' % film.id

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_relations.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_relations.html'

    return render_to_response(tmplt, {'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'films_rel': film_rel_dict.values(), 'film': film, 'imdb_id': imdb_id, 'menu': menu, 'kinoafisha_rel': kinoafisha_rel, 'official_site': official_site, 'world': world, "sources": sources, 'not_found': not_found, 'alt_names': alt_names, 'film_editor': film_editor}, context_instance=RequestContext(request))


@never_cache
def get_film_web(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
        
    nowru = Nowru.objects.only('url_player', 'name_ru').filter(kid=id)
    megogo = MovieMegogo.objects.filter(afisha_id=id)

    tvzavr = SourceFilms.objects.filter(source_obj__url='http://www.tvzavr.ru/', kid=id)

    codes = FilmsCodes.objects.using('afisha').exclude(player='').filter(film=id)
    codes_list = []
    for i in codes:
        data = None
        if 'now.ru' in i.player and not nowru:
            data = {'name': 'Now.ru', 'player': i.player.replace('&#034;', '"')}
        elif 'kinostok.tv' in i.player:
            data = {'name': 'Kinostok.tv', 'player': i.player.replace('&#034;', '"')}
        elif 'mail.ru' in i.player:
            data = {'name': 'Mail.ru', 'player': i.player.replace('&#034;', '"')}
        elif 'ivi.ru' in i.player:
            data = {'name': 'Ivi.ru', 'player': i.player.replace('&#034;', '"')}
        elif 'cinem.tv' in i.player:
            data = {'name': 'Cinem.tv', 'player': i.player.replace('&#034;', '"')}
        elif 'youtube.com' in i.player:
            data = {'name': 'Youtube.com', 'player': i.player.replace('&#034;', '"')}
        elif 'vk.com' in i.player:
            data = {'name': 'Vk.com', 'player': i.player.replace('&#034;', '"')}
        elif 'molodejj.tv' in i.player:
            data = {'name': 'Molodejj.tv', 'player': i.player.replace('&#034;', '"')}

        if data:
            codes_list.append(data)

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_web.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_web.html'
        
    return render_to_response(tmplt, {'nowru': nowru, 'megogo': megogo, 'codes_list': codes_list, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor, 'tvzavr': tvzavr}, context_instance=RequestContext(request))


@never_cache
def set_coord(request):
    if request.POST:
        redirect_to = request.POST.get('next', '')
        country = request.POST.get('countries')
        city = request.POST.get('cities')
        if country and city:
            city_obj = City.objects.get(name__id=city)
            person = request.profile.person
            person.city = city_obj
            person.country_id = country
            person.save()
        return HttpResponseRedirect(redirect_to)
    raise Http404


@never_cache
def get_film_schedules(request, id):

    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    country = None
    city = None
    city_id = ''
    card = {}
    if not request.user.is_anonymous():

        card = get_usercard(request.user)
        
        # если у юзера в профиле указана страна
        if card['country']:
            country = card['country']['id']
            # и город
            if request.current_user_city_id:
                city = request.current_user_city_id
    
    # если не указана, то получаю страну по IP
    if not country:
        ip = get_client_ip(request)
        if ip == '127.0.0.1':
            ip = '91.224.86.255' # для локальной машины
        country = get_country_by_ip(ip)
        country = country.id if country else 2
    
    city_name = None
    countries = Country.objects.filter(city__name__status=1).distinct('pk')
    
    filter = {}
    if city:
        filter = {'city__pk': city, 'status': 1}
        try:
            city_name = NameCity.objects.get(**filter)
            city = City.objects.get(name=city_name)
        except NameCity.DoesNotExist:
            city = None

    now = datetime.datetime.now()
    
    today = now.date()
    tomorrow = now + datetime.timedelta(days=1)
    
    now = now - datetime.timedelta(hours=1)
    next_month = now + datetime.timedelta(days=30)
    
    schedules = []
    if city:
        schedules = SourceSchedules.objects.defer('source_id').select_related('cinema__cinema').filter(dtime__gte=now, dtime__lte=next_month, cinema__city__city__id=city.id, film__kid=id).order_by('dtime')
        
    cinemas = set([i.cinema.cinema_id for i in schedules])

    cin_names = NameCinema.objects.filter(cinema__id__in=cinemas, status=1).values('cinema__id', 'name')
    cin_dict = {}
    for i in cin_names:
        cin_dict[i['cinema__id']] = i['name']

    cinemas = []
    first_sch = []
    film_sch = {}
    for ind, i in enumerate(schedules):
        schedule_time = i.dtime.time().strftime('%H:%M')
        schedule_date = i.dtime.date()
        cinema_id = i.cinema.cinema_id
        cinema_name = cin_dict.get(cinema_id)
        
        if ind < 6:
            first_sch.append({'times': schedule_time, 'obj': cinema_name})
        
        if film_sch.get(schedule_date):
            if film_sch[schedule_date]['cinemas'].get(cinema_id):
                if schedule_time not in film_sch[schedule_date]['cinemas'][cinema_id]['times']:
                    film_sch[schedule_date]['cinemas'][cinema_id]['times'].append(schedule_time)
            else:
                film_sch[schedule_date]['cinemas'][cinema_id] = {'obj': cinema_name, 'times': [schedule_time]}
        else:
            film_sch[schedule_date] = {'date': schedule_date, 'cinemas': {cinema_id: {'obj': cinema_name, 'times': [schedule_time]}}}
    
    # сортировка по названию кинотеатра
    f_sch = []
    for i in film_sch.values():
        cinemas_l = sorted([j for j in i['cinemas'].values()], key=operator.itemgetter('obj'))
        f_sch.append({'date': i['date'], 'cinemas': cinemas_l})
    # сортировка по дате
    f_sch = sorted(f_sch, key=operator.itemgetter('date'))

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_schedule.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_schedule.html'

    return render_to_response(tmplt, {'film_sch': f_sch, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'city_name': city_name, 'country': country, 'first_sch': first_sch, 'today': today, 'tomorrow': tomorrow.date(), 'menu': menu, 'countries': countries, 'film_editor': film_editor}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def film_persons(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    film_obj = None
    for i in Films.objects.filter(kid=id):
        if i.imdb_id:
            film_obj = i
        elif not film_obj:
            film_obj = i

    persons = RelationFP.objects.select_related('person', 'status_act', 'action').filter(films=film_obj)
    persons_id = [i.person.kid for i in persons]

    persons_name = NamePerson.objects.filter(person__kid__in=persons_id, status=1, language__id__in=(1,2)).values('name', 'person__kid', 'language')

    persons_name_dict = {}
    for i in persons_name:
        if not persons_name_dict.get(i['person__kid']):
            persons_name_dict[i['person__kid']] = {'name': [{'flag': i['language'], 'name': i['name']}]}
        else:
            persons_name_dict[i['person__kid']]['name'].append({'flag': i['language'], 'name': i['name']})

    data = {'directors': [], 'actors': [], 'other_person': []}

    for i in persons:
        pers = persons_name_dict.get(i.person.kid)

        xxx = {'type': i.action_id, 'type_name': i.action.name, 'id': i.person.kid, 'status': i.status_act_id, 'status_name': i.status_act.name, 'relation_id': i.id}
        empty_name = {'name': [{'flag': '', 'name': ''}]}

        pers_dict = dict(pers.items() + xxx.items()) if pers else dict(empty_name.items() + xxx.items())

        if i.action_id == 3:
            data['directors'].append(pers_dict)
        elif i.action_id == 1:
            data['actors'].append(pers_dict)
        else:
            data['other_person'].append(pers_dict)

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    person_types = Action.objects.all()
    person_status = StatusAct.objects.all()

    return render_to_response('film/film_persons.html', {'data': data, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'kid': id, 'id': film_obj.id, 'menu': menu, 'film_editor': film_editor, 'person_types': person_types, 'person_status': person_status}, context_instance=RequestContext(request))


@never_cache
def get_film_opinions(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    opinions_list = []

    filmsnews = NewsFilms.objects.select_related(
        'message', 'message__autor').filter(kid=id, message__visible=True)

    authors = set([i.message.autor for i in filmsnews])
    authors_dict = org_peoples(authors, dic=True)

    source = ImportSources.objects.get(url='http://www.kino.ru/')
    try:
        source_film = SourceFilms.objects.get(kid=id, source_obj=source)
    except SourceFilms.DoesNotExist:
        source_film = None

    rates = []
    my_rate_exist = False

    for i in filmsnews:
        author = authors_dict.get(i.message.autor.user_id)

        nick = author['name']
        if i.message.autor_nick == 1 and author['nickname']:
            nick = author['nickname']

        if i.source_obj_id and source_film:
            url = '%sfilm/%s/comments/%s' % (
                source.url, source_film.source_id.replace(
                    'film_', 'forum_'), i.source_id)
        else:
            url = None

        if i.rate:
            rates.append(i.rate)
            if request.profile and i.message.autor_id == request.profile.id:
                my_rate_exist = True

        full_txt = i.message.text
        if full_txt:
            edit_permission = False
            if request.user.is_superuser or (request.profile and i.message.autor_id == request.profile.id):
                edit_permission = True

            short_txt = None
            if len(full_txt) > 400:
                short_txt = cut_description(full_txt, True, 400)

            spam = True if u'http' in full_txt else False

            opinions_list.append({
                'date': i.message.dtime, 'nick': nick, 'spam': spam,
                'full_txt': full_txt, 'short_txt': short_txt, 'source': url,
                'source_name': 'kino.ru', 'id': i.id, 'rate': i.rate,
                'edit_permission': edit_permission})

    opinions_list = sorted(
        opinions_list, key=operator.itemgetter('date'), reverse=True)

    avg_rates = None
    if rates:
        avg_rates = '%1.1f' % (float(sum(rates)) / len(rates))

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_opinions.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_opinions.html'

    return render_to_response(tmplt, {'opinions': opinions_list, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor, 'avg_rates': avg_rates, 'my_rate_exist': my_rate_exist}, context_instance=RequestContext(request))


@never_cache
def get_film_download(request, id):
    if request.current_site.domain == 'kinoafisha.ru':
        raise Http404

    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    errors = []
    if request.POST and request.user.is_superuser:
        tfile = request.FILES.get('files')
        tquality = request.POST.get('quality_avg')

        if tfile:
            file_format = low(tfile.name).split('.')[-1]
            if file_format == 'torrent':
                film_name = name_ru if name_ru else name_en
                slug = low(del_separator(film_name.encode('utf-8')))

                current_year = datetime.datetime.today().year

                folder_char = ord(slug.decode('utf-8')[0]) if slug else '-'

                # если нет папки для текущего года, то создаем
                folder_path = '%s/%s' % (settings.TORRENT_PATH, current_year)
                try:
                    os.makedirs(folder_path)
                except OSError:
                    pass

                # если нет папки (буквы), то создаем
                folder_path = '%s/%s' % (folder_path, folder_char)
                try:
                    os.makedirs(folder_path)
                except OSError:
                    pass

                full_path = '%s/%s_%s.torrent' % (folder_path, id, md5_string_generate(folder_char))
                full_path_db = full_path.replace(settings.MEDIA_ROOT, '')

                Torrents.objects.create(
                    film=id,
                    quality_avg=tquality,
                    path=full_path_db,
                )

                with open(full_path, 'wb') as f:
                    f.write(tfile.read())

                return HttpResponseRedirect(reverse('get_film_download', kwargs={'id': id}))
            else:
                errors.append('Файл не является torrent файлом')

    topics = SourceFilms.objects.filter(source_obj__url="http://rutracker.org/", kid=id)

    torrents = Torrents.objects.filter(film=id).exclude(path=None)

    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_download.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_download.html'

    q = request.GET.get('q')

    return render_to_response(tmplt, {'topics': topics, 'q': q, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor, 'quality_avg': TORRENT_QUALITY, 'errors': errors, 'torrents': torrents}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def film_torrent_delete(request, id, torrent_type, torrent_id):
    if request.current_site.domain == 'kinoafisha.ru':
        raise Http404

    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    if torrent_type == '1':
        SourceFilms.objects.filter(
            source_obj__url="http://rutracker.org/",
            kid=id,
            pk=torrent_id
        ).delete()
    elif torrent_type == '2':
        obj = Torrents.objects.get(film=id, pk=torrent_id)
        path = '%s%s' % (settings.MEDIA_ROOT, obj.path)
        try:
            os.remove(path)
        except OSError:
            pass
        obj.delete()
    return HttpResponseRedirect(reverse('get_film_download', kwargs={'id': id}))


@never_cache
def get_film_list(request, year):
    if len(year) != 4:
        raise Http404
    
    years = list(Film.objects.using('afisha').exclude(year__exact='').all().values_list('year', flat=True).order_by('year').distinct('year'))
    
    films = list(FilmsName.objects.using('afisha').filter(type__in=(1, 2), status=1, film_id__year__exact=year).values("film_id", "name", "type"))
    
    films_dict = {}
    for i in films:
        if not films_dict.get(i['film_id']):
            films_dict[i['film_id']] = {'name_en': None, 'name_ru': None, 'id': i['film_id']}
        if i['type'] == 1:
            films_dict[i['film_id']]['name_en'] = i['name'].strip()
        else:
            films_dict[i['film_id']]['name_ru'] = i['name'].strip()
    
    films = sorted(films_dict.values(), key=operator.itemgetter('name_ru'))
    
    tmplt = 'film/films_list.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/films_list.html'
    
    return render_to_response(tmplt, {'films': films, 'year': year, 'years': years}, context_instance=RequestContext(request))


@never_cache
def get_film_trailers(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    film_editor = is_film_editor(request)

    if request.POST and film_editor:
        video = request.POST.get('trailer').strip()
        video_kid = request.POST.get('trailer_id')

        act = None
        if video:
            code = get_youtube_video_player(video, width=560, height=349)
            if code:
                trailer = TrailerInfo.objects.using('afisha').get(trailer_id=video_kid)
                if trailer.code != code:
                    act = '2'
                    trailer.code = code
                    trailer.save()
                
        else:
            act = '3'
            trailer = TrailerInfo.objects.using('afisha').get(trailer_id=video_kid).delete()

        if act:
            actions_logger(11, id, request.profile, act) # фильм Трейлер

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

        return HttpResponseRedirect(reverse('get_film_trailers', kwargs={'id': id}))


    trailers_rel = Objxres.objects.using('afisha').filter(objtypeid=3, objpkvalue=id)
    trailers_ids = [i.extresid_id for i in trailers_rel]
    
    trailers_objs = TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=trailers_ids)

    trailers = []
    
    for i in trailers_objs:
        trailer_url = ''
        trailer_code = ''
        trailer_id = None
        if i:
            trailer_id = i.trailer_id
            trailer = BeautifulSoup(i.code.replace('&#034;', '"'), from_encoding='utf-8')
            for i in trailer.findAll(['iframe', 'object', 'embed']):
                if i.get('src'):
                    trailer_url = i.get('src')
                    if 'http' not in trailer_url:
                        trailer_url = 'http:%s' % trailer_url
                i['width'] = 250
                i['height'] = 150
            
            trailer_code = str(trailer).replace('<html><head></head><body>', '').replace('</body></html>', '')
            
            trailer_code = trailer_code
        trailers.append({'code': trailer_code, 'url': trailer_url, 'id': trailer_id})
    
    trailers = sorted(trailers, key=operator.itemgetter('id'))
    
    menu = film_menu(film)
    
    tmplt = 'film/film_trailers.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_trailers.html'

    return render_to_response(tmplt, {'trailers': trailers, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor}, context_instance=RequestContext(request))
    

@never_cache
def get_film_slides(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    slides = []
    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=300, objpkvalue=id)
    
    for i in poster_obj:
        if i.extresid:
            file_name = i.extresid.filename
            img = re.findall('\d{0,}', file_name)
            step_gr = 1000
            iterat = step_gr
            group = '1'                          
            j = 1
            while int(img[0]) > (iterat - step_gr) and iterat <= int(img[0]):
                j += 1
                group = j
                iterat += step_gr

            if i.extresid.filepath:
                if not 'poster' in i.extresid.filepath:
                    poster_path = 'http://slides.kinoafisha.ru/%s/%s' % (group, file_name)

                    if 'small' in poster_path:
                        big_slide = poster_path.replace('_small','')
                        slides.append((big_slide, poster_path))
        
    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_slides.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_slides.html'

    return render_to_response(tmplt, {'slides': slides, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor}, context_instance=RequestContext(request))


@never_cache
def get_film_posters(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404
    
    posters = []
    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue=id)
    
    for i in poster_obj:
        if i.extresid:
            file_name = i.extresid.filename
            img = re.findall('\d{0,}', file_name)
            step_gr = 1000
            iterat = step_gr
            group = '1'                          
            j = 1
            while int(img[0]) > (iterat - step_gr) and iterat <= int(img[0]):
                j += 1
                group = j
                iterat += step_gr

            if i.extresid.filepath:
                if 'poster' in i.extresid.filepath:
                    poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                    if 'small' in poster_path:
                        poster_path_big = poster_path.replace('_small','')
                        posters.append((poster_path_big, poster_path))
            else:
                poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                if 'small' in poster_path:
                    poster_path_big = poster_path.replace('_small','')
                    posters.append((poster_path_big, poster_path))
        
    menu = film_menu(film)
    film_editor = is_film_editor(request)

    tmplt = 'film/film_posters.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/film/film_posters.html'

    return render_to_response(tmplt, {'posters': posters, 'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'film_editor': film_editor}, context_instance=RequestContext(request))



@never_cache
def film_create_rel(request, id):
    film, name_ru, name_en = get_names_and_film_obj(id)
    if not film:
        raise Http404

    name_ru_query = name_ru.encode('utf-8').replace("'", '').strip()
    name_en_query = name_en.encode('utf-8').replace("'", '').strip()
    
    limits = (0, 13, 16, 18, 21)
    countries = Country.objects.all().order_by('name')
 
    menu = film_menu(film)
    film_editor = is_film_editor(request)
    return render_to_response('film/film_create_rel.html', {'name_ru': name_ru, 'name_en': name_en, 'year': film.year, 'id': id, 'menu': menu, 'limits': limits, 'countries': countries, 'name_ru_query': name_ru_query, 'name_en_query': name_en_query, 'imdb_id': film.idalldvd, 'film_editor': film_editor}, context_instance=RequestContext(request))



@never_cache
def film_create(request, id):
    film_editor = is_film_editor(request)
    if film_editor:
        film, name_ru, name_en = get_names_and_film_obj(id)
        if not film:
            raise Http404
            
        data = identification_info(request, 'film')
        menu = film_menu(film)
        
        data['interface'] = True
        data['menu'] = menu
        data['name_ru'] = name_ru.strip()
        data['name_en'] = name_en.strip()
        data['year'] = film.year
        data['id'] = id
        data['film_editor'] = film_editor
        return render_to_response('film/film_objects_info.html', data, context_instance=RequestContext(request))
    else:
        raise Http404



def film_create_new_func(name, year, lang, create=True, imDB=None):
    new_id = Film.objects.using('afisha').latest('id').id + 1
    
    try:
        if not(imDB is None):
            if len(imDB) < 1:
                imDB=None
        film_obj = Film.objects.using('afisha').create(
            id = new_id,
            idalldvd = imDB,
            year = year,
            runtime = None,
            limits = None,
            comment = None,
            imdb = None,
            imdb_votes = 0,
            date = None,
            company_id = 0,
            country_id = 0,
            country2_id = 0,
            genre1_id = 0,
            genre2_id = 0,
            genre3_id = 0,
            director1 = 0,
            director2 = 0,
            director3 = 0,
            site = '',
            name = '',
            datelastupd = datetime.datetime.now(),
        )

        FilmExtData.objects.using('afisha').create(
            id = new_id,
            rate1 = 0,
            rate2 = 0,
            rate3 = 0,
            rate = float(0),
            vnum = 0,
            opinions = '',
        )
        
        slug = low(del_separator(name.encode('utf-8')))
        
        try:
            films_name_create(film_obj, name.encode('utf-8'), lang, 1, slug)
        except db.backend.Database._mysql.OperationalError:
            name = name.encode('ascii', 'xmlcharrefreplace')
            films_name_create(film_obj, name, lang, 1, slug)

    except db.IntegrityError:
        film_obj = Film.objects.using('afisha').get(id = new_id)

    if create:
        Films.objects.get_or_create(
            kid = film_obj.id,
            defaults = {
                'year': year,
                'kid': film_obj.id
            })
    
    return film_obj
    

@never_cache
def film_create_new(request):
    film_editor = is_film_editor(request)
    if film_editor:
        if request.POST:
            name = request.POST.get('new_name').strip()
            year = request.POST.get('new_year').strip()
            lang = request.POST.get('new_lang')
            imdb = request.POST.get('im_db').strip()
            if year and name:
                film_obj = film_create_new_func(name, year, lang, imDB=imdb)

                profile = request.profile
                actions_logger(5, film_obj.id, profile, '1') # фильм Название
                actions_logger(6, film_obj.id, profile, '1') # фильм Год
            
            return HttpResponseRedirect(reverse('get_film', kwargs={'id': film_obj.id}))
            
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404

@only_superuser
@never_cache
def film_delete(request):
    current_year = datetime.datetime.now().year

    if request.POST:
        id = request.POST.get('del')
        if id:
            # Киноафиша
            film_afisha = Film.objects.using('afisha').get(pk=id)
            FilmsName.objects.using('afisha').filter(film_id__pk=id).delete()
            FilmExtData.objects.using('afisha').filter(id=id).delete()
            PersonsRelationFilms.objects.using('afisha').filter(film_id__pk=id).delete()
            Schedule.objects.using('afisha').filter(film_id__pk=id).delete()
            AfishaNews.objects.using('afisha').filter(obj__pk=id).delete()
            FilmsRamb.objects.using('afisha').filter(id_film__pk=id).delete()
            FilmsCodes.objects.using('afisha').filter(film__pk=id).delete()
            Gathering.objects.using('afisha').filter(film__pk=id).delete()
            FilmSound.objects.using('afisha').filter(film_id__pk=id).delete()

            poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(
                objtypeid__in=[301, 300, 3], 
                objpkvalue=id
            )
            tr_ids = [i.extresid_id for i in poster_obj if i.objtypeid == 3]
            TrailerInfo.objects.using('afisha').filter(trailer_id__in=tr_ids).delete()
            for i in poster_obj:
                if i.objtypeid != 3 and i.extresid:
                    i.extresid.delete()
            poster_obj.delete()


            # Киноинфо
            film = Films.objects.filter(kid=id)
            Likes.objects.filter(film=id).delete()
            FilmsVotes.objects.filter(kid=id).delete()
            RelationFP.objects.filter(films__kid=id).delete()
            FilmsBudget.objects.filter(kid=id).delete()
            KIFilmRelations.objects.filter(kid=id).delete()
            SourceSchedules.objects.filter(film__source_id=id, source_obj__url="http://www.kinoafisha.ru/").delete()
            SourceFilms.objects.filter(source_id=id, source_obj__url="http://www.kinoafisha.ru/").delete()
            AwardsRelations.objects.filter(kid=id).delete()
            RaspishiRelations.objects.filter(kid=id).delete()
            Nowru.objects.filter(kid=id).delete()
            UkrainePosters.objects.filter(kid=id).delete()
            ReleasesRelations.objects.filter(film_kid=id).delete()
            NotFoundFilmsRelations.objects.filter(kid=id).delete()
            SubscriptionRelease.objects.filter(kid=id).delete()
            SubscriptionTopics.objects.filter(kid=id).delete()
            BoxOffice.objects.filter(kid=id).delete()
            NewsFilms.objects.filter(kid=id).delete()
            MovieMegogo.objects.filter(afisha_id=id).delete()
            IntegralRating.objects.filter(afisha_id=id).delete()

            film_afisha.delete()
            film.delete()

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

        return HttpResponseRedirect(reverse('get_film_list', kwargs={'year': current_year}))

    raise Http404


@only_superuser
@never_cache
def change_film_left_banner(request):
    if request.POST:
        img_path = '%s/film_left_banner.swf' % settings.BACKGROUND_PATH
        
        if 'save' in request.POST and 'banner' in request.FILES:
            file = request.FILES.get('banner').read()
            with open(img_path, 'wb') as f:
                f.write(file)
                
        elif 'delete' in request.POST:
            try:
                os.remove(img_path)
            except OSError: pass  
        
        
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404



