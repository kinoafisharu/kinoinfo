#-*- coding: utf-8 -*- 
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

@timer
def get_ivi_file():
    '''
    Получение txt файла
    '''
    source = ImportSources.objects.get(url='http://antipiracy.ivi.ru/')
    films = get_source_data(source, 'film', 'list')
    url = '%s-/' % source.url
  
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        links = BeautifulSoup(req.read(), from_encoding="windows-1251")
        
        for i in links.findAll('a'):
            link = i.string.encode('utf-8')
            if 'in one file.txt' in link:
                req2 = urllib.urlopen('%s%s' % (url, i.get('href')))
                data = BeautifulSoup(req2.read(), from_encoding="windows-1251")
                file = str(data).replace('<html><head></head><body>','').replace('</body></html>','')
                create_dump_file(source.dump, settings.API_DUMP_PATH, file, 'txt')

    cron_success('html', source.dump, 'file', 'txt файл с данными')


@timer
def ivi_ident():
    source = ImportSources.objects.get(url='http://antipiracy.ivi.ru/')
    sfilm_clean(source)
    
    ignored = get_ignored_films()
    
    REG_YEAR = re.compile(r'(\,\s\d{4}$)|(\s\(\d{4}\)$)')
    
    data_nof_film = ''
    noffilms = []
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    films_data = []
    
    with open('%s/dump_%s.txt' % (settings.API_DUMP_PATH, source.dump), 'r') as f:
        ftype = False
        count = 0
        tmp = {}
        for line in f:
            try:
                l = line.strip()
                if l == 'ФИЛЬМЫ:':
                    ftype = True
                
                if ftype:
                    if l:
                        count += 1
                        if count == 1:
                            tmp['name'] = l
                        elif count == 2:
                            tmp['code'] = l
                            films_data.append(tmp)
                    else:
                        if tmp:
                            tmp = {}
                        count = 0

            except ValueError: pass
    
    for i in films_data:
        name = i['name']
        code = i['code']
        
        year = REG_YEAR.findall(name)
            
        if year:
            name_clear = REG_YEAR.sub('', name)
            year = ''.join(year[0])
            year = year.replace(',','').replace('(','').replace(')','').strip()
        else:
            year = None
            name_clear = name
            
        
        name_slug = low(del_separator(name_clear))
        
        
        film_id = low(del_separator(name))
        if film_id.decode('utf-8') not in ignored and film_id not in noffilms:
            
            obj = films.get(film_id.decode('utf-8'))
            next_step = checking_obj(obj)
            
            if next_step:
                if obj:
                    kid = obj.kid
                else:
                    kid, info = film_identification(name_slug, None, {}, {}, year=year, source=source)
        
                objt = None
                if kid:
                    create_new, objt = unique_func(fdict, kid, obj)
                    if create_new:
                        new = create_sfilm(film_id, kid, source, name, txt=code)
                        films[film_id.decode('utf-8')] = new
                        if not fdict.get(kid):
                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                        fdict[kid]['script_rel'].append(new)
                elif not obj:
                    data_nof_film += xml_noffilm(name, name_slug, None, None, film_id, info, None, source.id)
                    noffilms.append(film_id)
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'players', 'Онлайн плееры')


