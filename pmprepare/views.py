#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
from random import randrange

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, get_language

from bs4 import BeautifulSoup

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits, resize_image
from user_registration.views import get_usercard
from user_registration.func import login_counter, only_superuser, md5_string_generate, only_superuser_or_admin
from news.views import cut_description, create_news
from vladaalfimov.forms import *
from organizations.forms import OrganizationImageSlideUploadForm
from kinoinfo_folder.func import low
from articles.views import pagination as pagi
from news.forms import NewsImageUploadForm
from news.views import news_edit, cut_description


@never_cache
def index(request):

    lang = get_language()

    data = {'obj': None, 'title': None, 'text': None, 'translated_obj': None}
    try:
        index_text = News.objects.select_related('language').get(reader_type='13', visible=True, site=request.current_site, subdomain=request.subdomain)

        data['obj'] = index_text

        if index_text.language.code != lang:
            try:
                index_text = NewsAlterTranslation.objects.get(news=index_text, language__code=lang)
                data['translated_obj'] = index_text
            except NewsAlterTranslation.DoesNotExist: pass

        data['title'] = index_text.title
        data['text'] = index_text.text

    except News.DoesNotExist: pass


    if request.POST and request.user.is_superuser:
        title = request.POST.get('title','').strip()
        text = request.POST.get('text','').strip()
        if text:
            if data['obj']:
                if data['obj'].language.code == lang:
                    data['obj'].title = title
                    data['obj'].text = text
                    data['obj'].save()
                else:
                    if data['translated_obj']:
                        data['translated_obj'].title = title
                        data['translated_obj'].text = text
                        data['translated_obj'].save()
                    else:
                        lang_obj = Language.objects.get(code=lang)
                        NewsAlterTranslation.objects.get_or_create(
                            news = data['obj'],
                            language = lang_obj,
                            defaults = {
                                'title': title,
                                'text': text,
                                'news': data['obj'],
                                'language': lang_obj,
                            })
            else:
                create_news(request, [], title, text, '13', nick=0, extra=None, visible=True)

            return HttpResponseRedirect(reverse('main'))

    return render_to_response('pmprepare/index.html', {'data': data}, context_instance=RequestContext(request))




