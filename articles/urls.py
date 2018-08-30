# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^$', 'articles.views.main', name='articles_main'),
    url(r'^post/(?P<article>\w+)/$', 'articles.views.main', name='articles_main'),
    url(r'^add/$', 'articles.views.add_article', name='add_article'),
    url(r'^edit/(?P<id>\w+)/$', 'articles.views.edit_article', name='edit_article'),
    url(r'^delete/(?P<id>\w+)/$', 'articles.views.delete_article', name='delete_article'),
)
