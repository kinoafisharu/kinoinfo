# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

#from base.feeds import FilmsFeed, ArticlesFeed, ReleasesFeed

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    
    (r'^', include('music.urls')),
    
    (r'^admin/', include('music.admin_urls')),
    
    url(r'^search/$', 'base.views.search', name='search'),
    
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
