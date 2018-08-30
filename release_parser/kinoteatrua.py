#-*- coding: utf-8 -*- 
import urllib2
import httplib2
import re
import datetime
import time
import operator
import random

from django.http import HttpResponse
from django.conf import settings

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


def give_me_cookie():
    import cookielib
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler())
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
    }
    opener.addheaders = headers.items()
    return opener


def get_kinoteatrua_films_links(link, page, year, source, opener, films_urls=[]):
    url = link if link else '%sru/main/films/year/%s/page/%s.phtml' % (source.url, year, page)

    req = opener.open(urllib2.Request(url))
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        if not data.find('center', {'class': 'xErr'}):
            for div in data.findAll('div', id='searchItemMainText'):
                a = div.find('a', {'class': 'searchItemLink'})
                film_ru_url = a.get('href')
                film_id = film_ru_url.replace('%sfilm/' % source.url, '').replace('.phtml', '').encode('utf-8')
                film_name = a.text.encode('utf-8')

                p = div.findAll('a', {'class': 'searchItemText'}, limit=1)
                if p:
                    film_year = re.findall(r'\d+', p[0])
                    film_year = film_year[0]
                else:
                    film_year = year

                if link:
                    year_block = div.findAll('p', {'class': 'searchItemText'}, limit=1)[0].text.encode('utf-8').strip()
                    film_year = year_block.split(' | ')[0]

                try:
                    film_year = int(film_year)
                except ValueError:
                    film_year = None

                films_urls.append({'id': film_id, 'name': film_name, 'url': film_ru_url, 'year': film_year})
                if page % 4 == 0:
                    time.sleep(random.uniform(1.0, 3.0))

            if not link:
                page + 1
                return get_kinoteatrua_films_links(None, page, year, source, opener, films_urls)
    return films_urls


@timer
def get_kinoteatrua_films_and_persons():
    '''
    Получение фильмов
    '''
    opener = give_me_cookie()

    source = ImportSources.objects.get(url='http://kino-teatr.ua/')
    sfilm_clean(source)

    try:
        with open('%s/dump_%s_nof_film.xml' % (settings.NOF_DUMP_PATH, source.dump), 'r') as f:
            xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
    except IOError:
        xml_data = BeautifulSoup('', from_encoding="utf-8")

    ignored = get_ignored_films()

    films_slugs = [i.get('slug_ru') for i in xml_data.findAll('film')]

    data_nof_film = ''
    persons_dict = {}
    data_nof_persons = ''

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    year = datetime.datetime.now().year
    lang = Language.objects.get(name='Украинский')

    def get_persons(data):
        persons = {}
        tags = ['director', 'actor']
        for tag in tags:
            for p in data.findAll('span', itemprop=tag):
                person_id = p.a.get('href')
                person_id = long(re.findall(r'\d+', person_id)[0])
                if p.a.text:
                    persons[person_id] = p.a.text.encode('utf-8')
        return persons

    films_urls = get_kinoteatrua_films_links('http://kino-teatr.ua/films-near.phtml', 1, year, source, opener)

    for ind, film in enumerate(films_urls):
        film_ua_url = film['url'].replace(source.url, '%suk/' % source.url)
        req_text = opener.open(urllib2.Request(film_ua_url))

        if req_text.getcode() == 200:
            film_data = BeautifulSoup(req_text.read(), from_encoding="utf-8")
            persons = get_persons(film_data)
            persons_dict[film['id']] = persons
            name = film_data.find('div', {'class': 'myriadFilm'}).text.encode('utf-8')
            name = name.replace('Фільм ', '').strip()
            text = film_data.find('div', itemprop='description')

            text_data = text.findAll('p', limit=1)
            if text_data:
                text = text_data[0].text.encode('utf-8')
            else:
                text = text.text.encode('utf-8').strip()
                text = text.replace('редактирование синопсиса', '').strip()

            if text in ('Проект оголошений', 'Підготовка до зйомок'):
                text = ''

            film_slug = low(del_separator(film['name']))
            temp_film_slug = film_slug.decode('utf-8')

            if temp_film_slug not in ignored and temp_film_slug not in films_slugs:
                obj = films.get(film['id'])
                next_step = checking_obj(obj)

                if next_step:
                    if obj:
                        kid = obj.kid
                    else:
                        kid, info = film_identification(film_slug, None, {}, {}, year, source=source)

                    objt = None
                    if kid:
                        create_new, objt = unique_func(fdict, kid, obj)
                        if create_new:
                            objt = create_sfilm(film['id'], kid, source, name, year=film.get('year'), txt=text)
                            films[film['id']] = objt
                            if not fdict.get(kid):
                                fdict[kid] = {'editor_rel': [], 'script_rel': []}
                            fdict[kid]['script_rel'].append(objt)
                    elif not obj:
                        if temp_film_slug not in films_slugs:
                            data_nof_film += xml_noffilm(film['name'], film_slug, None, None, film['id'], info, film['url'].encode('utf-8'), source.id)

                    if objt and not create_new:
                        try:
                            film_text = objt.text.encode('utf-8')
                        except UnicodeDecodeError:
                            film_text = objt.text

                        if film_text != text:
                            objt.text = text
                            objt.save()

        if ind % 2 == 0:
            time.sleep(random.uniform(1.0, 3.0))

    xml_data = str(xml_data).replace('<html><head></head><body><data>', '').replace('</data></body></html>', '')
    xml_data = '<data>%s%s</data>' % (xml_data, data_nof_film)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, xml_data)
    cron_success('html', source.dump, 'films', 'Укр. фильмы')

    # persons
    persons_nof_list = []
    persons_list = []
    for ind, film in enumerate(films_urls):
        req = opener.open(urllib2.Request(film['url']))

        if req.getcode() == 200:
            film_data = BeautifulSoup(req.read(), from_encoding="utf-8")
            persons = get_persons(film_data)
            for person_id, person_ru_name in persons.iteritems():
                if person_id not in persons_nof_list and person_id not in persons_list:
                    ukr_person = persons_dict.get(film['id'])
                    if ukr_person:
                        ukr_person_name = ukr_person.get(person_id)
                        if ukr_person_name:
                            ukr_person_name_slug = low(del_separator(ukr_person_name))
                            person_ru_name_slug = low(del_separator(person_ru_name))

                            person_obj = Person.objects.filter(name__name=person_ru_name_slug).exclude(kid=None)
                            if person_obj.count() == 1:
                                names = [
                                    {'name': ukr_person_name, 'status': 1},
                                    {'name': ukr_person_name_slug, 'status': 2}
                                ]
                                for i in names:
                                    name_obj, name_created = NamePerson.objects.get_or_create(
                                        name=i['name'],
                                        status=i['status'],
                                        language=lang,
                                        defaults={
                                            'name': i['name'],
                                            'status': i['status'],
                                            'language': lang,
                                        })
                                    if name_obj not in person_obj[0].name.all():
                                        person_obj[0].name.add(name_obj)
                            else:
                                data_nof_persons += '<person name="%s" slug="%s" code="%s" name_alt="%s" slug_alt="%s"></person>' % (person_ru_name.replace('"',"'"), person_ru_name_slug, person_id, ukr_person_name.replace('"', "'"), ukr_person_name_slug)
                            persons_list.append(person_id)
        if ind % 2 == 0:
            time.sleep(random.uniform(1.0, 3.0))

    create_dump_file('%s_nof_person' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_persons)
    cron_success('html', source.dump, 'persons', 'Укр. персоны')


@timer
def get_kinoteatrua_posters():
    '''
    Получение укр.постеров
    '''
    opener = give_me_cookie()
    source = ImportSources.objects.get(url='http://kino-teatr.ua/')

    films_dict = get_source_data(source, 'film', 'dict')
    posters_list = list(UkrainePosters.objects.filter(source_obj=source).values_list('source_id', flat=True))

    year = datetime.datetime.now().year
    pages = []

    def get_pages(page):
        url = '%suk/main/films/year/%s/page/%s.phtml' % (source.url, year, page)
        req = opener.open(urllib2.Request(url))

        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            if data.find('center', {'class': 'xErr'}):
                req2 = opener.open(urllib2.Request('http://kino-teatr.ua/uk/films-near.phtml'))

                if req2.getcode() == 200:
                    data2 = BeautifulSoup(req2.read(), from_encoding="utf-8")
                    pages.append({'page': 1000, 'data': data2})
            else:
                pages.append({'page': page, 'data': data})
                if page % 4 == 0:
                    time.sleep(random.uniform(1.0, 3.0))
                return get_pages(page + 1)

    get_pages(1)

    poster_srcs = []

    for i in sorted(pages, key=operator.itemgetter('page'), reverse=True):

        for block in i['data'].findAll('div', id='searchItemFilms'):
            a = block.find('a', {'class': 'searchItemLink'})
            film_ru_url = a.get('href')
            film_id = film_ru_url.replace('%suk/film/' % source.url, '').replace('.phtml', '').encode('utf-8')
            film_kid = films_dict.get(film_id)

            if film_kid:
                poster_src = block.a.img.get('src')

                if 'kt_logo' not in poster_src and 'blank_news_img' not in poster_src and poster_src not in poster_srcs:
                    poster_srcs.append(poster_src)
                    try:
                        poster = re.findall(r'poster\_(\d+|\w+)\.(jpg|png)', poster_src.lower())[0]
                    except IndexError:
                        poster = None

                    if poster:
                        poster_url = '%spublic/main/films/poster_%s.%s' % (source.url, poster[0], poster[1])
                        file_name = 'poster_%s_ua.%s' % (film_kid.kid, poster[1])

                        resp, content = httplib2.Http().request(poster_url, method="GET")
                        if content:
                            poster_path = '%s/%s' % (settings.POSTERS_UA_PATH, file_name)
                            try:
                                os.remove(poster_path)

                                with open(poster_path, 'wb') as f:
                                    f.write(content)

                                if poster[0] not in posters_list:
                                    UkrainePosters.objects.create(
                                        source_id=poster[0],
                                        source_obj=source,
                                        kid=film_kid.kid,
                                        poster=file_name,
                                    )
                                    posters_list.append(poster[0])
                            except OSError:
                                pass

    cron_success('html', source.dump, 'posters', 'Укр. постеры')


@timer
def get_kinoteatrua_schedules():
    opener = give_me_cookie()

    kinoteatrua_urls = [
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-alushta.phtml', 'name': 'Алушта', 'id': 51},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-alchevsk.phtml', 'name': 'Алчевск', 'id': 42},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-artemovsk.phtml', 'name': 'Артемовск', 'id': 37},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-belaya-tserkov.phtml', 'name': 'Белая церковь', 'id': 25},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-berdyansk.phtml', 'name': 'Бердянськ', 'id': 64},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-borispol.phtml', 'name': 'Борисполь', 'id': 38},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-brovary.phtml', 'name': 'Бровары', 'id': 2},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-bucha.phtml', 'name': 'Буча', 'id': 12},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-vinnitsa.phtml', 'name': 'Винница', 'id': 20},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-gorlovka.phtml', 'name': 'Горловка', 'id': 46},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-dnepropetrovsk.phtml', 'name': 'Днепропетровск', 'id': 5},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-donetsk.phtml', 'name': 'Донецк', 'id': 6},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-evpatoriya.phtml', 'name': 'Евпатория', 'id': 39},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-zhitomir.phtml', 'name': 'Житомир', 'id': 17},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-zaporozhe.phtml', 'name': 'Запорожье', 'id': 18},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-ivano-frankovsk.phtml', 'name': 'Ивано-Франковск', 'id': 7},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-irpen.phtml', 'name': 'Ирпень', 'id': 3},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kamenets-podolskiy.phtml', 'name': 'Каменец-Подольский', 'id': 40},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-kahovka.phtml', 'name': 'Каховка', 'id': 54},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-kerch.phtml', 'name': 'Керчь', 'id': 35},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kiev.phtml', 'name': 'Киев', 'id': 1},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kirovograd.phtml', 'name': 'Кировоград', 'id': 36},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-kovel.phtml', 'name': 'Ковель', 'id': 31},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-kolomiya.phtml', 'name': 'Коломыя', 'id': 58},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-komsomolsk.phtml', 'name': 'Комсомольск', 'id': 62},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-konotop.phtml', 'name': 'Конотоп', 'id': 52},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-korosten.phtml', 'name': 'Коростень', 'id': 49},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kramatorsk.phtml', 'name': 'Краматорск', 'id': 14},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-krasnyy-luch.phtml', 'name': 'Красный Луч', 'id': 55},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kremenchug.phtml', 'name': 'Кременчуг', 'id': 41},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-krivoy-rog.phtml', 'name': 'Кривой Рог', 'id': 15},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-lubny.phtml', 'name': 'Лубны', 'id': 59},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-lugansk.phtml', 'name': 'Луганск', 'id': 32},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-lutsk.phtml', 'name': 'Луцк', 'id': 29},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-lvov.phtml', 'name': 'Львов', 'id': 9},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-makeevka.phtml', 'name': 'Макеевка', 'id': 67},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-mariupol.phtml', 'name': 'Мариуполь', 'id': 19},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-melitopol.phtml', 'name': 'Мелитополь', 'id': 57},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-mukachevo.phtml', 'name': 'Мукачево', 'id': 43},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-nikolaev.phtml', 'name': 'Николаев', 'id': 11},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-nikopol.phtml', 'name': 'Никополь', 'id': 65},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-novaya-kahovka.phtml', 'name': 'Новая Каховка', 'id': 53},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-odessa.phtml', 'name': 'Одесса', 'id': 4},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-pavlograd.phtml', 'name': 'Павлоград', 'id': 66},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-pervomaysk.phtml', 'name': 'Первомайськ', 'id': 61},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-poltava.phtml', 'name': 'Полтава', 'id': 27},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-rovno.phtml', 'name': 'Ровно', 'id': 26},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-svetlovodsk.phtml', 'name': 'Светловодск', 'id': 60},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-sevastopol.phtml', 'name': 'Севастополь', 'id': 23},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-severodonetsk.phtml', 'name': 'Северодонецк', 'id': 56},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-simferopol.phtml', 'name': 'Симферополь', 'id': 21},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-stahanov.phtml', 'name': 'Стаханов', 'id': 44},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-sumy.phtml', 'name': 'Сумы', 'id': 16},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-ternopol.phtml', 'name': 'Тернополь', 'id': 10},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-uzhgorod.phtml', 'name': 'Ужгород', 'id': 33},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-fastov.phtml', 'name': 'Фастов', 'id': 45},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-feodosiya.phtml', 'name': 'Феодосия', 'id': 48},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kharkov.phtml', 'name': 'Харьков', 'id': 13},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-kherson.phtml', 'name': 'Херсон', 'id': 34},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-khmelnitskiy.phtml', 'name': 'Хмельницкий', 'id': 30},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-tsyurupinsk.phtml', 'name': 'Цюрупинск', 'id': 47},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-cherkassy.phtml', 'name': 'Черкассы', 'id': 8},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-chernigov.phtml', 'name': 'Чернигов', 'id': 28},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-chernovtsy.phtml', 'name': 'Черновцы', 'id': 24},
        {'status': 0, 'url': 'http://kino-teatr.ua/kinoafisha-shostka.phtml', 'name': 'Шостка', 'id': 50},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-yugnoe.phtml', 'name': 'Южное', 'id': 63},
        {'status': 1, 'url': 'http://kino-teatr.ua/kinoafisha-yalta.phtml', 'name': 'Ялта', 'id': 22},
    ]

    ignored = get_ignored_films()
    kinoteatrua_urls = sorted(kinoteatrua_urls, key=operator.itemgetter('status'), reverse=True)

    source = ImportSources.objects.get(url='http://kino-teatr.ua/')

    xml = open('%s/dump_%s_nof_film.xml' % (settings.NOF_DUMP_PATH, source.dump), 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()

    films_slugs = [i.get('slug_ru') for i in xml_data.findAll('film')]

    data_nof_films = ''
    data_nof_cinemas = ''
    data_nof_city = ''
    noffilms = []
    nofcinemas = []

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    cities_dict = get_source_data(source, 'city', 'dict')
    cinemas_dict = get_source_data(source, 'cinema', 'dict')
    schedules = get_source_data(source, 'schedule', 'list')

    date_from = datetime.date.today()
    date_to = date_from + datetime.timedelta(days=14)
    dates = []

    delta = date_to - date_from
    for day in range(delta.days + 1):
        d = date_from + datetime.timedelta(days=day)
        dates.append({'str': d.strftime('%d.%m.%Y'), 'obj': d})

    def get_kinoteatr_data(opener, date, city_obj):
        nof_films = ''
        nof_cinemas = ''
        url = '%sru/main/bill/order/cinemas/date/%s.phtml' % (source.url, date['str'])
        req = opener.open(urllib2.Request(url))

        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            main = data.find('div', id='news_page')
            if main:
                if main.find('center', {'class': 'xErr'}):
                    return nof_films, nof_cinemas, 'error'

                for cinema_tag in main.findAll('span', id='afishaKtName'):
                    cinema_name_block = cinema_tag.findAll('a', limit=1)[0]
                    cinema_name = cinema_name_block.text.encode('utf-8').replace('Кинотеатр', '')
                    cinema_slug = low(del_separator(del_screen_type(cinema_name)))
                    cinema_name = cinema_name.replace('"', "'").replace('&', '&amp;').strip()
                    cinema_id = cinema_name_block.get('href').replace('.phtml', '')
                    if 'cinema_id' in cinema_id:
                        cinema_id = cinema_id.replace('http://kino-teatr.ua/ru/main/cinema/cinema_id/', '').encode('utf-8')
                    else:
                        cinema_id = re.findall(r'\d+$', cinema_id)[0]

                    if cinema_id not in nofcinemas:
                        cinema_obj = cinemas_dict.get(str(cinema_id))
                        if not cinema_obj:
                            filter1 = {'name__name': cinema_slug, 'name__status': 2, 'city__id': city_obj.city_id}
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
                                    cinemas_dict[str(cinema_id)] = cinema_obj
                                except Cinema.DoesNotExist:
                                    pass
                            else:
                                try:
                                    name_city = city_obj.name.encode('utf-8')
                                except UnicodeDecodeError:
                                    name_city = city_obj.name
                                nof_cinemas += '<cinema name="%s" slug="%s" city="%s" city_kid="%s"></cinema>' % (cinema_name, cinema_slug, name_city, city_obj.city.kid)
                                nofcinemas.append(cinema_id)

                        if cinema_obj:
                            films_block = cinema_tag.find_next_sibling('div')
                            for film_block in films_block.findAll('div', id='afishaItem'):
                                film_name = film_block.find('div', {'class': 'filmName'})
                                full_url = film_name.a.get('href').encode('utf-8')
                                if film_name.a.text:
                                    film_name = film_name.a.text.encode('utf-8').strip()
                                    film_slug = low(del_separator(film_name))
                                    film_id = full_url.replace('http://kino-teatr.ua/film/', '').replace('.phtml', '').encode('utf-8')
                                    if film_slug.decode('utf-8') not in ignored and film_id not in noffilms:

                                        obj = films.get(film_id)
                                        next_step = True if obj and obj.rel_ignore else False

                                        if next_step:
                                            if obj:
                                                kid = obj.kid
                                            else:
                                                kid, info = film_identification(film_slug, None, {}, {}, source=source)

                                            if not obj:
                                                if kid:
                                                    uk_url = '%suk/film/%s' % (source.url, film_id)
                                                    uk_req = opener.open(urllib2.Request(uk_url))
                                                    if uk_req.getcode() == 200:
                                                        uk_data = BeautifulSoup(uk_req.read().decode('utf-8'), from_encoding="utf-8")

                                                        uk_name = uk_data.find('div', {'class': 'myriadFilm'}).text.encode('utf-8')
                                                        uk_text = uk_data.find('div', itemprop='description')

                                                        uk_text_data = uk_text.findAll('p', limit=1)
                                                        if uk_text_data:
                                                            uk_text = uk_text_data[0].text.encode('utf-8')
                                                        else:
                                                            uk_text = uk_text.text.encode('utf-8').strip()
                                                            uk_text = uk_text.replace('редактирование синопсиса', '').strip()

                                                        obj = create_sfilm(film_id, kid, source, uk_name, txt=uk_text)
                                                        films[film_id] = obj
                                                        if not fdict.get(kid):
                                                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                                        fdict[kid]['script_rel'].append(obj)
                                                else:
                                                    if film_slug.decode('utf-8') not in films_slugs:
                                                        nof_films += xml_noffilm(film_name, film_slug, None, None, film_id, info, full_url, source.id)
                                                        noffilms.append(film_id)

                                            if obj:
                                                shows = film_block.find('div', {'class': 'filmShows'})
                                                for times in shows.findAll('a', {'class': 'time'}):
                                                    try:
                                                        hours, minutes = times.text.split(':')
                                                    except AttributeError:
                                                        times.find('sup').extract()
                                                        hours, minutes = times.text.split(':')

                                                    dtime = datetime.datetime(date['obj'].year, date['obj'].month, date['obj'].day, int(hours), int(minutes))

                                                    sch_id = '%s%s%s%s' % (dtime, cinema_slug, city_slug, film_id)
                                                    sch_id = sch_id.replace(' ', '').decode('utf-8')

                                                    if sch_id not in schedules:
                                                        SourceSchedules.objects.create(
                                                            source_id=sch_id,
                                                            source_obj=source,
                                                            film=obj,
                                                            cinema=cinema_obj,
                                                            dtime=dtime,
                                                        )
                                                        schedules.append(sch_id)
        return nof_films, nof_cinemas, ''

    for ind, i in enumerate(kinoteatrua_urls):
        city_name = i['name']
        city_slug = low(del_separator(city_name))

        city_obj = cities_dict.get(str(i['id']))
        if not city_obj:
            city = City.objects.filter(name__name=city_slug, name__status=2).distinct('pk')
            if city.count() == 1:
                city_obj = SourceCities.objects.create(
                    source_id=i['id'],
                    source_obj=source,
                    city=city[0],
                    name=city_name,
                )
                cities_dict[str(i['id'])] = city_obj
            else:
                data_nof_city += '<city name="%s" slug="%s"></city>' % (city_name, city_slug)

        if city_obj:
            opener = give_me_cookie()
            opener.addheaders.append(('Cookie', 'main::city_id=%s' % i['id']))
            city_req = opener.open(urllib2.Request(i['url']))

            if city_req.getcode() == 200:
                for index, date in enumerate(dates):
                    nof_film, nof_cinema, error = get_kinoteatr_data(opener, date, city_obj)
                    data_nof_films += nof_film
                    data_nof_cinemas += nof_cinema
                    if error:
                        break

                    if index % 3 == 0:
                        time.sleep(random.uniform(1.0, 3.0))

        if ind % 2 == 0:
            time.sleep(random.uniform(1.0, 3.0))

    xml_data = str(xml_data).replace('<html><head></head><body><data>', '').replace('</data></body></html>', '')
    xml_data = '<data>%s%s</data>' % (xml_data, data_nof_films)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, xml_data)
    create_dump_file('%s_nof_city' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_city)
    create_dump_file('%s_nof_cinema' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_cinemas)
    cron_success('html', source.dump, 'schedules', 'Сеансы')


@timer
def get_kinoteatrua_releases():
    '''
    Получение укр.релизов
    '''
    opener = give_me_cookie()

    source = ImportSources.objects.get(url='http://kino-teatr.ua/')

    films_dict = get_source_data(source, 'film', 'dict')

    releases = SourceReleases.objects.select_related('film').filter(source_obj=source)
    releases_dict = {}
    for i in releases:
        releases_dict[i.film.source_id] = i

    url = '%sfilms-near.phtml' % source.url

    req = opener.open(urllib2.Request(url))
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        for ind, i in enumerate(data.findAll('a', {'class': 'searchItemLink'})):
            film_url = i.get('href')
            film_id = film_url.replace('http://kino-teatr.ua/film/', '').replace('.phtml', '').encode('utf-8')
            film_obj = films_dict.get(film_id)
            if film_obj:
                req2 = opener.open(urllib2.Request(film_url))
                if req2.getcode() == 200:
                    data2 = BeautifulSoup(req2.read(), from_encoding="utf-8")
                    block = data2.find('div', id='filmInfo')
                    strong = block.find('strong', text=u"Премьера (в Украине): ")
                    day, month, year = strong.find_next_sibling("a").text.strip().split('.')
                    showdate = datetime.date(int(year), int(month), int(day))
                    release_obj = releases_dict.get(film_id)
                    if release_obj:
                        if release_obj.release != showdate:
                            release_obj.release = showdate
                            release_obj.save()
                    else:
                        release_obj = SourceReleases.objects.create(
                            source_obj=source,
                            film=film_obj,
                            release=showdate,
                        )
                        releases_dict[film_id] = release_obj

            if ind % 1 == 0:
                time.sleep(random.uniform(1.0, 3.0))

    cron_success('html', source.dump, 'releases', 'Укр.релизы')


@timer
def kinoteatrua_schedules_export_to_kinoafisha():
    from release_parser.views import schedules_export
    source = ImportSources.objects.get(url='http://kino-teatr.ua/')
    autors = (source.code, 0)
    log = schedules_export(source, autors, False)
    # запись лога в xml файл
    create_dump_file('%s_export_to_kinoafisha_log' % source.dump, settings.LOG_DUMP_PATH, '<data>%s</data>' % log)
    cron_success('export', source.dump, 'schedules', 'Сеансы')
