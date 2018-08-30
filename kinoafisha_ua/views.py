#-*- coding: utf-8 -*- 
import urllib
import re
import os
import datetime
import time
import calendar

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.template.defaultfilters import dictsort
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.contrib.sites.models import Site

from bs4 import BeautifulSoup

from base.models import *
from user_registration.func import only_superuser

"""    
@never_cache
def homepage(request):
    ''' главная страница '''
    return render_to_response('kinoafisha_ua_base.html', context_instance=RequestContext(request))
"""

    
# Create your views here.
