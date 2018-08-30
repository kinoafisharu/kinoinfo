# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$', 'forums.views.women', name='women_forum'),
    url(r'^topic/(?P<topic>\d+)/$', 'forums.views.women', name='women_forum'),
    url(r'^settings/$', 'forums.views.settings_save', name='women_forum_settings'),
    url(r'^addfile/$', 'forums.views.addfile', name='women_forum_addfile'),
    url(r'^logout/$', 'forums.views.wf_logout', name='women_forum_logout'),
    url(r'^banner/$', 'forums.views.wf_banner', name='women_forum_banner'),
    url(r'^string/$', 'forums.views.wf_string', name='women_forum_string'),

    url(r'^(?P<m>\w+)/$', 'forums.views.women', name='women_forum'),
    url(r'^(?P<m>\w+)/topic/(?P<topic>\d+)/$', 'forums.views.women', name='women_forum'),
    url(r'^(?P<m>\w+)/settings/$', 'forums.views.settings_save', name='women_forum_settings'),
    url(r'^(?P<m>\w+)/addfile/$', 'forums.views.addfile', name='women_forum_addfile'),
    url(r'^(?P<m>\w+)/logout/$', 'forums.views.wf_logout', name='women_forum_logout'),
    url(r'^(?P<m>\w+)/banner/$', 'forums.views.wf_banner', name='women_forum_banner'),
    url(r'^(?P<m>\w+)/string/$', 'forums.views.wf_string', name='women_forum_string'),

    #url(r'^xget_forum_topic/$', 'forums.views.xget_forum_topic', name='xget_forum_topic'),
)

