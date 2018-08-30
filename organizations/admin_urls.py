# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from organizations.parser import get_orsk_organizations

urlpatterns = patterns('',

    # АДМИН
    # temp
    #url(r'^add/$', 'organizations.org_admin.admin_organization_add', name='admin_organization_add'),
    #url(r'^show/(?P<id>\d+)/$', 'organizations.org_admin.organization_details', name='organization_details'),
    url(r'^show/$', 'organizations.org_admin.organizations', name='organizations'),
    #url(r'^edit/(?P<id>\d+)/$', 'organizations.org_admin.admin_organization_edit', name='admin_organization_edit'),
    #url(r'^note/$', 'organizations.org_admin.admin_organization_note', name='admin_organization_note'),
    #url(r'^phones/$', 'organizations.org_admin.admin_organization_phones', name='admin_organization_phones'),
    #url(r'^sites/$', 'organizations.org_admin.admin_organization_sites', name='admin_organization_sites'),
    
    # постмодерация описаний организаций
    url(r'^accept_notes/(?P<id>\d+)/$', 'organizations.org_admin.admin_organization_notes', name='admin_organization_notes'),
    url(r'^accept_notes/$', 'organizations.org_admin.admin_organization_notes', name='admin_organization_notes'),
    
    # все действия над оргниациями
    url(r'^actions/$', 'organizations.org_admin.admin_organization_actions', name='admin_organization_actions'),
    
    url(r'^uni_temp/$', 'organizations.org_admin.organization_uni_temp', name='organization_uni_temp'),

    url(r'^organizations_doubles/$', 'organizations.org_admin.organizations_doubles', name='organizations_doubles'),

    url(r'^name_handler/$', 'organizations.org_admin.organizations_name_handler', name='organizations_name_handler'),
    
    url(r'^cron/get_orsk_organizations/$', 'release_parser.views.create', {'method': get_orsk_organizations}, name='get_orsk_organizations'),
    
    url(r'^orsk_streets_fix/$', 'organizations.parser.orsk_streets_fix', name='orsk_streets_fix'),
    
    url(r'^org_slufy_names/$', 'organizations.parser.org_slufy_names', name='org_slufy_names'),
    
    # текст приглашения
    url(r'^org_invite_text/$', 'organizations.org_admin.org_invite_text', name='org_invite_text'),
    
)


