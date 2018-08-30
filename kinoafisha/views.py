#-*- coding: utf-8 -*- 
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from bs4 import BeautifulSoup
from base.models_dic import *
from base.models import *
from kinoafisha.func import *
from kinoafisha.forms import *
from kinoinfo_folder.views import save_schedule, create_hallname, create_hall
from kinoinfo_folder.func import low, capit, del_screen_type, del_separator, logger
import datetime
import time
import urllib
import json
from user_registration.func import login_counter, only_superuser, org_peoples


def save_sms_sources(request):
    '''
    Парсер файла sms.txt
    '''
    # получаю объект для русского языка
    lang = Language.objects.get(pk=1)
    list_all = []
    sms_file = open(rel('sources/sms.txt'), 'r')
    # получаю данные из файла
    for line in sms_file.read().split('\n'):
        listt = []
        for i, l in enumerate(line.split('\t')):
            if i == 1: listt.append(capit(low(l)))
            elif i == 2: listt.append(l.split(' ')[0])
            elif i == 4: listt.append(l)
        # складываю данные в список
        list_all.append(listt)
    sms_file.close()
    # получаю объект для источника sms
    source = ImportSources.objects.get(source='SMS')
    # иду по списку с данными
    for l in list_all:
        try:
            if l[1] != 'ЗАКРЫТ':
                # очищаю название от спец.символов
                slug_city = low(del_separator(l[1]))
                # ищу по очищенному названию
                try: city = City.objects.get(name__name=slug_city)
                except City.DoesNotExist:
                    # если не найдено, то ищу по названию из источника
                    try: city = City.objects.get(name__name=l[1])
                    except City.DoesNotExist:
                        # если не найдено, то ищу по названию из источника в нижнем регистре
                        try: city = City.objects.get(name__name=capit(low(l[1])))
                        except City.DoesNotExist: city = None
                if city:
                    # очищаю название от спец.символов
                    slug_cinema = low(del_separator(l[0]))
                    # ищу по очищенному названию
                    try: cinema = Cinema.objects.get(name__name=slug_cinema, city=city.id)
                    except Cinema.DoesNotExist:
                        # если не найдено, то ищу по названию из источника
                        try: cinema = Cinema.objects.get(name__name=l[0], city=city.id)
                        except Cinema.DoesNotExist: cinema = None
                    if cinema:
                        # получаю/создаю залы для этого кинотеатра в этом городе
                        name1 = create_hallname(1, lang, 'без указания зала')
                        name2 = create_hallname(2, lang, 'безуказаниязала')
                        hall = create_hall((name1, name2), 0, 0, cinema)
                        # записываю url источника в БД, для последующего получения данных о сеансах
                        try: HallsSources.objects.get(id_hall=hall, source=source, url_hall_sources=l[2])
                        except HallsSources.DoesNotExist: HallsSources(id_hall=hall, source=source, url_hall_sources=l[2]).save()
                    else:
                        # если не найден кинотеатр, то запись в лог
                        logger(**{'event': 2, 'code': 2, 'bad_obj': l[0], 'obj1': l[1], 'obj2': l[2], 'extra': city.id})
                else:
                    # если не найден город, то запись в лог
                    logger(**{'event': 2, 'code': 1, 'bad_obj': capit(low(l[1])), 'obj2': l[2]})
        except IndexError: pass
    return HttpResponseRedirect(reverse("main_kai"))
    

def sms(url, page, source_name):
    '''
    Парсер источника sms
    '''
    fdate = get_ftd_date('%Y-%m-%d')
    # считываю данные страницы
    page_data = BeautifulSoup(page.read(), from_encoding="utf-8")
    content = ''
    # если есть данные, получаю их
    if page_data.findAll('data'):
        for tag in page_data.findAll('data'):
            data = tag['value']
            # беру сеансы для текущего числа
            if data >= fdate:
                for f in tag.findAll('film'): 
                    film_name = f['title'].strip()
                    for s in f.findAll('seans'):
                        time = '%s %s:00' % (data, s['time'])
                        # сохраняю в файл с именем дата_IDзала
                        content += '%s\t%s\t%s\t%s\n' % (time, url.id_hall_id, film_name, url.url_hall_sources)
                        files = open(rel('sources/%s/%s_%s' % (source_name, url.id_hall_id, fdate)),'w').write(str(content.encode('utf-8')))
    else:
        # если данных нет
        pass
        #logger(**{'event': 3, 'code': 2, 'bad_obj': url.url_hall_sources, 'obj1': url.id})

'''
# rambler
def rambler(url, page, source_name):
    page_data = BeautifulSoup(page.read(), from_encoding="utf-8")
    content = ''
    for tr in soup.findAll('tr', {'class': 'b-result-table__row'}):
        pass

# yandex
def yandex(s, page, so):
    date = get_ftd_date('%Y-%m-%d')
    content = ''
    cinema = Cinema.objects.get(id=s.cinema_id)
    soup = BeautifulSoup(page.read(), from_encoding="utf-8")
    for table in soup.findAll('table', {'class' : 'b-schedule-table b-schedule-table_header_yes b-schedule-table_type_place'}):
        count1 = 0
        for tr in table.findAll('tr'):
            if count1 == 1:
                count2 = 0
                fflag = 0
                for td in tr.findAll('td'):
                    # фильм
                    if count2 == 0:
                        film_n = td.a.string.encode('utf-8').strip()
                        film_obj = get_name_film_obj(film_n)
                        if film_obj:
                            pass
                        else:
                            film_obj = get_alter_film(film_n)
                            if film_obj:
                                pass
                            else:
                                schedule_log(3, film_n, 0, 0, so.id, 'save')
                        if film_obj:
                            fi = get_about_film_obj(film_obj)
                            fflag = 1
                        count2 += 1
                    # время
                    else:
                        if fflag > 0:
                            for t in td.findAll('span'):
                                time = date + ' ' + str(t.string.encode('utf-8')) + ':00'
                                content += str(time) + '\t' + str(film_obj[0].name.encode('utf-8')) + '(id:'+ str(fi.id) +')\n'
                                # -- cinema.id исправить на hall.id
                                open(rel('sources/' + str(so.name) + '/' + str(cinema.id)), 'w').write(str(content))
                                count2 = 0
                count1 = 0
            count1 += 1
'''

def get_source_response(u):
    '''
    Проверка url на ошибки
    '''
    try:
        # получаю страницу
        page = urllib.urlopen(u.url_hall_sources)
        # если страница недостпна, то запись в лог
        if page.getcode() == 404: logger(**{'event': 3, 'code': 1, 'bad_obj': u.url_hall_sources, 'obj1': u.id})
        # иначе возвращаю страницу
        elif page.getcode() == 200: return page
    except IOError: logger(**{'event': 3, 'code': 1, 'bad_obj': u.url_hall_sources, 'obj1': u.id})
    return None


@never_cache
def get_source_data(request, source_id):
    '''
    Получение данных из источников
    '''
    # засекаю  время начала выполнения скрипта
    t1 = time.time()
    # файл хранит id текущего url источника (в случае остановки скрипта, начинать с этого url)
    counter = open(rel('sources/counter_hallssources'), 'r').read()
    url = HallsSources.objects.filter(source__id=source_id, pk__gt=counter)
    source_name = ''
    # получаю название источника и создаю директорию с этим именем
    for j in url:
        source_name = j.source.source
        try: os.makedirs(rel('sources/' + source_name))
        except OSError: pass
        break
    t = 30 # кол-во записей для sleep
    for i, u in enumerate(url):
        # получаю страницу
        page = get_source_response(u)
        if page:
            if source_id == '3':
                # для источника sms
                sms(u, page, source_name)
            elif source_id == '4':
                # для источника yandex
                yandex(u, page, source_name)
        # каждую 30 запись засыпаю на 2 сек.
        if i == t:
            time.sleep(3.0)
            t += t
        # проверяю время выполнения скрипта, если равен или привышает 50 сек, 
        # то останавляиваю и предлагаю запустить его опять (обновить страницу) 
        if float(time.time()-t1) >= 50.0:
            # записываю в файл id текущего url
            open(rel('sources/counter_hallssources'), 'w').write(str(u.id))
            return HttpResponse('Обновите страницу')
    # записываю в файл начальное значение id url 
    open(rel('sources/counter_hallssources'), 'w').write('0')
    return HttpResponseRedirect(reverse("main_kai"))
    
    
def get_files_list():
    '''
    Список сгенерированных временных файлов с репертуарами
    '''
    files_list = []
    # получаю список фалов и возвращаю
    try: 
        path = rel('sources/SMS/')
        file_names = os.listdir(path)
        files_list = [name for name in file_names if '~' not in name]
    except OSError: pass
    return files_list
    
@never_cache    
def get_files_list_sms_schedule(request):
    '''
    Вывод списка временных файлов в шаблон
    '''
    if not request.user.is_anonymous(): login_counter(request)
    # получаю список фалов
    files_list = get_files_list()
    # узнаю кол-во фалов
    files_count = len(files_list)
    return render_to_response('kai/test_files_list.html', {'files_list': files_list, 'files_count': files_count}, context_instance=RequestContext(request))
    
    
def delete_sms_files(request):
    '''
    Удаление всех временных файлов
    '''
    if request.method == 'POST':
        # получаю список фалов
        files_list = get_files_list()
        for name in file_names:
            # удаляю
            if os.path.isfile('%s%s' % (path, name)): os.remove('%s%s' % (path, name))
    # получаю список фалов
    files_list = get_files_list()
    return HttpResponseRedirect(reverse("get_files_list_sms_schedule"))


def get_name_film_obj(film):
    '''
    Получение объекта названия фильма
    '''
    # очищаю названия от формата изображения (3D, 2D ...)
    f = del_screen_type(film)
    # очищаю названия от спец.символов и привожу в нижний регистр
    f = low(del_separator(f))
    # ищу по очищенному названию
    try: name = NameProduct.objects.filter(name=f)[0]
    except IndexError:
        # если не найден, ищу по названию источника
        try: name = NameProduct.objects.filter(name=film)[0]
        except IndexError:
            # если не найден, ищу по названию источника в нижнем регистре
            try: name = NameProduct.objects.filter(name=low(film))[0]
            except IndexError:
                # если не найден, ищу по названию источника в нижнем регистре с заглавной буквы
                try: name = NameProduct.objects.filter(name=capit(film))[0]
                except IndexError: name = None
    return name


def get_films_obj(name):
    '''
    Получение объекта фильма
    '''
    try: film = Films.objects.filter(name__name=name)[0]
    except IndexError: film = None
    return film
    
'''
# из старой БД
def get_name_film_obj(film):
    f = del_screen_type(film)
    f = low(del_separator(f))
    try: name = FilmsName.objects.using('afisha').filter(slug=f)[0]
    except IndexError:
        try: name = FilmsName.objects.using('afisha').filter(name=film)[0]
        except IndexError:
            try: name = FilmsName.objects.using('afisha').filter(name=low(film))[0]
            except IndexError:
                try: name = FilmsName.objects.using('afisha').filter(name=capit(film))[0]
                except IndexError: name = None
    return name
    
# из старой БД
def get_films_obj(name):
    try: film = FilmsName.objects.using('afisha').select_related('id_films').filter(name=name)[0]
    except IndexError: film = None
    return film.id_films
'''

@never_cache
def save_sms_schedule(request):
    '''
    Сохранение сеансов смс из файлов в БД
    '''
    # засекаю  время начала выполнения скрипта
    t1 = time.time()
    path = rel('sources/SMS/')
    fdate = get_ftd_date('%Y-%m-%d')
    # получаю список имен временных фалов с данными о сеансах
    file_names = os.listdir(path)
    # этот файл хранит названия файлов в которых фильмы были не найдены
    counter_files = open(rel('sources/counter_hallssources_files'),'r').read()
    text = ''
    content = ''
    old_hall = ''
    old_film_name = ''
    # иду по списку фалов
    for name in file_names:
        # если файл для текущего числа и его нет в counter_files
        if '~' not in name and fdate in name and name not in counter_files:
            file_schedule = open('%s%s' % (path, name),'r')
            try:
                # извлекаю данные из файла
                for lines in file_schedule.read().split('\n'):
                    line = lines.split('\t')
                    times = line[0]
                    if old_hall != line[1]:
                        # получаю объект зала
                        hall = Hall.objects.get(pk=line[1])
                        old_hall = line[1]
                    if old_film_name != line[2]:
                        # получаю объект названия фильма
                        film_name_obj = get_name_film_obj(line[2])
                        old_film_name = line[2]
                    if film_name_obj:
                        # передаю извлеченные данные и сохранию сеанс
                        save_schedule(times, hall, film_name_obj, line[2])
                    else:
                        # иначе запись в лог и в переменную для записи в файл для ненайденных
                        logger(**{'event': 3, 'code': 3, 'bad_obj': line[2], 'obj1': line[3], 'extra': name})
                        content += '%s\t%s\t%s\t%s\n' % (line[0], line[1], line[2], line[3])
            except IndexError: pass
            file_schedule.close()
            # если есть ненайденные названия фильмов, записываю обратно в файл
            if content:
                open('%s%s' % (path, name),'w').write(content)
                text += str(name) + ' '
                content = ''
            # если все ок, то удаляю временный файл
            else: os.remove('%s%s' % (path, name))
        # проверяю время выполнения скрипта, если равен или привышает 50 сек, 
        # то останавляиваю и предлагаю запустить его опять (обновить страницу) 
        if float(time.time()-t1) >= 50.0:
            # все имена файлов с ненайденными фильмами записываю в файл
            open(rel('sources/counter_hallssources_files'),'a').write(text)
            return HttpResponse('Обновите страницу')
    # все имена файлов с ненайденными фильмами записываю в файл
    open(rel('sources/counter_hallssources_files'),'a').write(text)
    return HttpResponseRedirect(reverse("main_kai"))
            

'''
def save_sms_schedule(request):
    path = rel('sources/SMS/')
    fdate = get_ftd_date('%Y-%m-%d %H-%M-%S')
    file_names = os.listdir(path)
    for name in file_names:
        if '~' not in name:
            file_schedule = open('%s%s' % (path, name),'r')
            try:
                for lines in file_schedule.read().split('\n'):
                    line = lines.split('\t')
                    time = line[0]
                    if time >= fdate:
                        hall = Hall.objects.get(pk=line[1])
                        film = Films.objects.get(pk=line[2])
                        film_name = line[3]
                        save_schedule(time, hall, film, film_name)         
            except IndexError: pass
            file_schedule.close()
    return HttpResponseRedirect(reverse("main_kai"))
'''


############################## редактор

def search(model, var, name, extra):
    '''
    Поиск
    '''
    if extra and var == 3:
        # поиск для кинотеатров
        result = model.objects.filter(name__name__contains=name, city=extra).distinct()
    else:
        # поиск для фильмов
        if var == 1: result = model.objects.filter(name__contains=name).order_by('name')
        # поиск для городов
        else: result = model.objects.filter(name__name__contains=name).distinct()
    return result
    
    
def part_search(model, var, name, extra):
    '''
    Поиск по частичному совпадению
    '''
    res_list = []
    # очищаю от формата изображения (3D, 2D ...), привожу в нижний регистр
    clear_name = low(del_screen_type(name.encode('utf-8')))
    # заменяю некоторые символы на символ пробела
    clear_name = clear_name.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('.', ' ').replace(':', ' ')
    # для городов/фильмов минимальное кол-во символов в с строке поиска должно быть не менее 3,
    # а для кинотеатров 2, иначе выведу сообщение об ошибке
    max_char = 3 if var == 1 or var == 2 else 2
    # разбиваю название по пробелу и произвожу поиск по каждой части названия
    for cn in clear_name.split(' '):
        if len(cn.decode('utf-8')) >= max_char:
            #result = model.objects.filter(name__name__contains=cn).distinct() # для новой БД
            
            # для старой БД ----
            #if var == 1:
            #    result = model.objects.filter(name__contains=cn)
            #else: result = model.objects.filter(name__name__contains=cn).distinct()
            result = search(model, var, cn, extra)
            # ------------------
            
            # результаты складываю в список и возвращаю
            for i in result:
                res_list.append(i)
    return res_list


@never_cache
def editor(request, event, code, id):
    '''
    Исправление ошибок в логе
    '''
    # удаление временного файла с данными о сеансах
    def delete_file_schedule(content):
        if content != '':
            # если после обработки файла осталась полезная информация, записываю в него
            file_sch = open(rel('sources/SMS/%s' % (extra)),'w').write(content)
            content = ''
        else:
            # если нет полезной информации, то удаляю файл
            os.remove(rel('sources/SMS/%s' % (extra)))
        # обновляю файл содержащий имена временных файлов
        file_counter = open(rel('sources/counter_hallssources_files'),'r').read()
        file_counter = file_counter.replace('%s ' % (extra), '')
        open(rel('sources/counter_hallssources_files'),'w').write(file_counter)
        
    # если метод GET
    def method_get(lang, search_msg, result, extra):
        # получаю частичные совпадения из БД
        result = part_search(model[0], model[2], name, extra) 
        return render_to_response('editor/editor.html', {'event': event, 'code': code, 'obj': name, 'result': result, 'id': id, 'lang': lang, 'search_msg': search_msg}, context_instance=RequestContext(request))
    
    # если метод POST
    def method_post(lang, search_msg, result):
        content = ''
        # если редактор удаляет запись из лога
        if 'log_del' in request.POST:
            # дополнительная обработка для имен фильмов
            if event == '1' and code == '4' or event == '3' and code == '3':
                file_sch = open(rel('sources/SMS/%s' % (extra)),'r')
                # во временном файле остаются только необходимые строки
                try:
                    for lines in file_sch.read().split('\n'):
                        line = lines.split('\t')
                        if line[2].replace('+', ' ') != name.encode('utf8'):
                            content += '%s\t%s\t%s\t%s\n' % (line[0], line[1], line[2], line[3])
                except IndexError: pass
                file_sch.close()
                # удаляю временный файл, если потребуется
                delete_file_schedule(content)
            # удаляю запись лога из БД
            Logger.objects.get(pk=id).delete()
        # если редактор производит поиск
        elif 'search' in request.POST:
            query = request.POST['search']
            # для городов/фильмов минимальное кол-во символов в с строке поиска должно быть не менее 3,
            # а для кинотеатров 2, иначе выведу сообщение об ошибке
            max_char = 3 if model[2] == 1 or model[2] == 2 else 2
            if len(query) >= max_char: result = search(model[0], model[2], query, extra) 
            else: search_msg = True
            return render_to_response('editor/editor.html', {'event': event, 'code': code, 'obj': name, 'result': result, 'id': id, 'lang': lang, 'search_msg': search_msg}, context_instance=RequestContext(request))
        # если редактор устанвлявает связь (сохранение алт.названия)
        else:
            # получаю данные
            obj = model[0].objects.get(pk=request.POST['set_rel_obj'])
            lang = Language.objects.get(pk=request.POST['set_rel_lang'])
            # если связь для фильмов
            if event == '1' and code == '4' or event == '3' and code == '3':
                file_sch = open(rel('sources/SMS/%s' % (extra)),'r')
                # извлекаю данные о сеансе из временного файла
                try:
                    for lines in file_sch.read().split('\n'):
                        line = lines.split('\t')
                        film_name = line[2].replace('+', ' ')
                        # получаю необходимую строку в файле
                        if film_name == name.encode('utf8'):
                            time = line[0]
                            # получаю объект зала
                            hall = Hall.objects.get(pk=line[1])
                            # сохраняю новое альт.название для фильма 
                            try: obj_name = model[1].objects.get(status=0, language=lang, name=line[2])
                            except model[1].DoesNotExist: obj_name = model[1].objects.create(status=0, language=lang, name=line[2])
                            # передаю извлеченные данные и сохранию сеанс
                            save_schedule(time, hall, obj_name, line[2])
                            # удаляю запись лога из БД
                            try: Logger.objects.get(pk=id).delete()
                            except Logger.DoesNotExist: pass
                        # все другие строки сохраняются дальше обратно в файл
                        else:
                            content += '%s\t%s\t%s\t%s\n' % (line[0], line[1], line[2], line[3])
                except IndexError: pass
                file_sch.close()
                # удаляю временный файл, если потребуется
                delete_file_schedule(content)
            # если связь для городов/кинотеатров
            else:
                # создаю новое альт.название для города/кинотеатра
                try: model[1].objects.get(status=0, language=lang, name=name)
                except model[1].DoesNotExist:           
                    obj_name = model[1].objects.create(status=0, language=lang, name=name)
                    # устанвляиваю связь
                    obj.name.add(obj_name)
                    # удаляю запись лога из БД
                    Logger.objects.get(pk=id).delete()
        return HttpResponseRedirect(reverse("get_log", kwargs={'event': event}))
    if not request.user.is_anonymous(): login_counter(request)
    # получаю переданные данные
    if request.method == 'GET' or request.method == 'POST':
        name = request.GET['obj']
        extra = request.GET['extra'] if 'extra' in request.GET else None
        lang = Language.objects.all()
        search_msg = False
        result = None
        #if event == '1' and code == '4' or event == '3' and code == '3': model = (Films, NameProduct) # для новой БД
        # задаю имена моделей в зависимости от события вызвавшее ошибку и запись в лог
        if event == '1' and code == '4' or event == '3' and code == '3': model = (NameProduct, NameProduct, 1) # для старой БД
        elif event == '2' and code == '1': model = (City, NameCity, 2)
        elif event == '2' and code == '2': model = (Cinema, NameCinema, 3)
    # обрабатываю данные в зависимости от метода
    if request.method == 'GET':
        return method_get(lang, search_msg, result, extra)
    elif request.method == 'POST':
        return method_post(lang, search_msg, result) 
    return HttpResponse('ошибка')


    
'''
def editor(request, event, code, id):
    def method_get():
        lang = Language.objects.all()
        result = None
        result = get_model_data(model[0], name) 
        return render_to_response('editor/editor.html', {'event': event, 'code': code, 'obj': name, 'result': result, 'id': id, 'lang': lang}, context_instance=RequestContext(request))
    def method_post():
        if 'log_del' in request.POST: 
            Logger.objects.get(pk=id).delete()
        else:
            obj = model[0].objects.get(pk=request.POST['set_rel_obj'])
            lang = Language.objects.get(pk=request.POST['set_rel_lang'])
            try: model[1].objects.get(status=0, language=lang, name=name)
            except model[1].DoesNotExist:           
                obj_name = model[1].objects.create(status=0, language=lang, name=name)
                obj.name.add(obj_name)
                Logger.objects.get(pk=id).delete()
        return HttpResponseRedirect(reverse("get_log", kwargs={'event': event}))

    if request.method == 'GET' or request.method == 'POST':
        name = request.GET['obj']
        if event == '1' and code == '4' or event == '3' and code == '3': model = (Films, NameProduct)
        elif event == '2' and code == '1': model = (City, NameCity)
        elif event == '2' and code == '2': model = (Cinema, NameCinema)
    if request.method == 'GET':
        return method_get()
    elif request.method == 'POST':
        return method_post() 
    return HttpResponse('ошибка')
'''

@only_superuser
@never_cache
def menu_visible(request, menu=None, submenu = 's00'):
    if menu is None:
        raise Http404 
    try:
        fileName = '{0}/{1}.json'.format(settings.KINOAFISHA_EXT, 'menu_settings')
        json_data = json_menu()
        menuArr = json_data['menu']
        menu_level_1 = [i for i in menuArr if (i['submenu']==submenu and i['name']==menu)]
        if len(menu_level_1):
            for x in menuArr:
                if x['submenu']==submenu and x['name']==menu:
                    x['enable'] = '1' if x['enable']=='0' else '0'

        else:
            accessDict = {}
            accessDict['name'] = str(menu)
            accessDict['submenu'] = str(submenu)
            accessDict['enable'] = '1'
            menuArr.append(accessDict)

        with open(fileName, 'w') as outfile:
            try:
                json_data['menu'] = menuArr
                jsonData = json.dumps(json_data) 
                outfile.write("%s\n" % jsonData)
            except Exception as e:
                error = str(e)
                text = ''' Напредвиденная ошибка во время сохранения настроек режима отображения меню'''
                return render_to_response('error.html', {'text': text, 'error': e}, context_instance=RequestContext(request))
        return HttpResponseRedirect(reverse('main'))
#        return render_to_response('error.html', {'text': str(get_menu_state()), 'error': 'no_error'}, context_instance=RequestContext(request))
    except Exception as e:
        error = str(e)
        text = ''' Напредвиденная ошибка во время операции по изменению режима отображения меню'''
        return render_to_response('error.html', {'text': text, 'error': e}, context_instance=RequestContext(request))
