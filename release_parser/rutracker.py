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
from django.template.defaultfilters import date as tmp_date

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data
from decors import timer
from release_parser.func import cron_success



@timer
def get_rutracker_topics():
    REG_SIZE = re.compile(r'\[\d+\.?\d+?\s?\w+\]')
    REG_SLUG = re.compile(ur'[a-zа-я0-9]+')
    data_nof_film = ''
    
    temp_data = {}
    
    source = ImportSources.objects.get(url='http://rutracker.org/')

    ignored = get_ignored_films()

    films = get_source_data(source, 'film', 'list')
    noffilms = []
    
    links = [
        'http://feed.rutracker.cc/atom/f/2200.atom',
        'http://feed.rutracker.cc/atom/f/2093.atom',
        'http://feed.rutracker.cc/atom/f/209.atom',
        'http://feed.rutracker.cc/atom/f/22.atom',
        'http://feed.rutracker.cc/atom/f/124.atom'
    ]

    send_msg = False

    for url in links:
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            
            for entry in data.findAll('entry'):
                id = entry.link.get('href').replace("http://rutracker.org/forum/viewtopic.php?t=", "").replace("viewtopic.php?t=", "")
                date_upd, time_upd = entry.updated.text.replace('+00:00','').split('T')

                dtime = '%s %s' % (date_upd, time_upd)

                if id not in films and id not in noffilms and id.decode('utf-8') not in ignored:
                    title = entry.title.text.encode('utf-8').replace('<![CDATA[','').replace(']]>','')
                    title = re.sub(REG_SIZE, '', title)
                    
                    name = title.replace('[Обновлено]','').replace('[Extended Cut]','').strip()
                    
                    year_temp = name.split('[')
                    if len(year_temp) > 1:
                        year = re.findall(r'\d+', year_temp[1])
                        if year:
                            year = year[0] 
                            
                            name_alt = re.findall(REG_SLUG, low(name).decode('utf-8'))
                            name_alt = ''.join(name_alt)

                            name_for_search = name.split('/')[0].strip()
                            name_for_search_slug = re.findall(REG_SLUG, low(name_for_search).decode('utf-8'))
                            name_for_search_slug = ''.join(name_for_search_slug)

                            full_url = '%sforum/viewtopic.php?t=%s' % (source.url, id)

                            kid = temp_data.get(name_for_search_slug + year)
                            
                            if not kid:
                                kid, info = film_identification(name_for_search_slug, None, {}, {}, year, source=source)
                                
                            if kid:
                                film_obj = SourceFilms.objects.create(
                                    source_id = id,
                                    source_obj = source,
                                    name = name,
                                    name_alter = name_alt,
                                    kid = kid,
                                    text = dtime,
                                    extra = 'new',
                                )
                                temp_data[name_for_search_slug + year] = kid
                                films.append(id)
                                send_msg = True
                            else:
                                data_nof_film += xml_noffilm(name_for_search, name_for_search_slug.encode('utf-8'), None, None, id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                                noffilms.append(id)
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'films', 'Новые фильмы') 


    if send_msg:
        current_site = DjangoSite.objects.get(domain='kinoinfo.ru')
        
        msg_from = Profile.objects.get(user__last_name='SYSTEM')
        msg_to = Profile.objects.get(accounts__login='kinoafisharu@gmail.com') # twohothearts@gmail.com
        msg = 'В сети появились новые фильмы <a href="http://kinoinfo.ru/torrents/listing/%s/" target="_blank">http://kinoinfo.ru/torrents/listing/%s/</a>' % (source.id, source.id)
        try:
            dialog_exist = DialogMessages.objects.filter(readers__user=msg_to, readers__message__autor=msg_from).order_by('-id')[0]
        except IndexError:
            dialog_exist = None

        reader_type = '1'
        msg_obj = News.objects.create(
            title = 'Сообщение',
            text = msg,
            autor = msg_from,
            site = current_site,
            subdomain = '0',
            reader_type = '1',
        )

        reader = NewsReaders.objects.create(user=msg_to, status='0', message=msg_obj)

        if dialog_exist:
            dialog_exist.readers.add(reader)
        else:
            dialog_obj = DialogMessages()
            dialog_obj.save()
            dialog_obj.readers.add(reader)




#@timer
def get_rutracker_topics_closed():

    REG_SIZE = re.compile(r'\[\d+\.?\d+?\s?\w+\]')
    REG_SLUG = re.compile(ur'[a-zа-я0-9]+')

    source = ImportSources.objects.get(url='http://rutracker.org/')

    films = SourceFilms.objects.filter(source_obj=source)
    films_dict = {}
    for i in films:
        films_dict[i.name_alter] = i
        
    url = 'http://rutracker.org/forum/index.php?closed=1'
    req = urllib.urlopen(url)
    for_del = []
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="windows-1251")
        
        nav = data.find('ul')
        if nav:
            for i in nav.findAll('li'):
                title = i.b.text.strip().encode('utf-8')
                if ' / ' in title:
                    name_alt = re.findall(REG_SLUG, low(title).decode('utf-8'))
                    name_alt = ''.join(name_alt)
                    obj = films_dict.get(name_alt)
                    if obj:
                        for_del.append(obj.id)

    SourceFilms.objects.filter(pk__in=set(for_del)).delete()

    '''
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        return HttpResponse(str(data))
        nav = data.find('div', {'class': 'cl-pg'})
        for a in nav.findAll('a'):
            link = a.get('href').encode('utf-8')
            if 'start' in link:
                new_url = '%sforum/%s' % (source.url, link)
                links.append(new_url)
    
    for url in links:
        req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            for i in data.findAll('b'):
                title = i.text.encode('utf-8').strip()
                if ' / ' in title:
                
                    name_alt = re.findall(REG_SLUG, low(title).decode('utf-8'))
                    name_alt = ''.join(name_alt)
                    
                    obj = films_dict.get(name_alt)
                    if obj:
                        obj.delete()
    '''
    cron_success('xml', source.dump, 'films_closed', 'Закрытые фильмы') 

# УДАЛИТЬ
@only_superuser
@never_cache
def rutracker_test(request):

    source = ImportSources.objects.get(url='http://rutracker.org/')

    source_films = SourceFilms.objects.filter(source_obj=source, extra='new')
    if not source_films:
        source_films = SourceFilms.objects.filter(source_obj=source)

    films = {}
    for i in source_films:
        new = True if i.extra == 'new' else False
        films[i.kid] = {'obj': i, 'names': {'name_en': None, 'name_ru': None}, 'source_id': i.source_id, 'new': new, 'release': ''}

    for i in list(Film.objects.using('afisha').filter(pk__in=films.keys()).values('id', 'date')):
        films[i['id']]['release'] = i['date'] if i['date'] else datetime.datetime(3000,1,1)


    names = list(FilmsName.objects.using('afisha').filter(type__in=(1, 2), status=1, film_id__id__in=films.keys()).values("film_id", "name", "type"))
    
    for i in names:
        if i['type'] == 1:
            films[i['film_id']]['names']['name_en'] = i['name'].strip()
        else:
            films[i['film_id']]['names']['name_ru'] = i['name'].strip()
    

    films = sorted(films.values(), key=operator.itemgetter('release'), reverse=True)

    upd = []

    html = u'''
        <link rel="stylesheet" href="http://kinoinfo.ru/static/base/css/style.css" type="text/css" media="screen" />
        <table class="modern_tbl">
            <th></th>
            <th>Релиз</th>
            <th>Название</th>
            <th>Источник</th>
        '''
    for i in films:
        kinoinfo_url = u'http://kinoinfo.ru/film/%s/' % i['obj'].kid
        name = u'%s / %s' % (i['names']['name_ru'], i['names']['name_en'])
        source_url = u'http://rutracker.org/forum/viewtopic.php?t=%s' % i['obj'].source_id
        if i['new']:
            new = '<span style="color: #009933;">NEW</span>'
            upd.append(i['obj'].id)
        else:
            new = ''
        release = tmp_date(i['release'], 'j E Y') if i['release'].year != 3000 else u'Нет'
        html += u'<tr><td>%s</td><td>%s</td><td><a href="%s" target="_blank">%s</a></td><td><a href="%s" target="_blank">перейти</a></td></tr>' % (new, release, kinoinfo_url, name, source_url)

    html += u'</table>'

    SourceFilms.objects.filter(pk__in=upd).update(extra=None)

    return HttpResponse(str(html.encode('utf-8')))