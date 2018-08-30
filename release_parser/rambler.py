#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time

from django import db
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
from release_parser.kinohod import create_schedule_data_range2
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from release_parser.func import cron_success
from decors import timer


RAMBLER_API_KEY = '0becca2f-7770-47ca-93f6-daff81809e31'

#@timer
def get_rambler_indexfile():
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    url = 'http://api.kassa.rambler.ru/v2/%s/xml/Movie/export/sale/' % RAMBLER_API_KEY # dump_rambler_index.xml
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        data = req.read()
        if 'InvalidClientIp' in data:
            return HttpResponse(str('InvalidClientIp'))
        create_dump_file('%s_index' % source.dump, settings.API_DUMP_PATH, data)
    cron_success('xml', source.dump, 'index', 'Индексный файл')
    return HttpResponse(str('OK'))
    
    
@timer
def get_rambler_cities():
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    
    cities_ids = get_source_data(source, 'city', 'list')
    data_nof_city = ''
    
    
    '''
    # LOCALHOST
    f = open('%s/dump_rambler_city.xml' % settings.API_DUMP_PATH, 'r')
    xml = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    if xml: # --- end localhost
    '''

    # SERVER
    url = 'http://api.kassa.rambler.ru/v2/%s/xml/cities/' % RAMBLER_API_KEY # dump_rambler_city.xml
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        xml = BeautifulSoup(req.read(), from_encoding="utf-8") # --- end server
        
        for i in xml.findAll('city'):
            id = i.cityid.string
            name = i.find('name').string.encode('utf-8')
            name_slug = low(del_separator(name))
            if id not in cities_ids:
                city = City.objects.filter(name__name=name_slug, name__status=2).distinct('pk')
                if city.count() == 1:
                    SourceCities.objects.create(
                        source_id = id,
                        source_obj = source,
                        city = city[0],
                        name = name,
                    )
                else:
                    if 'slug="%s"' % name_slug not in data_nof_city:
                        data_nof_city += '<city name="%s" slug="%s"></city>' % (name, name_slug)
                        
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    cron_success('xml', source.dump, 'cities', 'Города')
    

@timer
def get_rambler_cinemas():
    data_nof_cinema = ''
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    
    cinemas_ids = get_source_data(source, 'cinema', 'list')
    rambler_cities_dict = get_source_data(source, 'city', 'dict')

    cinemass = Cinema.objects.all()
    cinemass_dict = {}
    for i in cinemass:
        cinemass_dict[i.code] = i

    ignored_cinemas = get_ignored_cinemas()

    '''
    # LOCALHOST
    f = open('%s/dump_rambler_cinema.xml' % settings.API_DUMP_PATH, 'r')
    xml = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    if xml:
        if xml: # --- end localhost
    '''
    # SERVER
    f = open('%s/dump_rambler_index.xml' % settings.API_DUMP_PATH, 'r')
    xml_index = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    places = xml_index.find('places')
    filenames = []
    for i in places.findAll('file'):
        filename = i.get('filename')
        if filename:
            filenames.append(filename)
    
    for i in filenames:
        url = 'http://api.kassa.rambler.ru/v2/%s/xml/Movie/export/sale/%s' % (RAMBLER_API_KEY, i)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            xml = BeautifulSoup(req.read(), from_encoding="utf-8") # --- end server
            
            for i in xml.findAll('place'):
                id = i.objectid.string
                name = i.find('name').string.encode('utf-8')
                name_slug = low(del_separator(name))
                address = i.address.string.encode('utf-8') if i.address.string else None
                latitude = i.latitude.string
                longitude = i.longitude.string
                city_id = i.cityid.string
                city_obj = rambler_cities_dict.get(city_id)
                
                if city_obj:
                    cinema_ig_id = u'%s__%s' % (name_slug.decode('utf-8'), city_obj.city.kid)

                    if id not in cinemas_ids and cinema_ig_id not in ignored_cinemas:
                        filter1 = {'name__name': name_slug, 'name__status': 2, 'city__id': city_obj.city_id}
                        cinema = cinema_identification(name_slug, filter1)
                        cin_obj = cinemass_dict.get(cinema)
                        if cin_obj:
                            SourceCinemas.objects.create(
                                source_id = id,
                                source_obj = source,
                                city = city_obj,
                                cinema = cin_obj,
                                name = name,
                                address = address,
                                latitude = latitude,
                                longitude = longitude,
                            )
                        else:
                            if 'slug="%s"' % name_slug not in data_nof_cinema:
                                name_city = city_obj.name
                                data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (name, name_slug, name_city.encode('utf-8'), city_obj.city.kid)
                                
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('xml', source.dump, 'cinemas', 'Кинотеатры')

@timer
def get_rambler_films():
    ignored = get_ignored_films()
    
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    noffilms = []
    data_nof_films = ''
    
    '''
    # LOCALHOST
    f = open('%s/dump_rambler_films.xml' % settings.API_DUMP_PATH, 'r')
    xml = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    if xml:
        if xml: # --- end localhost
    '''
    
    # SERVER
    f = open('%s/dump_rambler_index.xml' % settings.API_DUMP_PATH, 'r')
    xml_index = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    creations = xml_index.find('creations')
    
    filenames = []
    for i in creations.findAll('file'):
        filename = i.get('filename')
        if filename:
            filenames.append(filename)

    for i in filenames:
        url = 'http://api.kassa.rambler.ru/v2/%s/xml/Movie/export/sale/%s' % (RAMBLER_API_KEY, i)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            xml = BeautifulSoup(req.read(), from_encoding="utf-8")  # --- end server

            for i in xml.findAll('creation'):
                film_id = i.objectid.string

                if film_id not in noffilms:
                    try:
                        year = int(i.year.string) if i.year.string else None
                    except UnicodeEncodeError:
                        year = None 
                    
                    full_url = 'https://kassa.rambler.ru/movie/%s' % film_id
                    name = i.find('name').string.encode('utf-8')
                    name_slug = low(del_separator(name))
                    
                    if year and name_slug.decode('utf-8') not in ignored:
                    
                        obj = films.get(film_id)
                        next_step = checking_obj(obj)
                        
                        if next_step:
                            if obj:
                                kid = obj.kid
                            else:
                                try:
                                    kid, info = film_identification(name_slug, None, {}, {}, year=year, source=source)
                                except db.backend.Database._mysql.OperationalError:
                                    next_step = False
                            
                            if next_step:
                                objt = None
                                if kid:
                                    create_new, objt = unique_func(fdict, kid, obj)
                                    if create_new:
                                        new = create_sfilm(film_id, kid, source, name, year=year)
                                        films[film_id] = new
                                        if not fdict.get(kid):
                                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                        fdict[kid]['script_rel'].append(new)
                                elif not obj:
                                    data_nof_films += xml_noffilm(name, name_slug, None, None, film_id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                                    noffilms.append(film_id)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films.replace('&', '&amp;'))
    cron_success('xml', source.dump, 'films', 'Фильмы')

@timer
def get_rambler_schedules(): # id 100
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    
    date_now = datetime.datetime.today().date()
    date_future = date_now + datetime.timedelta(days=28)
    date_past = date_now - datetime.timedelta(days=21)
    
    schedules_ids = list(SourceSchedules.objects.filter(source_obj=source, dtime__gte=date_past, dtime__lt=date_future).values_list('source_id', flat=True))
    
    rambler_cinemas_dict = get_source_data(source, 'cinema', 'dict')

    rambler_films_dict = get_source_data(source, 'film', 'dict')
    
    film_list = []
    film_nof_list = []

    '''
    # LOCALHOST
    f = open('%s/dump_rambler_schedules.xml' % settings.API_DUMP_PATH, 'r')
    xml = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    if xml:
        if xml: # --- end localhost
    '''

    # SERVER
    f = open('%s/dump_rambler_index.xml' % settings.API_DUMP_PATH, 'r')
    xml_index = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    creations = xml_index.find('sessions')
    
    filenames = []
    if creations:
        for i in creations.findAll('file'):
            filename = i.get('filename')
            if filename:
                filenames.append(filename)

    for i in filenames:
        url = 'http://api.kassa.rambler.ru/v2/%s/xml/Movie/export/sale/%s' % (RAMBLER_API_KEY, i)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            xml = BeautifulSoup(req.read(), from_encoding="utf-8")  # --- end server
            
            for i in xml.findAll('session'):
                id = i.sessionid.string.decode('utf-8')
                
                if id not in schedules_ids:
                    cinema = i.placeobjectid.string.encode('utf-8')
                    cinema_obj = rambler_cinemas_dict.get(cinema)
                    
                    if cinema_obj:
                        film = i.creationobjectid.string.encode('utf-8')
                        film_obj = rambler_films_dict.get(film)
                        
                        if film_obj:
                            sale = True if i.issaleavailable.string.encode('utf-8') == 'true' else False
                            show_d = i.datetime.string.split(' ')[0].split('-')
                            show_t = i.datetime.string.split(' ')[1]
                            
                            dtime = datetime.date(int(show_d[0]), int(show_d[1]), int(show_d[2]))
                            
                            hour = int(show_t.split(':')[0])
                            if hour >= 0 and hour <= 5:
                                dtime = dtime - datetime.timedelta(days=1)

                            show_t = show_t.split(':')
                            dtime = datetime.datetime(dtime.year, dtime.month, dtime.day, int(show_t[0]), int(show_t[1]), 0)
                            
                            SourceSchedules.objects.create(
                                source_id = id,
                                source_obj = source,
                                film = film_obj,
                                cinema = cinema_obj,
                                dtime = dtime,
                                sale = sale,
                            )
                            
    cron_success('xml', source.dump, 'schedules', 'Сеансы')



@timer
def rambler_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.rambler.ru/')
    autors = (source.code, 0, 2, 300, 500, 35, 130)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')



