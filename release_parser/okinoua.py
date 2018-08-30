#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import cookielib
import datetime
import time
import random

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django import db

from bs4 import BeautifulSoup
from base.models import *
from api.models import *
from base.models_choices import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data
from release_parser.forms import OkinoUploadForm
from decors import timer
from release_parser.func import cron_success


@never_cache
def get_okinoua_distributors(request):
    form = OkinoUploadForm()
    if request.POST:
        form = OkinoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            source = ImportSources.objects.get(url='http://www.okino.ua/')
            
            with open('%s/dump_%s_nof_film.xml' % (settings.NOF_DUMP_PATH, source.dump), 'r') as f:
                xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
            
            ignored = get_ignored_films()
            
            films_slugs = [i.get('slug_ru') for i in xml_data.findAll('film')]
            today = datetime.date.today()
            films_dict = get_source_data(source, 'film', 'dict')
            
            releases = SourceReleases.objects.select_related('film').filter(film__source_obj=source, release__gte=today)
            releases_dict = {}
            for i in releases:
                releases_dict[i.film.source_id] = i
            
            data_nof_films = ''

            data = request.FILES['file'].read()
            html_data = BeautifulSoup(data, from_encoding="utf-8")
            
            main = html_data.find('div', {'class': 'release_list'})
            
            year = datetime.date.today().year
            
            first_h3 = main.findAll('h3', limit=1)[0]
            for div in first_h3.find_next_siblings():
                film_tag = div.find('p', {'class': 'name'})
                flag = False
                if film_tag:
                    flag = True
                    film_tag = film_tag.a
                    film_name = film_tag.string.encode('utf-8')
                    full_url = film_tag.get('href').encode('utf-8')
                    film_id = re.findall(r'\d+\/$', full_url)[0].replace('/','').encode('utf-8')
                    film_slug = low(del_separator(film_name))
                    film_year = div.find('span', {'class': 'y'}).string.encode('utf-8').replace('(','').replace(')','')
                    full_url = 'http://www.okino.ua%s' % full_url

                    release_day = int(div.find('span', {'class': 'day'}).string)
                    release_month = div.find('span', {'class': 'month'}).string.encode('utf-8')
                    release_month = get_month(release_month)
                    
                    release_date = datetime.date(year, int(release_month), release_day)
                    
                    film_obj = films_dict.get(film_id)
                    if not film_obj:
                        kid, info = film_identification(film_slug, None, {}, {}, year=film_year, source=source)
                        if kid:
                            film_obj = SourceFilms.objects.create(
                                source_id = film_id,
                                source_obj = source,
                                name = film_name,
                                kid = kid,
                                year = film_year,
                            )
                        else:
                            temp_film_slug = film_slug.decode('utf-8')
                            if temp_film_slug not in films_slugs and temp_film_slug not in ignored:
                                films_slugs.append(film_slug.decode('utf-8'))
                                data_nof_films += xml_noffilm(film_name, film_slug, None, None, film_id, info, full_url.encode('utf-8'), source.id)
                        if film_obj:
                            for p in div.findAll('p'):
                                if p.string:
                                    text = p.string.encode('utf-8')
                                    if 'Дистрибьютор:' in text:
                                        distr = text.replace('Дистрибьютор: ','').decode('utf-8')
                                    
                                        release_obj = releases_dict.get(film_id)
                                        if release_obj:
                                            if release_obj.release != release_date or release_obj.distributor != distr:
                                                release_obj.release = release_date
                                                release_obj.distributor = distr
                                                release_obj.save()
                                        else:
                                            release_obj = SourceReleases.objects.create(
                                                source_obj = source,
                                                film = film_obj,
                                                release = release_date,
                                                distributor = distr,
                                            )
                                            releases_dict[film_id] = release_obj
                if div.string:
                    year = int(re.findall(r'\d+$', div.string.encode('utf-8'))[0])

            xml_data = str(xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
            xml_data = '<data>%s%s</data>' % (xml_data, data_nof_films)
            
            create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, xml_data)
            return HttpResponseRedirect(reverse('admin_source_releases_show'))
            
    return render_to_response('release_parser/okinoua_upload.html', {'form': form}, context_instance=RequestContext(request))


@timer
def get_okinoua_links():
    '''
    Получение urls укр. релизов
    '''
    links = []
    
    def get_link_from_tag(i):
        tag = i.find('p', {'class': 'name'})
        film_id = tag.a.get('href').replace('/film/','').replace('/','')
        link = 'http://www.okino.ua%s' % tag.a.get('href')
        return link, film_id
        
    url = 'http://www.okino.ua/comingsoon/'
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        html_data = BeautifulSoup(req.read(), from_encoding="utf-8")
        divs = [
            {'class': 'film'},
            {'class': 'film last'},
            {'class': 'film film-s'},
            {'class': 'film last film-s'},
        ]
        
        for div in divs:
            for i in html_data.findAll('div', div):
                distr = None
                link, film_id = get_link_from_tag(i)
                for j in i.findAll('p'):
                    if u'Дистрибьютор:' in j.text:
                        distr = j.text.split(':')
                        distr = distr[1].strip()
                        links.append({'link': link, 'distr': distr, 'id': film_id})

    f = open('%s/dump_okino.ua.links.xml' % settings.API_DUMP_PATH, 'w')
    xml = ''
    for i in links:
        xml += '<release>'
        xml += '<link value="%s"></link>' % i['link']
        xml += '<distr value="%s"></distr>' % i['distr'].replace('&', '&amp;')
        xml += '<id value="%s"></id>' % i['id']
        xml += '</release>'
    f.write('<data>%s</data>' % xml.encode('utf-8'))
    f.close()

    cron_success('html', 'okino.ua', 'links', 'Ссылки укр. релизов')


@timer
def get_okinoua_releases():
    '''
    Парсер укр. релизов
    '''
    f = open('%s/dump_okino.ua.links.xml' % settings.API_DUMP_PATH, 'r')
    links = BeautifulSoup(f.read(), from_encoding="utf-8")
    f.close()
    
    xml = open('%s/dump_okinoua_nof_film.xml' % settings.NOF_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()

    films_slugs = []
    for i in xml_data.findAll('film'):
        slug = i.get('slug_ru')
        films_slugs.append(slug)

    data_nof_film = ''
    for index, i in enumerate(links.findAll('release')):
        url = i.link['value']
        distr = i.distr['value']
        film_id = i.id['value']
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            html_data = BeautifulSoup(req.read(), from_encoding="utf-8")
            title = html_data.find('div', {'class': 'item'})
            name_ru = title.h1.text.encode('utf-8')
            name_ua = None
            if title.h4:
                name_ua = title.h4.text.encode('utf-8')
                if name_ua == '(Не)очікуваний принц (Un prince (presque) charmant)':
                    name_ua = '(Не)очікуваний принц'
                else:
                    name_ua = re.sub(r'\(.*?\)', '', name_ua).strip()
                name_ua = name_ua if re.findall(ur'[а-яА-Я]', name_ua.decode('utf-8')) else None

            name_slug = del_screen_type(name_ru)
            name_slug = low(del_separator(name_slug))

            details = html_data.find('div', {'class': 'params'})
            release_date = None
            year_m = None
            for i in details.ul.findAll('li'):
                if i.span.text == u'Год:':
                    year_main = i.text.split(':')
                    year_m = year_main[1].strip()
                elif i.span.text == u'Премьера в Украине:':
                    release_txt = i.text.split(':')
                    day, month, year = release_txt[1].strip().split(' ')
                    month = int(get_month(month.encode('utf-8')))
                    release_date = datetime.date(int(year), month, int(day))
            
            kid, info = film_identification(name_slug, None, {}, {}, year=year_m, source=source)
            
            if kid:
                if release_date:
                    obj, created = Okinoua.objects.get_or_create(
                        url=url,
                        defaults={
                            'url': url, 
                            'distributor': distr,
                            'release': release_date,
                            'kid': kid,
                            'name_ru': name_ru,
                            'name_ua': name_ua,
                        })
                    if not created:
                        if obj.distributor != distr:
                            obj.distributor = distr
                        if obj.release != release_date:
                            obj.release = release_date
                        name_ua = name_ua.decode('utf-8') if name_ua else None
                        if obj.name_ua != name_ua:
                            obj.name_ua = name_ua
                        obj.save()
            else:
                slug_tag = 'slug_ru="%s"' % name_slug
                if slug_tag not in data_nof_film and name_slug.decode('utf-8') not in films_slugs:
                    data_nof_film += xml_noffilm(name_ru, name_slug, name_ua, None, film_id.encode('utf-8'), info, url.encode('utf-8'), source.id)
                    
        # на каждом 4 обращении к источнику делаю паузу в 1-3 секунды
        if index % 3 == 0:
            time.sleep(random.uniform(1.0, 3.0))
            
    xml_data = str(xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
    xml_data = '<data>%s%s</data>' % (xml_data, data_nof_film)
    
    create_dump_file('okinoua_nof_film', settings.NOF_DUMP_PATH, xml_data)
    cron_success('html', 'okinoua', 'releases', 'Укр. релизы')

@timer
def get_okinoua_cities():
    """
    Парсинг городов Украины
    """
    source = ImportSources.objects.get(url='http://www.okino.ua/')
    
    # Получаем список городов с таблицы SourceCities в виде списка
    cities_ids = get_source_data(source, 'city', 'list')
    data_nof_city = ''

    # Открываем страницу с городами
    url = '%skinoafisha-kiev/' % source.url
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        page = BeautifulSoup(req.read(), from_encoding="utf-8") 
        # Находим все теги с городами и считываем из них id и названия городов
        for ul in page.findAll('ul', {'class': 'blist'}):
            for li in ul.findAll('li'):
                id = li.a.get('href').replace('/','')
                name = li.a.string.encode('utf-8').strip()
                name_slug = low(del_separator(name))
                # Сравниваем полученные города с городами в нашей БД и, если НЕТ совпадений, то
                if id not in cities_ids:
                    # идентифицируем новый город
                    city = City.objects.filter(name__name=name_slug, name__status=2).distinct('pk')
                    # если идентифицировали, то записываем в таблицу SourceCities
                    if city.count() == 1:
                        SourceCities.objects.create(
                            source_id = id,
                            source_obj = source,
                            city = city[0],
                            name = name,
                        )
                    # в противном случаем записываем ненайденые города в xml для дальнейших действий над ними
                    else:
                        if 'slug="%s"' % name_slug not in data_nof_city:
                            data_nof_city += '<city name="%s" slug="%s"></city>' % (name, name_slug)
    
    create_dump_file('okinoua_nof_city', settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    cron_success('html', 'okinoua', 'cities', 'Укр. города')


@timer
def get_okinoua_cinemas():
    """
    Парсинг кинотеатров Украины
    """
    source = ImportSources.objects.get(url='http://www.okino.ua/')

    # Получаем список идентифицированных кинотеатров OkinoUA
    cinemas_ids = get_source_data(source, 'cinema', 'list')
    data_nof_cinema = ''

    # Получаем словарь со списком идентифицированных городов OkinoUA
    okinoua_cities_dict = get_source_data(source, 'city', 'dict')

    cinemas = Cinema.objects.all()
    cinemas_dict = {}
    for i in cinemas:
        cinemas_dict[i.code] = i

    counter = 0
    # Открываем ссылку, если она доступна и считываем ее BeautifulSoup'ом
    for city_id, city_obj  in okinoua_cities_dict.iteritems():
        counter += 1
        url = '%s%s/' % (source.url, city_id)
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            page = BeautifulSoup(req.read(), from_encoding="utf-8") 
            # Находим все теги с городами и считываем из них id и названия городов
            for div in page.findAll('div', {'class': 'item0'}):
                cinema_tag = div.find('h3')
                cinema_id = cinema_tag.a.get('href').replace('/','')
                cinema_name = cinema_tag.a.string.encode('utf-8')
                cinema_slug = low(del_separator(cinema_name))
                if cinema_id not in cinemas_ids:
                    filter = {'name__name': cinema_slug, 'name__status': 2, 'city__id': city_obj.city_id}
                    cinema_kid = cinema_identification(cinema_slug, filter)
                    if cinema_kid:
                        try:
                            cinema = Cinema.objects.get(code=cinema_kid)
                            cinema_obj = SourceCinemas.objects.create(
                                source_id = cinema_id,
                                source_obj = source,
                                city = city_obj,
                                cinema = cinema,
                                name = cinema_name,
                            )
                        except Cinema.DoesNotExist: pass
                    else:
                        if 'slug="%s"' % cinema_slug not in data_nof_cinema:
                            data_nof_cinema += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, city_obj.name.encode('utf-8'), city_obj.city.kid)
        if counter % 4 == 0:
            time.sleep(random.uniform(1.0, 3.0))

        
    create_dump_file('okinoua_nof_cinema', settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinema)
    cron_success('html', 'okinoua', 'cinemas', 'Укр. кинотеатры')

@timer
def get_okinoua_films():
    """
    Парсинг фильмов Украины
    """
    xml = open('%s/dump_okinoua_nof_film.xml' % settings.NOF_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()

    films_slugs = []
    for i in xml_data.findAll('film'):
        slug = i.get('slug_ru')
        films_slugs.append(slug)
    
    source = ImportSources.objects.get(url='http://www.okino.ua/')
    data_nof_films = ''
    not_founded_films = []
    
    # Получаем словарь идентифицированных фильмов OkinoUA
    okinoua_films = get_source_data(source, 'film', 'list')
    # Получаем словарь со списком идентифицированных городов OkinoUA
    okinoua_cities_dict = get_source_data(source, 'city', 'dict')
    # Получаем словарь со списком идентифицированных кинотеатров OkinoUA
    okinoua_cinemas_dict = get_source_data(source, 'cinema', 'dict')

    counter = 0
    for city_id, city_obj  in okinoua_cities_dict.iteritems():
        counter += 1
        url = '%s%s/' % (source.url, city_id)
        req = urllib.urlopen(url)
        dates = []
        if req.getcode() == 200:
            page = BeautifulSoup(req.read(), from_encoding="utf-8")
            
            for div in page.findAll('div', {'class': 'item0'}):
                for film in div.findAll('div', {'class': 'item2'}):
                    alt_name = None
                    if film.div.div.a:
                        film_name = film.div.div.a.string.encode('utf-8')
                        film_a = film.div.div.a.get('href')
                        film_id = film_a.replace('/film/', '').replace('/', '').encode('utf-8')
                        full_url = '%sfilm/%s' % (source.url, film_id)
                        req_name = urllib.urlopen(full_url)
                        if req_name.getcode() == 200:
                            filmpage = BeautifulSoup(req_name.read(), from_encoding="utf-8")
                            title = filmpage.find('div', {'class': 'item'})
                            if title.h4:
                                alt_name = title.h4.text.encode('utf-8')
                                alt_name = re.sub(r'\(.*?\)', '', alt_name).strip()
                    else:
                        film_name = film.div.div.string.strip().encode('utf-8')
                        film_id = None

                    film_name_slug = low(del_separator(del_screen_type(film_name)))
                    if not film_id:
                        film_id = film_name_slug.decode('utf-8')

                    if film_id not in okinoua_films:
                        kid, info = film_identification(film_name_slug, None, {}, {}, source=source)
                        if kid:
                            film_obj, created = SourceFilms.objects.get_or_create(
                                source_id = film_id,
                                source_obj = source,
                                defaults = {
                                    'source_id': film_id,
                                    'source_obj': source,
                                    'name': film_name,
                                    'kid': kid,
                                    'name_alter': alt_name,
                                })
                        else:
                            slug_tag = 'slug_ru="%s"' % film_name_slug
                            if slug_tag not in data_nof_films and film_name_slug.decode('utf-8') not in films_slugs:
                                data_nof_films += xml_noffilm(film_name, film_name_slug, None, None, film_id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                        okinoua_films.append(film_id)
        if counter % 4 == 0:
            time.sleep(random.uniform(1.0, 3.0))
            
    xml_data = str(xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
    xml_data = '<data>%s%s</data>' % (xml_data, data_nof_films)
    
    create_dump_file('okinoua_nof_film', settings.NOF_DUMP_PATH, xml_data)
    cron_success('html', 'okinoua', 'films', 'Фильмы')



@timer
def get_okinoua_schedules():
    """
    Парсинг сеансов Украины
    """
    source = ImportSources.objects.get(url='http://www.okino.ua/')
    
    # Получаем словарь идентифицированных фильмов OkinoUA
    okinoua_films_dict = get_source_data(source, 'film', 'dict')
    # Получаем словарь со списком идентифицированных городов OkinoUA
    okinoua_cities_dict = get_source_data(source, 'city', 'dict')
    # Получаем словарь со списком идентифицированных кинотеатров OkinoUA
    okinoua_cinemas_dict = get_source_data(source, 'cinema', 'dict')
    # Получаем список идентифицированных сенсов OkinoUA
    okinoua_schedules = get_source_data(source, 'schedule', 'list')

    counter1 = 0
    for city_id, city_obj in okinoua_cities_dict.iteritems():
        counter1 += 1
        url = '%s%s/' % (source.url, city_id)
        req = urllib.urlopen(url)
        dates = []
        if req.getcode() == 200:
            page = BeautifulSoup(req.read(), from_encoding="utf-8")
            # если в городе есть сеансы
            item = page.find('div', {'class': 'item0'})
            if item:
                # получаю даты на которые есть расписание
                date_div = page.find('div', id='afisha-date')
                dates = [i.get('href').strip() for i in date_div.findAll('a')]
        
        counter = 0
        for date in dates:
            counter += 1
            url2 = '%s%s' % (url, date)
            req2 = urllib.urlopen(url2)
            if req2.getcode() == 200:
                page2 = BeautifulSoup(req2.read(), from_encoding="utf-8")
                for div in page2.findAll('div', {'class': 'item0'}):
                    cinema_tag = div.find('h3')
                    cinema_id = cinema_tag.a.get('href').replace('/','').encode('utf-8')
                    cinema_obj = okinoua_cinemas_dict.get(cinema_id)
                    if cinema_obj:
                        for film in div.findAll('div', {'class': 'item2'}):
                            if film.div.div.a:
                                film_name = film.div.div.a.string.encode('utf-8')
                                film_id = film.div.div.a.get('href').replace('/film/', '').replace('/', '').encode('utf-8')
                            else:
                                film_name = film.div.div.string.strip().encode('utf-8')
                                film_id = None

                            film_name_slug = low(del_separator(del_screen_type(film_name)))
                            if not film_id:
                                film_id = film_name_slug
                            
                            film_obj = okinoua_films_dict.get(film_id)
                            
                            if film_obj:
                                showtime = film.find('div', {'class': 'showtime'})
                                for time_tag in showtime.findAll('span'):
                                    hours, minutes = time_tag.string.encode('utf-8').split(':')
                                    year, month, day = date.replace('?date=', '').split('-')
                                    dtime = datetime.datetime(int(year), int(month), int(day), int(hours), int(minutes), 0)
                                    id = '%s%s%s%s' % (dtime, cinema_id, city_id.encode('utf-8'), film_id)
                                    id = id.replace(' ', '')
                                    if id.decode('utf-8') not in okinoua_schedules:
                                        SourceSchedules.objects.create(
                                            source_id = id,
                                            source_obj = source,
                                            cinema = cinema_obj,
                                            film = film_obj,
                                            dtime = dtime,
                                        )
                                        okinoua_schedules.append(id)
            if counter % 4 == 0:
                time.sleep(random.uniform(1.0, 3.0))
        if counter1 % 4 == 0:
            time.sleep(random.uniform(1.0, 3.0))
    cron_success('html', 'okinoua', 'schedules', 'Сеансы')



@only_superuser
@never_cache
def okinoua_schedules_list(request):

    schedules = SourceSchedules.objects.filter(source_obj__url='http://www.okino.ua/').order_by('-dtime')[:300]
    text = ''
    for i in schedules:
        city = i.cinema.city.name
        cinema = i.cinema.name
        film = i.film.name
        dtime = i.dtime
        text += '%s --- %s --- %s --- %s<br />' % (city, cinema, film, dtime)

    return HttpResponse(text)



@timer
def raspishi_relations():
    source = ImportSources.objects.get(url='http://распиши.рф/')
    
    ignored = get_ignored_films()
    data_nof_film = ''
    
    domain = u'распиши.рф'
    url = 'http://%s/getfilmxml.php' % domain.encode('idna')

    req = urllib.urlopen(url)
    if req.getcode() == 200:
        films_rid = list(RaspishiRelations.objects.exclude(kid=0).values_list('rid', flat=True))

        xml_data = BeautifulSoup(req.read(), from_encoding="utf-8")
        for i in xml_data.findAll('movie'):
            id = int(i['id'])
            if id not in films_rid:
                name_ru = i.find('name').text.encode('utf-8')
                name_en = i.find('nameeng').text.encode('utf-8')
                
                name_ru = re.sub(r'\(.*?\)', '', name_ru).strip()
                name_en = re.sub(r'\(.*?\)', '', name_en).strip()
                
                name_slug = low(del_separator(del_screen_type(name_ru)))
                name_en_slug = low(del_separator(del_screen_type(name_en)))
                
                if name_slug.decode('utf-8') not in ignored:
                    try:
                        kid, info = film_identification(name_slug, None, {}, {}, source=source)
                
                        if kid:
                            created = RaspishiRelations.objects.create(
                                rid = id,
                                kid = kid,
                                name_ru = name_ru,
                                name_en = name_en,
                            )
                        else:
                            data_nof_film += xml_noffilm(name_ru, name_slug, name_en, name_en_slug, id, info, None, source.id)
                    except db.backend.Database._mysql.OperationalError:
                        pass
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'films', 'Укр. сеансы')


