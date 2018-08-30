#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import random

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
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_vkinocomua_cities_and_cinemas():
    nofcities = []
    nofcinemas = []
    data_nof_cinema = ''
    data_nof_city = ''
    
    source = ImportSources.objects.get(url='http://vkino.com.ua/')

    cinemas_dict = get_source_data(source, 'cinema', 'dict')
    cities_dict = get_source_data(source, 'city', 'dict') 
    
    req = urllib.urlopen('%safisha/kiev' % source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        cities_tag = data.find('select', id='city-selector')
        for ind, i in enumerate(cities_tag.findAll('option')):
            if i['value']:
                city_name = i.string.encode('utf-8')
                city_slug = low(del_separator(city_name))
                city_id = i['value'].encode('utf-8')
                
                city_obj = cities_dict.get(city_id)
        
                if not city_obj and city_id not in nofcities:
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
                        data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)
                        nofcities.append(city_id)
                
                if city_obj:
                    url = '%scinema/%s' % (source.url, city_id)
                    req_cinema = urllib.urlopen(url)
                    if req_cinema.getcode() == 200:
                        data_cinema = BeautifulSoup(req_cinema.read(), from_encoding="utf-8")
                        for tag in data_cinema.findAll('a', {'class': 'cinema'}):
                            cinema_name = tag.string.encode('utf-8')
                            cinema_slug = low(del_separator(cinema_name))
                            cinema_id = tag.get('href').replace('/cinema/%s/' % city_id, '').encode('utf-8')
                        
                            cinema_obj = cinemas_dict.get(cinema_id)
                            
                            if not cinema_obj and cinema_id not in nofcinemas:
                                filter = {'name__name': cinema_slug, 'name__status': 2, 'city': city_obj.city}
                                cinema_kid = cinema_identification(cinema_slug, filter)
                                if cinema_kid:
                                    try:
                                        cin_obj = Cinema.objects.get(code=cinema_kid)
                                        cinema_obj = SourceCinemas.objects.create(
                                            source_id = cinema_id,
                                            source_obj = source,
                                            city = city_obj,
                                            cinema = cin_obj,
                                            name = cinema_name,
                                        )
                                        cinemas_dict[cinema_id] = cinema_obj
                                    except Cinema.DoesNotExist: pass
                                else:
                                    nofcinemas.append(cinema_id)
                                    data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_name, city_obj.city.kid)

            if ind % 4 == 0:
                time.sleep(random.uniform(1.0, 3.0))
        
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('html', source.dump, 'cities_and_cinemas', 'Города и кинотеатры')



@timer
def get_vkinocomua_films_and_schedules():
    ignored = get_ignored_films()

    data_nof_film = ''
    noffilms = []

    source = ImportSources.objects.get(url='http://vkino.com.ua/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')

    cinemas_data = SourceCinemas.objects.select_related('city').filter(source_obj=source)
    cinemas = {}
    for ind, i in enumerate(cinemas_data):
        url = '%scinema/%s/%s/showtimes' % (source.url, i.city.source_id, i.source_id)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            main = data.find('div', id='cinema-showtimes')
            if main:
                for content in main.findAll('div', {'class': 'content'}):
                    film_tag = content.find('a', {'class': 'navi'})
                    film_name = film_tag.string.encode('utf-8').strip()
                    film_slug = low(del_separator(film_name))
                    
                    full_url = film_tag.get('href').encode('utf-8')
                    film_id = re.findall(r'\/\d+\/', full_url)
                    if film_id:
                        film_id = film_id[0].replace('/','').encode('utf-8')
                    else:
                        film_id = film_slug
                    
                    full_url = '%s%s' % (source.url, full_url.lstrip('/'))
                    

                    if film_id not in noffilms and film_slug.decode('utf-8') not in ignored:

                        obj = films.get(film_id.decode('utf-8'))
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
                                data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, url.encode('utf-8'), source.id)
                                noffilms.append(film_id)
                        

                            if objt:
                                for div in content.findAll('div', {'class': 'date'}):
                                    year, month, day = div['data-date'].split('-')
                                    show = div.find_next_sibling("ul")
                                    for li in show.findAll('li'):
                                    
                                        
                                        if li.a:
                                            extra = li.a.get('href')
                                            hours, minutes = li.a.text.strip().split(':')
                                        else:
                                            extra = None
                                            hours, minutes = li.text.strip().split(':')
                                            
                                        # sale = True if extra else False
                                        
                                        
                                        dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))

                                        sch_id = u'%s%s%s%s' % (dtime, i.source_id, i.city_id, film_id.decode('utf-8'))
                                        sch_id = sch_id.replace(' ', '')

                                        if sch_id not in schedules:
                                            SourceSchedules.objects.create(
                                                source_id = sch_id,
                                                source_obj = source,
                                                film = objt,
                                                cinema = i,
                                                dtime = dtime,
                                                extra = extra,
                                            )
                                            schedules.append(sch_id)
        if ind % 4 == 0:
            time.sleep(random.uniform(1.0, 3.0))        
        
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')



@timer
def vkinocomua_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://vkino.com.ua/')
    autors = (source.code, 0, 75, 100)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


