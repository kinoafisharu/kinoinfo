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
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


# ~1 min
@timer
def get_etaj_schedules():
    ignored = get_ignored_films()
    
    data_nof_film = ''
    noffilms = []
    
    city_name = 'Челябинск'
    cinema_name = 'Этаж'
    city_slug = low(del_separator(city_name))
    cinema_slug = low(del_separator(cinema_name))
    
    source = ImportSources.objects.get(url='http://etaj.mega74.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')
    
    city = City.objects.get(name__name=city_name, name__status=1)
    cinema = Cinema.objects.get(name__name=cinema_name, name__status=1, city=city)
    
    city_obj, city_created = SourceCities.objects.get_or_create(
        source_id = city_slug,
        source_obj = source,
        defaults = {
            'source_id': city_slug,
            'source_obj': source,
            'city': city,
            'name': city_name,
        })
    
    cinema_obj, cinema_created = SourceCinemas.objects.get_or_create(
        source_id = cinema_slug,
        source_obj = source,
        defaults = {
            'source_id': cinema_slug,
            'source_obj': source,
            'city': city_obj,
            'cinema': cinema,
            'name': cinema_name,
        })
    
    today = datetime.datetime.now().date().strftime("%Y%m%d")
    dates = [today]
    
    url = '%skino/list/' % source.url
    
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read())
        show_days = data.find('div', id='kino-flags')
        for a in show_days.findAll('a'):
            day = a.get('href').replace('/kino/list/?day=', '')
            dates.append(day)

    
    for d in dates:
        url = '%skino/list/?day=%s' % (source.url, d)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read())
            for div in data.findAll('div', {'class': 'film'}):

                title = div.find('h3')
                
                div_info = div.find('div', {'class': 'complete_info_title'})
                film_id = div_info.findAll('a', limit=1)[0].get('href')
                film_id = film_id.replace('#trailer_film_', '').encode('utf-8')
                
                film_name = title.string.encode('utf-8').strip().replace('«','').replace('»','')
                film_slug = del_screen_type(low(del_separator(film_name)))
                
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
                            data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, None, source.id)
                            noffilms.append(film_id)
                                

                        if objt:
                            div_sess = div.find('div', {'class': 'film_sessions_new gradient-091100EEE'})

                            for t in div_sess.findAll('span', {'class': 'time'}):
                                
                                hours, minutes = t.string.split(':')
                                year = int(d[:4])
                                month = int(d[4:6])
                                day = int(d[6:8])
                                
                                dtime = datetime.datetime(year, month, day, int(hours), int(minutes))

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
def etaj_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://etaj.mega74.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')

