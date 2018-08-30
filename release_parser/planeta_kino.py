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

from bs4 import BeautifulSoup

from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from api.models import *
from base.models import *
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.func import cron_success
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer

planeta_kino_urls = [
    {'city': 'kiev', 'city_name': 'Киев', 'url': 'http://planetakino.ua/ru/showtimes/xml/'},
    {'city': 'odessa', 'city_name': 'Одесса', 'url': 'http://planetakino.ua/ru/odessa/showtimes/xml/'},
    {'city': 'odessa', 'city_name': 'Одесса', 'url': 'http://planetakino.ua/ru/odessa2/showtimes/xml/'},
    {'city': 'lvov', 'city_name': 'Львов', 'url': 'http://planetakino.ua/ru/lvov/showtimes/xml/'},
    {'city': 'kharkov', 'city_name': 'Харьков', 'url': 'http://planetakino.ua/ru/kharkov/showtimes/xml/'},
    {'city': 'yalta', 'city_name': 'Ялта', 'url': 'http://planetakino.ua/ru/yalta/showtimes/xml/'},
    {'city': 'sumy', 'city_name': 'Сумы', 'url': 'http://planetakino.ua/ru/sumy/showtimes/xml/'},
]

@timer
def get_planeta_cities_cinemas():
    '''
    Получение xml данных сеансов от PlanetaKino
    '''
    source = ImportSources.objects.get(url='http://planeta-kino.com.ua/')
    planeta_cities_dict = get_source_data(source, 'city', 'dict')
    planeta_cinemas = get_source_data(source, 'cinema', 'list')
    
    data_nof_city = ''
    data_nof_cinema = ''
    
    for i in planeta_kino_urls:
        city_name = i['city_name']
        city_slug = low(del_separator(city_name))
        city_id = i['city']

        req = urllib.urlopen(i['url'])
        if req.getcode() == 200:
            f = open('%s/dump_planetakino_%s.xml' % (settings.API_DUMP_PATH, city_id), 'w')
            f.write(str(req.read()))
            f.close()
        
        city_obj = planeta_cities_dict.get(city_id)
        if not city_obj:
            city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
            if city.count() == 1:
                city_obj = SourceCities.objects.create(
                    source_id = city_id,
                    source_obj = source,
                    city = city[0],
                    name = city_name,
                )
            else:
                if 'slug="%s"' % city_slug not in data_nof_city:
                    data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)

        if city_obj:
            city_kid = city_obj.city.kid
            cinema_name = 'Планета Кино IMAX'
            cinema_slug = low(del_separator(cinema_name))
            cinema_id = 'imax-%s' % i['city'] if i['city'] == 'kiev' else 'pk-%s' % i['city']
            
            if cinema_id not in planeta_cinemas:
                filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city__kid': city_kid}
                cinema_kid = cinema_identification(cinema_slug, filter1)
                if cinema_kid:
                    cinema = Cinema.objects.get(code=cinema_kid)
                    SourceCinemas.objects.create(
                        source_id = cinema_id,
                        source_obj = source,
                        city = city_obj,
                        cinema = cinema,
                        name = cinema_name,
                    )
                else:
                    tags = 'slug="%s" city_kid="%s"' % (cinema_slug, city_kid)
                    if tags not in data_nof_cinema:
                        data_nof_cinema += '<cinema name="%s" city="%s" slug="%s" city_kid="%s"></cinema>' % (cinema_name, city_name, cinema_slug, city_kid)
            
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('xml', source.dump, 'cities', 'Города')
    cron_success('xml', source.dump, 'cinemas', 'Кинотеатры')
    


@timer
def get_planeta_films():
    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://planeta-kino.com.ua/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    data_nof_film = ''
    noffilms = []
    for i in planeta_kino_urls:
        xml = open('%s/dump_planetakino_%s.xml' % (settings.API_DUMP_PATH, i['city']), 'r')
        xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
        xml.close()

        for film in xml_data.findAll('movie'):
            film_id = film['id']
            
            if film_id not in noffilms:
                film_url = film['url']
                film_name = film.title.text.replace('"', "'").encode('utf-8').strip()
                film_slug = low(del_separator(del_screen_type(film_name)))
                if film_slug.decode('utf-8') not in ignored:
                    
                    obj = films.get(film_id)
                    next_step = checking_obj(obj)
                    
                    if next_step:
                        if obj:
                            kid = obj.kid
                        else:
                            kid, info = film_identification(film_slug, film_name, {}, {}, source=source)
                
                        if kid:
                            create_new, objt = unique_func(fdict, kid, obj)
                            if create_new:
                                new = create_sfilm(film_id, kid, source, film_name)
                                films[film_id] = new
                                if not fdict.get(kid):
                                    fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                fdict[kid]['script_rel'].append(new)
                        elif not obj:
                            data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id.encode('utf-8'), info, None, source.id)
                            noffilms.append(film_id)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'films', 'Фильмы')


@timer
def get_planeta_schedules():
    data_nof_hall = ''
    
    source = ImportSources.objects.get(url='http://planeta-kino.com.ua/')
    
    planeta_schedules = get_source_data(source, 'schedule', 'list')
    planeta_cities_dict = get_source_data(source, 'city', 'dict')
    planeta_cinemas_dict = get_source_data(source, 'cinema', 'dict')
    planeta_films_dict = get_source_data(source, 'film', 'dict')
    
    nof_list = []
    
    for i in planeta_kino_urls:
        xml = open('%s/dump_planetakino_%s.xml' % (settings.API_DUMP_PATH, i['city']), 'r')
        xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
        xml.close()

        for day in xml_data.findAll('day'):
            release_date = day['date'].encode('utf-8')
            for show in day.findAll('show'):
                cinema_id = show['theatre-id'].encode('utf-8')
                city_id = cinema_id.split('-')[1].encode('utf-8')
                city = planeta_cities_dict.get(city_id)
                cinema = planeta_cinemas_dict.get(cinema_id)
                film_id = show['movie-id']
                film = planeta_films_dict.get(film_id)
                
                if city and cinema and film:
                    time_data = show['time'].encode('utf-8')
                    technology = show['technology'].encode('utf-8')
                    hall_id = show['hall-id'].encode('utf-8')
                    
                    d = release_date.split('-')
                    t = time_data.split(':')
                    dtimedate = datetime.datetime(int(d[0]), int(d[1]), int(d[2]), int(t[0]), int(t[1]))
                    
                    planeta_id = '%s%s%s%s%s' % (dtimedate, hall_id, cinema_id, city_id, film_id)
                    planeta_id = planeta_id.replace(' ','')
                    
                    id = '%s%s%s' % (hall_id, cinema_id, city_id)

                    if planeta_id not in planeta_schedules and id not in nof_list:
                        
                        # идентификация зала
                        hall_obj = Hall.objects.filter(name__name=hall_id, cinema=cinema.cinema).distinct('pk')
                        # если нашел
                        if hall_obj.count() == 1:
                            # все объекты идентифицированны, добавляю к идентифицированным
                            SourceSchedules.objects.get_or_create(
                                source_id = planeta_id,
                                source_obj = source,
                                defaults = {
                                    'source_id': planeta_id,
                                    'source_obj': source,
                                    'film': film,
                                    'cinema': cinema,
                                    'hall': hall_obj[0].kid,
                                    'dtime': dtimedate,
                                }
                            )
                        # если зал ненайден
                        else:
                            nof_list.append(id)
                            # если такого тега нет в ненайденных, то добавляю
                            data_nof_hall += '<hall city="%s" city_kid="%s" cinema="%s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city.name.encode('utf-8'), city.city.kid, cinema.name.encode('utf-8'), cinema.cinema.code, hall_id, hall_id, id)
                            
    create_dump_file('%s_nof_hall' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_hall)
    cron_success('xml', source.dump, 'schedules', 'Сеансы')


@timer
def planeta_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://planeta-kino.com.ua/')
    autors = (source.code,)
    log = schedules_export(source, autors, True)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


