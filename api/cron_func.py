#-*- coding: utf-8 -*-
import os
import datetime
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.cache import never_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse

from base.models import User, Accounts, DjangoSite, Background
from api.models import *
from api.func import *
from api.views import *
from release_parser.decors import timer
from release_parser.func import cron_success

source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

@timer
def cron_dump_schedules():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules *') + '\n')
    res, version = query_schedule(None, None)
    result_xml, result_json = get_schedule(res, None, True)
    save_dump(result_xml, None, None, 'schedule')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'schedule', '', 'json')
    cron_success('api', source.dump, 'schedules', 'Сеансы')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules') + '\n')

@timer
def cron_dump_schedules_v2():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules *') + '\n')
    res, date_from = query_schedule_v2(None, None)
    result_xml, result_json = get_schedule_v2(res, None, True, date_from)
    save_dump(result_xml, None, None, 'schedule_v2')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'schedule_v2', '', 'json')
    cron_success('api', source.dump, 'schedules_v2', 'Сеансы v2')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules') + '\n')

@timer
def cron_dump_schedules_v4():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules *') + '\n')
    res = query_schedule_v4(None, None)
    result_xml, result_json = get_schedule_v4(res, None, True)
    save_dump(result_xml, None, None, 'schedule_v4')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'schedule_v4', '', 'json')
    cron_success('api', source.dump, 'schedules_v4', 'Сеансы v4')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('schedules') + '\n')


@timer
def cron_dump_cinemas():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('cinemas *') + '\n')
    res = query_cinema(None)
    result_xml, result_json = get_cinema(res, None, True)
    save_dump(result_xml, None, None, 'cinema')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'cinema', '', 'json')
    cron_success('api', source.dump, 'cinemas', 'Кинотеатры')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('cinemas') + '\n')

@timer
def cron_dump_films():
    years_list = ['1990', '1990_1999', '2000_2009', '2010_2011'] + map(str, range(2012, datetime.date.today().year + 1))
    for i in years_list:
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_%s *' % i) + '\n')
        res = get_year_films(i)
        result_xml, result_json = get_film(res, None, None, True)
        save_dump(result_xml, None, None, 'film', i, 'xml')
        save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film', i, 'json')
        cron_success('api', source.dump, 'films_%s' % i, 'Фильмы %s' % i)
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_%s' % i) + '\n')

        
@timer
def cron_dump_films_v3():
    years_list = ['1990', '1990_1999', '2000_2009', '2010_2011'] + map(str, range(2012, datetime.date.today().year + 1))
    version = '3'
    for i in years_list:
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_v%s_%s *' % (version, i)) + '\n')
        res = get_year_films(i, version)
        result_xml, result_json = get_film(res, None, None, True, version)
        save_dump(result_xml, None, None, 'film', i, 'xml', version)
        save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film', i, 'json', version)
        cron_success('api', source.dump, 'films_v%s_%s' % (version, i), 'Фильмы v%s %s' % (version, i))
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_v%s_%s' % (version, i)) + '\n')

@timer
def cron_dump_films_v4():
    years_list = ['1990', '1990_1999', '2000_2009', '2010_2011'] + map(str, range(2012, datetime.date.today().year + 1))
    version = '4'
    for i in years_list:
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_v%s_%s *' % (version, i)) + '\n')
        res = get_year_films(i, version)
        result_xml, result_json = get_film(res, None, None, True, version)
        save_dump(result_xml, None, None, 'film', i, 'xml', version)
        save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film', i, 'json', version)
        cron_success('api', source.dump, 'films_v%s_%s' % (version, i), 'Фильмы v%s %s' % (version, i))
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_v%s_%s' % (version, i)) + '\n')

@timer
def cron_dump_persons():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('persons *') + '\n')
    res = query_persons(None)
    result_xml, result_json = get_persons(res, None, True)
    save_dump(result_xml, None, None, 'persons')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'persons', '', 'json')
    cron_success('api', source.dump, 'persons', 'Персоны')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('persons') + '\n')

@timer
def cron_dump_halls():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('halls *') + '\n')
    res = query_hall(None)
    result_xml, result_json = get_hall(res, None, True)
    save_dump(result_xml, None, None, 'hall')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'hall', '', 'json')
    cron_success('api', source.dump, 'halls', 'Залы')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('halls') + '\n')

@timer
def cron_dump_hall_dir():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('halls_dir *') + '\n')
    res = query_hall_dir(None)
    result_xml, result_json = get_hall_dir(res, None, True)
    save_dump(result_xml, None, None, 'hall_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'hall_dir', '', 'json')
    cron_success('api', source.dump, 'hall_dir', 'Названия залов')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('halls_dir') + '\n')

@timer
def cron_dump_city_dir():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('city_dir *') + '\n')
    res = query_city_dir(None)
    result_xml, result_json = get_city_dir(res, None, True)
    save_dump(result_xml, None, None, 'city_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'city_dir', '', 'json')
    cron_success('api', source.dump, 'city_dir', 'Названия городов')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('city_dir') + '\n')

@timer
def cron_dump_genre_dir():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('genre_dir *') + '\n')
    res = query_genre_dir(None)
    result_xml, result_json = get_genre_dir(res, None, True)
    save_dump(result_xml, None, None, 'genre_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'genre_dir', '', 'json')
    cron_success('api', source.dump, 'genre_dir', 'Названия жанров')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('genre_dir') + '\n')
    
@timer
def cron_dump_metro_dir():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('metro_dir *') + '\n')
    res = query_metro_dir(None)
    result_xml, result_json = get_metro_dir(res, None, True)
    save_dump(result_xml, None, None, 'metro_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'metro_dir', '', 'json')
    cron_success('api', source.dump, 'metro_dir', 'Метро')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('metro_dir') + '\n')

@timer
def cron_dump_theater():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('theater *') + '\n')
    res = query_theater(None)
    result_xml, result_json = get_theater(res, None, True)
    save_dump(result_xml, None, None, 'theater')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'theater', '', 'json')
    cron_success('api', source.dump, 'theater', 'Кинотеатры (Дания)')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('theater') + '\n')

@timer
def cron_dump_screens():
    vers = [{'ver': 1, 'name': 'screens'}, {'ver': 2, 'name': 'screens_v2'}]
    qresult = query_screens(None)
    for i in vers:
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('Сеансы v.%s (Дания) *' % i['ver']) + '\n')
        result_xml, result_json = get_screens(qresult, i['ver'], None, True)
        save_dump(result_xml, None, None, i['name'])
        save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, i['name'], '', 'json')
        cron_success('api', source.dump, i['name'], 'Сеансы v.%s (Дания)' % i['ver'])
        open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('Сеансы v.%s (Дания)' % i['ver']) + '\n')

@timer
def cron_dump_imovie():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('imovie *') + '\n')
    res = query_imovie(None)
    result_xml, result_json = get_imovie(res, None, True)
    save_dump(result_xml, None, None, 'imovie')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'imovie', '', 'json')
    cron_success('api', source.dump, 'imovie', 'Фильмы (Дания)')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('imovie') + '\n')

@timer
def cron_dump_films_name():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_name *') + '\n')
    res = query_films_name(None)
    result_xml, result_json = get_films_name(res, None, True)
    save_dump(result_xml, None, None, 'films_name')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'films_name', '', 'json')
    cron_success('api', source.dump, 'films_name', 'Названия фильмов')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('films_name') + '\n')
    
@timer
def cron_dump_imdb_rate():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('imdb_rate *') + '\n')
    res = query_imdb_rate(None, None)
    result_xml, result_json = get_imdb_rate(res, None, True)
    save_dump(result_xml, None, None, 'imdb_rate')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'imdb_rate', '', 'json')
    cron_success('api', source.dump, 'imdb_rate', 'IMDB рейтинги')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('imdb_rate') + '\n')

@timer
def cron_dump_movie_reviews():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('movie_reviews *') + '\n')
    res = query_movie_reviews(None, None)
    result_xml, result_json = get_movie_reviews(res, None, True)
    save_dump(result_xml, None, None, 'movie_reviews')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'movie_reviews', '', 'json')
    cron_success('api', source.dump, 'movie_reviews', 'Рецензии')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('movie_reviews') + '\n')

@timer
def cron_dump_film_posters():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_posters *') + '\n')
    res = query_film_posters(None, None)
    result_xml, result_json = get_film_posters(res, None, True)
    save_dump(result_xml, None, None, 'film_posters')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film_posters', '', 'json')
    cron_success('api', source.dump, 'film_posters', 'Постеры')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_posters') + '\n')

@timer
def cron_dump_film_trailers():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_trailers *') + '\n')
    res, version = query_film_trailers(None, None)
    result_xml, result_json = get_film_trailers(res, None, True)
    save_dump(result_xml, None, None, 'film_trailers')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film_trailers', '', 'json')
    cron_success('api', source.dump, 'film_trailers', 'Трейлеры')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_trailers') + '\n')
        
@timer
def cron_dump_film_trailers_v2():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_trailers_v%s *' % version) + '\n')
    res, version = query_film_trailers(None, None)
    version = '2'
    result_xml, result_json = get_film_trailers(res, None, True, version)
    save_dump(result_xml, None, None, 'film_trailers', '', 'xml', version)
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'film_trailers', '', 'json', version)
    cron_success('api', source.dump, 'film_trailers_v%s' % version, 'Трейлеры_v%s' % version)
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('film_trailers_v%s' % version) + '\n')
    

@timer
def cron_dump_releases_ua():
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('releases_ua *') + '\n')
    res = query_releases_ua(None)
    result_xml, result_json = get_releases_ua(res, None, True)
    save_dump(result_xml, None, None, 'releases_ua')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), None, None, 'releases_ua', '', 'json')
    cron_success('api', source.dump, 'releases_ua', 'Укр. релизы')
    open('%s/api_time_log.txt' % settings.API_DUMP_PATH, 'a').write(str(datetime.datetime.now()) + '\t' + str('releases_ua') + '\n')


