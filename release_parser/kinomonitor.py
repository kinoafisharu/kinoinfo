#-*- coding: utf-8 -*- 
import urllib
import datetime

from django import db
from django.http import HttpResponse
from django.conf import settings

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_kinomonitor_cities_and_cinemas():
    data_nof_cinema = ''
    data_nof_city = ''

    source = ImportSources.objects.get(url='http://kinomonitor.ru/')

    cinemas_dict = get_source_data(source, 'cinema', 'dict')
    cities_dict = get_source_data(source, 'city', 'dict')

    ignored_cinemas = get_ignored_cinemas()

    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        cinema_nav = data.find('ul', {'class': 'global-nav-drop'})
        for li in cinema_nav.findAll('li', {'class': 'global-nav-drop__item js-has-drop'}):
            city_id = li.get('data-city-id')
            cinema_link = li.findAll('a', limit=1)[0]
            cinema_href = cinema_link.get('href')
            cinema_id = cinema_href.replace('/cinemas/', '').replace('/', '')
            cinema_name, city_name = cinema_link.text.encode('utf-8').split(' (')
            cinema_name = cinema_name.replace('«', '').replace('»', '').strip()
            cinema_slug = low(del_separator(cinema_name))
            city_name = city_name.replace(')', '').strip()
            city_slug = low(del_separator(city_name))

            city_obj = cities_dict.get(city_id)

            if not city_obj:
                city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
                if city.count() == 1:
                    city_obj = SourceCities.objects.create(
                        source_id=city_id,
                        source_obj=source,
                        city=city[0],
                        name=city_name,
                    )
                    cities_dict[city_id] = city_obj
                else:
                    data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)

            if city_obj and cinema_slug.decode('utf-8') not in ignored_cinemas:

                cinema_obj = cinemas_dict.get(cinema_id)

                if not cinema_obj:
                    filter = {'name__name': cinema_slug, 'name__status': 2, 'city': city_obj.city}
                    cinema_kid = cinema_identification(cinema_slug, filter)
                    if cinema_kid:
                        try:
                            cin_obj = Cinema.objects.get(code=cinema_kid)
                            cinema_obj = SourceCinemas.objects.create(
                                source_id=cinema_id,
                                source_obj=source,
                                city=city_obj,
                                cinema=cin_obj,
                                name=cinema_name,
                            )
                            cinemas_dict[cinema_id] = cinema_obj
                        except Cinema.DoesNotExist:
                            pass
                    else:
                        data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_name, city_obj.city.kid)

    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('html', source.dump, 'cities_and_cinemas', 'Города и кинотеатры')


@timer
def get_kinomonitor_films_and_schedules():
    ignored = get_ignored_films()

    data_nof_film = ''
    noffilms = []

    source = ImportSources.objects.get(url='http://kinomonitor.ru/')
    sfilm_clean(source)

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    schedules = get_source_data(source, 'schedule', 'list')

    cinemas_data = SourceCinemas.objects.select_related('city').filter(source_obj=source)
    for i in cinemas_data:
        url = '%scinemas/%s/schedule/' % (source.url, i.source_id)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            for content in data.findAll('li', {'class': 'shedule-item shedule-item--expanded'}):
                film_tag = content.find('div', {'class': 'shedule-item-title js-context-film'})

                film_name = film_tag.find('span').text.encode('utf-8').strip()
                film_slug = low(del_separator(del_screen_type(film_name)))
                film_href = film_tag.get('data-ajax')
                film_id = film_href.split('?id=')[1]
                full_url = '%s%s' % (source.url, film_href.lstrip('/'))

                try:
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
                                data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                                noffilms.append(film_id)

                            if objt:
                                for row in content.findAll('div', {'class': 'shedule-item__sessions-row'}):

                                    showdate = row.find('div', {'class': 'shedule-item__sessions-label'})
                                    day, month, year = showdate.text.strip().split('.')

                                    showtimes = row.find('div', {'class': 'shedule-item__sessions-list'})

                                    for t in showtimes.findAll('li', {'class': 'session js-context-session'}):
                                        hours, minutes = t.find('div', {'class': 'session__time'}).text.strip().split(':')
                                        dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes))

                                        sch_id = '%s%s%s%s' % (dtime, i.source_id, i.city_id, film_id)
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

                except db.backend.Database._mysql.OperationalError:
                    pass

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def kinomonitor_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://kinomonitor.ru/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
