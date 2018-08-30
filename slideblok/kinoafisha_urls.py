# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'slideblok.views.week_releases', {'rtype': 'future'}, name='kinoafisha_main'),
    url(r'^past/$', 'slideblok.views.week_releases', {'rtype': 'past'}, name='kinoafisha_past'),
    
    url(r'^schedules/$', 'slideblok.views.schedules', name='kinoafisha_schedules'),

    #url(r'^wf/$', 'slideblok.views.wf', name='kinoafisha_wf'),
    url(r'^soon/$', 'slideblok.views.soon', name='kinoafisha_soon'),
    url(r'^soon/fr/$', 'slideblok.views.soon_fr', name='kinoafisha_soon_fr'),
    url(r'^boxoffice/(?P<country>\w+)/$', 'slideblok.views.boxoffice', name='boxoffice'),
    url(r'^online/$', 'slideblok.views.online', name='online'),
    url(r'^reviews/$', 'slideblok.views.reviews', name='kinoafisha_reviews'),
    url(r'^reviews/(?P<id>\d+)/$', 'slideblok.views.reviews', name='kinoafisha_reviews'),
    url(r'^opinions/$', 'slideblok.views.opinions', name='kinoafisha_opinions'),
    url(r'^best/schedules/$', 'slideblok.views.best_schedules', name='best_schedules'),
    url(r'^best/top250/$', 'slideblok.views.best_top250', name='best_top250'),
    
    url(r'^news/$', 'slideblok.views.kinoafisha_news', {'ntype': '17'}, name='kinoafisha_news'),
    url(r'^news/(?P<id>\d+)/$', 'slideblok.views.kinoafisha_news', {'ntype': '17'}, name='kinoafisha_news'),
    url(r'^news/world/$', 'slideblok.views.kinoafisha_news', {'ntype': '18'}, name='kinoafisha_world_news'),
    url(r'^news/world/(?P<id>\d+)/$', 'slideblok.views.kinoafisha_news', {'ntype': '18'}, name='kinoafisha_world_news'),
    url(r'^news/russia/$', 'slideblok.views.kinoafisha_news', {'ntype': '19'}, name='kinoafisha_russia_news'),
    url(r'^news/russia/(?P<id>\d+)/$', 'slideblok.views.kinoafisha_news', {'ntype': '19'}, name='kinoafisha_russia_news'),
    

    url(r'^rambler_test/$', 'slideblok.views.rambler_test', name='rambler_test'),

    # old url
    url(r'^ratingi(?P<id>\d+).png', 'base.views.kinoafisha_old_button', name='kinoafisha_old_button'),
    url(r'^gather_table.php/$', 'slideblok.views.old_boxoffice'),

)
