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
from bs4 import BeautifulSoup
from base.models import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success

@timer
def get_zapad24ru():
    ignored = get_ignored_films()
    ignored_cinemas = get_ignored_cinemas()

    source = ImportSources.objects.get(url='http://zapad24.ru/')
    sfilm_clean(source)
    
    cities_dict = get_source_data(source, 'city', 'dict')
    cinemas_dict = get_source_data(source, 'cinema', 'dict')
    schedules = get_source_data(source, 'schedule', 'list')
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    today = datetime.datetime.now()
    next_month = datetime.date.today() + datetime.timedelta(days=40)
    
    data_nof_films = ''
    data_nof_cinema = ''
    data_nof_city = ''
    noffilms = []

    req = urllib.urlopen('%safisha/' % source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read())#, from_encoding="utf-8"
        div = data.find('div', align="left")
        for ind, table in enumerate(div.findAll('table', border="0", cellpadding="0", cellspacing="0", width="100%")):
            cinema_tag = table.find('strong').string.encode('utf-8')
            cinema_name = re.findall(r'\".+\"', cinema_tag)[0].replace('"','').strip()
            cinema_slug = low(del_separator(cinema_name))
            cinema_id = cinema_slug.decode('utf-8')
            
            city_name = re.findall(r'\(.+\)', cinema_tag)[0].replace('(г. ','').replace(')','').strip()
            city_slug = low(del_separator(city_name))
            city_id = city_slug.decode('utf-8')
            
            city_obj = cities_dict.get(city_id)
            
            if not city_obj:
                city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
                if city.count() == 1:
                    city_obj = SourceCities.objects.create(
                        source_id = city_id,
                        source_obj = source,
                        city = city[0],
                        name = city_name,
                    )
                    cities_dict[city_id] = city_obj
                else:
                    if 'slug="%s"' % city_slug not in data_nof_city:
                        data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)
            

            if city_obj:
                cinema_ig_id = u'%s__%s' % (cinema_slug.decode('utf-8'), city_obj.city.kid)

                if cinema_ig_id not in ignored_cinemas:
                    cinema_obj = cinemas_dict.get(cinema_id)
                    if not cinema_obj:
                        filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city': city_obj.city}
                        cinema_kid = cinema_identification(cinema_slug, filter1)
                        if cinema_kid:
                            try:
                                cinema = Cinema.objects.get(code=cinema_kid)
                                cinema_obj = SourceCinemas.objects.create(
                                    source_id = cinema_id,
                                    source_obj = source,
                                    city = city_obj,
                                    cinema = cinema,
                                    name = cinema_name,
                                )
                                cinemas_dict[cinema_id] = cinema_obj
                            except Cinema.DoesNotExist: pass
                        else:
                            if 'slug="%s"' % cinema_slug not in data_nof_cinema:
                                data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_name, city_obj.city.kid)
                    
                    if cinema_obj:
                        film_table = table.find('table')
                        date_from = None
                        date_to = None
                        for tr in film_table.findAll('tr'):
                            film_name, film_slug, film_id = (None, None, None)
                            if ind == 0:
                                film_name = tr.find('b').string.encode('utf-8').strip()
                                film_slug = low(del_separator(film_name))
                                film_id = film_slug.decode('utf-8')
                            else:
                                showdate = ''
                                for f in tr.findAll('b'):
                                    if f.find('span'):
                                        showdate = f.find('span').string.encode('utf-8').strip()
                                    else:
                                        film_name = f.string.encode('utf-8').strip()
                                        film_name = re.findall(r'\«.+\»', film_name)[0]
                                        film_name = film_name.replace('«','').replace('»','').strip()
                                        film_slug = low(del_separator(film_name))
                                        film_id = film_slug.decode('utf-8')
                                        

                                if showdate and film_name:
                                    try:
                                        date_from, date_to = showdate.split('-')
                                        date_from_day, date_from_month = date_from.strip().split('.')
                                        date_to_day, date_to_month = date_to.strip().split('.')
                                    except ValueError:
                                        date_from, date_to = showdate.split(' – ')
                                        date_from_day, date_from_month = date_from.strip().split()
                                        date_from_month = get_month(date_from_month)
                                        date_to_day, date_to_month = date_to.strip().split()
                                        date_to_month = get_month(date_to_month)
                                    
                                    date_from = datetime.date(today.year, int(date_from_month), int(date_from_day))
                                    date_to = datetime.date(today.year, int(date_to_month), int(date_to_day))
                                    
                            full_url = tr.find('a').get('href').encode('utf-8')
                            
                            if film_id not in noffilms and film_id not in ignored:
                                obj = films.get(film_id)
                                next_step = checking_obj(obj)
                        
                                if next_step:
                                    if obj:
                                        kid = obj.kid
                                    else:
                                        kid, info = film_identification(film_slug, None, {}, {}, source=source)
                                    
                                    objt = None
                                    if kid:
                                        create_new, objt = unique_func(fdict, kid, obj)
                                        if create_new:
                                            objt = create_sfilm(film_id, kid, source, film_name)
                                            films[film_id] = objt
                                            if not fdict.get(kid):
                                                fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                            fdict[kid]['script_rel'].append(objt)
                                    elif not obj:
                                        data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id.encode('utf-8'), info, full_url, source.id)
                                        noffilms.append(film_id)
                                

                                    if objt:
                                        req_film = urllib.urlopen(full_url)
                                        if req_film.getcode() == 200:
                                            data_film = BeautifulSoup(req_film.read())#, from_encoding="utf-8"

                                            td = data_film.find('td', {'class': 'news'}).div.text.encode('utf-8')
                                            
                                            showtime = []
                                            
                                            if ind == 0:
                                                showtime = re.findall(r'\d+\:\d+\s\s?', td)
                                            else:
                                                if date_from and date_to:
                                                    if date_to < next_month:
                                                        showtimes = re.findall(r'Начало сеансов:\s?[\d+\-\d+\,?\s?]+', td)
                                                        times = []
                                                        for t in showtimes:
                                                            t = t.replace('Начало сеансов:','').split(',')
                                                            times = [i.strip() for i in t if i.strip()]
                                                        
                                                        delta = date_to - date_from
                                                        for day in range(delta.days + 1):
                                                            d = date_from + datetime.timedelta(days=day)
                                                            for t in times:
                                                                hours, minutes = t.split('-')
                                                                dtime = datetime.datetime(d.year, d.month, d.day, int(hours), int(minutes))
                                                                showtime.append(dtime)
                                                    
                                                    
                                            for t in showtime:
                                                if ind == 0:
                                                    hours, minutes = t.strip().split(':')
                                                    dtime = datetime.datetime(today.year, today.month, today.day, int(hours), int(minutes))
                                                else:
                                                    dtime = t
                                                    
                                                    
                                                sch_id = '%s%s%s%s' % (dtime, cinema_slug, city_slug, film_id.encode('utf-8'))
                                                sch_id = sch_id.replace(' ', '').decode('utf-8')

                                                if sch_id not in schedules:
                                                    SourceSchedules.objects.create(
                                                        source_id = sch_id,
                                                        source_obj = source,
                                                        film = objt,
                                                        cinema = cinema_obj,
                                                        dtime = dtime,
                                                    )
                                                    schedules.append(sch_id)
                                            
    
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)  
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def zapad24ru_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://zapad24.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')

