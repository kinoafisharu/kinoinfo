# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
	url(ur'^list/$', 'person.views.get_person_list', name='get_person_list'),
    url(ur'^list/(?P<char>.*)/$', 'person.views.get_person_list', name='get_person_list'),

    url(r'^(?P<id>\d+)/$', 'person.views.get_person', name='get_person'),
	url(r'^delete/$', 'person.views.delete_person', name='delete_person'),
    url(r'^create_new/$', 'person.views.create_person', name='create_person'),
    
    
)

