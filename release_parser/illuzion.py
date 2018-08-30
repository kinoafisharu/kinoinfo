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
def get_illuzion_schedules():
    current_year = datetime.datetime.now().year
    next_year = current_year + 1
    
    data_nof_film = ''
    noffilms = []
    
    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://www.illuzion.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    cinemas = get_source_data(source, 'cinema', 'dict')
    schedules = get_source_data(source, 'schedule', 'list')
    
    data = {
        'Иллюзион': {'name': 'Владивосток', 'obj': ''},
        'Океан': {'name': 'Владивосток', 'obj': ''},
        'Уссури': {'name': 'Владивосток', 'obj': ''},
        'Русь': {'name': 'Находка', 'obj': ''},
        'Буревестник': {'name': 'Находка', 'obj': ''},
        'Каскад': {'name': 'Врангель', 'obj': ''},
    }
    
    cities = {}
    for i in ['Владивосток', 'Находка', 'Врангель']:
        city_slug = low(del_separator(i))
        
        city = City.objects.get(name__name=i, name__status=1)
    
        city_obj, city_created = SourceCities.objects.get_or_create(
            source_id = city_slug,
            source_obj = source,
            defaults = {
                'source_id': city_slug,
                'source_obj': source,
                'city': city,
                'name': i,
            })
        cities[i] = city_obj

    for k, v in data.iteritems():
        city = cities.get(v['name'])
        v['obj'] = city
        
    url = 'http://illuzion.ru/timetable'
    
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        page_data = BeautifulSoup(req.read())
        divs = page_data.find('div', id='timetable')
        for div in divs.findAll('div', {'class': 'tt-group-date'}):
            year, month, day = div['data-date'].split('-')
            for i in div.findAll('div', {'class': 'tt-seance clear clearfix'}):
                hours, minutes = i.find('div', {'class': 'seance-time'}).string.split(':')
                dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))
                cinema = i.find('div', {'class': "tt-sc"}).string.split(' / ')[0].encode('utf-8')
                cinema_slug = low(del_separator(cinema))
                cinema_obj = cinemas.get(cinema_slug.decode('utf-8'))
                
                if cinema_obj:
                    film_name = i.find('div', {'class': "seance-title"})
                    if film_name.a:
                        film_name = film_name.a.string.encode('utf-8').strip().replace('"', "'")
                    else:
                        film_name = film_name.string.encode('utf-8').strip().replace('"', "'")

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
                                sch_id = '%s%s%s%s' % (dtime, cinema_slug, city_slug, film_id)
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
def illuzion_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.illuzion.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


