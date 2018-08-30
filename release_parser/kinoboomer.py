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
from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success



@timer
def get_kinoboomer_schedules():
    ignored = get_ignored_films()
    
    data_nof_film = ''
    data_nof_hall = ''
    data_nof_cinema = ''
    noffilms = []
    nofhalls = []
    
    city_name = 'Киев'
    cinema_name = 'Boomer'
    city_slug = low(del_separator(city_name))
    cinema_slug = low(del_separator(cinema_name))
    
    source = ImportSources.objects.get(url='http://www.kinoboomer.com.ua/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    schedules = get_source_data(source, 'schedule', 'list')
    
    halls = get_source_data(source, 'hall', 'dict')

    city = City.objects.get(name__name=city_name, name__status=1)

    try:
        cinema = Cinema.objects.get(name__name=cinema_name, name__status=1, city=city)
    except Cinema.DoesNotExist:
        cinema = None
        data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name,  cinema_slug, city_name, city.kid)

    film_urls = []

    if cinema:
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
        
        cinema_kid = cinema.code
        city_kid = city.kid

        today = datetime.date.today()

        url = '%sseances' % source.url
        
        req = urllib.urlopen(url)

        if req.getcode() == 200:

            data = BeautifulSoup(req.read())
            content = data.find('div', {'class': 'view-content'})
            for i in content.findAll('h3'):
                a = i.find('a')
                film_id = a.get('href').strip().encode('utf-8')
                full_url = '%s%s' % (source.url, film_id.lstrip('/'))
                film_name = a.text.strip().encode('utf-8')
                film_slug = low(del_separator(film_name))

                film_urls.append({
                    'film_id': film_id,
                    'film_name': film_name,
                    'film_slug': film_slug,
                    'full_url': full_url,
                })


    for i in film_urls:

        if i['film_id'] not in noffilms and i['film_slug'].decode('utf-8') not in ignored:
            # Идентифицирую фильм
            obj = films.get(i['film_id'])
            next_step = checking_obj(obj)
            
            if next_step:
                if obj:
                    kid = obj.kid
                else:
                    kid, info = film_identification(i['film_slug'], None, {}, {}, source=source)
        
                objt = None
                if kid:
                    create_new, objt = unique_func(fdict, kid, obj)
                    if create_new:
                        new = create_sfilm(i['film_id'], kid, source, i['film_name'])
                        films[i['film_id']] = new
                        if not fdict.get(kid):
                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                        fdict[kid]['script_rel'].append(new)
                elif not obj:
                    #open('ddd.txt','a').write(str((type(i['film_name']), type(i['film_slug']), type(i['full_url']))))
                    data_nof_film += xml_noffilm(i['film_name'], i['film_slug'], None, None, i['film_id'], info, i['full_url'].encode('utf-8'), source.id)
                    noffilms.append(i['film_id'])


                # если фильм найден, то идентифицирую зал
                if objt:

                    req = urllib.urlopen(i['full_url'])
                    if req.getcode() == 200:

                        data = BeautifulSoup(req.read())

                        hall_name = ''

                        content = data.find('div', {'class': 'view-grouping-content'})

                        if content:
                            wrapper = content.findAll('div', {'class': 'group-wrapper'}, limit=1)
                            if wrapper:
                                widget_links = wrapper[0].findAll('a', {'class': 'vkino-link'}, limit=1)
                                widget_req = urllib.urlopen(widget_links[0].get('href'))
                                if widget_req.getcode() == 200:
                                    widget_data = BeautifulSoup(widget_req.read(), from_encoding="utf-8")
                                    nav = widget_data.find('div', id='purchase-navigation')
                                    li = nav.findAll('li', limit=1)[0]
                                    li.a.extract()
                                    li.nobr.extract()
                                    hall_name = li.text.strip().encode('utf-8').split('«')[-1].split('»')[0]

                        
                        hall_name_slug = low(del_separator(hall_name))
               
                        if hall_name and hall_name_slug not in nofhalls:

                            hall_obj = halls.get(hall_name_slug)

                            if not hall_obj:
                                halls_obj = Hall.objects.filter(name__name=hall_name_slug, cinema=cinema_obj.cinema).distinct('pk')
                                if halls_obj.count() == 1:
                                    hall_kid = halls_obj[0].kid

                                    hall_obj = SourceHalls.objects.create(
                                        source_id = hall_name_slug,
                                        source_obj = source,
                                        cinema = cinema_obj,
                                        name = hall_name,
                                        kid = hall_kid,
                                    )

                                    halls[hall_name_slug] = hall_obj
                                else:
                                    id = '%s%s%s%s' % (city_kid, cinema_kid, hall_name, hall_name_slug)
                                    id = id.replace(' ','')
                                    data_nof_hall += '<hall city="%s" city_kid="%s" cinema="%s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city_name, city_kid, cinema_name, cinema_kid, hall_name, hall_name_slug, id)
                                    nofhalls.append(hall_name_slug)


                            if hall_obj:
                                # если зал найден, то получаю сеансы и создаю

                                #day, day_month = wrapper.find('h3').text.strip().split()
                                #day, month = day_month.split('.')
                                #date_sch = datetime.date(today.year, int(month), int(day))

                                for wrapper in content.findAll('div', {'class': 'group-wrapper'}):
                                    widget_links = wrapper.findAll('a', {'class': 'vkino-link'})
                                    for link in widget_links:
                                        dtime = link.find('span').get('content').replace('T', ' ').split('+')[0]

                                        dtime = datetime.datetime.strptime(dtime, "%Y-%m-%d %H:%M:%S")
                                        
                                        sch_id = '%s%s%s' % (dtime, hall_obj.id, i['film_id'])
                                        sch_id = sch_id.replace(' ', '').decode('utf-8')
                                        
                                        if sch_id not in schedules:
                                            SourceSchedules.objects.create(
                                                source_id = sch_id,
                                                source_obj = source,
                                                film = objt,
                                                cinema = cinema_obj,
                                                hall = hall_obj.kid,
                                                dtime = dtime,
                                            )
                                            schedules.append(sch_id)


    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    create_dump_file('%s_nof_hall' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_hall)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы') 



@timer
def kinoboomer_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.kinoboomer.com.ua/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')

