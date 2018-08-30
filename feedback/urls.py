# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *


urlpatterns = patterns('',
    url(r'^$', 'feedback.views.main', name='feedback_main'),
  
    #url(r'^panel/$', 'feedback.views.feedback_panel', name='feedback_panel'),

)

