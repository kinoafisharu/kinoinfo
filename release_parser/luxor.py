#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import httplib
import socket

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils import simplejson as json
from django.db.models import Q
from django import db

from bs4 import BeautifulSoup
from base.models import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


LUXOR_SERVER = '212.248.42.242'
LUXOR_PORT = 9195
LUXOR_ID = '1247333558'



def get_luxor_data_by_socket(query):
    # составлен запрос по документации UCS-Премьера
    query = 'ServiceID=%s&%s&Encoding=utf-8&Version=3' % (LUXOR_ID, query)
    
    # подсчет символов в запросе, например их 159, 
    # в итоге должно быть 10 значное число (0000000159)
    query_lenght = ''
    for i in range(len(str(len(query))), 10):
        query_lenght += '0'
    query_lenght += str(len(query))
    
    # складываем в одну строку кол-во символов в запросе и сам запрос
    query = '%s&%s' % (query_lenght, query)
    
    # создаем сокет
    sock = socket.socket()
    # подключаемся к серверу
    sock.connect((LUXOR_SERVER, LUXOR_PORT))
    # отправляем запрос
    sock.send(query)
    
    # получаем данные через цикл, 1 итерация = 1024 байт данных
    # цикл продолжается пока все данные не будут получены
    data = ''
    while 1:
        sock_data = sock.recv(1024)
        if sock_data: 
            data += sock_data
        else:
            break
    
    # закрываем соединение с сервером
    sock.close()

    return data[11:]


@timer
def get_luxor_cinemas():
    query = 'QueryCode=GetHalls'
    
    data = get_luxor_data_by_socket(query)

    source = ImportSources.objects.get(url='http://luxor.ru/')
    
    #create_dump_file('%s_cinemas' % source.dump, settings.API_DUMP_PATH, data)
    
    data_nof_cinema = ''
    data_nof_city = ''
    data_nof_hall = ''
    nofcities = []
    nofcinemas = []
    
    cinemas = get_source_data(source, 'cinema', 'dict')
    cities = get_source_data(source, 'city', 'dict')
    
    ignored_cinemas = get_ignored_cinemas()

    halls = get_source_data(source, 'hall', 'dict')
    '''
    xml = open('%s/dump_%s_cinemas.xml' % (settings.API_DUMP_PATH, source.dump), 'r')# temp
    data = xml.read()# temp
    xml.close()# temp
    '''
    xml_data = BeautifulSoup(data, from_encoding="utf-8")
    
    for cinema in xml_data.findAll('theatre'):
        cinema_id = cinema['id'].encode('utf-8')
        cinema_name = cinema.find('name').text.encode('utf-8')
        cinema_name = cinema_name.replace('[CDATA[','').replace(']]','').strip()
        cinema_slug = low(del_separator(cinema_name))

        cinema_alt_name = 'Люксор'
        cinema_alt_slug = 'люксор'
        
        address = cinema.find('address').text.encode('utf-8')
        address = address.replace('[CDATA[','').replace(']]','').replace('"',"'").strip()

        city_obj = cities.get(cinema_slug.decode('utf-8'))
        if not city_obj and cinema_slug not in nofcities:
            city = City.objects.filter(name__name=cinema_slug, name__status=2).distinct('pk')
            if city.count() == 1:
                city_obj = SourceCities.objects.create(
                    source_id = cinema_slug,
                    source_obj = source,
                    city = city[0],
                    name = cinema_name,
                )
                cities[cinema_slug] = city_obj
            else:
                data_nof_city += '<city name="%s" slug="%s" info="%s"></city>' % (cinema_name, cinema_slug, address)
                nofcities.append(cinema_slug)
        
        if city_obj:
            cinema_obj = cinemas.get(cinema_id)
            city_kid = city_obj.city.kid
            
            cinema_ig_id = u'%s__%s' % (cinema_slug.decode('utf-8'), city_kid)

            if cinema_ig_id not in ignored_cinemas:
            
                if not cinema_obj:
                    filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city__kid': city_kid}
                    cinema_kid = cinema_identification(cinema_slug, filter1, {}, city_kid)
                    if cinema_kid:
                        cin_obj = Cinema.objects.get(code=cinema_kid)
                        cinema_obj = SourceCinemas.objects.create(
                            source_id = cinema_id,
                            source_obj = source,
                            city = city_obj,
                            cinema = cin_obj,
                            name = cinema_name,
                        )
                        cinemas[cinema_id] = cinema_obj
                    else:
                        city_name = ''
                        for i in city_obj.city.name.all():
                            if i.status == 1:
                                city_name = i.name.encode('utf-8')
                        
                        data_nof_cinema += '<cinema name="Люксор %s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name,  cinema_slug, city_name, city_kid)

                if cinema_obj:
                    for i in cinema.findAll('hall'):
                        hall_id = i['id'].encode('utf-8')
                        hall_name = i.find('name').string.encode('utf-8')
                        hall_name = hall_name.replace('[CDATA[','').replace(']]','').strip()
                        hall_slug = low(del_separator(hall_name))
                        
                        hall_obj = halls.get(hall_id)
                        if not hall_obj:
                            hall_obj = Hall.objects.filter(name__name=hall_slug, cinema=cinema_obj.cinema).distinct('pk')
                            if hall_obj.count() == 1:
                                hall_kid = hall_obj[0].kid

                                SourceHalls.objects.create(
                                    source_id = hall_id,
                                    source_obj = source,
                                    cinema = cinema_obj,
                                    name = hall_name,
                                    kid = hall_kid,
                                )
                            else:
                                city_name = ''
                                for i in city_obj.city.name.all():
                                    if i.status == 1:
                                        city_name = i.name.encode('utf-8')
                                
                                cinema_kid = cinema_obj.cinema.code
                                id = '%s%s%s%s' % (city_kid, cinema_kid, hall_name, hall_slug)
                                id = id.replace(' ','')
                                data_nof_hall += '<hall city="%s" city_kid="%s" cinema="Люксор %s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city_name, city_kid, cinema_name, cinema_kid, hall_name, hall_slug, id)
        
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    create_dump_file('%s_nof_hall' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_hall)
    
    cron_success('xml', source.dump, 'cities_and_cinemas', 'Города и кинотеатры')

                            

@timer
def get_luxor_films():
    query = 'QueryCode=GetMovies'

    data = get_luxor_data_by_socket(query)

    source = ImportSources.objects.get(url='http://luxor.ru/')
    sfilm_clean(source)
    
    #create_dump_file('%s_films' % source.dump, settings.API_DUMP_PATH, data)
    
    data_nof_films = ''
    noffilms = []
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    '''
    xml = open('%s/dump_%s_films.xml' % (settings.API_DUMP_PATH, source.dump), 'r')# temp
    data = xml.read()# temp
    xml.close()# temp
    '''
    ignored = get_ignored_films()
    
    xml_data = BeautifulSoup(data, from_encoding="utf-8")

    for film in xml_data.findAll('movie'):
        film_id = film['id'].encode('utf-8')
        film_name = film.find('othername').string.encode('utf-8').replace('[CDATA[','').replace(']]','')
        film_slug = low(del_separator(del_screen_type(film_name)))
        

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
                        new = create_sfilm(film_id, kid, source, film_name)
                        films[film_id] = new
                        if not fdict.get(kid):
                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                        fdict[kid]['script_rel'].append(new)
                elif not obj:
                    data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, None, source.id)
                    noffilms.append(film_id)
        
                                    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    cron_success('xml', source.dump, 'films', 'Фильмы')
    
    

@timer
def get_luxor_schedules():

    query = 'QueryCode=GetSessions'

    data = get_luxor_data_by_socket(query)

    source = ImportSources.objects.get(url='http://luxor.ru/')
    
    #create_dump_file('%s_schedules' % source.dump, settings.API_DUMP_PATH, data)
    '''
    xml = open('%s/dump_%s_schedules.xml' % (settings.API_DUMP_PATH, source.dump), 'r')# temp
    data = xml.read()# temp
    xml.close()# temp
    '''
    films = get_source_data(source, 'film', 'dict')
    cinemas = get_source_data(source, 'cinema', 'dict')
    halls = get_source_data(source, 'hall', 'dict')
    schedules = get_source_data(source, 'schedule', 'list')
    
    xml_data = BeautifulSoup(data, from_encoding="utf-8")
    
    for session in xml_data.findAll('session'):
        sch_id = session['id']
        if sch_id not in schedules:
            cinema_id = session.theatre['id'].encode('utf-8')
            hall_id = session.theatre.hall['id'].encode('utf-8')
            film_id = session.movie['id'].encode('utf-8')
            
            cinema_obj = cinemas.get(cinema_id)
            film_obj = films.get(film_id)
            hall_obj = halls.get(hall_id)
            
            if cinema_obj and film_obj and hall_obj:
                showdate = session.date.string.encode('utf-8')
                showtime = session.time.string.encode('utf-8')

                day, month, year = showdate.split('.')
                hours, minutes = showtime.split(':')
                
                dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))

                SourceSchedules.objects.create(
                    source_id = sch_id,
                    source_obj = source,
                    film = film_obj,
                    cinema = cinema_obj,
                    dtime = dtime,
                    hall = hall_obj.kid,
                )

    cron_success('xml', source.dump, 'schedules', 'Сеансы')


@timer
def luxor_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://luxor.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, True)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')


