# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$', 'vladaalfimov.views.index', name='main'),
    
    url(r'^about/$', 'vladaalfimov.views.about', name='about'),
    
    #url(r'^when-you-need-a-new-design/$', 'vladaalfimov.views.main', {'id': 'new_design'}, name='new_design'),
    url(r'^gallery/(?P<vid>\d+)/$', 'vladaalfimov.views.gallery', name='gallery'),
    
    # blog
    #url(r'^blog/$', 'vladaalfimov.views.blog', name='blog'),
    #url(r'^blog/post/(?P<id>\d+)/$', 'vladaalfimov.views.post', {'slug': 'vlada-alfimov-design'}, name='post'),
    #url(r'^blog/post/add/$', 'news.views.news_add', name='news_add'),
    #url(r'^blog/post/delete/(?P<id>\d+)/$', 'news.views.news_delete', name='news_delete'),
    
    url(r'^view/(?P<vid>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/$', 'letsgetrhythm.views.view', {'type': 'org'}, name='letsget_view_post'),
    url(r'^view/(?P<vid>\d+)/post/(?P<id>\d+)/delete/$', 'letsgetrhythm.views.view_post_del', {'type': 'org'}, name='letsget_view_post_del'),
    
    
    # im looking for
    url(r'^(?P<id>[\w-]+)/offers_and_advert/$', 'organizations.views.organization_offers_and_advert', name='organization_offers_and_advert'),
    url(r'^im-looking-for/(?P<id>\d+)/$', 'letsgetrhythm.views.offers_and_adv', {'slug': 'vlada-alfimov-design', 'flag': '4'}, name='i_seek'),
    
    # my offers
    #url(r'^my-offers/(?P<id>\d+)/$', 'letsgetrhythm.views.offers_and_adv', {'slug': 'vlada-alfimov-design', 'flag': '3'}, name='my_offers'),
    
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
    
    # page type
    url(r'^view/change_page_type/(?P<vid>\d+)/$', 'letsgetrhythm.views.change_page_type', name='change_page_type'),
    
)
