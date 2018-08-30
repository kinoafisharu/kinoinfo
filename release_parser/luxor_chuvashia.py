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
def get_luxor_chuvashia_schedules():
    today = datetime.datetime.now().strftime('%d.%m.%Y')
    data_nof_film = ''
    noffilms = []
    
    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://luxor.chuvashia.com/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')


    data = [
        {'city': 'Чебоксары', 'cinema': 'Мир Луксор', 'url': '%sschedule.aspx?kinoteatr=luxor' % source.url},
        {'city': 'Новочебоксарск', 'cinema': 'Атал', 'url': '%sschedule.aspx?kinoteatr=atal' % source.url},
    ]

    def get_page_data(date, data_list):
        url = '%s&date=%s' % (i['url'], date)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            page_data = BeautifulSoup(req.read())
            
            div = page_data.find('div', id='BodyContener_ScheduleBlock')
            table = div.find('table', id='BodyContener_TCalendar')
            
            for j in div.findAll('div', {'class': 'ScheduleTitle'}):
                data_list.append({'date': date, 'title': j, 'sch': j.next_sibling})

            day, month, year = date.split('.')
            date_obj_current = datetime.date(int(year), int(month), int(day))
            
            for a in table.findAll('a'):
                link = a.get('href')
                d = re.findall(r'\=[\d+\.?]+', link.encode('utf-8'))[0].replace('=','')
                day, month, year = d.split('.')
                date_obj = datetime.date(int(year), int(month), int(day))

                if date_obj > date_obj_current:
                    get_page_data(d, data_list)
                    
        return data_list


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
    
        cinema_slug = low(del_separator(i['cinema']))
        cinema = Cinema.objects.get(name__name=i['cinema'], name__status=1, city=city)
        
        cinema_obj, cinema_created = SourceCinemas.objects.get_or_create(
            source_id = cinema_slug,
            source_obj = source,
            defaults = {
                'source_id': cinema_slug,
                'source_obj': source,
                'city': city_obj,
                'cinema': cinema,
                'name': i['cinema'],
            })
        
        data_list = get_page_data(today, [])
            
        for schedule in data_list:
            tag_a = schedule['title'].find('a')
            film_name = tag_a.text.encode('utf-8')
            film_slug = low(del_separator(del_screen_type(film_name)))
            film_url = tag_a.get('href')
            film_id = film_url.replace('films.aspx?id=','').encode('utf-8')
            
            full_url = '%s%s' % (source.url, film_url)
            
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
                        sch_div = schedule['sch'].find('div', {'class': 'ScheduleClock'}).text.encode('utf-8').strip()
                        showtimes = re.findall(r'\d+\:\d+', sch_div)
                        day, month, year = schedule['date'].split('.')
                        
                        for showtime in showtimes:
                            hours, minutes = showtime.split(':')
                            dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))
                            
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
def luxor_chuvashia_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://luxor.chuvashia.com/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')    
        
