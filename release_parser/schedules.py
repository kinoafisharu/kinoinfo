#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import os
import datetime
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.utils import translation

from bs4 import BeautifulSoup
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from api.models import *
from base.models import *
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, language_identify
from release_parser.func import cron_success

from movie_online.IR import check_int_rates, check_int_rates_inlist


                        
'''
@only_superuser
@never_cache
def cmc_film_ident(request):

    #Идентификация фильмов, городов, кинотеатров, залов от СМС

    # xml файлы для чтения/хранения данных
    xml = open('%s/dump_cmc_schedules.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    # переменные для хранения найденных/ненайденных данных
    good_data = ''
    data_good_film = ''
    data_nof_film = ''
    data_nof_cinema = ''
    data_nof_city = ''
    data_nof_hall = ''
    today = datetime.date.today()
    next_month = today + datetime.timedelta(days=30)
    # разбор xml тегов
    for release in xml_data.findAll('data'):
        release_date = release['value'].encode('utf-8')
        release_date = datetime.date(int(release_date[:4]), int(release_date[5:7]), int(release_date[8:10]))
        if release_date <= next_month:
            for cinema in release.findAll('cinema'):
                cinema_name = cinema['name'].replace('"', "'").encode('utf-8').strip()
                city = cinema['city'].encode('utf-8')
                for hall in cinema.findAll('hall'):
                    hall_name = hall['title'].replace('"', "'").encode('utf-8')
                    for film in hall.findAll('film'):
                        # получение, приведение к нужному виду названий фильмов
                        film_name = film['title'].replace('"', "'").encode('utf-8').strip()
                        film_slug = del_screen_type(film_name)
                        film_slug = low(del_separator(film_slug))
                        # блок с данными времени сеансов
                        seans_xml_block = ''
                        for seans in film.findAll('seans'):
                            stime = seans['time'].encode('utf-8')
                            seans_xml_block += '<seans time="%s"></seans>' % stime
                        # если СМС не предоставил id киноафиши, то идентифицирую фильм
                        kid, info = film_identification(film_slug, None, {}, {})
                        # если фильм нашел (идентифицировал)
                        if kid:
                            # создаю xml тег для фильма
                            film_tag = '<film name_ru="%s" slug_ru="%s" name="*" slug="*" kid="%s" data="%s">' % (film_name, film_slug, kid, release_date)
                            # если такого тега нет в найденных, то добавляю
                            if 'slug_ru="%s"' % film_slug not in data_good_film:
                                ctag = '<cinema title="%s" id="%s" hall="%s"></cinema>' % (cinema_name, cinema['id'].encode('utf-8'), hall_name)
                                data_good_film += '%s%s%s</film>' % (film_tag, ctag, seans_xml_block)

                            # приведение к нужному виду названий города, кинотеатра, зала
                            cin = cinema_name
                            
                            cin_slug = low(del_separator(cin))
                            city_slug = low(del_separator(city))
                            hall_slug = low(del_separator(hall_name))
                            hall_n = hall_name if hall_name else 'None'
                            hall_s = hall_slug if hall_slug else 'None'
                            # идентификация города
                            c = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
                            # если нашел
                            if c.count() == 1:
                                # идентификация кинотеатра
                                filter1 = {'name__name': cin_slug, 'name__status': 2, 'city': c[0]}
                                cinema_kid = cinema_identification(cin_slug, filter1)
                                if cinema_kid:
                                    # идентификация зала
                                    hall_obj = Hall.objects.filter(name__name=hall_slug, cinema__code=cinema_kid).distinct('pk')
                                    # если нашел
                                    if hall_obj.count() == 1:
                                        # все объекты идентифицированны, добавляю к идентифицированным
                                        cinema_tag = '<cinema title="%s" kid="%s" id="%s" hall="%s" hall_kid="%s"></cinema>' % (cinema_name, cinema_kid, cinema['id'].encode('utf-8'), hall_name, hall_obj[0].kid)
                                        good_data += '%s%s%s</film>' % (film_tag, cinema_tag, seans_xml_block)
                                    # если зал ненайден
                                    else:
                                        id = '%s%s%s%s' % (city, cin, hall_n, hall_s)
                                        id = id.replace(' ','')
                                        # если такого тега нет в ненайденных, то добавляю
                                        if 'id="%s"' % id not in data_nof_hall:
                                            data_nof_hall += '<hall city="%s" city_kid="%s" cinema="%s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city, c[0].kid, cin, cinema_kid, hall_n, hall_s, id)
                                # если кинотеатр ненайден
                                else:


                                    # если такого тега нет в ненайденных, то добавляю
                                    if 'city_kid="%s"' % c[0].kid not in data_nof_cinema:
                                        data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cin, cin_slug, city, c[0].kid)
                            # если город ненайден
                            else:

                                # если такого тега нет в ненайденных, то добавляю
                                if 'slug="%s"' % city_slug not in data_nof_city:
                                    data_nof_city += '<city name="%s" slug="%s"></city>' % (city, city_slug)
                        # если фильм ненайден
                        else:
                            # если такого тега нет в ненайденных, то добавляю
                            if 'slug_ru="%s"' % film_slug not in data_nof_film:
                                film_tag = '<film name_ru="%s" slug_ru="%s" name="*" slug="*" data="%s">' % (film_name, film_slug,  release_date)
                                ctag = '<cinema title="%s" id="%s" hall="%s"></cinema>' % (cinema_name, cinema['id'].encode('utf-8'), hall_name)
                                data_nof_film += '%s%s%s</film>' % (film_tag, ctag, seans_xml_block)
    
    # сохранение найденных/ненайденных данных
    open('%s/dump_cmc_good_films.xml' % settings.API_DUMP_PATH, 'w').write('<data>%s</data>' % data_good_film)
    open('%s/dump_cmc_nof_films.xml' % settings.NOF_DUMP_PATH, 'w').write('<data>%s</data>' % data_nof_film)
    open('%s/dump_cmc_nof_city.xml' % settings.NOF_DUMP_PATH, 'w').write('<data>%s</data>' % data_nof_city)
    open('%s/dump_cmc_nof_cinema.xml' % settings.NOF_DUMP_PATH, 'w').write('<data>%s</data>' % data_nof_cinema)
    open('%s/dump_cmc_nof_hall.xml' % settings.NOF_DUMP_PATH, 'w').write('<data>%s</data>' % data_nof_hall)
    open('%s/dump_cmc_kid_schedules.xml' % settings.API_DUMP_PATH, 'w').write('<data>%s</data>' % good_data)
    return HttpResponseRedirect(reverse('schedule_main'))
'''
      
@only_superuser
@never_cache
def city_nof_list(request, method):
    '''
    Форма для ненайденных городов/кинотеатров/залов
    '''
    xml_files = ['dump_cmc_nof_', 'dump_planeta_nof_', 'dump_kinohod_nof_', 'dump_rambler_nof_', 'dump_megamag_nof_', 'dump_okinoua_nof_']
    count = 0
    f = {}
    kid = ''
    for x in xml_files:
        # чтение из xml
        try:
            xml_nof = open('%s/%s%s.xml' % (settings.NOF_DUMP_PATH, x, method), 'r')
            xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
            xml_nof.close()
            for i in xml_nof_data.findAll(method):
                # формирую данные для выводв в форму
                name = i['name'].encode('utf-8').replace('&', '&amp;')
                slug = i['slug'].encode('utf-8')
                if method == 'cinema':
                    kid = i['city_kid'].encode('utf-8')
                if method == 'hall':
                    kid = i['cinema_kid'].encode('utf-8')
                key = '%s @ %s @ %s' % (name, slug, kid)
                if method == 'hall':
                    key = '%s @ %s @ %s @ %s' % (name, slug, i['id'].encode('utf-8'), kid)
                if method != 'city':
                    if method == 'cinema':
                        value = '%s @ %s' % (name, i['city'].encode('utf-8'))
                    else:
                        value = '%s @ %s @ %s' % (name, i['cinema'].encode('utf-8'), i['city'].encode('utf-8'))
                else:
                    value = name
                if not f.get(key):
                    f[key] = {'value': value, 'key': key}
                    count += 1
        except IOError: pass
    if f:
        f = sorted(f.values())
    return render_to_response('release_parser/city_nof_list.html', {'f': f, 'count': count, 'method': method}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def city_cinema_nof(request, method):
    '''
    Обработка ненайденных городов/кинотеатров
    '''
    if request.method == 'POST':
        nof_data = request.POST['nof_data']
        data = request.POST['data']
        
        if data:
            xml_files = ['dump_cmc_nof_', 'dump_planeta_nof_', 'dump_kinohod_nof_', 'dump_rambler_nof_', 'dump_megamag_nof_', 'dump_okinoua_nof_']
            for x in xml_files:
                try:
                    # чтение из xml
                    xml_nof = open('%s/%s%s.xml' % (settings.NOF_DUMP_PATH, x, method), 'r')
                    xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
                    xml_nof.close()
                    # получение данных для связи между собой
                    nof = nof_data.split(' @ ')
                    nof_name = nof[0]
                    nof_slug = nof[1]
                    # удаление обрабатываемого элемента их xml файла
                    for i in xml_nof_data.find_all(method, slug=nof_slug):
                        xml_nof_data.find(method, slug=nof_slug).extract()
                    
                    # получаю объект для связи
                    model1, model2 = (City, NameCity) if method == 'city' else (Cinema, NameCinema)
                    obj = model1.objects.get(pk=data)
                    
                    names = [
                        {'name': nof_name, 'status': 0}, 
                        {'name': nof_slug, 'status': 2}
                    ]
                    
                    if request.POST.get('kid_sid'):
                        if method == 'cinema':
                            nof_obj, nof_created = NotFoundCinemasRelations.objects.get_or_create(
                                name=nof_slug,
                                defaults={
                                    'kid': data, 
                                    'name': nof_slug,
                                })
                    else:
                        # создаю объект названия, если не создан, и связываю, если нет связи
                        for i in names:
                            name_obj, created = model2.objects.get_or_create(
                                name=i['name'], 
                                status=i['status'], 
                                defaults={
                                    'name': i['name'], 
                                    'status': i['status']
                                })
                            if name_obj not in obj.name.all():
                                obj.name.add(name_obj)

                    # запись изменений в файл
                    xml_nof = open('%s/%s%s.xml' % (settings.NOF_DUMP_PATH, x, method), 'w')
                    xml_nof.write(str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>',''))
                    xml_nof.close()
                except IOError: pass
    return HttpResponseRedirect(reverse("city_nof_list", kwargs={'method': method}))


@only_superuser
@never_cache
def hall_nof(request):
    '''
    Обработка ненайденных залов
    '''
    if request.method == 'POST':
        nof_data = request.POST['nof_data']
        data = request.POST['data']
        if data:
            xml_files = ['dump_cmc_nof_', 'dump_planeta_nof_']
            for x in xml_files:
                try:
                    # чтение из xml
                    xml_nof = open('%s/%shall.xml' % (settings.NOF_DUMP_PATH, x), 'r')
                    xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
                    xml_nof.close()
                    # получение данных для связи между собой
                    nof = nof_data.split(' @ ')
                    nof_name = nof[0]
                    nof_slug = nof[1]
                    nof_id = nof[2]

                    # удаление обрабатываемого элемента их xml файла
                    for i in xml_nof_data.find_all('hall', id=nof_id):
                        xml_nof_data.find('hall', id=nof_id).extract()
                    
                    # получаю объект для связи
                    obj = Hall.objects.get(pk=data)
                    
                    names = [
                        {'name': nof_name, 'status': 0}, 
                        {'name': nof_slug, 'status': 2}
                    ]
                    
                    # создаю объект названия, если не создан, и связываю, если нет связи
                    for i in names:
                        if i['name'] != 'None':
                            name_obj, created = NameHall.objects.get_or_create(name=i['name'], status=i['status'], defaults={'name': i['name'], 'status': i['status']})
                            
                            if name_obj not in obj.name.all():
                                obj.name.add(name_obj)

                    # запись изменений в файл
                    xml_nof = open('%s/%shall.xml' % (settings.NOF_DUMP_PATH, x), 'w')
                    xml_nof.write(str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>',''))
                    xml_nof.close()
                except IOError: pass
    return HttpResponseRedirect(reverse("city_nof_list", kwargs={'method': 'hall'}))

# deprecated
@only_superuser
@never_cache
def cmc_film_list_form(request):
    '''
    Обработка ненайденных фильмов с фильтами
    '''
    from api.panel import pagination
    xml = open('%s/dump_cmc_good_films.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    xml = open('%s/dump_cmc_nof_film.xml' % settings.NOF_DUMP_PATH, 'r')
    xml_nof_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    f_name = None
    f_value = '0'
    city_filter = None
    cinema_filter = None
    f = []
    cities = []
    cinemas = []
    # фильтрация в режиме ручного выбора фильтра
    xml_data_list = [xml_data, xml_nof_data]
    if request.POST:
        # фильт Найденные/Ненайденные
        if 'found' in request.POST and request.POST['found']:
            f_name = 'found'
            f_value = request.POST[f_name]
            xml_data_list = [xml_data] if int(request.POST['found']) == 1 else [xml_nof_data]
        elif 'city' in request.POST and request.POST['city']:
            f_name = 'city'
            f_value = request.POST[f_name].encode('utf-8')
            city_filter = f_value
        elif 'cinema' in request.POST and request.POST['cinema']:
            f_name = 'cinema'
            f_value = request.POST[f_name].encode('utf-8')
            cinema_filter = f_value
    if not f_name:
        if 'filter_cmc_name' in request.COOKIES and 'filter_cmc_value' in request.COOKIES:
            filter_name = request.COOKIES["filter_cmc_name"]
            filter_value = request.COOKIES["filter_cmc_value"]
            f_name = filter_name
            f_value = filter_value
            # фильт Найденные/Ненайденные
            if 'found' in filter_name:
                xml_data_list = [xml_data] if int(filter_value) == 1 else [xml_nof_data]
            elif 'city' in filter_name:
                city_filter = f_value
            elif 'cinema' in filter_name:
                cinema_filter = f_value
    try:
        f_v = int(f_value)
    except ValueError:
        f_v = f_value
    fil = {'name': f_name, 'value': f_v}
    
    def create_film_dict(i):
        name_ru = i['name_ru'].encode('utf-8').replace('&', '&amp;')
        slug_ru = i['slug_ru'].encode('utf-8')
        kid = i.get('kid')
        if kid:
            try:
                kid = Film.objects.using('afisha').get(pk=kid)
            except Film.DoesNotExist:
                kid = None
        key = '%s @ *' % name_ru
        di = {
            'name': key,
            'name2': '%s / *' % name_ru,
            'k_obj': kid
        }
        if di not in f:
            f.append(di)
    
    for j in xml_data_list:
        for i in j.findAll('film'):
            cinema = i.cinema['title'].encode('utf-8').split(' ')
            cin = ''
            for ind, c in enumerate(cinema):
                if ind == 0:
                    city = c
                else:
                    cin += c + ' '
            cin = cin.strip()
            if city not in cities:
                cities.append(city)
            if cin not in cinemas:
                cinemas.append(cin)
            if city_filter:
                if city_filter == city:
                    create_film_dict(i)
            elif cinema_filter:
                if cinema_filter == cin:
                    create_film_dict(i)
            else:
                create_film_dict(i)
    cities = sorted(cities)
    cinemas = sorted(cinemas)
    p = pagination(request, sorted(f, key=operator.itemgetter('name')), 17)
    resp = render_to_response('release_parser/cmc_film_list_form.html', {'p': p, 'fil': fil, 'cities': cities, 'cinemas': cinemas}, context_instance=RequestContext(request))
    # ставлю куки с данными фильтра
    resp.set_cookie("filter_cmc_name", f_name)
    resp.set_cookie("filter_cmc_value", f_value)
    return resp


# структурирование данных, создание диапозонов
def create_schedule_data_range(data):
    schedule = {}
    for i in data:
        s = schedule.get(i['film'])
        if s:
            m = schedule.get(i['film']).get(i['movie'])
            if m:
                h = schedule[i['film']][i['movie']].get(i['hall'])
                if h:
                    d = schedule[i['film']][i['movie']][i['hall']].get(i['date'].date())
                    if d:
                        if i['date'].time not in d:
                            schedule[i['film']][i['movie']][i['hall']][i['date'].date()].append(i['date'].time())
                            schedule[i['film']][i['movie']][i['hall']][i['date'].date()].sort()
                    else:
                        schedule[i['film']][i['movie']][i['hall']][i['date'].date()] = [i['date'].time()]
                else:
                    schedule[i['film']][i['movie']][i['hall']] = {i['date'].date(): [i['date'].time()]}
            else:
                schedule[i['film']][i['movie']] = {i['hall']: {i['date'].date(): [i['date'].time()]}}
        else:
            schedule[i['film']] = {i['movie']: {i['hall']: {i['date'].date(): [i['date'].time()]}}}

    schedule_listt = []
    for k, v in schedule.iteritems():
        film = k
        for kk, vv in v.iteritems():
            movie = kk
            for kkk, vvv in vv.iteritems():
                hall = kkk
                d = ''
                dates = {}
                keyy = ''
                for i in sorted(vvv.items()):
                    if not d:
                        d = i[0]
                        dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'hall': hall, 'movie': movie}
                        keyy = d
                    else:
                        d = i[0]
                        d_prev = d - datetime.timedelta(days=1)
                        if d_prev == dates[keyy]['to']:
                            if set(dates[keyy]['time']) == set(i[1]):
                                dates[keyy]['to'] = d
                            else:
                                dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'hall': hall, 'movie': movie}
                                keyy = d
                        else:
                            dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'hall': hall, 'movie': movie}
                            keyy = d
                for i in dates.values():
                    schedule_listt.append(i)
    return schedule_listt



@never_cache
def sources_schedules_list_ajax(request, city=None, cinema=None,  id=None):
    kinohod_key = settings.KINOHOD_APIKEY_CLIENT
    current_site = request.current_site
    current_language = translation.get_language()
    user = request.user if request.user.is_authenticated() else None

    filter = {}
    film_list = []
    country = None
    alert = None
    city_name = None
    cinema_name = None
    flag = False
    
    # если вместо ид (цифры) города передали буквы
    if city:
        try:
            city = int(city)
            flag = True
        except (UnicodeEncodeError, ValueError):
            city = 'error'
    
    # если вместо ид (цифры) кинотеатра передали буквы
    if cinema:
        try:
            cinema = int(cinema)
        except (UnicodeEncodeError, ValueError):
            cinema = 'error'
    
    acc_list = RequestContext(request).get('acc_list')
    
    if acc_list:
        user_country = acc_list.get('country_id')

        if user_country:
            country = user_country
            user_city = acc_list.get('city_id')
            if not city and city != 'error':
                city = user_city
    
    if current_site.domain == 'kinoafisha.in.ua':
        country = 43
        
    # если указана страна у юзера
    if country:
        filter = {'cinema__cinema__city__country__id': country}

    today = datetime.date.today()
    #today = datetime.date(2013, 10, 17)
    next_month = today + datetime.timedelta(days=30)
    
    cities = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lte=next_month, cinema__cinema__city__name__status=3, cinema__cinema__name__status=1).filter(**filter).exclude(film__source_id=0).values('cinema__cinema__city', 'cinema__cinema__city__name__name', 'cinema__cinema', 'cinema__cinema__name__name').distinct('cinema__cinema__city'))
    
    cities_dict = {}
    for i in cities:
        cin_dic = {'name': i['cinema__cinema__name__name'], 'id': int(i['cinema__cinema'])}
        if cities_dict.get(i['cinema__cinema__city']):
            cities_dict[i['cinema__cinema__city']]['cinema'].append(cin_dic)
        else:
            cities_dict[i['cinema__cinema__city']] = {'name': i['cinema__cinema__city__name__name'], 'id': int(i['cinema__cinema__city']), 'cinema': [cin_dic]}

    cities = sorted(cities_dict.values(), key=operator.itemgetter('name'))

    if cities:
        if city:
            if city != 'error':
                city_data = cities_dict.get(int(city))
                # указан город и есть в БД
                if city_data:
                    city = city_data
                # указан город и нет в БД
                else:
                    city = None
            else:
                city = None
        else:
            # в первый раз без города, даю первый город в списке
            city = cities[0]

        if city:
            if not cinema:
                cinemas = sorted(city['cinema'], key=operator.itemgetter('name'))
                cinema = cinemas[0]['id']
            city = city['id']

    
    if city == 'error':
        city = None
    
    if city:
        city_name = NameCity.objects.get(city__id=city, status=3)
        if cinema and cinema != 'error':
            try:
                cinema_name = NameCinema.objects.get(cinema__id=cinema, status=1, cinema__city__id=city)
            except NameCinema.DoesNotExist: pass
            except NameCinema.MultipleObjectsReturned:
                cinema_name = NameCinema.objects.filter(cinema__id=cinema, status=1, cinema__city__id=city)[0]
            
            film_list = set(list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lte=next_month, cinema__cinema__id=cinema, cinema__cinema__city__id=city).exclude(film__source_id=0).values_list('film__kid', flat=True)))
        else:
            cinema_name = ''
    
    fnames_dict = {}

    t = '' 
    uk_films = []
    
    if current_site.domain == 'kinoafisha.in.ua':
        t = 'kua_'
        if city:
            if current_language == 'uk':
                uk_sources = ('http://www.okino.ua/', 'http://kino-teatr.ua/')
                film_name = SourceFilms.objects.select_related('source_obj').filter(source_obj__url__in=uk_sources, kid__in=film_list)
                for n in film_name:
                    if n.source_obj.url == 'http://www.okino.ua/' and n.name_alter:
                        if fnames_dict.get(n.kid):
                            fnames_dict[n.kid]['names'].append(n.name_alter)
                        else:
                            fnames_dict[n.kid] = {'names': [n.name_alter], 'genres': [], 'rate_imdb': [], 'obj': None}
                        if re.findall(ur'[а-яА-Я]', n.name_alter):
                            uk_films.append(n.kid)
                    elif n.source_obj.url == 'http://kino-teatr.ua/':
                        if fnames_dict.get(n.kid):
                            fnames_dict[n.kid]['names'].append(n.name)
                        else:
                            fnames_dict[n.kid] = {'names': [n.name], 'genres': [], 'rate_imdb': [], 'obj': None}
                        if re.findall(ur'[а-яА-Я]', n.name):
                            uk_films.append(n.kid)
    
    if city and film_list:
        film_name = FilmsName.objects.using('afisha').select_related('film_id', 'film_id__genre1', 'film_id__genre2', 'film_id__genre3', 'film_id__imdb').filter(type=2, film_id__id__in=film_list, status=1).order_by('-type')

        for n in film_name:
            if n.film_id_id not in uk_films:
                if fnames_dict.get(n.film_id_id):
                    fnames_dict[n.film_id_id]['names'].append(n.name)
                else:
                    fnames_dict[n.film_id_id] = {'names': [n.name], 'genres': [], 'rate_imdb': n.film_id.imdb, 'obj': n.film_id}
            else:
                fnames_dict[n.film_id_id]['rate_imdb'] = n.film_id.imdb
                
            if not fnames_dict[n.film_id_id]['genres']:
                genres = [n.film_id.genre1, n.film_id.genre2, n.film_id.genre3]
                for i in genres:
                    if i:
                        fnames_dict[n.film_id_id]['genres'].append(i.name)
    data_rate = {}
    
    frates = check_int_rates_inlist(fnames_dict.keys())
    
    ids_list = []
    for k, v in fnames_dict.iteritems():
        name_ru = (sorted(v['names'], reverse=True))
        name_ru = name_ru[0]

        # получит интегральную оценку
        frate = frates.get(k)
        int_rate = frate['int_rate']
        show_ir = frate['show_ir']
        show_imdb = frate['show_imdb']
        rotten = frate['rotten']
            
        fdata = {'name': name_ru, 'kid': k, 'genres': v['genres'], 'rate': int_rate, 'show_ir': show_ir, 'show_imdb': show_imdb, 'rotten': rotten}
        
        ids_list.append(int(k))
        
        if data_rate.get(int_rate):
            data_rate[int_rate]['data'].append(fdata)
        else:
            data_rate[int_rate] = {'rate': int_rate, 'data': [fdata]}
            

    kinoinfo_film = sorted(data_rate.values(), key=operator.itemgetter('rate'), reverse=True)
    first_load_film = None
    # для slideblock проверяем получен ли в функцию айди фильма для отображения
    # отобразит фильм, который загрузится первым
    if id and int(id) in ids_list:
        first_load_film = id
    else:
        if kinoinfo_film:
            first_load_film = sorted(kinoinfo_film[0]['data'], key=operator.itemgetter('name'))
            first_load_film = first_load_film[0]['kid']   

    template = 'release_parser/%scmc_schedules_list_ajax2.html' % ''
    return render_to_response(template, {'data': kinoinfo_film, 'cities': cities,  'first_load_film': first_load_film, 'alert': alert, 'city': city, 'city_name': city_name, 'cinema': cinema, 'cinema_name': cinema_name, 'flag': flag, 'kinohod_key': kinohod_key}, context_instance=RequestContext(request))




@never_cache
def sources_schedules_list_ajax2(request):
    '''
    Киноафиша Вашего города
    '''
    user_city = request.user.get_profile().person.city_id if request.user.is_authenticated() else None

    #request.session['filter_schedule_city_cinema'] = '' # ------------__!!!!!!!!!!
    
    cities = {}
    
    fil = {}
    city_filter = {}
    f_city = None
    f_cinema = None
    alert = None
    sch_dict = {}
    
    extended_data = {}
    kinoinfo_film_list = []
    kinoinfo_film = []
    
    today = datetime.date.today()
    
    #today = datetime.date(2013, 7, 18) # ----------------------------!!!!!!!!!!!!!!!!
    
    next_month = today + datetime.timedelta(days=30)
    
    # массив кинотеатров в которых есть сеансы в конкретном городе
    def get_cinema_data(fcity):
        cinemas = {}
        s = KinobitSchedules.objects.select_related('cinema', 'cinema__cinema', 'cinema__cinema__city', 'film').filter(dtime__gte=today, dtime__lte=next_month, cinema__cinema__city__id=fcity).distinct('cinema__cinema__city_id')
        for i in s:
            if not cinemas.get(i.cinema.cinema_id):
                for j in i.cinema.cinema.name.all():
                    if j.status == 1:
                        cinemas[i.cinema.cinema_id] = {'name': j.name, 'city': fcity, 'id': i.cinema.cinema_id}
        cinemas = sorted(cinemas.values(), key=operator.itemgetter('name'))
        return cinemas
                        
    # получаю список id городов в которых есть сеансы
    citcit = list(KinobitSchedules.objects.select_related('cinema', 'cinema__cinema', 'cinema__cinema__city', 'film').filter(dtime__gte=today, dtime__lte=next_month).values_list('cinema__cinema__city', flat=True).distinct('cinema__cinema__city'))

    # получаю города по списку id
    user_country = request.user.get_profile().person.country_id if request.user.is_authenticated() else None
    country_filter = {'pk__in': citcit, 'country': user_country} if user_country else {'pk__in': citcit}
    citycity = City.objects.filter(**country_filter)

    # массив id города : название города
    for i in citycity:
        for n in i.name.all():
            if n.status == 1:
                cities[i.id] = {'name': n.name, 'id': i.id}
    
    
    user_city = cities.get(user_city) if cities.get(user_city) else None

    cities = sorted(cities.values(), key=operator.itemgetter('name'))
    
    
    # беру данные отправленные пользователем
    if request.POST:
        if 'city' in request.POST and 'cinema' in request.POST:
            cinema_post = request.POST['cinema'].split(' @ ')
            ci_id = cinema_post[0]
            ci_city = cinema_post[1]
            # если был выбран другой кинотеатр
            if ci_city == request.POST['city']:
                f_city = request.POST['city']
                city_filter = {'hall__cinema__id': ci_id}
                cinemas = get_cinema_data(f_city)
                f_cinema = ci_id
            
    # беру данные из сессии пользователя
    if not f_city and request.POST.get('city') is None:
        if request.session.get('filter_schedule_city_cinema'):
            session_value = request.session['filter_schedule_city_cinema'].split(';')
            f_city = session_value[0]
            f_cinema = session_value[1]
            if f_cinema != 'None':
                city_filter = {'cinema__cinema__id': f_cinema}
                cinemas = get_cinema_data(f_city)
            else:
                f_cinema = None

    # если первая загрузка страницы, город небыл выбран
    if f_city is None:
        if request.POST.get('city'):
            f_city = request.POST['city']
            if user_city and user_city['id'] != int(f_city):
                alert = int(f_city)
        else:
            f_city = user_city['id'] if user_city else 1
        cinemas = get_cinema_data(f_city)
        for i in cinemas:
            f_cinema = i['id']
            break
        city_filter = {'cinema__cinema__id': f_cinema}
    
    if f_city and not f_cinema:
        cinemas = get_cinema_data(f_city)
        for i in cinemas:
            f_cinema = i['id']
            break
        city_filter = {'cinema__cinema__id': f_cinema}

    if f_cinema:
        
        fil = {
            'city': int(f_city),
            'cinema' : int(f_cinema),
        }

        kinoinfo_film_list = list(KinobitSchedules.objects.select_related('cinema', 'cinema__cinema', 'film').filter(**city_filter).filter(dtime__gte=today, dtime__lte=next_month).values_list('film__kid', flat=True).distinct('kid'))

        

        film_name = FilmsName.objects.using('afisha').filter(type__in=(1, 2), film_id__id__in=kinoinfo_film_list, status=1).order_by('-type')
        fnames_dict = {}
        for n in film_name:
            if fnames_dict.get(n.film_id_id):
                fnames_dict[n.film_id_id].append(n.name)
            else:
                fnames_dict[n.film_id_id] = [n.name]
                
        kinoinfo_film = []
        for k, v in fnames_dict.iteritems():
            name_ru = v[0]
            kinoinfo_film.append({'name': name_ru, 'kid': k})
            
    if kinoinfo_film:
        kinoinfo_film = sorted(kinoinfo_film, key=operator.itemgetter('name'))
    #kinoinfo_film = sorted(kinoinfo_film)
    
    first_load_film = kinoinfo_film[0]['kid'] if kinoinfo_film else None

    sess_data = '%s;%s' % (f_city, f_cinema)
    request.session['filter_schedule_city_cinema'] = sess_data

    

    return render_to_response('release_parser/cmc_schedules_list_ajax.html', {'data': kinoinfo_film, 'fil': fil, 'cities': cities, 'cinemas': cinemas, 'first_load_film': first_load_film, 'f_cinema': f_cinema, 'alert': alert}, context_instance=RequestContext(request))



def get_time_hours(h):
    time_hours = {
        '0': '24', '1': '25', '2': '26', '3': '27', '4': '28', '5': '29',
        '24': 0, '25': 1, '26': 2, '27': 3, '28': 4, '29': 5,
    }
    return time_hours.get(str(h))
    

def str_to_datetime(obj):
    '''
     преобразование строки к формату дата-время
    '''
    yyyy = int(obj[:4])
    mm = int(obj[4:6])
    dd = int(obj[6:8])
    h = int(obj[8:10])
    m = int(obj[10:12])
    s = int(obj[12:14])
    if h > 23:
        h = get_time_hours(h)
    return datetime.datetime(yyyy, mm, dd, h, m, s)


def datetime_to_str(i):
    '''
     преобразование дата-время к строковому формату
    '''
    if i.hour >= 0 and i.hour <= 5:
        hour = get_time_hours(i.hour)
        minute = '{0:0=2d}'.format(i.minute)
        t = '%s%s00' % (hour, minute)
    else:
        t = str(i.time()).replace(':','')
    dtime = int('%s%s' % (str(i.date()).replace('-',''), t))
    return dtime



@only_superuser
@never_cache
def schedules_export_to_kinoafisha_log(request, dump):
    '''
    Лог экспорта на киноафишу
    '''
    from api.panel import pagination
    # открываю файл лога
    try:
        xml = open('%s/dump_%s.xml' % (settings.LOG_DUMP_PATH, dump), 'r')
    except IOError:
        return HttpResponse('Не существует лог-дампа')
        
    
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    movies_obj = {}
    films_obj = {}
    movies = []
    
    today = datetime.date.today()
    
    log = xml_data.find('info')
    cinema_del = log.get('cinema_del')
    session_del = log.get('session_del')
    cinema_save = log.get('cinema_save')
    session_save = log.get('session_save')

    cinema_now = len(list(AfishaSession.objects.using('afisha').filter(schedule_id__date_to__gte=today).values_list('schedule_id__movie_id', flat=True).distinct('schedule_id__movie_id')))
    
    session_now = len(list(AfishaSession.objects.using('afisha').filter(schedule_id__date_to__gte=today).values_list('id', flat=True).distinct('id')))

    cinema_ids = [i.text for i in xml_data.find_all('id')]
    cinema_ids_count = len(cinema_ids)

    for i in xml_data.find_all('movie'):
        try:
            # получаю объект кинотеатр, и его название
            movie_data = movies_obj.get(i['kid'])
            if not movie_data:
                movie = Cinema.objects.get(code=i['kid'])
                for n in movie.name.all():
                    if n.status==1:
                        name = n.name
                movies_obj[i['kid']] = {'obj': movie, 'name': name}
            else:
                movie = movie_data['obj']
                name = movie_data['name']
            
            # получаю объект фильм, и его название
            film_data = films_obj.get(i['film_kid'])
            
            if not film_data:
                film = Film.objects.using('afisha').get(pk=i['film_kid'])
                for n in film.filmsname_set.all():
                    if n.type == 2 and n.status==1:
                        film_name = n.name.encode('utf-8')
                films_obj[i['film_kid']] = {'obj': film, 'name': film_name}
            else:
                film = film_data['obj']
                film_name = film_data['name']
            
            # добавляю массив данных о сеансе в список, для вывода в шаблоне
            movies.append({'kid': i['kid'], 'name': name, 'from': i['from'].split('-')[2], 'to': i['to'].split('-')[2], 'time': i['time'], 'film': film_name, 'film_kid': i['film_kid']})
        except: pass

    m = sorted(movies)
    p = pagination(request, m, 17)
    return render_to_response('release_parser/export_to_kinoafisha_log.html', {'p': p, 'cinema_del': cinema_del, 'cinema_save': cinema_save, 'cinema_now': cinema_now, 'session_del': session_del, 'session_save': session_save, 'session_now': session_now, 'cinema_ids': cinema_ids, 'cinema_ids_count': cinema_ids_count}, context_instance=RequestContext(request))

    

@only_superuser
@never_cache
def equal_cmc_kinoafisha(request):
    '''
    Дубли на кинафише
    '''
    today = datetime.date.today()
    # выборка сеансов у которых текущая дата попадает в диапозон
    afisha_obj = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id').filter(schedule_id__date_from__lte=today, schedule_id__date_to__gte=today).order_by('session_list_id')

    equal_list = []
    dic = {}
    
    # вычисляю дубли сеансов
    for i in afisha_obj:
        date_from = i.schedule_id.date_from
        date_to = i.schedule_id.date_to
        delta = date_to - date_from
        for t in range(delta.days + 1):
            ddate = date_from + datetime.timedelta(days=t)
            if ddate == today:
                x = (i.schedule_id.film_id_id, i.schedule_id.movie_id_id, str(ddate), str(i.session_list_id.time), i.schedule_id.hall_id_id)
                if not dic.get(x):
                    dic[x] = i.schedule_id
                else:
                    e = dic.get(x)
                    equal_list.append({'obj': i.schedule_id_id, 'data': x, 'autor': i.schedule_id.autor})
                    equal_list.append({'obj': e, 'data': x, 'autor': e.autor})

    # данные оборачиваю в html теги прям в коде, т.к. это тестовая/временная функция
    count = len(equal_list) / 2
    log = 'Дублей %s<br /><table border=1><th>Кинотеатр</th><th>Фильм</th><th>Зал</th><th>Дата</th><th>Время</th><th>Автор</th>' % count
    for i in equal_list:
        log += '<tr>'
        log += '<td><a href="http://www.kinoafisha.ru/index.php3?id2=%s&status=2" target="_blank">%s</a></td>' % (i['data'][1], i['data'][1])
        log += '<td><a href="http://www.kinoafisha.ru/index.php3?id1=%s&status=1" target="_blank">%s</a></td>' % (i['data'][0], i['data'][0])
        log += '<td>%s</td>' % i['data'][4]
        log += '<td>%s</td>' % i['data'][2]
        log += '<td>%s</td>' % i['data'][3]
        log += '<td>%s</td>' % i['autor']
        log += '</tr>'
    log += '</table>'
    
    return HttpResponse(str(log))



@only_superuser
@never_cache
def equal_cmc_kinoafisha2(request):
    '''
    Дубли на кинафише
    '''
    # формирование массива из queryset
    def afisha_dict(afisha_obj):
        dic = {}
        for i in afisha_obj:
            date_from = i.schedule_id.date_from
            date_to = i.schedule_id.date_to
            delta = date_to - date_from
            for t in range(delta.days + 1):
                d = date_from + datetime.timedelta(days=t)
                ti = i.session_list_id.time
                d = datetime.datetime(d.year, d.month, d.day, ti.hour, ti.minute, 0)

                unique_id = '%s-%s-%s-%s' % (i.schedule_id.film_id_id, i.schedule_id.movie_id_id, i.schedule_id.hall_id_id, d)
                data = {'film': int(i.schedule_id.film_id_id), 'movie': int(i.schedule_id.movie_id_id), 'hall': int(i.schedule_id.hall_id_id), 'date': d, 'source': i.schedule_id.autor, 'obj': i}
                if dic.get(unique_id):
                    dic[unique_id].append(data)
                else:
                    dic[unique_id] = [data,]
        return dic
    
    
    today = datetime.date.today()
    # выборка сеансов у которых текущая дата попадает в диапозон
    afisha_obj = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id').filter(schedule_id__date_from__lte=today, schedule_id__date_to__gte=today).order_by('session_list_id')

    
    data_sess = afisha_dict(afisha_obj)
    
    equals_elements = []
    
    equals_elements = [v for k, v in data_sess.iteritems() if len(v) > 1]
            
    return HttpResponse(str(equals_elements))
    
    
    equal_list = []
    dic = {}
    
    # вычисляю дубли сеансов
    for i in afisha_obj:
        date_from = i.schedule_id.date_from
        date_to = i.schedule_id.date_to
        delta = date_to - date_from
        for t in range(delta.days + 1):
            ddate = date_from + datetime.timedelta(days=t)
            if ddate == today:
                x = (i.schedule_id.film_id_id, i.schedule_id.movie_id_id, str(ddate), str(i.session_list_id.time), i.schedule_id.hall_id_id)
                if not dic.get(x):
                    dic[x] = i.schedule_id
                else:
                    e = dic.get(x)
                    equal_list.append({'obj': i.schedule_id_id, 'data': x, 'autor': i.schedule_id.autor})
                    equal_list.append({'obj': e, 'data': x, 'autor': e.autor})

    # данные оборачиваю в html теги прям в коде, т.к. это тестовая/временная функция
    count = len(equal_list) / 2
    log = 'Дублей %s<br /><table border=1><th>Кинотеатр</th><th>Фильм</th><th>Зал</th><th>Дата</th><th>Время</th><th>Автор</th>' % count
    for i in equal_list:
        log += '<tr>'
        log += '<td><a href="http://www.kinoafisha.ru/index.php3?id2=%s&status=2" target="_blank">%s</a></td>' % (i['data'][1], i['data'][1])
        log += '<td><a href="http://www.kinoafisha.ru/index.php3?id1=%s&status=1" target="_blank">%s</a></td>' % (i['data'][0], i['data'][0])
        log += '<td>%s</td>' % i['data'][4]
        log += '<td>%s</td>' % i['data'][2]
        log += '<td>%s</td>' % i['data'][3]
        log += '<td>%s</td>' % i['autor']
        log += '</tr>'
    log += '</table>'
    
    return HttpResponse(str(log))



'''
def cvbcvb(request):
    session = AfishaSession.objects.using('afisha').values_list('id', flat=True)
    schedule = Schedule.objects.using('afisha').values_list('id', flat=True)
    
    
    #session_list = [i.schedule_id_id for i in session_obj]
    #schedule_list = [i.id for i in schedule_obj]
    #x = [i for i in schedule if i not in set(session)]
    
    x = set(schedule) - set(session)
    
    return HttpResponse(str(len(x)))
'''
