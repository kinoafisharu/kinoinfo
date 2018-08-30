#-*- coding: utf-8 -*- 
import urllib
import urllib2
import httplib2
import re
import datetime
import time
import cookielib
import operator
import json

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings

from bs4 import BeautifulSoup

from base.models import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser, md5_string_generate
from kinoinfo_folder.func import get_month_en, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from decors import timer
from release_parser.func import cron_success
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean


@timer
def get_rottentomatoes_films(everyday=True):

    def get_critic(block):
        critic = block.findAll('div', id="scoreStats", limit=1)
        
        if critic:
            critic = critic[0].findAll('div')
            
            average = critic[0].find('span', {'class': 'subtle superPageFontColor'}).next_sibling.string.strip()
            reviews = critic[1].findAll('span', limit=2)[1].text.strip()
            fresh = critic[2].find('span', {'class': 'subtle superPageFontColor'}).next_sibling.string.strip()
            rotten = critic[3].find('span', {'class': 'subtle superPageFontColor'}).next_sibling.string.strip()
            
            return '%s;%s;%s;%s' % (average.replace('/10',''), reviews, fresh, rotten)
        else:
            return 'N/A;0;0;0'
        '''
        critic = block.findAll('p', {'class': 'critic_stats'}, limit=1)[0]
        average, reviews = critic.findAll('span', limit=2)
        try:
            fresh, rotten = reviews.next_sibling.next_sibling.encode('utf-8').strip().split(' | ')
        except AttributeError:
            return 'N/A;0;0;0'
            
        fresh = fresh.replace('Fresh:','').strip()
        rotten = rotten.replace('Rotten:','').strip()
        average = average.string.encode('utf-8').split('/')[0]
        reviews = reviews.string.encode('utf-8')

        return '%s;%s;%s;%s' % (average, reviews, fresh, rotten)
        '''

    source = ImportSources.objects.get(url='http://www.rottentomatoes.com/')
    sfilm_clean(source)
    
    noffilms = []
    data_nof_film = ''
    
    filter = {'source_obj': source}

    if everyday:
        today = datetime.datetime.today().date()
        day7 = today + datetime.timedelta(days=7)
        today = today - datetime.timedelta(days=30)
        filter['text__gte'] = today
        filter['text__lt'] = day7
        
    exists = get_source_data(source, 'film', 'list')

    films = {}
    source_films = SourceFilms.objects.filter(**filter)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    ignored = get_ignored_films()

    opener = urllib2.build_opener()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
    }
    opener.addheaders = headers.items()
    
    updated = []
    
    for k, f in films.items():
        film_url = '%s%s' % (source.url, k)
        req = opener.open(film_url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            extra = get_critic(data)
            f.extra = extra
            f.save()
            updated.append(k)
        time.sleep(1)
    
    u = 'http://www.rottentomatoes.com/api/private/v1.0/m/list/find?page=1&limit=50&type=opening&minTomato=0&maxTomato=100&minPopcorn=0&maxPopcorn=100&services=&genres=1%3B2%3B4%3B5%3B6%3B8%3B9%3B10%3B11%3B13%3B14%3B18&sortBy=popularity&certified=false'
    
    req = opener.open(u)
    if req.getcode() == 200:
        data = json.loads(req.read(), encoding="latin-1")
        
        for i in data['results']:
            title = i['title'].encode('utf-8')
            title_slug = low(del_separator(title))

            url = i['url'].lstrip('/')
            
            full_url = '%s%s' % (source.url, url)
            
            if url not in exists and url not in noffilms:
                if title_slug.decode('utf-8') not in ignored and url not in updated:
            
                    time.sleep(1)
                    req2 = opener.open(full_url)
                    if req2.getcode() == 200:

                        data2 = BeautifulSoup(req2.read(), from_encoding="utf-8")


                        year_block = data2.find('h1', {'class': 'title hidden-xs'})
                        if not year_block:
                            year_block = data2.find('h1', id='movie-title')

                        year_tmp = year_block.find('span', {'class': 'h3 year'}).text.encode('utf-8')

                        year = int(year_tmp.replace('(','').replace(')', ''))
                        
                        release_date = data2.find('td', itemprop="datePublished")
                        if release_date:
                            release_date = release_date.get('content')

                        extra = get_critic(data2)
                        
                        
                        obj = films.get(url)
                        next_step = checking_obj(obj)
                    
                        if next_step:
                            if obj:
                                kid = obj.kid
                                obj.extra = extra
                                obj.save()
                            else:
                                kid, info = film_identification(None, title_slug, {}, {}, year, source=source)
                            
                            
                            objt = None
                            if kid:
                                create_new, objt = unique_func(fdict, kid, obj)
                                if create_new:
                                    new = create_sfilm(url, kid, source, title, txt=release_date, extra=extra)
                                    films[url] = new
                                    if not fdict.get(kid):
                                        fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                    fdict[kid]['script_rel'].append(new)
                            elif not obj:
                                data_nof_film += xml_noffilm(title, title_slug, None, None, url.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                                noffilms.append(url)
                                    
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'films', 'Фильмы, рейтинг')


@only_superuser
@never_cache
def rottentomatoes_demo(request):
    source = ImportSources.objects.get(url='http://www.rottentomatoes.com/')
    films = SourceFilms.objects.filter(source_obj=source)
    
    txt = ''
    for i in films:
        txt += '<h2><a href="%s%s" target="_blank">%s</a></h2>' % (source.url, i.source_id, i.name)
        average, reviews, fresh, rotten = i.extra.split(';')
        txt += 'Average: %s<br />Reviews: %s<br />Fresh: %s<br />Rotton: %s<hr />' % (average, reviews, fresh, rotten)
    return HttpResponse(str(txt))


