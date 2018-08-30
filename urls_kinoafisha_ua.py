# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import FilmsFeed, ArticlesFeed, ReleasesFeed

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    # сервисное меню
    #url(r'^$', 'kinoafisha_ua.views.homepage', name='main'),

    url(r'^rss/schedules/(?P<city>\w+)/$', FilmsFeed(), name='rss'),
    url(r'^rss/articles/$', ArticlesFeed(), name='rss_articles'),
    url(r'^rss/releases/$', ReleasesFeed(), name='rss_releases'),
    
    (r'^movie_online/', include('movie_online.urls')),
    
    # api
    (r'^api/', include('api.urls')),

    # передвигаемые блоки
    (r'^', include('slideblok.urls')),

    # авторизация/регистрация
    (r'^user/', include('user_registration.urls')),
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    
    # парсер релизов
    (r'^releases/', include('release_parser.urls')),
    
    # сеансы
    url(r'^schedule/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    
    # статьи
    (r'^articles/', include('articles.urls')),

    # текстовый редактор
    (r'^tinymce/', include('tinymce.urls')),
    
    # обратная связь
    (r'^feedback/', include('feedback.urls')),
    
    # текстовый редактор
    (r'^tinymce/', include('tinymce.urls')),

    # админ панель киноафиша
    (r'^kinoafisha/admin/', include('release_parser.kinoafisha_admin_urls')),
    
    # трейлеры
    #(r'^trailers/', include('trailers.urls')),

    (r'^i18n/', include('django.conf.urls.i18n')),

    # адмынька
    (r'^admin/', include(admin.site.urls)),
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
