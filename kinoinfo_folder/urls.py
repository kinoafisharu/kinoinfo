#-*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from base.models import *


urlpatterns = patterns('kinoinfo.views',
    # Навигация
    # Главная страница
    url(r'^$', 'main', name='main_kai'),
    
    # Импорт из источника 'Киноафиша'
    # Справочник Страны
    url(r'^save/country_dir/$', 'save_dir', {'af': AfishaCountry, 'ki': Country}, name='save_country_dir'),
    # Справочник Жанры
    url(r'^save/genre_dir/$', 'save_dir', {'af': AfishaGenre, 'ki': Genre}, name='save_genre_dir'),
    # Справочник Метро
    url(r'^save/metro_dir/$', 'save_dir', {'af': AfishaMetro, 'ki': Metro}, name='save_metro_dir'),
    # Справочник Сети
    url(r'^save/seti_dir/$', 'save_dir', {'af': Seti, 'ki': CinemaCircuit}, name='save_seti_dir'),
    # Справочник Статус участия персоны
    url(r'^save/persons_status_dir/$', 'save_dir', {'af': PersonsTypeAct, 'ki': Action}, name='save_persons_status_dir'),
    # Справочник Тип участия персоны
    url(r'^save/persons_type_dir/$', 'save_dir', {'af': Seti, 'ki': CinemaCircuit}, name='save_persons_type_dir'),
    # Справочник Источники (Киноафиша, IMDb, SMS)
    url(r'^save/sources_dir/$', 'save_sources_dir', name='save_sources_dir'),
    # Справочник Языки
    url(r'^save/lang_dir/$', 'save_lang_dir', name='save_lang_dir'),
    # Справочник Название типа улицы
    url(r'^save/street_type_dir/$', 'save_street_type_dir', name='save_street_type_dir'),
    # Справочник Города
    url(r'^save/city_dir/$', 'save_city_dir', name='save_city_dir'),
    # Справочник Связь страны и языка
    url(r'^save/country_lang_rel/$', 'save_country_lang_rel', name='save_country_lang_rel'),
    # Кинотеатры
    url(r'^save/cinema/$', 'save_cinema', name='save_cinema'),
    # Залы
    url(r'^save/hall/$', 'save_hall', name='save_hall'),
    # Персоны
    url(r'^save/persons/$', 'save_persons', name='save_persons'),
    # Сеансы
    url(r'^save/schedule/$', 'save_kai_sch', name='save_schedule'),
    # Названия фильмов
    url(r'^save/films_name/(?P<year>\w+)/$', 'save_films_name', name='save_films_name'),
    # Фильмы
    url(r'^save/film/(?P<year>\w+)/$', 'save_film', name='save_film'),

    # Log
    # Получить лог
    url(r'^get_log/(?P<event>\d+)/$', 'get_log', name='get_log'),
    # Очистка лога
    url(r'^clear_log/$', 'clear_log', name='clear_log'),
    
    # Test
    # IP сервера
    url(r'^get_server_ip/$', 'get_server_ip', name='get_server_ip'),
    # Список фильмов
    url(r'^get_films/$', 'get_films', name='get_films'),
    # Список кинотеатров
    url(r'^get_cinema/$', 'get_cinema', name='get_cinema'),
    # Список сеансов
    url(r'^get_schedule/$', 'get_schedule', name='get_schedule'),
    # Список фильмов
    url(r'^save/films_name2/(?P<year>\w+)/$', 'save_films_name2', name='save_films_name2'),
    # Список названий фильмов
    url(r'^get_film_names/$', 'get_film_names', name='get_film_names'),
    # Поиск названий фильмов в старой и новой БД
    url(r'^test_search_name/$', 'test_search_name', name='test_search_name'),
    # Удаление сеансов
    url(r'^del_schedule/$', 'del_schedule', name='del_schedule'),

)
urlpatterns += patterns('kinoinfo.func',
    # список таблиц в БД
    url(r'^tables_list/$', 'tables_list', name='tables_list'),
)


