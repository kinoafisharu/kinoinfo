#-*- coding: utf-8 -*- 
import urllib
import re
import datetime
import time
import cgi
import random

from django.http import HttpResponse
from django.conf import settings

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, \
    xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, \
    get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_premierzal_cities():
    source = ImportSources.objects.get(url='http://www.premierzal.ru/')

    cities = get_source_data(source, 'city', 'list')

    data_nof_city = ''

    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read())

        block = data.find('div', {'class': 'drop'})

        for i in block.findAll('a'):
            city_name = i.text.encode('utf-8').strip()
            city_id = low(del_separator(city_name))

            if city_id.decode('utf-8') not in cities:

                city = City.objects.filter(
                    name__name=city_id, name__status=2).distinct('pk')

                if city.count() == 1:
                    SourceCities.objects.create(
                        source_id=city_id,
                        source_obj=source,
                        city=city[0],
                        name=city_name,
                    )
                else:
                    data_nof_city += '<city name="%s" slug="%s"></city>' % (
                        city_name, city_id)

                cities.append(city_id.decode('utf-8'))

    create_dump_file(
        '%s_nof_city' % source.dump,
        settings.NOF_DUMP_PATH,
        '<data>%s</data>' % data_nof_city)
    cron_success('html', source.dump, 'cities', 'Города')


@timer
def get_premierzal_cinemas():
    source = ImportSources.objects.get(url='http://www.premierzal.ru/')

    cinemas = get_source_data(source, 'cinema', 'list')

    cities_dict = get_source_data(source, 'city', 'dict')

    cinemas_dict = {}
    for i in Cinema.objects.all():
        cinemas_dict[i.code] = i

    ignored_cinemas = get_ignored_cinemas()

    data_nof_cinema = ''

    city = cities_dict.values()[0]

    body = urllib.urlencode({
        'city': city.name.encode('utf-8'),
    })

    url = '%stheatres?%s' % (source.url, body)

    req = urllib.urlopen(url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read())

        blocks = []

        block1 = data.find('div', {'class': 'this_city_theatres'})
        block2 = data.find('div', {'class': 'other_city_theatres'})

        if block1:
            blocks.append(block1)

        if block2:
            blocks.append(block2)

        for ind, block in enumerate(blocks):
            for a in block.findAll('a'):
                cinema_name = a.text.encode('utf-8').strip().replace('"', '')
                cinema_id = a.get('href').replace('/theatres/', '').replace('/', '')

                if ind == 0:
                    city_obj = city
                else:
                    city_name, cinema_name = cinema_name.split(',')
                    cinema_name = cinema_name.strip()
                    city_slug = low(del_separator(city_name.strip()))
                    city_obj = cities_dict.get(city_slug.decode('utf-8'))

                cinema_slug = low(del_separator(cinema_name))

                if city_obj:
                    cinema_ig_id = u'%s__%s' % (
                        cinema_slug.decode('utf-8'), city_obj.city.kid)

                    if cinema_id.decode('utf-8') not in cinemas and cinema_ig_id not in ignored_cinemas:

                        filter1 = {
                            'name__name': cinema_slug,
                            'name__status': 2,
                            'city__id': city_obj.city_id}

                        cinema = cinema_identification(cinema_slug, filter1)

                        cin_obj = cinemas_dict.get(cinema)
                        if cin_obj:
                            SourceCinemas.objects.create(
                                source_id=cinema_id,
                                source_obj=source,
                                city=city_obj,
                                cinema=cin_obj,
                                name=cinema_name,
                            )
                            cinemas.append(cinema_id.decode('utf-8'))
                        else:
                            data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_obj.name.encode('utf-8'), city_obj.city.kid)

    create_dump_file(
        '%s_nof_cinema' % source.dump,
        settings.NOF_DUMP_PATH,
        '<data>%s</data>' % data_nof_cinema)
    cron_success('html', source.dump, 'cinemas', 'Кинотеатры')


@timer
def get_premierzal_schedules():
    data_nof_film = ''
    noffilms = []

    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://www.premierzal.ru/')
    sfilm_clean(source)

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    schedules = get_source_data(source, 'schedule', 'list')

    cities_cinemas = {}
    for i in SourceCinemas.objects.select_related('city').filter(source_obj=source):
        if not cities_cinemas.get(i.city.source_id):
            cities_cinemas[i.city.source_id] = {'city': i.city, 'cinemas': []}
        cities_cinemas[i.city.source_id]['cinemas'].append(i)

    for k, v in cities_cinemas.iteritems():
        city_url_encode = urllib.quote(v['city'].name.encode('utf-8'))
        for i in v['cinemas']:
            main_url = '%s?theatre=%s&city=%s' % (
                source.url, i.source_id, city_url_encode)

            main_req = urllib.urlopen(main_url)
            if main_req.getcode() == 200:
                data = BeautifulSoup(main_req.read())
                data = data.find('div', id="films-list")

                if data:
                    dates = []
                    for calendar in data.findAll('table', {'class': 'calendar'}):
                        for a in calendar.findAll('a'):
                            href = a.get('href', '')
                            href_dict = dict(cgi.parse_qsl(href))
                            calendar_date = href_dict.get(u'?date', href_dict.get(u'date'))
                            if calendar_date:
                                dates.append({
                                    'date': calendar_date,
                                    'href': href})

                    for ind, d in enumerate(dates):
                        films_blocks = []
                        if ind == 0:
                            films_blocks = data.findAll(
                                'div', {'class': 'film-item-wrapper'})
                        else:
                            url = '%s?date=%s&city=%s&theatre=%s' % (
                                source.url, d['date'],
                                city_url_encode, i.source_id)

                            req = urllib.urlopen(url)
                            if req.getcode() == 200:
                                data = BeautifulSoup(req.read())
                                data = data.find('div', id="films-list")
                                films_blocks = data.findAll(
                                    'div', {'class': 'film-item-wrapper'})
                            time.sleep(random.uniform(0.8, 2.2))

                        for block in films_blocks:
                            title = block.find(
                                'div', {'class': 'title'}).find('a')

                            film_name = title.text.encode('utf-8').strip()
                            film_slug = low(
                                del_separator(del_screen_type(film_name)))
                            film_id = film_slug

                            if film_id not in noffilms and film_slug.decode('utf-8') not in ignored:

                                obj = films.get(film_id.decode('utf-8'))
                                next_step = checking_obj(obj)

                                if next_step:
                                    if obj:
                                        kid = obj.kid
                                    else:
                                        kid, info = film_identification(
                                            film_slug, None, {}, {},
                                            source=source)

                                    objt = None
                                    if kid:
                                        create_new, objt = unique_func(
                                            fdict, kid, obj)
                                        if create_new:
                                            objt = create_sfilm(
                                                film_id, kid,
                                                source, film_name)
                                            films[film_id.decode('utf-8')] = objt
                                            if not fdict.get(kid):
                                                fdict[kid] = {
                                                    'editor_rel': [],
                                                    'script_rel': []}
                                            fdict[kid]['script_rel'].append(
                                                objt)
                                    elif not obj:
                                        data_nof_film += xml_noffilm(
                                            film_name, film_slug,
                                            None, None, film_id,
                                            info, None, source.id)
                                        noffilms.append(film_id)

                                    if objt:
                                        year, month, day = d['date'].split(u'-')

                                        for tm in block.findAll('div', {'class': 'seanse-item'}):
                                            for t in tm.text.encode('utf-8').split('|'):
                                                t = re.findall(
                                                    r'\d{2}\:\d{2}', t)
                                                if t:
                                                    hours, minutes = t[0].strip().split(':')
                                                    dtime = datetime.datetime(
                                                        int(year), int(month),
                                                        int(day), int(hours),
                                                        int(minutes))

                                                    sch_id = '%s%s%s' % (
                                                        dtime, i.source_id.encode('utf-8'), film_id)
                                                    sch_id = sch_id.replace(' ', '').decode('utf-8')

                                                    if sch_id not in schedules:
                                                        SourceSchedules.objects.create(
                                                            source_id=sch_id,
                                                            source_obj=source,
                                                            film=objt,
                                                            cinema=i,
                                                            dtime=dtime,
                                                        )
                                                        schedules.append(sch_id)
            time.sleep(random.uniform(1.1, 1.8))

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def premierzal_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.premierzal.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file(
        '%s_export_to_kinoafisha_log' % source.dump,
        settings.LOG_DUMP_PATH,
        '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
