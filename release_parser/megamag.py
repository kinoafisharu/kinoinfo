#-*- coding: utf-8 -*- 
import urllib2
import re
import datetime
import time
import httplib

from django.http import HttpResponse
from django.conf import settings
from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films, get_ignored_cinemas
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


def get_megamag():
    '''
    Получение urls фильмов
    '''
    import cookielib

    def give_me_cookie():
        cookie = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler())
        return opener

    ignored = get_ignored_films()

    ignored_cinemas = get_ignored_cinemas()

    source = ImportSources.objects.get(url='http://megamag.by/')
    sfilm_clean(source)

    megamag_cities_dict = get_source_data(source, 'city', 'dict')
    megamag_cinemas_dict = get_source_data(source, 'cinema', 'dict')

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    cities_data = {}

    data_nof_films = ''
    data_nof_cinema = ''
    data_nof_city = ''
    noffilms = []
    schedules_data = []

    opener = give_me_cookie()
    req = opener.open(urllib2.Request('http://kinoteatr.megamag.by/index.php'))
    event_dict = {}
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")

        cities = data.find('div', id="box-region")

        for i in cities.findAll('a'):

            city_name = i.text.encode('utf-8')
            city_slug = low(del_separator(city_name))
            city_id = i.get('href').replace('http://kinoteatr.megamag.by/index.php?region_id=', '')

            mcity = megamag_cities_dict.get(city_id)

            if not mcity:
                city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
                if city.count() == 1:
                    mcity = SourceCities.objects.create(
                        source_id=city_id,
                        source_obj=source,
                        city=city[0],
                        name=city_name,
                    )
                else:
                    if 'slug="%s"' % city_slug not in data_nof_city:
                        data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)

            if mcity:
                cities_data[city_name] = mcity

        try:
            cinemas_tag = data.findAll('td', {'class': 'Cinema_new_box_1_BoxText'}, limit=1)[0]
        except IndexError:
            cinemas_tag = None

        if cinemas_tag:
            for i in cinemas_tag.findAll('a'):
                cinema_url = i.get('href')
                cinema_id = cinema_url.replace('http://kinoteatr.megamag.by/index.php?cPath=','')
                cinema_obj = megamag_cinemas_dict.get(cinema_id)

                opener = give_me_cookie()
                try:
                    req2 = opener.open(urllib2.Request(cinema_url))

                    if req2.getcode() == 200:
                        schedules_page = BeautifulSoup(req2.read(), from_encoding="utf-8")
                        city_name = schedules_page.findAll('div', {'class': 'object_param_value'}, limit=1)[0].text.encode('utf-8')

                        city_obj = cities_data.get(city_name)
                        if city_obj:
                            cinema_name = schedules_page.find('div', {'class': 'object_title'}).text.encode('utf-8')
                            cinema_name = cinema_name.replace('"', '').replace('Кинотеатр', '')
                            cinema_slug = low(del_separator(cinema_name))

                            cinema_ig_id = u'%s__%s' % (cinema_slug.decode('utf-8'), city_obj.city.kid)

                            if cinema_ig_id not in ignored_cinemas:

                                if not cinema_obj:
                                    filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city': city_obj.city}
                                    cinema_kid = cinema_identification(cinema_slug, filter1)
                                    if cinema_kid:
                                        try:
                                            cinema = Cinema.objects.get(code=cinema_kid)
                                            cinema_obj = SourceCinemas.objects.create(
                                                source_id=cinema_id,
                                                source_obj=source,
                                                city=city_obj,
                                                cinema=cinema,
                                                name=cinema_name,
                                            )
                                        except Cinema.DoesNotExist: pass
                                else:
                                    cinema_kid = cinema_obj.cinema.code

                                if cinema_kid:
                                    for event in schedules_page.findAll('td', {'class': 'eventsHeading'}):
                                        if event.a.get('name'):
                                            ev = event.a['name'].split('_')[1]
                                            fname = event.a.text.encode('utf-8')
                                            fid = event.a.get('href').replace('http://kinoteatr.megamag.by/newsdesk_info.php?newsdesk_id=','')
                                            event_dict[int(ev)] = {'name': fname, 'id': int(fid)}

                                    links = []
                                    for td in schedules_page.findAll('td', {'class': 'main'}):
                                        for link in td.findAll('a'):
                                            l = link.get('href')
                                            if l and 'cPath' in l:
                                                links.append(l)
                                    schedules_data.append({'mcity': city_obj, 'city': city_obj.city, 'mcinema': cinema_obj, 'cinema': cinema_kid, 'schedules': set(links)})
                                else:
                                    if 'slug="%s"' % cinema_slug not in data_nof_cinema:
                                        data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_name, city_obj.city.kid)
                except httplib.HTTPException: pass
        create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
        create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)  

        megamag = get_source_data(source, 'schedule', 'list')

        for obj in schedules_data:
            cinema_object = obj['mcinema']

            for index, i in enumerate(obj['schedules']):
                opener = give_me_cookie()
                try:
                    req3 = opener.open(urllib2.Request(i))
                    if req3.getcode() == 200:

                        id_schedule = i.replace('http://kinoteatr.megamag.by/index.php?cPath=', '').encode('utf-8')
                        if id_schedule not in megamag:
                            sch_page = BeautifulSoup(req3.read(), from_encoding="utf-8")

                            tables = sch_page.findAll('table', {'class': 'Cinema_new_box_2_TemplateCenterPart'}, limit=1)[0]
                            main_table = tables.findAll('table', cellpadding='4', limit=1)[0]
                            tr = main_table.findAll('tr')[1]
                            td = tr.findAll('strong')

                            event_id = id_schedule.split('_')[2]
                            film_data = event_dict.get(int(event_id))
                            if film_data:
                                film_name = film_data['name']
                                film_name_slug = low(del_separator(del_screen_type(film_name)))
                                film_id = film_data['id']

                                if film_id not in noffilms and film_name_slug.decode('utf-8') not in ignored:

                                    obj = films.get(str(film_id).decode('utf-8'))
                                    next_step = checking_obj(obj)

                                    if next_step:
                                        if obj:
                                            kid = obj.kid
                                        else:
                                            kid, info = film_identification(film_name_slug, None, {}, {}, source=source)

                                        objt = None
                                        if kid:
                                            create_new, objt = unique_func(fdict, kid, obj)
                                            if create_new:
                                                objt = create_sfilm(film_id, kid, source, film_name)
                                                films[str(film_id).decode('utf-8')] = objt
                                                if not fdict.get(kid):
                                                    fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                                fdict[kid]['script_rel'].append(objt)
                                        elif not obj:
                                            data_nof_films += xml_noffilm(film_name, film_name_slug, None, None, film_id, info, None, source.id)
                                            noffilms.append(film_id)

                                        if objt:
                                            dtime_info = td[1].text.encode('utf-8').split()
                                            year_info = datetime.datetime.now().year
                                            day_info = int(dtime_info[0])
                                            month_low = low(dtime_info[1].replace(',', ''))
                                            month_info = int(get_month(month_low))
                                            time_info = dtime_info[-1].replace('(', '').replace(')', '').split(':')

                                            dtime = datetime.datetime(year_info, month_info, day_info, int(time_info[0]), int(time_info[1]), 0)
                                            SourceSchedules.objects.create(
                                                source_id=id_schedule,
                                                source_obj=source,
                                                cinema=cinema_object,
                                                film=objt,
                                                dtime=dtime,
                                            )
                except httplib.HTTPException:
                    open('%s/httplib_errors.txt' % settings.API_DUMP_PATH, 'a').write('%s\n' % i)
                # на каждом 60 обращении к источнику делаю паузу в 2 секунды
                if (index + 1) % 60 == 0:
                    time.sleep(2.0)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def megamag_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://megamag.by/')
    autors = (source.code, 0, 2)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
