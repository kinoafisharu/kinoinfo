import os
import sys
#exit()
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo/base/templatetags')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'
os.environ['PYTHON_EGG_CACHE'] = '/var/www/kinoinfo/data/www/kinoinfo/temp/'


import django.core.handlers.wsgi

import settings_kinoinfo
from django.utils import datastructures
from base.models import *
from django.db import models
import datetime
import operator
from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django import db
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import date as tmp_date
from django.core.cache import cache
from django.utils.html import escape
from django.db.models import Q
from bs4 import BeautifulSoup
from dajaxice.decorators import dajaxice_register
from api.views import create_dump_file
from api.models import *
from base.models import *
from kinoinfo_folder.func import low, capit, uppercase, del_separator
from user_registration.func import org_peoples, is_film_editor
from release_parser.imdb import imdb_searching, get_imdb_data
from release_parser.myhit import myhit_searching
from release_parser.func import actions_logger
from film.views import films_name_create
from movie_online.IR import integral_rate
from news.views import create_news
from film.ajax import exp_film_data

def imdb_search2(imdb_id, name, year, kid):
            film_name = name
            slug = low(del_separator(film_name.encode('utf-8')))
            film_name = film_name.encode('ascii', 'xmlcharrefreplace')
            xml = '<film n="%s" s="%s" y="%s" id="%s" d="" r=""></film>' % (film_name, slug, str(year).encode('utf-8'), str(imdb_id).encode('utf-8'))
            data = exp_film_data(imdb_id)
            
            if data:
                if data.get('double'):
                    return simplejson.dumps(data)
                else:
                    if not data['kid']:
                        pass
                    elif int(data['kid']) != int(kid):
                        return simplejson.dumps({'status': True, 'redirect': True, 'kid': data['kid']})
            
            data_nof_persons, distr_nof_data, dump, good = get_imdb_data(xml, False, 1, [int(imdb_id),], True, kid)
            
            if good:
                data = exp_film_data(imdb_id)
                if not data:
                    data = {'status': False}
            else:
                data = {'status': False}
            if kid:
                cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])
            return simplejson.dumps(data)









#                        RelationFP.objects.filter(films__id=data['pk']).delete()
#                        Films.objects.filter(pk=data['pk']).delete()


#with open("/var/www/kinoinfo/data/www/kinoinfo/ext2017/test.LOG", "a") as myfile:
#    myfile.write("ok\n" )






imdb_search2(imdb_id, name, year, kid)


imdb_search('Entourage', 2015, 'false', 1674771);

imdb_search2(1674771, 'Entourage', 2015, '32828')
#################################################
#OFC076
def is_not_func():
fileName = '{0}/{1}.json'.format(settings.KINOAFISHA_EXT, 'test_settings')
with open(fileName, 'a') as outfile:
    outfile.write("my!\n")

##################################################
# Кнопка для рутрекера

base.views.kinoafisha_button


