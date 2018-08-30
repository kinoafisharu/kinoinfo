# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('',

    url(r'^(?P<id>\d+)/$', 'news.views.news', name='news'),
    url(r'^add/$', 'news.views.news_add', name='news_add'),
    url(r'^delete/(?P<id>\d+)/$', 'news.views.news_delete', name='news_delete'),

)


