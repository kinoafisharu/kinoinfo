#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import httplib

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils import simplejson as json
from django.db.models import Q
from django import db

from bs4 import BeautifulSoup
from base.models import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


SERVER_API_KEY = 'b8386438-8cb9-345a-8e3d-54de1522d9d1'
CLIENT_API_KEY = '7b2ec866-69d3-380a-86d2-870c16614856'


@timer
def get_kinohod_cities():
#    print "BEGIN get_kinohod_cities()"
    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    cron_data_new = ''
    cron_data_nof = ''
    cron_count = 0
    
    url = 'http://www.kinohod.ru/api/rest/partner/v1/cities?apikey=%s' % SERVER_API_KEY
    
    source = ImportSources.objects.get(url='http://kinohod.ru/')
    
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        kinohod_cities = get_source_data(source, 'city', 'list')

        data_nof_city = ''
        json_data = req.read()
        data = json.loads(json_data)
        for i in data:
            cron_count += 1
            id = str(i['id']).decode('utf-8')
            
            if id not in kinohod_cities:
                alias = i['alias']
                name = i['name'].encode('utf-8')
                name_slug = del_screen_type(low(del_separator(name)))
                
                city = City.objects.filter(name__name=name_slug, name__status=2).distinct('pk')
                if city.count() == 1:
                    SourceCities.objects.create(
                        source_id = id,
                        source_obj = source,
                        city = city[0],
                        name = name,
                        name_alter = alias,
                    )
                    cron_data_new += '%s<br />' % name
                else:
                    data_nof_city += '<city name="%s" slug="%s"></city>' % (name, name_slug)
                    cron_data_nof += '%s<br />' % name
                kinohod_cities.append(id)
                
        create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
        
    # cron log
    end_time = datetime.datetime.now().strftime('%H:%M:%S')
    cron_data = '%s | %s - %s %s<br />' % (datetime.datetime.now().date(), start_time, end_time, 'Импорт городов киноход')
    cron_data += '<br /><b>Обработано</b>: %s' % cron_count
    cron_data += '<br /><b>Новые</b>: <br />%s' % cron_data_new
    cron_data += '<br /><b>Ненайденные</b>: <br />%s' % cron_data_nof
    for i in range(50):
        cron_data += '- '
    process_time = time.time()-t1
    cron_data = '<br />* %s сек.<br />%s' % (process_time, cron_data)
    open('%s/cron_log_kinohod_cities.txt' % settings.CRON_LOG_PATH, 'a').write(cron_data)
    cron_success('json', source.dump, 'cities', 'Города')


@timer
def get_kinohod_cinemas():
#    print "BEGIN get_kinohod_cinemas()"
    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')

    cron_data_new = ''
    cron_data_nof = ''
    cron_count = 0

    main_url = 'http://www.kinohod.ru/api/rest/partner/v1/cinemas?apikey=%s' % SERVER_API_KEY
    
    source = ImportSources.objects.get(url='http://kinohod.ru/')
    kinohod_cinemas = get_source_data(source, 'cinema', 'list')
    kinohod_cities_dict = get_source_data(source, 'city', 'dict')
    
    cinemass = Cinema.objects.all()
    cinemass_dict = {}
    for i in cinemass:
        cinemass_dict[i.code] = i

    count = 0
    data_nof_cinema = ''
    for cid, kinohod_city in kinohod_cities_dict.iteritems():
        try:
            url = '%s&city=%s' % (main_url, cid)
            req = urllib.urlopen(url)
            if req.getcode() == 200:
                json_data = req.read()
                data = json.loads(json_data)
                for i in data:
                    cron_count += 1
                    id = str(i['id']).decode('utf-8')
                    if id not in kinohod_cinemas:
                        name = i['title']
                        name_slug = del_screen_type(name.encode('utf-8'))
                        name_slug = low(del_separator(name_slug))
                        short_name = i['shortTitle']
                        short_name_slug = del_screen_type(short_name.encode('utf-8'))
                        short_name_slug = low(del_separator(short_name_slug))
                        
                        filter1 = {'name__name': name_slug, 'name__status': 2, 'city__id': kinohod_city.city_id}
                        filter2 = {'name__name': short_name_slug, 'name__status': 2, 'city__id': kinohod_city.city_id}
                        cinema_kid = cinema_identification(short_name_slug, filter1, filter2)
                        cin_obj = cinemass_dict.get(cinema_kid)
                        if cin_obj:
                            SourceCinemas.objects.create(
                                source_id = id,
                                source_obj = source,
                                city = kinohod_city,
                                cinema = cin_obj,
                                name = name,
                                name_alter = short_name,
                            )
                            cron_data_new += '%s<br />' % short_name.encode('utf-8')
                        else:
                            count += 1
                            name_city = kinohod_city.name
                            data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (short_name.encode('utf-8'), short_name_slug, name_city.encode('utf-8'), kinohod_city.city.kid)
                            cron_data_nof += '%s<br />' % short_name.encode('utf-8')
                        kinohod_cinemas.append(id)
        except IOError:
            open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write(str(url) + '\n')
    data_nof_cinema += '<sum>%s</sum>' % count
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    
    # cron log
    end_time = datetime.datetime.now().strftime('%H:%M:%S')
    cron_data = '%s | %s - %s %s\n' % (datetime.datetime.now().date(), start_time, end_time, 'Импорт кинотеатров киноход')
    cron_data += '<br /><b>Обработано</b>: %s' % cron_count
    cron_data += '<br /><b>Новые</b>: <br />%s' % cron_data_new
    cron_data += '<br /><b>Ненайденные</b>: <br />%s' % cron_data_nof
    for i in range(50):
        cron_data += '- '
    process_time = time.time()-t1
    cron_data = '<br />* %s сек.<br />%s' % (process_time, cron_data)
    open('%s/cron_log_kinohod_cinemas.txt' % settings.CRON_LOG_PATH, 'a').write(cron_data)
    cron_success('json', source.dump, 'cinemas', 'Кинотеатры')


@timer
def get_kinohod_films():
#    print "BEGIN get_kinohod_films()"

    ignored = get_ignored_films()

    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    cron_data_new = ''
    cron_data_nof = ''
    cron_count = 0
    noffilms = []
    
    source = ImportSources.objects.get(url='http://kinohod.ru/')
    
    sfilm_clean(source)
    
    kinohod_cities = get_source_data(source, 'city', 'list')
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    data_nof_films = ''
    main_url = 'http://www.kinohod.ru/api/rest/partner/v1/movies?apikey=%s' % SERVER_API_KEY
    for city_id in kinohod_cities:
        try:
            url = '%s&city=%s' % (main_url, city_id)
            req = urllib.urlopen(url)

            if req.getcode() == 200:
                json_data = req.read()
                data = json.loads(json_data)
                for i in data:
                    cron_count += 1
                    film_id = str(i['id']).decode('utf-8')
                    year = int(i['productionYear']) if i['productionYear'] else None
                    name_ru = i['title'].encode('utf-8')
                    name_ru_slug = low(del_separator(del_screen_type(name_ru)))
                    full_url = '%smovie/%s/' % (source.url, film_id)
                    name_en = None
                    name_en_slug = None
                    if i['originalTitle']:
                        name_en = i['originalTitle'].encode('utf-8')
                        name_en_slug = low(del_separator(del_screen_type(name_en)))
                    
                    if year and name_ru_slug.decode('utf-8') not in ignored and film_id not in noffilms:

                        obj = films.get(film_id)
                        next_step = checking_obj(obj)
                        
                        if next_step:
                            try:
                                if obj:
                                    kid = obj.kid
                                else:
                                    kid, info = film_identification(name_ru_slug, name_en_slug, {}, {}, year=year, source=source)
                        
                                objt = None
                                if kid:
                                    create_new, objt = unique_func(fdict, kid, obj)
                                    if create_new:
                                        new = create_sfilm(film_id, kid, source, name_ru, name_alt=name_en, year=year)
                                        films[film_id] = new
                                        if not fdict.get(kid):
                                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                        fdict[kid]['script_rel'].append(new)
                                        cron_data_new += '%s<br />' % name_ru
                                elif not obj:
                                    if not name_en:
                                        name_en = '*'
                                        name_en_slug = '*'
                                    data_nof_films += xml_noffilm(name_ru, name_ru_slug, name_en, name_en_slug, film_id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                                    noffilms.append(film_id)
                                    cron_data_nof += '%s<br />' % name_ru
                            except db.backend.Database._mysql.OperationalError:
                                pass

        except IOError:
            open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write(str(url) + '\n')
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    
    # cron log
    end_time = datetime.datetime.now().strftime('%H:%M:%S')
    cron_data = '%s | %s - %s %s\n' % (datetime.datetime.now().date(), start_time, end_time, 'Импорт фильмов киноход')
    cron_data += '<br /><b>Обработано</b>: %s' % cron_count
    cron_data += '<br /><b>Новые</b>: <br />%s' % cron_data_new
    cron_data += '<br /><b>Ненайденные</b>: <br />%s' % cron_data_nof
    for i in range(50):
        cron_data += '- '
    process_time = time.time()-t1
    cron_data = '<br />* %s сек.<br />%s' % (process_time, cron_data)
    open('%s/cron_log_kinohod_films.txt' % settings.CRON_LOG_PATH, 'a').write(cron_data)
    cron_success('json', source.dump, 'films', 'Фильмы')

@timer
def get_kinohod_schedules():
#    print "BEGIN get_kinohod_schedules()"
    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    opener = urllib2.build_opener()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
    }
    opener.addheaders = headers.items()
    
    cron_data_new = 0
    cron_data_new_sale = 0
    cron_data_nof = ''
    cron_count = 0
    cron_count_sale = 0
    film_list = []
    film_nof_list = []
    cinemas_count = 0
    
    source = ImportSources.objects.get(url='http://kinohod.ru/')
    kinohod_cinemas_dict = get_source_data(source, 'cinema', 'dict')
    kinohod_films_dict = get_source_data(source, 'film', 'dict')
        
    today = datetime.datetime.now().date()
    today_add_seven_days = today + datetime.timedelta(days=6)

    kinohod_schedules = list(SourceSchedules.objects.filter(dtime__gte=today, source_obj=source).values_list('source_id', flat=True))
    
    for cinema_id, cinema_obj in kinohod_cinemas_dict.iteritems():
        today_temp = today
        while today_temp <= today_add_seven_days:
            today_str = today_temp.strftime("%d%m%Y")
            today_temp += datetime.timedelta(days=1)
            
            url = 'http://www.kinohod.ru/api/rest/partner/v1/cinemas/%s/schedules?apikey=%s&date=%s' % (cinema_id, SERVER_API_KEY, today_str)
     
            #url = 'http://www.kinohod.ru/api/rest/partner/v1/cinemas/%s/schedules?apikey=%s' % (cinema_id, SERVER_API_KEY)
            #url = 'http://www.kinohod.ru/api/rest/partner/v1/cinemas/300/schedules?apikey=%s' % SERVER_API_KEY # ------ !!!!
            try:
                try:
                    req = opener.open(url)
                    if req.getcode() == 200:
                        cinemas_count += 1
                        json_data = req.read()
                        data = json.loads(json_data)

                        for i in data:
                            film_id = str(i['movie']['id'])
                            film_obj = kinohod_films_dict.get(film_id)
                        
                            if film_obj:
                                film_list.append(film_id)
                            else:
                                film_nof_list.append(film_id)
                                     
                            for s in i['schedules']: 
                                sale = s['isSaleAllowed']
                                cron_count += 1
                                if sale:
                                    cron_count_sale += 1
                                    
                                if film_obj:
                                    id = str(s['id'])
                                    if id not in kinohod_schedules:
                                        show_d = s['startTime'].split('T')[0].split('-')
                                        dtime = datetime.date(int(show_d[0]), int(show_d[1]), int(show_d[2]))
                                        
                                        hour = int(s['time'].split(':')[0])
                                        if hour >= 0 and hour <= 5:
                                            dtime = dtime - datetime.timedelta(days=1)
                                        
                                        show_t = '%s:00' % s['time']
                                        show_t = show_t.split(':')
                                        dtime = datetime.datetime(dtime.year, dtime.month, dtime.day, int(show_t[0]), int(show_t[1]), 0)
                                        
                                        SourceSchedules.objects.create(
                                            source_id = id,
                                            source_obj = source, 
                                            cinema = cinema_obj,
                                            film = film_obj,
                                            dtime = dtime,
                                            sale = sale,
                                        )
                                        
                                        cron_data_new += 1
                                        if sale:
                                            cron_data_new_sale += 1
                except httplib.HTTPException:
                    open('%s/httplib_errors.txt' % settings.API_DUMP_PATH, 'a').write('%s\n' % url)
            except (urllib2.HTTPError, urllib2.URLError): 
                open('%s/httplib_errors.txt' % settings.API_DUMP_PATH, 'a').write('urllib2***\t%s\n' % url)

    # cron log
    film_sum = len(set(film_list + film_nof_list))
    end_time = datetime.datetime.now().strftime('%H:%M:%S')
    cron_data = u'%s | %s - %s %s<br />' % (datetime.datetime.now().date(), start_time, end_time, u'Импорт сеансов киноход')
    cron_data += u'<br /><b>Получено</b>: %s (с продажей: %s)' % (cron_count, cron_count_sale)
    cron_data += u'<br /><b>Новых</b>: %s (с продажей: %s)' % (cron_data_new, cron_data_new_sale)
    cron_data += u'<br /><b>Кинотеатров</b>: %s' % cinemas_count
    cron_data += u'<br /><b>Фильмов</b>: %s (не идент: %s)<br />' % (film_sum, len(set(film_nof_list)))
    
    for i in range(50):
        cron_data += u'- '
    process_time = time.time()-t1
    cron_data = u'<br />* %s сек.<br />%s' % (process_time, cron_data)
    
    open('%s/cron_log_kinohod_schedules.txt' % settings.CRON_LOG_PATH, 'a').write(cron_data.encode('utf-8'))
    cron_success('json', source.dump, 'schedules', 'Сеансы')
#    print cron_data



def create_schedule_data_range(data):
#    print "BEGIN create_schedule_data_range(data)"
    schedule = {}
    for i in data:
        s = schedule.get(i['film'])
        if s:
            m = schedule.get(i['film']).get(i['movie'])
            if m:
                d = schedule[i['film']][i['movie']].get(i['date'].date())
                if d:
                    if i['date'].time not in d:
                        schedule[i['film']][i['movie']][i['date'].date()].append(i['date'].time())
                        schedule[i['film']][i['movie']][i['date'].date()].sort()
                else:
                    schedule[i['film']][i['movie']][i['date'].date()] = [i['date'].time()]
            else:
                schedule[i['film']][i['movie']] = {i['date'].date(): [i['date'].time()]}
        else:
            schedule[i['film']] = {i['movie']: {i['date'].date(): [i['date'].time()]}}
    
    schedule_listt = []
    for k, v in schedule.iteritems():
        film = k
        for kk, vv in v.iteritems():
            movie = kk
            d = ''
            dates = {}
            keyy = ''
            for i in sorted(vv.items()):
                if not d:
                    d = i[0]
                    dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'movie': movie}
                    keyy = d
                else:
                    d = i[0]
                    d_prev = d - datetime.timedelta(days=1)
                    if d_prev == dates[keyy]['to']:
                        if set(dates[keyy]['time']) == set(i[1]):
                            dates[keyy]['to'] = d
                        else:
                            dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'movie': movie}
                            keyy = d
                    else:
                        dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'movie': movie, }
                        keyy = d
            for i in dates.values():
                schedule_listt.append(i)
    return schedule_listt




def create_schedule_data_range2(data):
#    print "BEGIN create_schedule_data_range2(data)"
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
                            dates[d] = {'from': d, 'to': d, 'time': i[1], 'film': film, 'hall': hall, 'movie': movie, }
                            keyy = d
                for i in dates.values():
                    schedule_listt.append(i)
    return schedule_listt


@timer
def kinohod_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://kinohod.ru/')
    autors = (source.code, 0, 2, 11, 300)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


