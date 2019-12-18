# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import FilmsFeed, ArticlesFeed, ReleasesFeed
from urls_kinoafisha import robots_file

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    url(r'^robots\.txt$', robots_file, name="robots_file"),
    url(r'^kb_data_sync/$', 'release_parser.kinobilety.main', name='kb_data_sync'),
    url(r'^yandex_35c18ae022681480.html$', 'base.views.yandex', name='yandex_kinoinfo'),
    
    url(r'^spec/url/(?P<url>\w+)/$', 'base.spec.get_spec', name='get_spec'),
    url(r'^spec/url/(?P<url>\w+)/post/(?P<id>\d+)/$', 'base.spec.get_spec', name='get_spec'),
    url(r'^spec/delete/(?P<vid>\d+)/post/(?P<id>\d+)/$', 'letsgetrhythm.views.view_post_del', {'type': 'spec'}, name='spec_post_del'),

    url(r'^torrents/$', 'base.views.new_torrents', name='new_torrents'),
    url(r'^torrents/listing/(?P<source>\d+)/$', 'base.views.torrents_listing', name='torrents_listing'),
    url(r'^torrent/get/(?P<id>\d+)/$', 'base.views.get_torrent', name='get_torrent'),

    url(r'^booking/$', 'base.views.booking', name='booking'),
    url(r'^booking/article/add/$', 'base.views.booking_article_add', name='booking_article_add'),
    url(r'^booking/excel/get/$', 'base.views.booking_get_excel_doc', name='booking_get_excel_doc'),


    # search
    (r'^search/', include('base.urls')),
    
    url(r'^banner/uploader/$', 'base.ajax.add_left_banner', name='add_left_banner'),
    url(r'^background/uploader/$', 'base.ajax.add_background_adm', name='add_background_adm'),
    
    url(r'^rss/schedules/(?P<city>\w+)/$', FilmsFeed(), name='rss'),
    url(r'^rss/articles/$', ArticlesFeed(), name='rss_articles'),
    url(r'^rss/releases/$', ReleasesFeed(), name='rss_releases'),

    # movie_online
    (r'^online/', include('movie_online.urls')),
    
    # api
    (r'^api/', include('api.urls')),

    # передвигаемые блоки
    (r'^', include('slideblok.urls')),
    #(r'^Yalta/', include('slideblok.kinoafisha_urls')),
    
    # авторизация/регистрация
    (r'^user/', include('user_registration.urls')),
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    
    # парсер релизов
    (r'^releases/', include('release_parser.urls')),
    
    url(r'^news/', include('news.urls')),
    
    # сеансы
    url(r'^schedule/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/(?P<id>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    
    # админ панель киноафиша
    (r'^kinoafisha/admin/', include('release_parser.kinoafisha_admin_urls')),
    
    # статьи
    (r'^articles/', include('articles.urls')),

    # текстовый редактор
    (r'^tinymce/', include('tinymce.urls')),
    
    # обратная связь
    #(r'^feedback/', include('feedback.urls')),

    (r'^organizations/', include('organizations.urls')),
    
    (r'^film/', include('film.urls')),
    
    (r'^person/', include('person.urls')),
    
    (r'^cinema/', include('organizations.urls')),
    
    #(r'^distributor/', include('distributor.urls')),
    
    (r'^i18n/', include('django.conf.urls.i18n')),
    
    #(r'^articles/\d+-\d+-\d+/.+$', 'linkexchange_django.views.handle_request'),
    
    #url(r'', include('registration.urls')),
    
    #url(r'^ulogin/', include('django_ulogin.urls')),
     

    #(r'^admin/', include(admin.site.urls)),
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
