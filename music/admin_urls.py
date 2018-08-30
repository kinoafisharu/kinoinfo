# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    
    url(r'^$', 'music.admin.admin_main', name='admin_main'),
    url(r'^background/$', 'api.panel.change_background', name='change_background'),
    url(r'^users/$', 'api.panel.api_users_2', name='api_users'),
    url(r'^media/$', 'music.admin.admin_media', name='admin_media'),
    url(r'^media/upload/$', 'music.admin.admin_media_upload', name='admin_media_upload'),
    url(r'^media/del/$', 'music.admin.admin_media_del', name='admin_media_del'),
    
    url(r'^media/ajax/upload/$', 'music.ajax.track_upload', name='track_upload'),
    
    
)

