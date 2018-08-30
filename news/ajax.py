# -*- coding: utf-8 -*- 
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.template.context import RequestContext

from dajaxice.decorators import dajaxice_register

from base.models import *
from kinoinfo_folder.func import low, capit, del_separator

        
@dajaxice_register
def get_news_title(request, id, val):
    #try:
    news = News.objects.get(pk=id)
    if val:
        profile = RequestContext(request).get('profile')
        is_editor = False
        try:
            org = OrganizationNews.objects.select_related('organization').get(news=news)
            if profile in org.organization.editors.all():
                is_editor = True
        except OrganizationNews.DoesNotExist: pass
            
        if request.user.is_superuser or is_editor or request.is_admin:
            news.title = val
            news.save()
            return simplejson.dumps({'status': True, 'content': val})
    
    return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def get_news_tags(request, id, arr):
    #try:
    news = News.objects.get(pk=id)
    if arr:
        profile = RequestContext(request).get('profile')
        is_editor = False
        try:
            org = OrganizationNews.objects.select_related('organization').get(news=news)
            if profile in org.organization.editors.all():
                is_editor = True
        except OrganizationNews.DoesNotExist: pass
        
        if request.user.is_superuser or is_editor or request.is_admin:
            arr = set(arr)
            tags_error = False
            
            tags_objs = {}
            tags_list = []
            tags = NewsTags.objects.all()
            for i in tags:
                tags_objs[i.name] = i
                
            for i in arr:
                t_list = (i, capit(i).decode('utf-8'), low(i).decode('utf-8'))
                tag_obj = None
                for t in t_list:
                    tag_obj = tags_objs.get(t)
                    if tag_obj:
                        break
                
                if not tag_obj:
                    tag_obj = NewsTags.objects.create(name=t_list[0])
                
                tags_list.append(tag_obj)
                
            org_tags = [i for i in news.tags.all()]
            for i in org_tags:
                news.tags.remove(i)
            
            for i in tags_list:
                news.tags.add(i)
            
            return simplejson.dumps({'status': True, 'err': False, 'content': sorted(arr)})
    
    return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def get_news_visibles(request, id, val, type):
    news = News.objects.get(pk=id)
    
    profile = RequestContext(request).get('profile')
    is_editor = False
    try:
        org = OrganizationNews.objects.select_related('organization').get(news=news)
        if profile in org.organization.editors.all():
            is_editor = True
    except OrganizationNews.DoesNotExist: pass
        
        
    if request.user.is_superuser or is_editor or request.is_admin:
        if type == 'visible':
            news.visible = val
        elif type == 'world_pub':
            subdomain = request.subdomain if val else None
            news.world_pub = val
        news.save()
    else:
        return simplejson.dumps({'status': False})
    return simplejson.dumps({})
