# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$', 'vladaalfimov.views.about', name='about'),
    url(r'^$', 'vladaalfimov.views.about', name='main'),
    
    url(r'^gallery/(?P<vid>\d+)/$', 'vladaalfimov.views.gallery', name='gallery'),
    
    url(r'^imiagroup_projects/edit/$', 'imiagroup.views.imiagroup_projects_edit', name='imiagroup_projects_edit'),
    url(r'^imiagroup_projects/delete/$', 'imiagroup.views.imiagroup_projects_delete', name='imiagroup_projects_delete'),

    #localhost
    #url(r'^view/77/$', 'imiagroup.views.imiagroup_projects', name='imiagroup_projects'),
    #url(r'^view/121/$', 'imiagroup.views.imiagroup_projects', name='imiagroup_projects'),

    url(r'^projects/$', 'imiagroup.views.imiagroup_projects', name='imiagroup_projects'),

    url(r'^projects/stage/edit/$', 'imiagroup.views.imiagroup_stage_edit', name='imiagroup_stage_edit'),
    url(r'^projects/stage/delete/$', 'imiagroup.views.imiagroup_stage_del', name='imiagroup_stage_del'),
    url(r'^projects/(?P<id>\d+)/$', 'imiagroup.views.imiagroup_project_budget', name='imiagroup_project_budget'),
    url(r'^projects/(?P<id>\d+)/discussion/(?P<dis>\d+)/$', 'imiagroup.views.imiagroup_project_discussion', name='imiagroup_project_discussion'),
    

    
    #localhost
    #url(r'^view/99/$', 'imiagroup.views.question_answer', name='imiagroup_question_answer'),
    #url(ur'^view/99/question/(?P<id>\d+)/$', 'imiagroup.views.question', name='imiagroup_question'),
    #url(ur'^view/99/tag/(?P<tag>.*)/$', 'imiagroup.views.question_answer', name='imiagroup_question_answer_tag'),
    #url(ur'^view/99/admin/answers/$', 'imiagroup.views.answers_admin', name='imiagroup_answers_admin'),
    #url(ur'^view/99/admin/$', 'imiagroup.views.question_answer_admin', name='imiagroup_questions_admin'),
    #url(ur'^view/99/admin/translate/(?P<id>\d+)/(?P<code>[-\w]+)/$', 'imiagroup.views.questions_translate_admin', name='imiagroup_questions_translate_admin'),
    #url(ur'^view/99/admin/translate/answer/(?P<id>\d+)/(?P<parent>\d+)/(?P<code>[-\w]+)/$', 'imiagroup.views.answers_translate_admin', name='imiagroup_answers_translate_admin'),
    #url(ur'^view/99/(?P<qtype>\w+)/answers/$', 'imiagroup.views.question_answer_type', name='imiagroup_question_answer_type'),

    url(r'^view/95/$', 'imiagroup.views.question_answer', name='imiagroup_question_answer'),
    url(ur'^view/95/question/(?P<id>\d+)/$', 'imiagroup.views.question', name='imiagroup_question'),
    url(ur'^view/95/tag/(?P<tag>.*)/$', 'imiagroup.views.question_answer', name='imiagroup_question_answer_tag'),
    url(ur'^view/95/admin/answers/$', 'imiagroup.views.answers_admin', name='imiagroup_answers_admin'),
    url(ur'^view/95/admin/$', 'imiagroup.views.question_answer_admin', name='imiagroup_questions_admin'),
    url(ur'^view/95/admin/translate/(?P<id>\d+)/(?P<code>[-\w]+)/$', 'imiagroup.views.questions_translate_admin', name='imiagroup_questions_translate_admin'),
    url(ur'^view/95/admin/translate/answer/(?P<id>\d+)/(?P<parent>\d+)/(?P<code>[-\w]+)/$', 'imiagroup.views.answers_translate_admin', name='imiagroup_answers_translate_admin'),
    url(ur'^view/95/(?P<qtype>\w+)/answers/$', 'imiagroup.views.question_answer_type', name='imiagroup_question_answer_type'),

    url(r'^view/(?P<vid>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view_post'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_post_del', {'type': 'org'}, name='letsget_view_post_del'),
    
    
    # im looking for
    url(r'^(?P<id>[\w-]+)/offers_and_advert/$', 'organizations.views.organization_offers_and_advert', name='organization_offers_and_advert'),
    url(r'^im-looking-for/(?P<id>\d+)/$', 'letsgetrhythm.views.offers_and_adv', {'slug': 'vlada-alfimov-design', 'flag': '4'}, name='i_seek'),
    
    
    # my tools
    url(r'^admin/clients/$', 'letsgetrhythm.views.clients', name='letsget_clients'),
    url(r'^admin/clients/add/$', 'letsgetrhythm.views.clients_add', name='letsget_clients_add'),
    url(r'^admin/clients/invite/$', 'letsgetrhythm.views.letsget_inv_template', {'itype': 'invite'}, name='letsget_invite_template'),
    url(r'^admin/clients/del/$', 'letsgetrhythm.views.clients_del', name='letsget_clients_del'),
    url(r'^admin/calendar/$', 'letsgetrhythm.views.calendar', name='letsget_calendar'),
    url(r'^admin/calendar/add/$', 'letsgetrhythm.views.calendar_add', name='letsget_calendar_add'),
    
    url(r'^admin/upload-images/$', 'letsgetrhythm.views.upload_images', name='letsget_upload_images'),
    
    url(r'^admin/invoices/data/$', 'letsgetrhythm.views.invoice', name='letsget_invoice'),
    url(r'^admin/invoices/list/$', 'letsgetrhythm.views.invoices_list', name='letsget_invoices_list'),
    
    url(r'^admin/set_social_icons/$', 'vladaalfimov.views.set_social_icons', name='set_social_icons'),
    
    
    # orgs
    url(r'^org/(?P<id>[\w-]+)/$', 'letsgetrhythm.views.orgs', name='orgs'), 
    #url(r'^org/(?P<id>[\w-]+)/staff/$', 'letsgetrhythm.views.org_staff', name='org_staff'), 
    url(r'^org/(?P<id>[\w-]+)/im-looking-for/(?P<iid>\d+)/$', 'letsgetrhythm.views.org_offers_and_adv', {'flag': '4'}, name='org_seek'),
    url(r'^org/(?P<id>[\w-]+)/my-offers/(?P<iid>\d+)/$', 'letsgetrhythm.views.org_offers_and_adv', {'flag': '3'}, name='org_offers'),
    
    url(r'^admin/invoice_gen/$', 'imiagroup.views.invoice_gen', name='invoice_gen'),
    
    
    # page type
    url(r'^view/change_page_type/(?P<vid>\d+)/$', 'letsgetrhythm.views.change_page_type', name='change_page_type'),
)

