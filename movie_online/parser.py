 #-*- coding: utf-8 -*- 
import operator
import os
import time 
import urllib

from django.shortcuts import HttpResponse, render_to_response, HttpResponseRedirect, RequestContext
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache

from user_registration.func import only_superuser
from movie_online.forms import MegogoUploadForm
from release_parser.func import cron_success, get_file_modify_datetime
from api.views import create_dump_file, give_me_dump_please 
from movie_online.debug import debug_logs
from base.models import *

@never_cache
@only_superuser
def movie_online_main_admin(request):
    """Набор функций для работы с файлом дампа мегого.
       Чтение, Загрузка, Обновление, Данные о файле
    """
    source = ImportSources.objects.get(url='http://megogo.net/')

    # Пробуем получить информацию о файле
    try:
        filepath = '%s/dump_%s.xml' % (settings.API_DUMP_PATH, source.dump)
        filesize = os.path.getsize(filepath)
        filepath = filepath[28:]
        modify_date = get_file_modify_datetime(settings.API_DUMP_PATH, 'dump_%s.xml' % source.dump)
        modify_date = modify_date + datetime.timedelta(hours=4)
        filedate = modify_date
    # Если файла нет, то присваиваем нулевые значения 
    except (OSError, IOError):
        filepath = None
        filedate = None
        filesize = 0

    # вычисляем размер файла в мегабайтах 
    filesize = str(int(filesize)/(1024*1024)) + ".МБ"

    # Загружаем форму, для ручной загрузки файла-дампа на сервер
    form = MegogoUploadForm()

    # Обрабатываем форму, если загружается файл на сервер
    if request.POST:

        # получаем значение из формы
        form = MegogoUploadForm(request.POST, request.FILES)
        
        # Перезаписываем данные с загруженного файла с помощью функции create_dump_file
        if form.is_valid():
            data = request.FILES['file']
            
            with open('%s/dump_%s.xml' % (settings.API_DUMP_PATH, source.dump), 'wb+') as destination:
                for chunk in data.chunks():
                    destination.write(chunk)

            return HttpResponseRedirect(reverse("movie_online_main_admin"))

    # Передаем в интерфейс данные о файле, включая форму для ручной загрузки файла на сервер
    return render_to_response('movie_online/movie_online_main_admin.html', {'form': form, 'obj': "http://megogo.net/b/partner", 'filedate': filedate, 'filepath': filepath,'filesize': filesize}, context_instance=RequestContext(request))


@never_cache
@only_superuser
def data_file_create(request):
    """Функция загружает данные с мегого 
       и сохраняет их в виде дампа на серве
    """


    # Начинаем отчет времени выполнения всей фукнции
    start = time.time()

    # Обнуляем переменные, что бы не вызывалось исключение
    filesize = 0
    filepath = None


    # Информация об источнике 
    source = ImportSources.objects.get(url='http://megogo.net/')

    # адрес АПИ мегого для получения их данных 
    url_page    = 'http://megogo.net/b/partner' 

    # читаем страницу передав ей адрес    
    url_request = urllib.urlopen(url_page)             


    # Если megogo отдал мне страницу, а не ошибку 404, 500 
    if url_request.getcode() == 200:
        # Передаем необходимые данные в функцию, которая считает и запишет на сервер 
        # данные с мегого в виде файла-дампа
        create_dump_file(source.dump, settings.API_DUMP_PATH, url_request.read()) 

    # Пробуем получить путь к файлу и его размер
    try:
        filesize = os.path.getsize(filepath) 
        filepath = '%s/%s' % (settings.API_DUMP_PATH, 'dump_megogo.xml')
    # Обнуляем значения в случае ошибки
    except: 
        filesize = 0
        filepath = None

    # Получаем размер файла
    filesize = str(int(filesize)/(1024*1024)) + ".МБ"

    # Получаем итоговое время выполнения функции
    finish = time.time()
    timer = "%.2f .min" % ((float(finish - start))/60)
 
    # Возвращаемся в интерфейс
    return render_to_response('movie_online/parsed_file.html', {'obj': url_page, 'time': timer, 'filesize':filesize, 'filepath':filepath}, context_instance=RequestContext(request))


@never_cache
@only_superuser
def data_file_open(request):
    """Функция используется для скачивания файла дампа мегого с нашего сервера.
    """
    source = ImportSources.objects.get(url='http://megogo.net/')
    return give_me_dump_please(request, source.dump, '', True)


@never_cache
@only_superuser
def parse_data_file(request):
    """Страница парсинга файла-дампа мегого.
       Вся обработчка через аякс (movie_online/ajax.py и base/static/base/js/script.js)
    """
    return render_to_response('movie_online/parse_data_file.html', {}, context_instance=RequestContext(request))


@never_cache
@only_superuser
def parse_data_identification(request):
    """Страница парсинга файла-дампа мегого.
       Вывоид список фильмов, к-е не проходили процедуру индентификации отмеченны в базе как (afisha_id=None)
       Подготавливает интерфейс, вся обработка через аякс (movie_online/ajax.py и base/static/base/js/script.js)
    """

    # Готовим переменные для хранения данных о фильме
    name = "" 
    parsed_data = {}
    
    # Делаем выборку из базы на фильмы не проходившие идентификацию
    data = MovieMegogo.objects.filter(afisha_id__in=(0, None))

    # Готовим список фильм на идентификацию в виде словаря и передаем в интерфейс
    count = 0
    for i in data:
        count += 1
        parsed_data[i.megogo_id] = "%s (%s)" % (i.title, i.year) 
    
    # Возвращаемся в интерфейс со списком фильмов для идентификации
    return render_to_response('movie_online/parse_data_identification.html', {'p_data': parsed_data, 'count': count}, context_instance=RequestContext(request))

