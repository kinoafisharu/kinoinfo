#-*- coding: utf-8 -*- 
#----------del from production
import os
import sys
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo/base/templatetags')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'
os.environ['PYTHON_EGG_CACHE'] = '/var/www/kinoinfo/data/www/kinoinfo/temp/'


import django.core.handlers.wsgi

import settings_kinoinfo
#----------end del

import urllib
import urllib2
import re
import datetime
import time
    
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success
from user_registration.views import get_user




#@timer
def get_megacritic():

    current_site = DjangoSite.objects.get(domain='kinoinfo.ru')
    exit()


