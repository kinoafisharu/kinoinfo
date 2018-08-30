 #-*- coding: utf-8 -*-
import operator
import os
import time 
import urllib
import datetime
import codecs
import random

from django.shortcuts import HttpResponse, render_to_response, HttpResponseRedirect, RequestContext
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
from django.db.models import Q

from kinoinfo_folder.func import del_separator, del_screen_type, low
from release_parser.views import film_identification
from user_registration.func import only_superuser
from movie_online.IR import check_int_rates, check_int_rates_inlist
from base.models import *
from api.models import *

 

@only_superuser 
@never_cache
def movie_online_admin(request):
    """Амин панель
       Возможность ручного запуска парсера
       Отчистка модели
       Просмотр логов
    """
    value = "!#@#!@# ADMIN PANEL !@#!@#"
     
    return render_to_response('movie_online/admin_main.html', { 'value': value }, context_instance=RequestContext(request))


#def rel(*x):
   # """Что бы на сервер мог определять путь к файлам (тхт логи и тп.)
   # """
   # return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


def error_func(send, **kwargs):
    """Функция используется для вывовда данных в лог
    """
    my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_log.txt') 
  
    text_log = open(my_path, 'a')  # открываем файл с логами, для записи в конец файла (атрибут "а")
    log_size = os.path.getsize(my_path)  # получаем размер файла с логами
    text_log.seek(log_size)  # переходим в конец файла, что бы каждый раз данные при записи перезаписывывались, не накладывались друг на друга
    try:
        text_log.writelines("%s" % send + '\n')  # записываем полученные данные в лог
    finally:
        text_log.close()
  


@only_superuser
@never_cache
def movie_logs(request, *args):
    """Страница с логами 
    Используется для вывода логов из файла (error_log.txt)
    """
    my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_log.txt') 
    f = open(my_path, 'r')
    #f = open(rel("error_log.txt"), 'r')  
    text = f.read().replace('\n', '<br />') 
    f.close()
    return render_to_response('movie_online/movie_logs.html', {'text': text}, context_instance=RequestContext(request)) 


@only_superuser
@never_cache
def clear_model(request):
    """Отчищает модель от всех записей
    """
    clear = MovieMegogo.objects.all().delete()

    text = ' Все данные удалены' + '\n'

    return render_to_response('movie_online/admin_main.html', {'text': text}, context_instance=RequestContext(request)) 


@only_superuser
@never_cache
def clear_logs(request):
    """Отчищает логи
    """
    my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_log.txt') 
    f = open(my_path, 'w').write(" ")


    # open(rel("error_log.txt"), 'w').write(" ")

    text = ' Все данные удалены' + '\n'

    return render_to_response('movie_online/admin_main.html', {'text': text}, context_instance=RequestContext(request)) 


@only_superuser
@never_cache
def model_in_log(request):
    """Выводит содержимое модели в лог
    """
    count = 0
    
    m = MovieMegogo.objects.all()
    for i in m:
        
        count += 1 
        error_func(" %s " % count + i.title.encode('utf-8') + " afisha_id - %s " % i.afisha_id + '\n')
        
       
    return redirect('movie_logs') 




#[Интерфейс]###################################################################################


@never_cache
def show_film_list_ajax(request,  id=None):
    """Фунция генерирует интерфейс для главнай страницы "Онлайн просмотра"
       Возвращает список фильмов, фильтры, плеер с фильмом

    """
    
    current_site = request.current_site
    current_language = translation.get_language()
    
    load_countries = ['Зарубежные', 'Наши'] 
    load_years = ['Новинки','Недавние','Старые']
    
    # текущий год
    now_year = datetime.datetime.now().year
    
    years_filter = {
        'Новинки': {'year__gte': now_year - 2},
        'Недавние': {'year__gte': now_year - 12, 'year__lt': now_year - 2},
        'Старые': {'year__lt': now_year - 12}
    }
    
    s_years = 'Новинки'
    s_countries = 'Зарубежные'
    
    if request.POST:
        id = None  # что бы не получать в функцию выбранный фильм для отображения(речь о slideblock)
        if 'selected_countries' in request.POST:
            s_countries = request.POST['selected_countries'].encode('utf-8')
        if 'selected_years' in request.POST:
            s_years = request.POST['selected_years'].encode('utf-8') 
    
    filter = years_filter.get(s_years, {'year__gte': now_year - 2})
    filter['rel_ignore'] = False

    if s_countries == 'Зарубежные':
        megogo_ids = list(MovieMegogo.objects.exclude(Q(country__icontains='Россия') | Q(country__icontains='Украина') | Q(country__icontains='Беларусь') | Q(country__icontains='СССР') | Q(afisha_id=0) | Q(afisha_id=None)).filter(**filter).values_list('afisha_id', flat=True))
    else:
        megogo_ids = list(MovieMegogo.objects.exclude(Q(afisha_id=0) | Q(afisha_id=None)).filter(Q(country__icontains='Россия') | Q(country__icontains='Украина') | Q(country__icontains='Беларусь') | Q(country__icontains='СССР'), **filter).values_list('afisha_id', flat=True))
    
    nowru = list(Nowru.objects.exclude(Q(kid=None) | Q(kid__in=megogo_ids)).filter(**filter).values_list('kid', flat=True))
    
    tvzavr = list(SourceFilms.objects.filter(source_obj__url='http://www.tvzavr.ru/').filter(**filter).values_list('kid', flat=True))
    
    ids = set(megogo_ids + nowru + tvzavr)
    
    
    if s_countries == 'Зарубежные':
        film_list = list(Film.objects.using('afisha').exclude(Q(country__name='Россия') | Q(country__name='Украина') | Q(country__name='Беларусь') | Q(country__name='СССР')).filter(pk__in=ids).values_list('id', flat=True))
    else:
        film_list = list(Film.objects.using('afisha').filter(Q(country__name='Россия') | Q(country__name='Украина') | Q(country__name='Беларусь') | Q(country__name='СССР'), pk__in=ids).values_list('id', flat=True))
        
    # Проверка что бы не вернуть пользователю пустой список
    
    #len(film_list) <= 1
    #my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_film_list.txt') 
    #open(my_path, 'a').write("Exception - %s" % film_list + '\n') 
    #film_list = Get_film_list(None, None, False)  
    #if film_list is None:
     #   film_list = ""        


    # если укр то фильмы будут выводиться с укр названиями

    fnames_dict = {} 
    t = '' 
    uk_films = []
    if current_site.domain == 'kinoafisha.in.ua':
        t = 'kua_'
        if current_language == 'uk':
            uk_sources = ('http://www.okino.ua/', 'http://kino-teatr.ua/')
            film_name = SourceFilms.objects.select_related('source_obj').filter(source_obj__url__in=uk_sources, kid__in=film_list)
            
            for n in film_name:

                if n.source_obj.url == 'http://www.okino.ua/' and n.name_alter:
                   if fnames_dict.get(n.kid):
                       
                        fnames_dict[n.kid]['names'].append(n.name_alter)
                   else:
                        fnames_dict[n.kid] = {'names': [n.name_alter], 'genres': [], 'rate_imdb': [], 'obj': None}
                   uk_films.append(n.kid)
                elif n.source_obj.url == 'http://kino-teatr.ua/':
                    if fnames_dict.get(n.kid):
                        fnames_dict[n.kid]['names'].append(n.name)
                    else:
                        fnames_dict[n.kid] = {'names': [n.name], 'genres': [], 'rate_imdb': [], 'obj': None}
                    uk_films.append(n.kid)

    film_name = FilmsName.objects.using('afisha').select_related('film_id', 'film_id__genre1', 'film_id__genre2', 'film_id__genre3', 'film_id__imdb').filter(type=2, film_id__id__in=film_list, status=1).order_by('-type')

    for n in film_name:
        if n.film_id_id not in uk_films:
            if fnames_dict.get(n.film_id_id):
                fnames_dict[n.film_id_id]['names'].append(n.name)
            else:
                fnames_dict[n.film_id_id] = {'names': [n.name], 'genres': [], 'rate_imdb': n.film_id.imdb, 'obj': n.film_id}
        else:
            fnames_dict[n.film_id_id]['rate_imdb'] = n.film_id.imdb
            
        if not fnames_dict[n.film_id_id]['genres']:
            genres = [n.film_id.genre1, n.film_id.genre2, n.film_id.genre3]
            for i in genres:
                if i:
                    fnames_dict[n.film_id_id]['genres'].append(i.name)
 

    # делаем список с данными о фильме, для передачи в шаблон
    kinoinfo_film = []
    rates = check_int_rates_inlist(fnames_dict.keys())

    for k, v in fnames_dict.iteritems():
        
        name_ru = (sorted(v['names'], reverse=True))
        name_ru = name_ru[0]
        rate = float(v['rate_imdb'].replace(',','.')) if v['rate_imdb'] else 0

        # получит интегральную оценку
        xrate = rates.get(k, {'int_rate': 0, 'show_ir': 0, 'show_imdb': 0, 'rotten': 0})

        kinoinfo_film.append({'name': name_ru, 'kid': k, 'genres': v['genres'], 'rate': xrate['int_rate'], 'show_ir': xrate['show_ir'], 'show_imdb': xrate['show_imdb'], 'rotten': xrate['rotten']})

 
    if kinoinfo_film:
        kinoinfo_film = sorted(kinoinfo_film, key=operator.itemgetter('rate'), reverse=True)
    
    # для slideblock проверяем получен ли в функцию айди фильма для отображения
    if id is None:
        # отобразит фильм, который загрузится первым
        first_load_film = kinoinfo_film[0]['kid'] if kinoinfo_film else None   
    else:
        first_load_film = id

    tmplt = 'movie_online/film_list_ajax.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/movie_online/film_list_ajax.html'

    return render_to_response(tmplt, {'countries': load_countries, 'selected_countries': s_countries, 'years': load_years, 'selected_years': s_years, 'data': kinoinfo_film,  'first_load_film': first_load_film, }, context_instance=RequestContext(request))
   

def get_film_player(id, mobile=False):
    """Функция для проверки идентифицирован ли фильм киноафиши с фильмом мегого
       вызывается из аякса release_parser/ajax.py
       На входе получает id киноафиши
       На выходе соответствующий этому id, id мегого
    """
    player = None
    source = None
    
    width, height = (250, 180) if mobile else (350, 230)

    try:
        obj = SourceFilms.objects.get(source_obj__url="http://www.tvzavr.ru/", kid=id, rel_ignore=False)
        source = obj.source_obj_id
        player = '<iframe width="%s" height="%s" src="http://mgm.iframe.tvzavr.ru/action/window/%s??autoplay=0" frameborder="0" allowfullscreen></iframe>' % (width, height, obj.source_id)
    except SourceFilms.DoesNotExist: pass

    if not player:
        players = MovieMegogo.objects.filter(afisha_id=id, rel_ignore=False)
        if players:
            player = '<iframe width="%s" height="%s" src="http://megogo.net/e/%s" frameborder="0" allowfullscreen></iframe>' % (width, height, players[0].megogo_id)
            source = 29
    
    if not player:
        try:
            player = Nowru.objects.get(kid=id, rel_ignore=False).player_code
            player = player.replace('height="480"', 'height="%s"' % height).replace('width="852"', 'width="%s"' % width)#.replace('scrolling="no"', '')
            source = 9
        except Nowru.DoesNotExist: pass

    return player, source




#####################################################################################################################################################
   
