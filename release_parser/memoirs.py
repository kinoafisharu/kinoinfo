#-*- coding: utf-8 -*- 
import datetime

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
from base.models import *
from release_parser.models import MyStoryStrArticles
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low



def get_all_story():
    site = DjangoSite.objects.get(domain='vsetiinter.net')
    
    
    profile = Profile.objects.get(accounts__login='kinoafisharu@gmail.com')
    
    
    users = {
        u'Саечка': 3307116,
        u'AlDuma': 26143,
        u'Гоги': 3022194,
        u'sayros': 30,
    }

    

    for i in MyStoryStrArticles.objects.using('story').select_related('user').filter(user__nick__in=users.keys()):
        user_id = users.get(i.user.nick)
        try:
            profile = Profile.objects.get(user__id=user_id)
        except Profile.DoesNotExist: 
            pass
        else:
            msg_obj = News.objects.create(
                title = i.name,
                text = i.text,
                visible = True,
                site = site,
                subdomain = 'memoirs',
                autor = profile,
                autor_nick = 1,
            )
            
            msg_obj.dtime = i.date
            msg_obj.save()
    
    return HttpResponse(str())
    
