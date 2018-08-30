# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',

    url(r'^$', 'letsgetrhythm.views.index', name='main'),
    
    # my offers
    #url(r'^community-centres/$', 'vladaalfimov.views.main', {'id': 'community'}, name='community_centres'),
    #url(r'^healthy-drumming-program/$', 'vladaalfimov.views.main', {'id': 'healthy'}, name='healthy_drumming'),
    #url(r'^drums-and-percussion-info/$', 'vladaalfimov.views.main', {'id': 'info'}, name='drums_info'),
    #url(r'^my-bands-and-events/$', 'vladaalfimov.views.main', {'id': 'bands'}, name='my_bands'),
    
    # im looking for
    url(r'^(?P<id>[\w-]+)/offers_and_advert/$', 'organizations.views.organization_offers_and_advert', name='organization_offers_and_advert'),
    url(r'^im-looking-for/(?P<id>\d+)/$', 'letsgetrhythm.views.offers_and_adv', {'slug': 'lets-get-rhythm', 'flag': '4'}, name='i_seek'),
    
    
    url(r'^view/(?P<vid>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view_post'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_post_del', {'type': 'org'}, name='letsget_view_post_del'),
    
    url(r'^gallery/(?P<vid>\d+)/$', 'vladaalfimov.views.gallery', name='gallery'),
    
    # my tools
    url(r'^admin/clients/$', 'letsgetrhythm.views.clients', name='letsget_clients'),
    url(r'^admin/clients/add/$', 'letsgetrhythm.views.clients_add', name='letsget_clients_add'),
    url(r'^admin/clients/del/$', 'letsgetrhythm.views.clients_del', name='letsget_clients_del'),
    url(r'^admin/clients/invite/$', 'letsgetrhythm.views.letsget_inv_template', {'itype': 'invite'}, name='xletsget_invite_template'),
    url(r'^admin/clients/invoice/$', 'letsgetrhythm.views.letsget_inv_template', {'itype': 'invoice'}, name='xletsget_invoice_template'),
    url(r'^admin/calendar/$', 'letsgetrhythm.views.calendar', name='letsget_calendar'),
    url(r'^admin/calendar/add/$', 'letsgetrhythm.views.calendar_add', name='letsget_calendar_add'),
    
    url(r'^admin/upload-images/$', 'letsgetrhythm.views.upload_images', name='letsget_upload_images'),
    url(r'^admin/upload-files/$', 'letsgetrhythm.views.upload_files', name='letsget_upload_files'),

    url(r'^admin/invoices/data/$', 'letsgetrhythm.views.invoice', name='letsget_invoice'),
    url(r'^admin/invoices/list/$', 'letsgetrhythm.views.invoices_list', name='letsget_invoices_list'),

    url(r'^admin/clients/invites/$', 'letsgetrhythm.views.letsget_inv_templates', {'itype': 'invite'}, name='letsget_invite_template'),
    url(r'^admin/clients/invoices/$', 'letsgetrhythm.views.letsget_inv_templates', {'itype': 'invoice'}, name='letsget_invoice_template'),
    url(r'^admin/clients/invites/(?P<id>\d+)/$', 'letsgetrhythm.views.letsget_inv_templates', {'itype': 'invite'}, name='letsget_invite_template'),
    url(r'^admin/clients/invoices/(?P<id>\d+)/$', 'letsgetrhythm.views.letsget_inv_templates', {'itype': 'invoice'}, name='letsget_invoice_template'),
    url(r'^admin/clients/invites/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_ipost_del', {'itype': 'invite'}, name='letsget_invite_del'),
    url(r'^admin/clients/invoices/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_ipost_del', {'itype': 'invoice'}, name='letsget_invoice_del'),

    url(r'^admin/actions/$', 'letsgetrhythm.views.admin_actions', name='letsget_admin_actions'),
    
    url(r'^admin/lets_img_auto_size/$', 'letsgetrhythm.views.lets_img_auto_size', name='lets_img_auto_size'),
    
    #url(r'^admin/events_msg_sender/$', 'letsgetrhythm.views.events_msg_sender', name='events_msg_sender'),
    #url(r'^admin/invoice_msg_sender/$', 'letsgetrhythm.views.invoice_msg_sender', name='invoice_msg_sender'),
    
    #url(r'^admin/parse_clients/$', 'letsgetrhythm.parser_xls.parse_xls', name='letsget_parse_clients'),
    #url(r'^admin/create_pdf/$', 'letsgetrhythm.views.create_pdf', name='create_pdf'),
    #url(r'^admin/test_pdf/$', 'letsgetrhythm.views.test_pdf', name='test_pdf'),
    
    
    # orgs
    url(r'^org/(?P<id>[\w-]+)/$', 'letsgetrhythm.views.orgs', name='orgs'), 
    #url(r'^org/(?P<id>[\w-]+)/staff/$', 'letsgetrhythm.views.org_staff', name='org_staff'), 
    url(r'^org/(?P<id>[\w-]+)/im-looking-for/(?P<iid>\d+)/$', 'letsgetrhythm.views.org_offers_and_adv', {'flag': '4'}, name='org_seek'),
    url(r'^org/(?P<id>[\w-]+)/my-offers/(?P<iid>\d+)/$', 'letsgetrhythm.views.org_offers_and_adv', {'flag': '3'}, name='org_offers'),
    
    
    # comment delete
    url(r'^view/comment/delete/$', 'letsgetrhythm.views.comment_delete', name='blog_comment_delete'),
    
    # page type
    url(r'^view/change_page_type/(?P<vid>\d+)/$', 'letsgetrhythm.views.change_page_type', name='change_page_type'),
    

    
    
)

