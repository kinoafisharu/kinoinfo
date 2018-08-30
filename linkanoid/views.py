#-*- coding: utf-8 -*-
import operator
import datetime
import time

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.db.models import Q

from base.models import *
from kinoinfo_folder.func import low, del_separator, uppercase
from articles.views import pagination as pagi
from user_registration.func import is_linkanoid_user


@never_cache
def inform(request, id=None):
    from letsgetrhythm.views import view_func

    slug = 'linkanoid'
    linkanoid_user = is_linkanoid_user(request)
    
    access = True if request.user.is_superuser or request.is_admin or linkanoid_user else False

    org = get_object_or_404(Organization, uni_slug=slug)

    orgmenu, created = OrgMenu.objects.get_or_create(
        organization=org,
        defaults={
            'organization': org,
            'name': slug,
    })
    if created:
        submenu = OrgSubMenu.objects.create(name=slug, page_type='1')
        orgmenu.submenu.add(submenu)
    else:
        submenu = orgmenu.submenu.all()[0]

    
    data = view_func(request, submenu.id, id, 'org', access, slug)

    if data == 'redirect':
        return HttpResponseRedirect(request.get_full_path())

    '''
    c = Client(
        charset='utf-8',
        TRUSTLINK_USER='e4b4a24eba7a02936a947af7b59866f7c7edba6d',
        host='www.kinoafisha.ru',
        tl_multi_site=True,
    )
    links = c.build_links()
    '''
    data.update({'linkanoid_user': linkanoid_user})
    
    return render_to_response('linkanoid/inform.html', data, context_instance=RequestContext(request))


@never_cache
def inform_post_del(request, id):
    if request.POST:
        linkanoid_user = is_linkanoid_user(request)
        profile = request.profile
        
        if request.user.is_superuser or request.is_admin or linkanoid_user:
            current_site = request.current_site
            subdomain = request.subdomain
            if not subdomain:
                subdomain = 0
                
            filter = {'pk': id, 'site': current_site, 'subdomain': subdomain}
            if not linkanoid_user:
                filter['autor'] = profile

            news = News.objects.get(**filter)
            attr = news.title if news.title else ''
            if not attr:
                attr = news.text[:128]
            news.delete()
            
            ActionsLog.objects.create(
                profile = profile,
                object = '6',
                action = '3',
                object_id = id,
                attributes = attr,
                site = current_site,
            )
            
            return HttpResponseRedirect(reverse('linkanoid_inform'))
            
    raise Http404

