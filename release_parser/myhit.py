#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import cookielib

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
from release_parser.kinobit_cmc import get_source_data, afisha_dict
from decors import timer
from release_parser.func import cron_success

def give_me_cookie():
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler())
    return opener

def myhit_searching(name, year):
    
    main_url = 'https://my-hit.org/search/'
    
    slug = low(del_separator(name))
    
    params = urllib.urlencode({
        'q': name,
    })
    
    url = '%s?%s' % (main_url, params)

    opener = give_me_cookie()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1',
    }
    opener.addheaders = headers.items()
    
    req = opener.open(urllib2.Request(url))

    result = []

    if req.getcode() == 200:
        data = BeautifulSoup(req.read())
        main_div = data.find('div', {'class': "film-list"})
        if main_div:
            for div in main_div.findAll('div', {'class': 'row'}, limit=20):
                
                img = div.find('img', {'class': "img-rounded img-responsive"})
                
                a = img.previous_element
                title = a.get('title').encode('utf-8')
                
                title_tmp = title.split(' / ')
                title_tmp1, title_tmp2 = title_tmp if len(title_tmp) > 1 else (title_tmp[0], '')
                
                title_slug1 = low(del_separator(title_tmp1))
                title_slug2 = low(del_separator(title_tmp2))
                
                film_url = 'https://my-hit.org%s' % a.get('href').encode('utf-8')
                
                img = img.get('src').encode('utf-8')
                img = 'https://my-hit.org/%s' % img.lstrip('/')
                
                if slug == title_slug1 or slug == title_slug2:
                    details = div.find('ul', {'class': "list-unstyled"})
                    
                    year_tmp = None
                    country = None
                    director = None
                    note = None
                    for li in details.findAll('li'):
                        tmp = li.b.string.encode('utf-8')
                        if tmp == 'Год:':
                            year_tmp = int(li.b.find_next('a').string.encode('utf-8').strip())
                        if tmp == 'Страна:':
                            country = [i.string.encode('utf-8') for i in li.findAll('a')]
                            country = ', '.join(country)
                        if tmp == 'Режиссер:':
                            director = [i.string.encode('utf-8') for i in li.findAll('a')]
                            director = ', '.join(director)
                        if tmp == 'Краткое описание:':
                            note = li.find('p')
                            if note:
                                note = note.text.encode('utf-8')
                    
                    if year_tmp == year:
                        result.append({'title': title_tmp1, 'country': country, 'persons': director, 'link': film_url, 'img': img, 'note': note})
                        
    return result
    
    
