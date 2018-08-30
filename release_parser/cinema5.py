#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import operator

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
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_cinema5_schedules():
    data_nof_cinema = ''
    data_nof_film = ''
    noffilms = []
    
    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://cinema5.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')

    data = [
        {'city': 'Нижнекамск', 'url': '%snk' % source.url},
        {'city': 'Оренбург', 'url': '%soren' % source.url},
        {'city': 'Саратов', 'url': '%ssaratov' % source.url},
        {'city': 'Уфа', 'url': '%sufa' % source.url},
        {'city': 'Чебоксары', 'url': '%scheby' % source.url},
    ]

    params = ['today', 'tomorrow', '+2days']

    cinema_name = 'Синема 5'
    cinema_slug = low(del_separator(cinema_name))

    for i in data:
        city_slug = low(del_separator(i['city']))
        city = City.objects.get(name__name=i['city'], name__status=1)

        city_obj, city_created = SourceCities.objects.get_or_create(
            source_id = city_slug,
            source_obj = source,
            defaults = {
                'source_id': city_slug,
                'source_obj': source,
                'city': city,
                'name': i['city'],
            })

        cinema = None
        
        try:
            cinema = Cinema.objects.get(name__name=cinema_name, name__status=1, city=city)
        except Cinema.DoesNotExist:
            data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, i['city'], city_obj.city.kid)
        
        if cinema:
            cinema_id = '%s_%s' % (cinema_slug, city_slug) 
            
            cinema_obj, cinema_created = SourceCinemas.objects.get_or_create(
                source_id = cinema_id,
                source_obj = source,
                defaults = {
                    'source_id': cinema_id,
                    'source_obj': source,
                    'city': city_obj,
                    'cinema': cinema,
                    'name': cinema_name,
                })

            for param in params:
                url = '%s?date=%s' % (i['url'], param)
                req = urllib.urlopen(url)
                if req.getcode() == 200:
                    page_data = BeautifulSoup(req.read())
                    divs = page_data.find('div', {'class': 'content clearfix'})
                    
                    showdate = divs.find('h1')
                    if showdate:
                        showdate = showdate.string.encode('utf-8')
                        day, month, year = showdate.replace('Расписание на ','').strip().split('.')

                        for div in divs.findAll('div', {'class': 'show-wrapper'}):
                            film_name = div.find('div', {'class': 'title'}).string.encode('utf-8')
                            film_slug = low(del_separator(del_screen_type(film_name)))
                            film_id = film_slug
                            
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
                                            films[film_id.decode('utf-8')] = objt
                                            if not fdict.get(kid):
                                                fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                            fdict[kid]['script_rel'].append(objt)
                                    elif not obj:
                                        data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, None, source.id)
                                        noffilms.append(film_id)

                                    if objt:
                                        for span in div.findAll('span', {'class': 'time'}):
                                            hours, minutes = span.string.strip().split(':')
                                            dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))
                  
                                            sch_id = '%s%s%s%s' % (dtime, cinema_id, city_slug, film_id)
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
                                        
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def cinema5_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://cinema5.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


