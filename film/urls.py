# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^list/(?P<year>\d+)$', 'film.views.get_film_list', name='get_film_list'),
    url(r'^create_new/$', 'film.views.film_create_new', name='film_create_new'),
    url(r'^delete/$', 'film.views.film_delete', name='film_delete'),

    url(r'^(?P<id>\d+)/$', 'film.views.get_film', name='get_film'),
    url(r'^(?P<id>\d+)/rating/$', 'film.views.get_film_rating', name='get_film_rating'),
    url(r'^(?P<id>\d+)/reviews/$', 'film.views.get_film_reviews', name='get_film_reviews'),
    url(r'^(?P<id>\d+)/reviews/addnew/$', 'film.views.add_film_review', name='add_film_review'),
    url(r'^(?P<id>\d+)/reviews/delrev/$', 'film.views.delete_film_review', name='delete_film_review'),
    url(r'^(?P<id>\d+)/relations/$', 'film.views.get_film_relations', name='get_film_relations'),
    url(r'^(?P<id>\d+)/boxoffice/$', 'film.views.get_film_boxoffice', name='get_film_boxoffice'),
    url(r'^(?P<id>\d+)/web/$', 'film.views.get_film_web', name='get_film_web'),
    url(r'^(?P<id>\d+)/schedule/$', 'film.views.get_film_schedules', name='get_film_schedule'),
    url(r'^(?P<id>\d+)/opinions/$', 'film.views.get_film_opinions', name='get_film_opinions'),
    url(r'^(?P<id>\d+)/trailers/$', 'film.views.get_film_trailers', name='get_film_trailers'),
    url(r'^(?P<id>\d+)/slides/$', 'film.views.get_film_slides', name='get_film_slides'),
    url(r'^(?P<id>\d+)/posters/$', 'film.views.get_film_posters', name='get_film_posters'),
    url(r'^(?P<id>\d+)/download/$', 'film.views.get_film_download', name='get_film_download'),
    url(r'^(?P<id>\d+)/download/delete/(?P<torrent_type>\d+)/(?P<torrent_id>\d+)/$', 'film.views.film_torrent_delete', name='film_torrent_delete'),
    url(r'^(?P<id>\d+)/create_rel/$', 'film.views.film_create_rel', name='film_create_rel'),
    url(r'^(?P<id>\d+)/create/$', 'film.views.film_create', name='film_create'),
    url(r'^(?P<id>\d+)/persons/$', 'film.views.film_persons', name='film_persons'),
    
    url(r'^change_film_left_banner/$', 'film.views.change_film_left_banner', name='change_film_left_banner'),
    
    url(r'^set_coord/$', 'film.views.set_coord', name='set_coord'),
    
    
)
