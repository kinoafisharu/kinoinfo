# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    
    url(r'^$', 'linkanoid.views.inform', name='linkanoid_inform'),
    
    url(r'^(?P<id>\d+)/$', 'linkanoid.views.inform', name='linkanoid_inform_view'),
    url(r'^(?P<id>\d+)/delete/$', 'linkanoid.views.inform_post_del', name='linkanoid_inform_del'),
    
)

