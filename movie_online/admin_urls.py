# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from movie_online.views import *
from movie_online.parser import *
from movie_online.IR import *




urlpatterns = patterns('',

    # Админ панель - используется для управление парсером (парсинг данных, сохраненине в модель, отчистка)
    url(r'^movie_online_admin/$', 'movie_online.views.movie_online_admin', name='movie_online_admin'),

    # Выводит содержимое файла с логами 
    url(r'^movie_logs/$', 'movie_online.views.movie_logs', name='movie_logs'),
    # Полная отчитска модели megogo
    url(r'^clear_model/$', 'movie_online.views.clear_model', name='clear_model'),
    # Отчистка логов 
    url(r'^clear_logs/$', 'movie_online.views.clear_logs', name='clear_logs'),
    # Выводит содержимое модели в лог
    url(r'^model_in_log/$', 'movie_online.views.model_in_log', name='model_in_log'),

    url(r'^movie_online_main_admin/$', 'movie_online.parser.movie_online_main_admin', name='movie_online_main_admin'),
    url(r'^data_file_create/$', 'movie_online.parser.data_file_create', name='data_file_create'),
    url(r'^data_file_open/$', 'movie_online.parser.data_file_open', name='data_file_open'),
    url(r'^parse_data_file/$', 'movie_online.parser.parse_data_file', name='parse_data_file'),
    url(r'^parse_data_identification/$', 'movie_online.parser.parse_data_identification', name='parse_data_identification'),


)
