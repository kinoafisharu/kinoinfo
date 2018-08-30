#-*- coding: utf-8 -*-
import re
import os
import datetime
import time
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils import simplejson
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
#from unidecode import unidecode

from base.models import *
from kinoinfo_folder.func import low, capit
from user_registration.func import only_superuser, md5_string_generate
from articles.views import pagination as pagi
from news.forms import NewsImageUploadForm





@never_cache
def messenger(request):

    if request.POST and request.user.is_superuser:

        user_id = request.POST.get('u_id')
        user_id_re = request.POST.get('u_id_re')
        mess_title = request.POST.get('mess_title')
        mess_text = request.POST.get('mess_text')


        if mess_title and mess_text:
            try:
                if user_id_re:
                    reader = Profile.objects.get(user__id=user_id_re)
                else:
                    r = Profile.objects.get(accounts__id=user_id)
                    reader = Profile.objects.get(user__id=r.user_id)
            except Accounts.DoesNotExist:
                reader = None

            if reader:
                profile = RequestContext(request).get('profile')
                current_site = request.current_site
                subdomain = request.subdomain

                if not subdomain:
                    subdomain = 'kinoinfo'

                news = News.objects.create(
                    title = mess_title,
                    text = mess_text,
                    autor = profile,
                    site = current_site,
                    subdomain = subdomain,
                    reader_type = 1,
                )


                r = NewsReaders.objects.create(user=reader,status=0)
                news.readers.add(r)



            ref = request.META.get('HTTP_REFERER', '/')
            return HttpResponseRedirect(ref)

    raise Http404

