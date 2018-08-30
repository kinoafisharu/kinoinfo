# -*- coding: utf-8 -*- 
import time, os

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib import auth
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache

from base.models import *
from user_registration.func import login_counter, only_superuser
from articles.forms import ArticlesForm


def pagination(page, content, rows):
    paginator = Paginator(content, rows)
    try:
        p = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        p = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        p = paginator.page(page)
    return p, page


@never_cache
def main(request, article=None):
    current_site = request.current_site
    if current_site.domain == 'kinoinfo.ru':
        template = 'articles/articles_main.html'
    elif current_site.domain == 'umru.net':
        template = 'articles/umrunet_articles_main.html'
    elif current_site.domain == 'kinoafisha.in.ua':
        template = 'articles/kua_articles_main.html'

    if request.user.is_authenticated():
        login_counter(request)
    if article:
        try:
            article = int(article)
            article = get_object_or_404(Articles, pk=article, site=current_site.id)
        except (ValueError, TypeError):
            raise Http404

    return render_to_response(template, {'article': article}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def add_article(request):
    current_site = request.current_site
    if current_site.domain == 'kinoinfo.ru':
        template = 'articles/add_article.html'
    elif current_site.domain == 'umru.net':
        template = 'articles/umrunet_add_article.html'
    elif current_site.domain == 'kinoafisha.in.ua':
        template = 'articles/kua_add_article.html'
        
    if request.POST:
        form = ArticlesForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_article"))
        else:
            return render_to_response(template, {'form': form, 'add': True}, context_instance=RequestContext(request))
    else:
        form = ArticlesForm()
    return render_to_response(template, {'form': form, 'add': True}, context_instance=RequestContext(request))
    
    
 
@only_superuser
@never_cache
def edit_article(request, id):
    current_site = request.current_site
    if current_site.domain == 'kinoinfo.ru':
        template = 'articles/add_article.html'
    elif current_site.domain == 'umru.net':
        template = 'articles/umrunet_add_article.html'
    elif current_site.domain == 'kinoafisha.in.ua':
        template = 'articles/kua_add_article.html'
        
    article = get_object_or_404(Articles, pk=id, site=current_site.id)
    if request.POST:
        form = ArticlesForm(request.POST)
        if form.is_valid():
            article.title = form.cleaned_data['title']
            article.text = form.cleaned_data['text']
            article.site = current_site
            article.save()
            return HttpResponseRedirect(reverse("edit_article", kwargs={'id': id}))
    else:
        form = ArticlesForm(
            initial={
                'title': article.title,
                'text': article.text,
            }
        )
    return render_to_response(template, {'form': form, 'id': id}, context_instance=RequestContext(request)) 


@only_superuser
@never_cache
def delete_article(request, id):
    site = settings.SITE_ID
    article = get_object_or_404(Articles, pk=id, site=site)
    if request.POST:
        article.delete()
    return HttpResponseRedirect(reverse("articles_main"))
    
