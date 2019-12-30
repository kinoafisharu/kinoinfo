# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import redirect_to
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import FilmsFeed, ArticlesFeed, ReleasesFeed

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    url(r'^wf/$', redirect_to, {'url': 'http://forums.vsetiinter.net/women/'}),

    url(r'^$', 'slideblok.views.week_releases', {'rtype': 'future'}, name='main'),
    url(r'^yandex_4318c3791bcdbc7f.html$', 'slideblok.views.yandex', name='yandex'),
    url(r'^google3f3c67d1889fcc48.html$', 'slideblok.views.google_verify', name='google_verify'),

    url(r'^banner/uploader/$', 'base.ajax.add_left_banner', name='add_left_banner'),
    url(r'^background/uploader/$', 'base.ajax.add_background_adm', name='add_background_adm'),
    
    # генерация кнопки для рутрекера
    url(r'^button/$', 'base.views.kinoafisha_button', name='kinoafisha_button'),
    url(r'^buttom.php/$', 'base.views.kinoafisha_button', name='kinoafisha_button'),
    
    # linkanoid
    #(r'^inform/', include('linkanoid.urls')),
    
    # search
    (r'^search/', include('base.urls')),
    
    url(r'^rss/schedules/(?P<city>\w+)/$', FilmsFeed(), name='rss'),
    url(r'^rss/articles/$', ArticlesFeed(), name='rss_articles'),
    url(r'^rss/releases/$', ReleasesFeed(), name='rss_releases'),

    # movie_online
    (r'^online/', include('movie_online.urls')),
    
    url(r'^panel/change_background/$', 'api.panel.change_background', name='change_background'),
    url(r'^panel/api_users/$', 'api.panel.api_users_2', name='api_users'),
    
    # передвигаемые блоки
    (r'^', include('slideblok.kinoafisha_urls')),

    # авторизация/регистрация
    (r'^user/', include('user_registration.urls')),
    
    url(r'^new/news/', include('news.urls')),
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
    
    # парсер релизов
    (r'^releases/', include('release_parser.urls')),
    
    # сеансы
    #url(r'^schedule/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    #url(ur'^schedule/(?P<city>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    #url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    #url(ur'^schedule/(?P<city>\w+)/(?P<cinema>\w+)/(?P<id>\w+)/$', 'release_parser.schedules.sources_schedules_list_ajax', name='schedule_ajax'),
    
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
    #(r'^admin/', include(admin.site.urls)),
    
    
    url(r'^index.php3/$', 'slideblok.views.old_kinoafisha', name='old_kinoafisha'),
    url(r'^kinoafisha/menu_visible/(?P<method>\w+)/$', 'kinoafisha.views.menu_visible', name='menu_visible'),
    url(r'^kinoafisha/menu_visible/(?P<menu>\w+)/(?P<submenu>\w+)/$', 'kinoafisha.views.menu_visible', name='menu_visible'),

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
