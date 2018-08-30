#-*- coding: utf-8 -*- 
import cProfile
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
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from decors import timer
from release_parser.func import cron_success
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean

def cprofiler(func):
    def wrapper(*args, **kwargs):
        profile_filename = func.__name__ + '.profile'
        profiler = cProfile.Profile()
        result = profiler.runcall(func, *args, **kwargs)
        profiler.dump_stats(profile_filename)
        return result
    return wrapper


@timer
def get_tvzavr_dump():
    '''
    Получение дампа фильмов
    '''
    source = ImportSources.objects.get(url='http://www.tvzavr.ru/')
    main_url = '%sapi/mgm/sitemap-video.xml' % source.url
    req = urllib.URLopener()
    path = '%s/dump_%s_index.xml' % (settings.API_DUMP_PATH, source.dump)
    req.retrieve(main_url, path)
    cron_success('xml', source.dump, 'index', 'Дамп с фильмами')


@timer
#@cprofiler
def tvzavr_ident():
    
    source = ImportSources.objects.get(url='http://www.tvzavr.ru/')
    sfilm_clean(source)
    
    path = '%s/dump_%s_index.xml' % (settings.API_DUMP_PATH, source.dump)
    
    data_nof_film = ''
    noffilms = []
    
    ignored = get_ignored_films()

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    with open(path, 'r') as f:
        data = BeautifulSoup(f.read(), "html.parser")
        
    for i in data.findAll('url'):
        title = i.find('video:video').find('video:title').text.encode('utf-8')
        slug = low(del_separator(title))
        film_id = i.find('tvzavr:video').find('tvzavr:id').text
        
        if not 'серия' in slug and film_id not in noffilms:

            if slug.decode('utf-8') not in ignored:
                url = i.find('loc').text.encode('utf-8')
                year = i.find('tvzavr:video').find('tvzavr:year').text
                
                obj = films.get(film_id)
                next_step = checking_obj(obj)
                    
                if next_step:
                    if obj:
                        kid = obj.kid
                    else:
                        kid, info = film_identification(slug, None, {}, {}, year=year, source=source)
                            
                    objt = None
                    if kid:
                        create_new, objt = unique_func(fdict, kid, obj)
                        if create_new:
                            new = create_sfilm(film_id, kid, source, title, year=year, extra=url)
                            films[film_id] = new
                            if not fdict.get(kid):
                                fdict[kid] = {'editor_rel': [], 'script_rel': []}
                            fdict[kid]['script_rel'].append(new)
                    elif not obj:
                        data_nof_film += xml_noffilm(title, slug, None, None, film_id.encode('utf-8'), info, url, source.id)
                        noffilms.append(film_id)
                

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'players', 'Онлайн плееры')

