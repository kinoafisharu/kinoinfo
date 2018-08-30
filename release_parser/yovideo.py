#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import operator

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
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success


@timer
def get_yovideo():
    source = ImportSources.objects.get(url='http://www.yo-video.net/')
    sfilm_clean(source)
    
    today = datetime.datetime.now()

    french_month = {
        '1': 'janvier',
        '2': 'fevrier',
        '3': 'mars',
        '4': 'avril',
        '5': 'mai',
        '6': 'juin',
        '7': 'juillet',
        '8': 'aout',
        '9': 'septembre',
        '10': 'octobre',
        '11': 'novembre',
        '12': 'decembre',
    }
    
    data_nof_film = ''
    noffilms = []
    
    ignored = get_ignored_films()

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    main_urls = []
    for i in range(today.month, 13):
        m = french_month.get(str(i))
        url = '%sfr/sorties/cinema/%s/%s/' % (source.url, today.year, m)

        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            
            for h2 in data.findAll('h2'):
                day = h2.findAll('span', limit=1)[0].string.encode('utf-8')
                
                time.sleep(1)
                
                req2 = urllib.urlopen('%s%s' % (url, day))
                if req2.getcode() == 200:
                    data2 = BeautifulSoup(req2.read(), from_encoding="utf-8")
                    
                    release_date = datetime.date(today.year, int(i), int(day))
                    
                    for film_block in data2.findAll('div', {'class': 'sfilm'}):

                        film_id = film_block.find('a').get('href').encode('utf-8')
                        full_url = '%s%s' % (source.url, film_id.lstrip('/'))
                        
                        name = film_block.find('img').get('alt').encode('utf-8').replace('Film ', '')
                        slug = low(del_separator(name))
                        
                        if slug.decode('utf-8') not in ignored and film_id not in noffilms:
                        
                            obj = films.get(film_id)
                            next_step = checking_obj(obj)
                    
                            if next_step:
                                kid = None
                                if obj:
                                    kid = obj.kid
                                
                                if not kid:
                                    req3 = urllib.urlopen(full_url)
                                    
                                    if req3.getcode() == 200:
                                        data3 = BeautifulSoup(req3.read(), from_encoding="utf-8")

                                        h3 = data3.find('h3')
                                        
                                        alter_name = None
                                        alter_name_slug = None
                                            
                                        if h3:
                                            alter_name = h3.string.encode('utf-8')
                                            alter_name_slug = low(del_separator(alter_name))
                                        
                                        
                                        kid, info = film_identification(slug, alter_name_slug, {}, {}, source=source)

                                        txt = None
                                        if not kid:
                                            div = data3.find('div', {'class': "filmLeft"})
                                            img_url = div.find('img').get('src').encode('utf-8')
                        
                                            details = data3.find('div', {'class': "details"})
                                            director = details.find('span', itemprop="name")
                                            if director:
                                                director = director.string.encode('utf-8').strip()
                                            
                                            year = re.findall(ur'Année\s?\: \d+', details.text)
                                            if year:
                                                year = year[0].encode('utf-8').replace('Année','').replace(':','').strip()
                                            
                                            txt = '%s;%s;%s;%s' % (full_url.encode('utf-8'), img_url, director, year)
                                            kid = None
                                            
                                        
                                        objt = None
                                        
                                        if kid:
                                            create_new, objt = unique_func(fdict, kid, obj)
                                            if create_new:
                                                new = create_sfilm(film_id, kid, source, name, name_alt=alter_name, txt=txt, extra=release_date)
                                                films[film_id] = new
                                                if not fdict.get(kid):
                                                    fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                                fdict[kid]['script_rel'].append(new)
                                        else:
                                            if not obj:
                                                new = create_sfilm(film_id, kid, source, name, name_alt=alter_name, txt=txt, extra=release_date)
                                                films[film_id] = new
                                                if not fdict.get(kid):
                                                    fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                                fdict[kid]['script_rel'].append(new)

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'releases', 'Франц.релизы')



