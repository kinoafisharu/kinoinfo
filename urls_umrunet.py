# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    # сервисное меню ПОРА УДАЛЯТЬ ЭТОТ САЙТ
    url(r'^$', 'umrunet.views.homepage', name='main'),

    
    (r'^panel/', include('api.urls')),
    
    # авторизация/регистрация
    (r'^user/', include('user_registration.urls')),

    # обратная связь
    (r'^feedback/', include('feedback.urls')),

    # статьи
    (r'^articles/', include('articles.urls')),
    
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
