#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_surkino_cinemas():
    data_nof_cinema = ''
    source = ImportSources.objects.get(url='http://surkino.ru/')

    city_name = 'Сургут'
    city_slug = low(del_separator(city_name))
    city = City.objects.get(name__name=city_name, name__status=1)
    
    city_obj, city_created = SourceCities.objects.get_or_create(
        source_id = city_slug,
        source_obj = source,
        defaults = {
            'source_id': city_slug,
            'source_obj': source,
            'city': city,
            'name': city_name,
        })
    
    cinemas = get_source_data(source, 'cinema', 'list')
    
    ignored_cinemas = get_ignored_cinemas()

    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="windows-1251")

        div = data.find('div', {'class': 'cinemas'})

        div_classes = ['ciname', 'ciname last']
        for cl in div_classes:
            for cinema_tag in div.findAll('div', {'class': cl}):
                cinema_name = cinema_tag.a.get('title').encode('utf-8').replace('Кинотеатр ','')
                cinema_slug = low(del_separator(cinema_name))
                cinema_id = cinema_tag.a.get('href').replace('?cinema=','')

                cinema_ig_id = u'%s__%s' % (cinema_slug.decode('utf-8'), city_obj.city.kid)

                if cinema_id not in cinemas and cinema_ig_id not in ignored_cinemas:
                    filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city__id': city_obj.city_id}
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
                        except Cinema.DoesNotExist: pass
                    else:
                        if 'slug="%s"' % cinema_slug not in data_nof_cinema:
                            data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_obj.name.encode('utf-8'), city_obj.city.kid)
                            
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('html', source.dump, 'cinemas', 'Кинотеатры')


@timer
def get_surkino_schedules():
    ignored = get_ignored_films()
    
    data_nof_film = ''
    noffilms = []
    source = ImportSources.objects.get(url='http://surkino.ru/')
    sfilm_clean(source)
    
    cinemas = get_source_data(source, 'cinema', 'dict')
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')
    
    dates = []
    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read())
        show_days = data.find('div', {'class': 'days'})
        for a in show_days.findAll('a'):
            dates.append(a.get('href').replace('?date=',''))
            
    for d in dates:
        url = '%s?date=%s' % (source.url, d)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="windows-1251")
            
            div = data.find('div', id='filmlist')
            if div:
                for cinema_tag in div.findAll('div', {'class': 'filmname'}):
                    
                    cinema_id = cinema_tag.a.get('href').replace('?cinema=','')
                    cinema_obj = cinemas.get(cinema_id)
                    if cinema_obj:
                        films_block = cinema_tag.find_next_siblings('div', limit=1)[0]
                        for tr in films_block.findAll('tr'):
                            film_tag = tr.findAll('a')
                            film_tag = film_tag[1] if len(film_tag) == 2 else film_tag[0]
                                
                            full_url = '%s%s' % (source.url, film_tag.get('href'))
                            film_id = film_tag.get('href').replace('?film=','').encode('utf-8')
                            film_name = film_tag.string.encode('utf-8')
                            film_slug = low(del_separator(film_name))
                            
                            if film_id not in noffilms and film_slug.decode('utf-8') not in ignored:
                            
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
                                        data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, full_url.encode('utf-8'), source.id)
                                        noffilms.append(film_id)
                                    
                                            
                                    if objt:
                                        showtime = tr.td.string.encode('utf-8')
                                        hours, minutes = showtime.split('.')
                                        year, month, day = d.split('-')
                                        dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))
                                        
                                        sch_id = '%s%s%s' % (dtime, cinema_id, film_id)
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
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')
        
   

@timer
def surkino_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://surkino.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')    
        
