# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls.defaults import include, patterns, url
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from dajaxice.core import dajaxice_autodiscover, dajaxice_config

from base.feeds import NewsFeed
from organizations.views import organization_reviews_and_questions

admin.autodiscover()
dajaxice_autodiscover()

urlpatterns = patterns('',
    url(r'^rss/news/$', NewsFeed(), name='rss_news'),

    url(r'^$', 'news.views.index', name='main'),
    url(r'^add/$', 'organizations.views.organizations_add', name='organizations_add'),
    url(r'^delete/(?P<id>\d+)/$', 'organizations.views.organizations_delete', name='organizations_delete'),
    url(r'^search/$', 'organizations.views.organization_search', name='search'),
    url(r'^lists/$', 'organizations.views.organization_lists', name='lists'),
    url(r'^organizations/list/(?P<char>\w+)/$', 'organizations.views.organization_list', name='organization_list'),
    
    url(r'^news/', include('news.urls')),
    
    url(r'^background/change/', 'api.panel.change_background', name='change_background'),
    
    url(r'^messenger/$', 'user_registration.messenger.messenger', name='messenger'),

    url(r'^org_tags_upd/$', 'organizations.views.org_tags_upd', name='org_tags_upd'),


    url(r'^(?P<id>[\w-]+)/$', 'organizations.views.organization_show_new', name='organization_show_new'),
    url(r'^(?P<id>[\w-]+)/staff/$', 'organizations.views.organization_staff', name='organization_staff'),
    url(r'^(?P<id>[\w-]+)/relations/$', 'organizations.views.organization_relations', name='organization_relations'),
    
    url(r'^(?P<id>[\w-]+)/offers/(?P<offer_id>\d+)/$', 'organizations.views.organization_offers', name='organization_offers'),
    url(r'^(?P<id>[\w-]+)/adverts/(?P<advert_id>\d+)/$', 'organizations.views.organization_adverts', name='organization_adverts'),
    url(r'^(?P<id>[\w-]+)/offers_and_advert/$', 'organizations.views.organization_offers_and_advert', name='organization_offers_and_advert'),
    
    url(r'^(?P<id>[\w-]+)/offers/(?P<offer_id>\d+)/item/(?P<item_id>\d+)/$', 'organizations.views.organization_offers_news', name='organization_offers_news'),
    url(r'^(?P<id>[\w-]+)/adverts/(?P<advert_id>\d+)/item/(?P<item_id>\d+)/$', 'organizations.views.organization_adverts_news', name='organization_adverts_news'),
    
    url(r'^(?P<id>[\w-]+)/reviews/(?P<item_id>\d+)/$', 'organizations.views.organization_reviews_and_questions_news', {'type': 'reviews'}, name='organization_reviews_news'),
    url(r'^(?P<id>[\w-]+)/reviews/', 'organizations.views.organization_reviews_and_questions', {'type': 'reviews'}, name='organization_reviews'),
    
    url(r'^(?P<id>[\w-]+)/questions/(?P<item_id>\d+)/$', 'organizations.views.organization_reviews_and_questions_news', {'type': 'questions'}, name='organization_questions_news'),
    url(r'^(?P<id>[\w-]+)/questions/', 'organizations.views.organization_reviews_and_questions', {'type': 'questions'}, name='organization_questions'),

    url(r'^(?P<id>[\w-]+)/comments/(?P<item_id>\d+)/$', 'organizations.views.organization_reviews_and_questions_news', {'type': 'comments'}, name='organization_comments_news'),
    url(r'^(?P<id>[\w-]+)/comments/', 'organizations.views.organization_reviews_and_questions', {'type': 'comments'}, name='organization_comments'),

    url(r'^(?P<id>[\w-]+)/change_org_branding/', 'organizations.views.change_org_branding', name='change_org_branding'),
    
    url(r'^(?P<id>[\w-]+)/schedules/', 'organizations.views.organization_schedules', name='organization_schedules'),
    
    
    url(r'^(?P<id>[\w-]+)/view/(?P<vid>\d+)/$', 'organizations.views.view', name='org_view'),
    url(r'^(?P<id>[\w-]+)/view/(?P<vid>\d+)/post/(?P<pid>\d+)/$', 'organizations.views.view', name='org_view_post'),
    url(r'^(?P<id>[\w-]+)/view/(?P<vid>\d+)/post/(?P<pid>\d+)/delete/$', 'organizations.views.org_view_post_del', name='org_view_post_del'),
    
    url(r'^(?P<id>[\w-]+)/gallery/(?P<vid>\d+)/$', 'organizations.views.org_gallery', name='org_gallery'),
    
    # page type
    url(r'^(?P<id>[\w-]+)/view/(?P<vid>\d+)/change_page_type/$', 'organizations.views.org_change_page_type', name='org_change_page_type'),
    
    
    # dajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),
)
 
if settings.DEBUG:
    urlpatterns += patterns('',
       url(r'^' + settings.MEDIA_URL.lstrip('/') \
               + '(?P<path>.*)$', 'django.views.static.serve',
           {
                'document_root': settings.MEDIA_ROOT,
           }),
    )
    urlpatterns += staticfiles_urlpatterns()
