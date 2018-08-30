# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from api.views import *

urlpatterns = patterns('',
    url(r'^$', 'api.views.main', name='main_api'),
    
    url(r'^download/(?P<method>\w+)/$', 'api.views.download', name='download'),
    url(r'^download/(?P<method>\w+)/(?P<param>\w+)/$', 'api.views.download', name='download'),
   
    url(r'^panel/edit_api_description/$', 'api.panel.edit_api_description', name='edit_api_description'),
    url(r'^panel/change_background/$', 'api.panel.change_background', name='change_background'),
    url(r'^panel/api_users/$', 'api.panel.api_users_2', name='api_users'),
    url(r'^panel/get_user_request_list/$', 'api.panel.get_user_request_list', name='get_user_request_list'),
    url(r'^panel/get_user_request_list/(?P<rows>\w+)/$', 'api.panel.get_user_request_list', name='get_user_request_list'),
    url(r'^panel/get_user_list/$', 'api.panel.get_user_list', name='user_list'),
    url(r'^panel/daniya_films/$', 'api.panel.daniya_films', name='daniya_films'),

    url(r'^details/(?P<method>\w+)/$', 'api.views.get_details', name='get_details'),
    
    url(r'^schedule/$', 'api.views.show_method', {'method': content_schedule}, name='schedule'),
    url(r'^schedule/v2/$', 'api.views.show_method', {'method': content_schedule_v2}, name='schedule_v2'),
    url(r'^schedule/v3/$', 'api.views.show_method', {'method': content_schedule_v3}, name='schedule_v3'),
    url(r'^schedule/v4/$', 'api.views.show_method', {'method': content_schedule_v4}, name='schedule_v4'),
    
    url(r'^cinema/$', 'api.views.show_method', {'method': content_cinema}, name='cinema'),
    url(r'^film/$', 'api.views.show_method', {'method': content_film}, name='film'),
    url(r'^persons/$', 'api.views.show_method', {'method': content_persons}, name='persons'),
    url(r'^hall/$', 'api.views.show_method', {'method': content_hall}, name='hall'),
    url(r'^country_dir/$', 'api.views.show_method', {'method': content_country_dir}, name='country_dir'),
    url(r'^city_dir/$', 'api.views.show_method', {'method': content_city_dir}, name='city_dir'),
    url(r'^hall_dir/$', 'api.views.show_method', {'method': content_hall_dir}, name='hall_dir'),
    url(r'^genre_dir/$', 'api.views.show_method', {'method': content_genre_dir}, name='genre_dir'),
    url(r'^metro_dir/$', 'api.views.show_method', {'method': content_metro_dir}, name='metro_dir'),
    url(r'^theater/$', 'api.views.show_method', {'method': content_theater},  name='theater'),
    url(r'^screens/$', 'api.views.show_method', {'method': content_screens, 'ver': 1}, name='screens'),
    url(r'^screens/v2/$', 'api.views.show_method', {'method': content_screens, 'ver': 2}, name='screens_v2'),
    url(r'^imovie/$', 'api.views.show_method', {'method': content_imovie}, name='imovie'),
    url(r'^films_name/$', 'api.views.show_method', {'method': content_films_name}, name='films_name'),
    url(r'^imdb_rate/$', 'api.views.show_method', {'method': content_imdb_rate}, name='imdb_rate'),
    url(r'^movie_reviews/$', 'api.views.show_method', {'method': content_movie_reviews}, name='movie_reviews'),
    url(r'^film_posters/$', 'api.views.show_method', {'method': content_film_posters}, name='film_posters'),
    url(r'^film_trailers/$', 'api.views.show_method', {'method': content_film_trailers}, name='film_trailers'),
    url(r'^releases_ua/$', 'api.views.show_method', {'method': content_releases_ua}, name='releases_ua'),
    url(r'^all_films/$', 'api.views.show_method', {'method': content_all_films}, name='allfilms'),
    
    url(r'^actions_log/$', 'api.views.content_actions_log', name='actions_log'),

    url(r'^dump/schedule/$', 'api.views.dump_schedule', name='dump_schedule'),
    url(r'^dump/schedule/v2/$', 'api.views.dump_schedule_v2', name='dump_schedule_v2'),
    url(r'^dump/schedule/v4/$', 'api.views.dump_schedule_v4', name='dump_schedule_v4'),
    url(r'^dump/cinema/$', 'api.views.dump_cinema', name='dump_cinema'),
    url(r'^dump/film/(?P<year>\w+)/$', 'api.views.dump_film', name='dump_film'),
    url(r'^dump/persons/$', 'api.views.dump_persons', name='dump_persons'),
    url(r'^dump/hall/$', 'api.views.dump_hall', name='dump_hall'),
    url(r'^dump/country_dir/$', 'api.views.dump_country_dir', name='dump_country_dir'),
    url(r'^dump/city_dir/$', 'api.views.dump_city_dir', name='dump_city_dir'),
    url(r'^dump/hall_dir/$', 'api.views.dump_hall_dir', name='dump_hall_dir'),
    url(r'^dump/genre_dir/$', 'api.views.dump_genre_dir', name='dump_genre_dir'),
    url(r'^dump/metro_dir/$', 'api.views.dump_metro_dir', name='dump_metro_dir'),
    url(r'^dump/theater/$', 'api.views.dump_theater', name='dump_theater'),
    url(r'^dump/screens/$', 'api.views.dump_screens', {'ver': 1}, name='dump_screens'),
    url(r'^dump/screens/v2/$', 'api.views.dump_screens', {'ver': 2}, name='dump_screens_v2'),
    
    url(r'^dump/imovie/$', 'api.views.dump_imovie', name='dump_imovie'),
    url(r'^dump/films_name/$', 'api.views.dump_films_name', name='dump_films_name'),
    url(r'^dump/imdb_rate/$', 'api.views.dump_imdb_rate', name='dump_imdb_rate'),
    url(r'^dump/movie_reviews/$', 'api.views.dump_movie_reviews', name='dump_movie_reviews'),
    url(r'^dump/film_posters/$', 'api.views.dump_film_posters', name='dump_film_posters'),
    url(r'^dump/film_trailers/$', 'api.views.dump_film_trailers', name='dump_film_trailers'),
    url(r'^dump/releases_ua/$', 'api.views.dump_releases_ua', name='dump_releases_ua'),
    url(r'^dump/all_films/$', 'api.views.dump_all_films', name='dump_allfilms'),

    
    url(r'^widget/schedule/$', 'api.widgets.schedule_widget', name='schedule_widget'),
    url(r'^widget_test/$', 'api.widgets.widget_test', name='widget_test'),

    # для мобильного приложения
    url(r'^mobile/film/(?P<id>\d+)/$', 'api.views.mobile_film', name='mobile_film'),
    
    # очистка постеров вручную для мобильного апи
    url(r'^cron_func/api_img_tmp_delete/$', 'api.views.cron_func',  {'method': api_img_tmp_delete}, name='cron_func'),
    
    #url(r'^kinohod_stat/$', 'api.views.screens_kinohod_stat', name='screens_kinohod_stat'),
    
    url(r'^statistics_main/$', 'api.views.statistics_main', name='statistics_main'),
    
    url(r'^ip_statistics/$', 'api.panel.get_api_request_statistic', name='get_api_request_statistic'),

    url(r'^cities_relations/$', 'api.views.cities_relations', name='cities_relations'),
    
    url(r'^toru/$', 'api.views.switch_to_ru', name='switch_to_ru'),
    url(r'^toen/$', 'api.views.switch_to_en', name='switch_to_en'),
    url(r'^api_dev/$', 'api.views.api_dev', name='api_dev'),
    url(r'^panel/edit_api_dev/$', 'api.panel.edit_api_dev', name='edit_api_dev'),

    url(r'^set_api_cron/$', 'api.views.set_api_cron', name='set_api_cron'),
    url(r'^dump_visible/(?P<method>\w+)/$', 'api.views.dump_visible', name='dump_visible'),
    url(r'^api_users/$', 'api.views.api_users_2017', name='api_users_2017'),
    url(r'^api_users_new/$', 'api.views.api_users_2017_new', name='api_users_2017_new'),
    url(r'^unblock_api_user/(?P<userid>\w+)/$', 'api.views.unblock_api_user', name='unblock_api_user'),
    url(r'^api_user_edit/$', 'api.views.api_user_edit', name='api_user_edit'),
    url(r'^get_user_request_list2017/$', 'api.views.get_user_request_list2017', name='get_user_request_list2017'),
    url(r'^get_user_request_list2017/(?P<rows>\w+)/$', 'api.views.get_user_request_list2017', name='get_user_request_list2017'),
    url(r'^get_one_user_request_list/$', 'api.views.get_one_user_request_list', name='get_one_user_request_list'),
    url(r'^get_one_user_request_list/(?P<id>\w+)/$', 'api.views.get_one_user_request_list', name='get_one_user_request_list'),

)
