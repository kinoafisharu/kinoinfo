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
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, get_month_en, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, afisha_dict
from decors import timer
from release_parser.func import cron_success, get_imdb_id


@timer
def get_top250():
    source = ImportSources.objects.get(url='http://top250.info/')
    
    films_exist = SourceFilms.objects.filter(source_obj=source)
    films_exist_dict = {}
    for i in films_exist:
        films_exist_dict[int(i.source_id)] = i
    
    data_nof_films = ''
    films = {}
    keys = []
    
    url = '%scharts/' % source.url
    req = urllib.urlopen(url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        main = data.find('div', {'class': "layout"})
        tables = main.findAll('table', limit=2)
        trr = tables[0].findAll('tr', limit=1)[0]
        tdd = trr.findAll('td', limit=2)[1]
        
        date_tmp = tdd.text.encode('utf-8').replace('Date: ','').replace(',','').strip()
        month, day, year, times = date_tmp.split()
        month = get_month_en(low(month))
        date_upd = datetime.date(int(year), month, int(day))
        
        #'-' без изменений
        #'↑' поднялся
        #'↓' опустился
        #'*' новый в топе
        
        for tr in tables[1].findAll('tr', {'class': ['row_same', 'row_up', 'row_down', 'row_new']}):
            td = tr.findAll('td')
            
            position = int(td[0].text)
            change = td[1].text.encode('utf-8')
            rating = float(td[3].text)
            votes = int(td[4].text)
            
            title = td[2].a.text.encode('utf-8')
            
            year = re.findall(r'\(.*?\)', title)[0].replace('(','').replace(')','')
            title = re.sub(r'\(.*?\)', '', title).strip()
            
            imdb_id = int(td[2].a.get('href').encode('utf-8').replace('/movie/?',''))
            
            if '-' in change:
                change = 1
                change_val = None
            elif '↑' in change:
                change_val = int(change.replace('↑','').strip())
                change = 2
            elif '↓' in change:
                change_val = int(change.replace('↓','').strip())
                change = 3
            elif '*' in change:
                change_val = None
                change = 4
        
            # получаю объект фильм от источника из БД, если существует
            obj = films_exist_dict.get(imdb_id)
            
            unique = '%s%s' % (imdb_id, date_upd)
            keys.append(unique)
            
            # записываю в словарь все спарсенные данные и объект
            films[imdb_id] = {
                'imdb_id': imdb_id,
                'position': position,
                'change': change,
                'change_val': change_val,
                'rating': rating,
                'votes': votes,
                'title': title,
                'year': year,
                'obj': obj,
                'key': unique,
            }
    
    top = Top250.objects.filter(key__in=keys)
    tops = [i.key.encode('utf-8') for i in top]
    
    # достаю все совпавшие фильмы по id imdb из БД для идентификации
    films_afisha = Film.objects.using('afisha').only('id', 'idalldvd').filter(idalldvd__in=films.keys())
    films_afisha_dict = {}
    for i in films_afisha:
        films_afisha_dict[int(i.idalldvd)] = i.id
    
    # иду по всем спарсенным фильмам
    for i in films.values():
        # идентифицирую фильм
        kid = films_afisha_dict.get(i['imdb_id'])
        # если у нас уже есть такой фильм от источника
        if i['obj']:
            # и он неидентифицирован, но сейчас идентифицировался, то сохраняю kid
            if kid and not i['obj'].kid:
                i['obj'].kid = kid
                i['obj'].save()
        # если у нас нет такого фильма от источника, то сохраняю
        else:
            sobj = SourceFilms.objects.create(
                source_id = i['imdb_id'],
                source_obj = source,
                name = i['title'],
                kid = kid,
                imdb = i['imdb_id'],
                year = i['year'],
            )
            i['obj'] = sobj
    
        
        if i['key'] not in tops:
            Top250.objects.create(
                key = i['key'],
                date_upd = date_upd,
                film = i['obj'],
                position = i['position'],
                change = i['change'],
                change_val = i['change_val'],
                rating = i['rating'],
                votes = i['votes'],
            )
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    cron_success('html', source.dump, 'films', 'Фильмы')


#@timer
def get_top250_awards():
    source = ImportSources.objects.get(url='http://top250.info/')

    fest, fest_created = FestCompetition.objects.get_or_create(
        name_en = 'Oscar',
        type = '1', 
        defaults = {
            'type': '1',
            'name_en': 'Oscar',
            'name_ru': 'Оскар',
        })

    awards_names = AwardsNames.objects.exclude(Q(name_en=None) | Q(name_en=''))
    awards_names_dict = {}
    for i in awards_names:
        awards_names_dict[i.name_en.encode('utf-8')] = i

    current_year = datetime.date.today().year
    past_years = current_year - 3#00

    films = SourceFilms.objects.filter(source_obj=source, year__lte=current_year, year__gte=past_years).exclude(kid=None)

    

    for i in films:
        imdb =  get_imdb_id(i.imdb)
        url = '%smovie/?%s' % (source.url, imdb)
        
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            
            main = data.find('div', {'class': "movie_left"})
            
            awards = []
            p_tag = main.findAll('p', limit=1)
            if p_tag:
                p_tag = p_tag[0]
                if p_tag.find('b'):
                    p_tag.find('b').extract()
                
                    lines = str(p_tag).replace('<p>', '').replace('</p>','').split('<br/>')
                    
                    lines_list = []
                    for j in lines:
                        if j:
                            year, title = j.split('<i>')
                            try:
                                year = int(year.strip())
                            except ValueError:
                                year = None
                                
                            if year:
                                name, award_type = title.split('</i>')
                                
                                name = name.replace(' - ', '').strip()
                                award_type = award_type.replace('(','').replace(')','').strip()
                                
                                if award_type == u'nomination':
                                    award_type = '1'
                                else:
                                    award_type = '2'
                                    
                                
                                name_obj = awards_names_dict.get(name.encode('utf-8'))
                                if not name_obj:
                                    name_obj = AwardsNames.objects.create(name_en=name)
                                    awards_names_dict[name.encode('utf-8')] = name_obj

                                award_obj, award_created = Awards.objects.get_or_create(
                                    awards = name_obj,
                                    year = year,
                                    type = award_type,
                                    fest = fest,
                                    defaults = {
                                        'awards': name_obj,
                                        'year': year,
                                        'type': award_type,
                                        'fest': fest,
                                    })
                                
                                rel, rel_created = AwardsRelations.objects.get_or_create(
                                    kid = i.kid,
                                    defaults = {
                                        'kid': i.kid,
                                    })
                                
                                if award_obj not in rel.awards.all():
                                    rel.awards.add(award_obj)
    
    cron_success('html', source.dump, 'awards', 'Награды')
    
    
