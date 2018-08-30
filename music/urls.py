# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    
    url(r'^$', 'music.views.main', name='main'),
    url(ur'^artist/list/(?P<char>\w+)/$', 'music.views.artist_list', name='artist_list'),
    url(r'^artist/(?P<id>\d+)/$', 'music.views.artist', name='artist'),
    
    url(r'^artist/(?P<id>\d+)/comp/list/$', 'music.views.composition_list', name='composition_list'),
    url(r'^artist/(?P<id>\d+)/comp/(?P<comp_id>\d+)/$', 'music.views.composition', name='composition'),
    
    url(r'^track/download/$', 'music.views.track_download', name='track_download'),
    
    
)

