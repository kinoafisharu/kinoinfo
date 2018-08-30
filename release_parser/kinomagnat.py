#-*- coding: utf-8 -*- 
import urllib
import datetime

from django.conf import settings
from django.http import HttpResponse

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month_ua, del_separator, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


#@timer
def get_kinomagnat_schedules():
    ignored = get_ignored_films()

    data_nof_film = ''
    data_nof_hall = ''
    data_nof_cinema = ''
    noffilms = []
    nofhalls = []

    city_name = 'Киев'
    cinema_name = 'Магнат'
    city_slug = low(del_separator(city_name))
    cinema_slug = low(del_separator(cinema_name))

    source = ImportSources.objects.get(url='http://www.kinomagnat.com.ua/')
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

    if cinema:
        city_obj, city_created = SourceCities.objects.get_or_create(
            source_id=city_slug,
            source_obj=source,
            defaults={
                'source_id': city_slug,
                'source_obj': source,
                'city': city,
                'name': city_name,
            })

        cinema_obj, cinema_created = SourceCinemas.objects.get_or_create(
            source_id=cinema_slug,
            source_obj=source,
            defaults={
                'source_id': cinema_slug,
                'source_obj': source,
                'city': city_obj,
                'cinema': cinema,
                'name': cinema_name,
            })

        cinema_kid = cinema.code
        city_kid = city.kid

        today = datetime.date.today()

        url = '%sseans.html?device=iphone' % source.url

        req = urllib.urlopen(url)

        if req.getcode() == 200:

            data = BeautifulSoup(req.read())
            div = data.find('div', {'class': 'contentpaneopen'})

            for table in div.findAll('table'):
                try:
                    day, month = table.find_all_previous("p", limit=2)[1].text.strip().split()
                except ValueError:
                    try:
                        day, month = table.find_all_previous("p", limit=3)[2].text.strip().split()
                    except ValueError:
                        day, month = table.find_all_previous("p", limit=4)[3].text.strip().split()

                month = get_month_ua(low(month.encode('utf-8')))
                date_sch = datetime.date(today.year, month, int(day))

                hall_name = table.findAll('tr', limit=1)[0].text.strip().encode('utf-8')
                hall_name_slug = low(del_separator(hall_name))

                if hall_name_slug not in nofhalls:

                    hall_obj = halls.get(hall_name_slug)

                    if not hall_obj:
                        halls_obj = Hall.objects.filter(name__name=hall_name_slug, cinema=cinema_obj.cinema).distinct('pk')
                        if halls_obj.count() == 1:
                            hall_kid = halls_obj[0].kid

                            hall_obj = SourceHalls.objects.create(
                                source_id=hall_name_slug,
                                source_obj=source,
                                cinema=cinema_obj,
                                name=hall_name,
                                kid=hall_kid,
                            )

                            halls[hall_name_slug] = hall_obj
                        else:
                            id = '%s%s%s%s' % (city_kid, cinema_kid, hall_name, hall_name_slug)
                            id = id.replace(' ', '')
                            data_nof_hall += '<hall city="%s" city_kid="%s" cinema="%s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city_name, city_kid, cinema_name, cinema_kid, hall_name, hall_name_slug, id)
                            nofhalls.append(hall_name_slug)

                    if hall_obj:
                        for ind, tr in enumerate(table.findAll('tr')):
                            if ind != 0:
                                showtime, film_data = tr.findAll('td', limit=2)

                                hour, minute = showtime.text.strip().encode('utf-8').split(':')

                                dtime = datetime.datetime(date_sch.year, date_sch.month, date_sch.day, int(hour), int(minute))

                                a = film_data.find('a')
                                film_id = a.get('href').encode('utf-8')
                                full_url = '%s%s' % (source.url, film_id.lstrip('/'))
                                film_name = a.text.strip().encode('utf-8')
                                film_slug = low(del_separator(film_name))

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
                                            data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, full_url.encode('utf-8'), source.id)
                                            noffilms.append(film_id)

                                        if objt:
                                            sch_id = '%s%s%s' % (dtime, hall_obj.id, film_id)
                                            sch_id = sch_id.replace(' ', '').decode('utf-8')

                                            if sch_id not in schedules:
                                                SourceSchedules.objects.create(
                                                    source_id=sch_id,
                                                    source_obj=source,
                                                    film=objt,
                                                    cinema=cinema_obj,
                                                    hall=hall_obj.kid,
                                                    dtime=dtime,
                                                )
                                                schedules.append(sch_id)

    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    create_dump_file('%s_nof_hall' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_hall)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def kinomagnat_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://www.kinomagnat.com.ua/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
