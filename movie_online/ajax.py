# -*- coding: utf-8 -*-   
import os
import time
import re
import operator
import urllib

from django import db
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.conf import settings
from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup, Doctype, SoupStrainer

from base.models import *
from api.views import create_dump_file
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from kinoinfo_folder.func import del_separator, del_screen_type, low
from movie_online.debug import debug_logs

# Тип каждого загружаемыого в модель фильма определяется значением в поле "afisha_id":
# 1 значение - "none" - присваивается новым записям, еще не проходившим идентификацию с киноафишей (NULL)
# 2 значение - "0" - фильм проходил индентификацию, но (по каким-то причинам) не был индентифицирован  
# 3 значение - "2123" - айди фильма в базе киноафиши, фильм проходил идентификацию и был идентифицирован, соответственно
# получил значение номера записи такого же фильма киноафиши

@never_cache
@dajaxice_register
    
def parse_data_show(request, count, check):
    #try:
      
    # определяем функцию, вызываемую из интерфейса.  Cпомощью Ajax
    # переменная check - это идентификатор, определяющий тип запроса (считываем одну запись или все запси с дальнейшем сохраненением их в модель)
    # переменная count содержит порядковый номер нажатия кнопки в интерфейсе.
    """Набор функций для чтения/разбора дампа с мегого и записи в модель всех данных источника.

    """

    debug_logs("start parse %s" % check)
    # Начинаем отчет времени выполнения шага
    start = time.time()

    REG_RATE = re.compile(r'\d+\.\d+')

    # Обнуляем счетчик, для раоты цикла чтения дампа 
    cnt = 0

    # Обнуляем счетчик, для подсчета новых записей в модель
    cnt_in_model = 0

    source = ImportSources.objects.get(url='http://megogo.net/')

    # 1.Step - чтение дампа
    try:
        # Пробуем открыть файл для чтения
        read_from_xml = open("%s/dump_%s.xml" % (settings.API_DUMP_PATH, source.dump), 'r') 
        # Читаем данные из файла
        data = BeautifulSoup(read_from_xml.read(), "html.parser")
        # Закрываем файл
        read_from_xml.close() 
    except (OSError, IOError):
        # в случае ошибки прерываем функцию и возвращаемся в интерфейс
        return simplejson.dumps({
           'error': 'error',
        })
    
    # Если запрос на считывание и запись в модель содержимого дампа
    if check == 1:
        # Подготавливаем список уже имеющихся данных модели megogo, для дальнейшего сравнения на повторы
        megogo_data = list(MovieMegogo.objects.all().values_list('megogo_id', flat=True))

    # Время выполнения первого шага - считывание дампа и считывание модели
    finish1 = time.time()

    # Начинаем отчет времени выполнения следующего шага
    start2 = time.time()
    
    # Используем метод try для генерации исключения, при чтении дампа,
    # при запросе на полный разбор содержимого дампа
    #try:
    # 2.Step - НАчало цикла. Разбор дампа      
    for i in data.findAll('object'):
       
        # Извлекаем из массива data первую запись
        id = long(i['id'])

        # Для прерывания цикла в случае если разбирается одна запись, используем метку
        # check == 0 и переданное число нажатий кнопки для сопостовления количеству раз прохождения цикла cnt == count
        if cnt == count and check == 0: 
            debug_logs("Парсинг одной записи: %s (%s)" % (check, film_name))
            break
    
        # Увеличивыем счетчик прохождения цикла (чтение содержимого дампа)
        cnt +=1

        # Начало идентификации

        # 1) - идентифицируем сериалы, они пока нам не нужны
        serial = i['serial'].encode('utf-8')   # сериал (true/false)
        serial = True if serial == 'true' else False
        # 2) - идентифицируем  тип записи, фильмы берем, мультфильмы и новсти не берем
        type_f = i['type'].encode('utf-8')
            
        # Обрабатываем только фильмы, сериалы и проч. пока не берем
        if type_f == "FILM" and not serial:

            # 3) - идентифицируем остальные записи по тегам           
            film_name = i['title'].encode('utf-8')  # название
            film_name_en = i['title_en'].encode('utf-8')  # название en
            genres = i['genres'].encode('utf-8')  # жанры
            page = i['page'].encode('utf-8')  # ссылка на страницу на Мегого
            kinopoisk_id = int(i['kinopoisk_id']) if i['kinopoisk_id'] else None # id на кинопоске    
            year = int(i.info['year'])  # год
            
            country = i.info['country'].encode('utf-8')  # страна
            budget = i.info['budget'].encode('utf-8') if i.info['budget'] else None      # бюджет
            premiere = i.info['premiere'].encode('utf-8')  if i.info['premiere'] else None # дата премьеры
            dvd = i.info['dvd'].encode('utf-8') if i.info['dvd'] else None   # дата на DVD
            duration = i.info['duration'].encode('utf-8')  # длительность
            
            kinopoisk = REG_RATE.findall(i.ratings['kinopoisk'])
            kinopoisk = float(kinopoisk[0]) if kinopoisk else None

            imdb = REG_RATE.findall(i.ratings['imdb'])
            imdb = float(imdb[0]) if imdb else None
         
            story = i.story.string.encode('utf-8')  # описание фильма
            poster_thumbnail = i.poster['thumbnail'].encode('utf-8')   # адрес постера 720px × 400px
            poster_url  = i.poster['url'].encode('utf-8')  # адрес постер 126px × 71px

            # Приводим формат данных дампа для разбора 
            xml_films_data = ' film_name = "%s" <br /> genres = "%s" <br />  page_megogo = "<a href="%s" target="_blank">link</a>" <br /> page_kinopoisk = "<a href="http://www.kinopoisk.ru/film/%s/" target="_blank">link</a>" <br /> id = "%s" <br /> year = "%s" <br /> country = "%s" <br /> budget = "%s"  <br /> premiere = "%s" <br /> dvd = "%s" <br /> duration = "%s" <br /> kinopoisk = "%s" <br /> imdb = "%s" <br /> story = "%s" <br /> poster_thumbnail = "<a href="%s" target="_blank">link</a>" <br />  ' % (film_name, genres, page,  kinopoisk_id, id, year, country, budget, premiere, dvd, duration, kinopoisk, imdb, story, poster_url )

            # Если заданно условие чтения всего дампа, то запишем данные в модель
            # предворительно проверив на повторы
            # Перед записью данных в модель, проверяем, работаем ли мы с записью впервые(новая) или ранее она читалась(старая)
            # Если в дампе новая запись
            if check == 1 and id not in megogo_data:

                # Увеличивыем счетчик прохождения цикла (запись в модель)
                cnt_in_model += 1

                # 3.Step - Сохраняем полученные данные в модель MovieMegogo
                MovieMegogo.objects.create(
                    megogo_id = id,
                    title = film_name,
                    title_en = film_name_en,
                    genres = genres,
                    serial = serial,
                    page = page,
                    type_f = type_f,
                    kinopoisk_id = kinopoisk_id,
                    year = year,                           
                    country = country,                                                       
                    budget = budget,
                    premiere = premiere,
                    dvd = dvd,
                    duration = duration,
                    kinopoisk = kinopoisk,
                    imdb = imdb,
                    story = story,
                    poster_url = poster_url,
                    poster_thumbnail = poster_thumbnail,
                )

        # Время выполнения второго шага - обработка одной записи
        finish2 = time.time()

    # Итоговое время выполнения всей функции
    finish3 = time.time()

    timer_1step = "%.2f мин" % ((float(finish1 - start))/60)
    timer_2step = "%.2f мин" % ((float(finish2 - start2))/60)
    timer_full = "%.2f мин" % ((float(finish3 - start))/60)
    debug_logs("finish")
    debug_logs("Time: %s " % timer_1step)
    debug_logs("Time: %s " % timer_2step)
    debug_logs("Time: %s " % timer_full)
    # Возвращаемся в интерфейс в стандартном режимие, без исключений,
    # т.к. запрос был лишь на обработку одной записи (check=0)
    
    return simplejson.dumps({
           'pased_data': xml_films_data,
           'poster_thumbnail': poster_thumbnail,
           'timer1': timer_1step,
           'timer2': timer_2step,
           'timerf': timer_full,
           'check': check,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
   

@never_cache
@dajaxice_register
def parse_data_ident(request, selected):
    """Функция для идентификации полученных записей
    """
    #try:
    debug_logs("start ident %s " % selected)
    # Начинаем отчет времени выполнения фукнции
    start = time.time()

    data_nof_film = ''
    noffilms = []

    ignored = get_ignored_films()

    # Задаем тип идентификации, для передачи в качестве параметра в функцию идентификации
    ident_type = 'movie_online'

    # Делаем выборку всех фильмов из базы с пометкой (afisha_id=None),
    # так помечаются все фильмы при парсинге,
    # это фильмы, которые не разу не проходифшие идентификацию киноафиши
    data = MovieMegogo.objects.filter(afisha_id__in=(0, None))

    # Получаем необходимые для идентификации параметры,
    # проходим итерациями в цикле для каждого отдельного фильма
    for i in data:  

        year = i.year
        name_ru = i.title
        name_en = i.title_en
        country = i.country

        # Отчищаем названия ru en для идентификации фильма
        name_ru_slug = del_separator(low(name_ru))
        name_en_slug = del_separator(low(name_en))
        
        # Задаем диапазон лет для идентификации фильма
        new_year = year + 2
        old_year = year - 2
        filter_year = {'year__gte': old_year, 'year__lte': new_year}
        
        try:
            # Передаем фильм в функцию на идентификацию
            kid, info = film_identification(name_ru_slug, name_en_slug, {}, {}, filter_year, ident_type, country)
            
            if kid:
                # Записываем результат в модель
                i.afisha_id = kid
                i.save()
            else:
                if i.megogo_id not in noffilms and name_ru_slug.decode('utf-8') not in ignored:
                    data_nof_film += xml_noffilm(name_ru.encode('utf-8'), name_ru_slug, None, None, i.megogo_id, info, i.page.encode('utf-8'))
                    noffilms.append(i.megogo_id)
        except db.backend.Database._mysql.OperationalError:
            if i.megogo_id not in noffilms and name_ru_slug.decode('utf-8') not in ignored:
                data_nof_film += xml_noffilm(name_ru.encode('utf-8'), name_ru_slug, None, None, i.megogo_id, None, i.page.encode('utf-8'))
                noffilms.append(i.megogo_id)
        
        # Время выполнения функции
        finish = time.time()
        timer = "%.2f мин" % ((float(finish - start))/60)

        debug_logs("finish")
        debug_logs("timer: %s " % timer)
        debug_logs("Идентификация: название %s / инфо %s %s" % (name_ru_slug, kid, info))

    source = ImportSources.objects.get(url='http://megogo.net/')
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    
    # Возвращаемся в интерфейс
    return simplejson.dumps({ 
          'request_type': 1,
          'timer': timer,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

