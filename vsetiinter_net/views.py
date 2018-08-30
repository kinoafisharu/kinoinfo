#-*- coding: utf-8 -*- 
import urllib
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

#from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from base.models_dic import *
from base.models_choices import *
from base.models import *
from organizations.forms import OrganizationImageUploadForm, OrganizationImageSlideUploadForm
from kinoinfo_folder.func import low, capit
from user_registration.func import only_superuser, md5_string_generate
#from release_parser.func import cron_success, get_imdb_id
from articles.views import pagination as pagi


@never_cache
def index(request):
    return render_to_response('vsetiinter_net/main.html', {}, context_instance=RequestContext(request))
    
