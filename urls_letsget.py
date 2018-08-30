# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import NewsFeed

dajaxice_autodiscover()

urlpatterns = patterns('',
    url(r'^rss/news/$', NewsFeed(), name='rss_news'),

    url(r'^', include('letsgetrhythm.urls')),
    
    url(r'^search/$', 'letsgetrhythm.views.searching_text', name='search'),
    
    url(r'^news/', include('news.urls')),
    
    url(r'^background/change/', 'api.panel.change_background', name='change_background'),

    # авторизация/регистрация
    (r'^user/', include('user_registration.urls')),
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
)
 
if settings.DEBUG:
    urlpatterns += patterns('',
       url(r'^' + settings.MEDIA_URL.lstrip('/') \
               + '(?P<path>.*)$', 'django.views.static.serve',
           {
                'document_root': settings.MEDIA_ROOT,
           }),
    )
    urlpatterns += staticfiles_urlpatterns()
