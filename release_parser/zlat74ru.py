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
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


# ~1 min
@timer
def get_zlat74ru_schedules():
    ignored = get_ignored_films()
    
    data_nof_film = ''
    noffilms = []
    
    city_name = 'Златоуст'
    cinema_name = 'Космос'
    city_slug = low(del_separator(city_name))
    cinema_slug = low(del_separator(cinema_name))
    
    source = ImportSources.objects.get(url='http://www.zlat74.ru/')
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
    

    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        div = data.find('div', id='schedule')
        for tr in div.findAll('tr'):
            if tr.th:
                show_date = tr.th.string.encode('utf-8')
                day, month, year, temp = show_date.split()
                month = get_month(month)
                date = datetime.date(int(year), int(month), int(day))
            
            if tr.td:
                film_tag = tr.td.a
                film_id = film_tag.get('href').replace('/movies/','').encode('utf-8')
                film_name = film_tag.string.encode('utf-8')
                film_slug = del_screen_type(low(del_separator(film_name)))
                
                full_url = '%smovies/%s' % (source.url, film_id.decode('utf-8'))

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
                            for time in tr.findAll('span'):
                                hours, minutes = time.string.split(':')
                                
                                dtime = datetime.datetime(date.year, date.month, date.day, int(hours), int(minutes))

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
def zlat74ru_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.zlat74.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


