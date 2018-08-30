# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from movie_online.views import *
from movie_online.parser import *
from movie_online.IR import *




urlpatterns = patterns('',

    # Главная страница для "Онлайн просмотра" - выдает список фильмов по фильрам
    url(r'^movie/$', 'movie_online.views.show_film_list_ajax', name='show_film_list'),
    url(r'^movie/(?P<id>\w+)/$', 'movie_online.views.show_film_list_ajax', name='show_film_list'),
   

)
