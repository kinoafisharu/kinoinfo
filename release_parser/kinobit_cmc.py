#-*- coding: utf-8 -*- 
import urllib
import urllib2
import datetime

from django.http import HttpResponse
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from decors import timer
from release_parser.func import cron_success


def get_kinobit_dump():
    '''
    Получение xml данных сеансов от СМС
    '''
    import cookielib
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    
    cookie = cookielib.CookieJar()
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie)))
    # захожу на страницу авторизации, что б получить куки и токен
    url = 'http://kinobit.pro/Account/LogOn?ReturnUrl=%2f'
    req = urllib2.urlopen(url)
    page = BeautifulSoup(req.read(), from_encoding="utf-8")
    # нахожу в html форме токен
    div_main = page.find('div', {'class': 'main'})
    input_tag = div_main.find_all('input', limit=1)
    # данные для отправки формы
    input_tag = input_tag[0]['value']
    login = 'mivanov'
    passwd = 'cftxrf888'
    values = urllib.urlencode({
        '__RequestVerificationToken': input_tag,
        'UserName' : login,
        'Password' : passwd,
    })
    # отправка формы авторизации
    url = 'http://kinobit.pro/Account/LogOn'
    
    try:
        req = urllib2.urlopen(url, values)
    except urllib2.HTTPError, error:
        return HttpResponse(str(error.read()))
        
    # авторизовался, теперь можно получить xml данные сеансов
    url = 'http://kinobit.pro/Schedule/Xml'
    
    try:
        req = urllib2.urlopen(url)
    except urllib2.HTTPError, error:
        return HttpResponse(str(error.read()))
    
    # сохранияю в сеансы в xml дамп
    xml = str(req.read())
    create_dump_file('cmc_schedules', settings.API_DUMP_PATH, xml)
    cron_success('html', source.dump, 'schedules_dump', 'Дамп с сеансами')



def get_source_data(source, obj, type):
    '''
    Принимает: 
        source  - источник, объект ImportSources
        obj     - категория возвращаемых даннах (city, cinema, film, schedule)
        type    - тип возвращаемых данных (list, dict)
    Возвращает:
        list или dict или None
        list - список всех идов источника, 
        dict - словарь, ид_источника:объект
        None - в случае, если переданы неверные данные
    '''

    filter = {'source_obj': source}
    dict = {
        'city': {'name': SourceCities, 'related': ['city']},
        'cinema': {'name': SourceCinemas, 'related': ['cinema', 'cinema__city']},
        'film': {'name': SourceFilms, 'related': []},
        'schedule': {'name': SourceSchedules, 'related': ['cinema', 'cinema__cinema', 'cinema__cinema__city', 'film']},
        'hall': {'name': SourceHalls, 'related': []}
    }
    model = dict.get(obj)
    
    if obj == 'schedule':
        past = datetime.datetime.today() - datetime.timedelta(days=7)
        filter['dtime__gt'] = past

    if model:
        if type == 'list':
            if obj == 'film':
                return list(model['name'].objects.filter(**filter).exclude(Q(kid=None) | Q(kid=0) | Q(rel_ignore=True)).values_list('source_id', flat=True))
            else:
                return list(model['name'].objects.filter(**filter).values_list('source_id', flat=True))
        elif type == 'dict':
            if obj == 'film':
                source_objs = model['name'].objects.select_related(*model['related']).filter(**filter).exclude(Q(kid=None) | Q(kid=0))
            else:
                source_objs = model['name'].objects.select_related(*model['related']).filter(**filter)
            source_objs_dict = {}
            for i in source_objs:
                source_objs_dict[i.source_id] = i
            return source_objs_dict


def checking_obj(obj):
    if obj:
        if obj.rel_ignore or obj.rel_double:
            next_step = False
        else:
            next_step = True
    else:
        next_step = True
    return next_step


def create_sfilm(sid, kid, source, name, name_alt=None, year=None, imdb=None, txt=None, extra=None):
    '''
    Создание фильма у источника
    '''
    obj = SourceFilms.objects.create(
        source_id = sid,
        source_obj = source,
        name = name,
        name_alter = name_alt,
        kid = kid,
        year = year,
        imdb = imdb,
        text = txt,
        extra = extra,
        rel_dtime = datetime.datetime.now(),
    )
    return obj


def get_all_source_films(source, sfilms=[]):
    fdict = {}
    #if not sfilms:
    sfilms = SourceFilms.objects.filter(source_obj=source).exclude(kid=None)
    for i in sfilms:
        if not fdict.get(i.kid):
            fdict[i.kid] = {'editor_rel': [], 'script_rel': []}
        if i.rel_dtime:
            fdict[i.kid]['editor_rel'].append(i)
        else:
            fdict[i.kid]['script_rel'].append(i)
    return fdict


def sfilm_clean(source):
    dict = {}
    for_delete = []
    
    for i in SourceFilms.objects.filter(source_obj=source):
        if dict.get(i.source_id):
            for_delete.append(i.id)
        else:
            dict[i.source_id] = i
            
    SourceFilms.objects.filter(pk__in=for_delete).delete()
    SourceSchedules.objects.filter(film__pk__in=for_delete).delete()



def unique_func(fdict, kid, obj, kinometro=False):
    if kid:
        exist = fdict.get(kid)
        if exist:
            if not obj:
                if exist['script_rel']:
                    # разорвать связь и в ненайденные, те что в 'script_rel' + новый
                    for i in exist['script_rel']:
                        if not kinometro:
                            i.kid = None
                        i.rel_double = True
                        i.save()
                return True, None # создать новый объект
            else:
                if exist['script_rel']:
                    if obj in exist['script_rel']:
                        if len(exist['script_rel']) == 1:
                            return False, obj # новый объект не создавать, использовть текущий
                        else:
                            for i in exist['script_rel']:
                                if not kinometro:
                                    i.kid = None
                                i.rel_double = True
                                i.save()
                            return False, None # пропустить действие
                    else:
                        if len(exist['script_rel']) > 1:
                            # разорвать связь и в ненайденные, те что в 'script_rel'
                            for i in exist['script_rel']:
                                if not kinometro:
                                    i.kid = None
                                i.rel_double = True
                                i.save()
                        return False, None # пропустить действие
                if exist['editor_rel']:
                    return False, obj # новый объект не создавать, использовть текущий
        else:
            return True, None # создать новый объект
    else:
        return False, None # пропустить действие



@timer
def get_kinobit_cities():
    '''
    Идентификация городов от СМС
    '''
    # xml файлы для чтения/хранения данных
    xml = open('%s/dump_cmc_schedules.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    
    kinobit_cities = get_source_data(source, 'city', 'list')
    data_nof_city = ''
    
    # разбор xml тегов
    for cinema in xml_data.findAll('cinema'):
        city_name = cinema['city'].encode('utf-8')
        city_slug = low(del_separator(del_screen_type(city_name)))
        city_eq = city_slug.decode('utf-8')
        if city_eq not in kinobit_cities:
            city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
            if city.count() == 1:
                SourceCities.objects.create(
                    source_id = city_slug,
                    source_obj = source,
                    city = city[0],
                    name = city_name,
                )
            else:
                data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)
            kinobit_cities.append(city_eq)
            
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    cron_success('xml', source.dump, 'cities', 'Города')


@timer
def get_kinobit_cinemas():
    '''
    Идентификация кинотеатров от СМС
    '''
    # xml файлы для чтения/хранения данных
    xml = open('%s/dump_cmc_schedules.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    
    kinobit_cities_dict = get_source_data(source, 'city', 'dict')
    kinobit_cinemas = get_source_data(source, 'cinema', 'list')
    
    data_nof_cinema = ''
    
    # разбор xml тегов
    for cinema in xml_data.findAll('cinema'):
        city_name = cinema['city'].encode('utf-8')
        city_slug = low(del_separator(del_screen_type(city_name)))
        
        city_obj = kinobit_cities_dict.get(city_slug.decode('utf-8'))
        
        if city_obj:
            cinema_name = cinema['name'].replace('"', "'").encode('utf-8').strip()
            cinema_name = cinema_name.replace('Репертуар', '').strip()
            cinema_slug = low(del_separator(cinema_name))
            cinema_id = cinema['id'].encode('utf-8')
            city_kid = city_obj.city.kid
            
            if cinema_id not in kinobit_cinemas:
                filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city__kid': city_kid}
                cinema_kid = cinema_identification(cinema_slug, filter1)
                if cinema_kid:
                    cinema_obj = Cinema.objects.get(code=cinema_kid)
                    SourceCinemas.objects.create(
                        source_id = cinema_id,
                        source_obj = source,
                        city = city_obj,
                        cinema = cinema_obj,
                        name = cinema_name,
                    )
                else:
                    data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_name, city_kid)
                kinobit_cinemas.append(cinema_id)
    
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('xml', source.dump, 'cinemas', 'Кинотеатры')
    
    
@timer
def get_kinobit_films():
    '''
    Идентификация фильмов от СМС
    '''
    # xml файлы для чтения/хранения данных
    with open('%s/dump_cmc_schedules.xml' % settings.API_DUMP_PATH, 'r') as f:
        xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    ignored = get_ignored_films()
    
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    data_nof_film = ''
    noffilms = []
    
    # разбор xml тегов
    for film in xml_data.findAll('film'):
        film_name = film['title'].encode('utf-8').replace('"', "'")
        film_slug = low(del_separator(del_screen_type(film_name)))
        film_id = film['id'].encode('utf-8')
        kid = None
        if int(film_id) == 0:
            film_id = '%s%s' % (film_id, film_slug)
            film_id = film_id.decode('utf-8')
            
        if film_slug.decode('utf-8') not in ignored and film_id not in noffilms:
        
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
                    data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id.encode('utf-8'), info, None, source.id)
                    noffilms.append(film_id)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'films', 'Фильмы')


@timer
def get_kinobit_schedules():
    '''
    Идентификация сеансов от СМС
    '''
    # xml файлы для чтения/хранения данных
    xml = open('%s/dump_cmc_schedules.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    
    data_nof_hall = ''
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    
    kinobit_schedules = get_source_data(source, 'schedule', 'list')
    kinobit_cities_dict = get_source_data(source, 'city', 'dict')
    kinobit_cinemas_dict = get_source_data(source, 'cinema', 'dict')
    kinobit_films_dict = get_source_data(source, 'film', 'dict')

    next_month = datetime.date.today() + datetime.timedelta(days=30)
    
    # разбор xml тегов
    for release in xml_data.findAll('data'):
        rdate = release['value'].encode('utf-8').split('-')
        rdate = datetime.date(int(rdate[0]), int(rdate[1]), int(rdate[2]))
        if rdate <= next_month:
            for cinema in release.findAll('cinema'):
                city_id = low(del_separator(cinema['city'].encode('utf-8')))
                city_obj = kinobit_cities_dict.get(city_id.decode('utf-8'))
                cinema_id = cinema['id'].encode('utf-8')
                cinema_obj = kinobit_cinemas_dict.get(cinema_id)
                if cinema_obj:
                    for hall in cinema.findAll('hall'):
                        hall_name = hall['title'].replace('"', "'").encode('utf-8')
                        hall_slug = low(del_separator(hall_name))
                        
                        for film in hall.findAll('film'):
                            film_id = film['id'].encode('utf-8')
                            flag = False
                            if int(film_id) == 0:
                                film_name = film['title'].encode('utf-8')
                                film_name = low(del_separator(del_screen_type(film_name)))
                                film_id = '0%s' % film_name
                                film_obj = kinobit_films_dict.get(film_id.decode('utf-8'))
                            else:
                                film_obj = kinobit_films_dict.get(film_id)
                            if film_obj:
                                for stime in film.findAll('seans'):
                                    t = stime['time'].split(':')
                                    release_date = datetime.datetime(rdate.year, rdate.month, rdate.day, int(t[0]), int(t[1]), 0)
                                    kinobit_id = '%s%s%s%s%s' % (release_date, hall_slug, cinema_id, city_id, film_id)
                                    kinobit_id = kinobit_id.replace(' ','').decode('utf-8')
                                    if kinobit_id not in kinobit_schedules:
                                        
                                        hall_obj = Hall.objects.filter(name__name=hall_slug, cinema=cinema_obj.cinema).distinct('pk')
                                        if hall_obj.count() == 1:
                                            hall_obj = hall_obj[0].kid

                                            SourceSchedules.objects.create(
                                                source_id = kinobit_id,
                                                source_obj = source,
                                                film = film_obj,
                                                cinema = cinema_obj,
                                                dtime = release_date,
                                                hall = hall_obj,
                                            )
                                        else:
                                            city_kid = city_obj.city.kid
                                            cinema_kid = cinema_obj.cinema.code
                                            id = '%s%s%s%s' % (city_kid, cinema_kid, hall_name, hall_slug)
                                            id = id.replace(' ','')
                                            # если такого тега нет в ненайденных, то добавляю
                                            if 'id="%s"' % id not in data_nof_hall:
                                                data_nof_hall += '<hall city="%s" city_kid="%s" cinema="%s" cinema_kid="%s" name="%s" slug="%s" id="%s"></hall>' % (city_obj.name.encode('utf-8'), city_kid, cinema_obj.name.encode('utf-8'), cinema_kid, hall_name, hall_slug, id)
                                        kinobit_schedules.append(kinobit_id)
    
    create_dump_file('%s_nof_hall' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_hall)
    cron_success('xml', source.dump, 'schedules', 'Сеансы')


def afisha_dict(afisha_obj):
    '''
    формирование массива из queryset киноафиши
    '''
    dic = []
    for i in afisha_obj:
        date_from = i.schedule_id.date_from
        date_to = i.schedule_id.date_to
        delta = date_to - date_from
        for t in range(delta.days + 1):
            d = date_from + datetime.timedelta(days=t)
            ti = i.session_list_id.time
            d = datetime.datetime(d.year, d.month, d.day, ti.hour, ti.minute, ti.second)
            dic.append({'film': int(i.schedule_id.film_id_id), 'movie': int(i.schedule_id.movie_id_id), 'hall': int(i.schedule_id.hall_id_id), 'date': d, 'obj': i})
    return dic
    
    
@timer
def kinobit_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://kinobit.pro/')
    autors = (source.code, 105, 90, 11, 2, 0)
    log = schedules_export(source, autors, True)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
