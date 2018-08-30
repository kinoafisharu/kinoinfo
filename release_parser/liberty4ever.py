#-*- coding: utf-8 -*- 
import httplib2
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
from user_registration.ajax import create_by_email
from user_registration.func import md5_string_generate



@timer
def get_liberty4ever_cat():

    source = ImportSources.objects.get(url='http://web.archive.org/web/20110208000925/http://www.liberty4ever.com/downloads.html')
    
    xml = ''
    
    req = urllib.urlopen(source.url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        for span in data.findAll('span', {'class': 'smalltext'}):
            for a in span.findAll('a'):
                a = a.get('href')
                if u'http://www.liberty4ever.com' in a:
                    xml += u'<a href="%s"></a>' % a
                
    create_dump_file('%s_main_links' % source.dump, settings.API_DUMP_PATH, u'<data>%s</data>' % xml)


@timer
def get_liberty4ever_artist():
    source = ImportSources.objects.get(url='http://web.archive.org/web/20110208000925/http://www.liberty4ever.com/downloads.html')

    main_url = 'http://web.archive.org'
    
    xml = ''
    
    with open('%s/dump_%s_main_links.xml' % (settings.API_DUMP_PATH, source.dump), 'r') as f:
        xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    for link in xml_data.findAll('a'):
        url = link['href']
    
        req = urllib.urlopen('%s%s' % (main_url, url))
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            for td in data.findAll('td', {'class': 'windowbg', 'width': '10%'}):
                img = td.find('img')
                img = img['src'] if img else ''
                
                td2 = td.find_next('td', {'class': 'windowbg2'})
                if td2:
                    a = td2.find('a')
                    a_href = a.get('href')
                    a_txt = a.text.strip().replace(u'&',u'&amp;').replace(u'"',u'&quot;')

                    xml += u'<a href="%s" name="%s" img="%s"></a>' % (a_href, a_txt, img)

    create_dump_file('%s_artist_links' % source.dump, settings.API_DUMP_PATH, u'<data>%s</data>' % xml)


#@timer
def get_liberty4ever_track():

    def get_tracklist(table, name, img, musicians, tracks, person_type, main_url):
        tracklist = []
        for tr in table.findAll('tr'):
            td = tr.findAll('td', limit=1)
            if td:
                td = td[0]
            
                a = td.find('a')
                if a:
                    track_href = a.get('href')
                    track_name = a.text.strip()

                    track = ''
                    slug = ''

                    parts = track_name.split(' - ')
                    if len(parts) > 1:
                        track = parts[1].split('(')[0].strip()
                        track = track.split('+')[0].strip()
                        slug = low(del_separator(track.encode('utf-8')))
                    
                    if track:
                        track_id = '%s-%s' % (low(del_separator(name.encode('utf-8'))), slug)
                        
                        track_obj = tracks.get(track_id)
                        
                        if not track_obj:
                            track_obj = Composition.objects.create(source_id=track_id)
                            for tname in ({'n': track, 's': 2}, {'n': slug, 's': 5}):
                                track_name_obj, track_name_obj_created = CompositionName.objects.get_or_create(
                                    name = tname['n'],
                                    status = tname['s'],
                                    defaults = {
                                        'name': tname['n'],
                                        'status': tname['s'],
                                    })
                                track_obj.name.add(track_name_obj)
                            tracks[track_id] = track_obj
                            
                            
                        if track_obj:
                            musician = musicians.get(name)
                            if not musician:

                                musician = Person.objects.create(artist=True)

                                name_obj, name_created = NamePerson.objects.get_or_create(
                                    name = name, 
                                    status = 4, 
                                    defaults = {
                                        'name': name, 
                                        'status': 4,
                                    })
                                musician.name.add(name_obj)
                            
                                resp, content = httplib2.Http().request('%s%s' % (main_url, img), method="GET")
                                poster_path_db = ''
                                if resp['status'] == '200' and content:
                                    ext = img.split('.')[-1]
                                    file_name = '%s_%s.%s' % (musician.id, md5_string_generate(musician.id), ext)
                                    poster_path = '%s/%s' % (settings.PERSONS_IMGS, file_name)
                                    poster_path_db = poster_path.replace(settings.MEDIA_ROOT, '')
                                    
                                    with open(poster_path, 'wb') as f:
                                        f.write(content)
                                        
                                if poster_path_db:
                                    img_obj = Images.objects.create(file=poster_path_db, status='1')
                                    musician.poster.add(img_obj)
                            
                                musicians[name] = musician

                            try:
                                cpr = CompositionPersonRel.objects.get(type=person_type, person=musician, composition=track_obj)
                            except CompositionPersonRel.DoesNotExist:
                                if track_id not in tracklist:
                                    cpr = CompositionPersonRel.objects.create(person=musician, composition=track_obj)
                                    cpr.type.add(person_type)
                                    tracklist.append(track_id)
            
        return musicians, tracks


    def get_data(xml_data, musicians, tracks, parsed, person_type, main_url):
        for link in xml_data.findAll('a'):
            url = link['href']
            name = link['name']
            img = link['img']
            if url not in parsed:
                req = urllib.urlopen('%s%s' % (main_url, url))
                if req.getcode() == 200:
                    data = BeautifulSoup(req.read(), from_encoding="utf-8")
                    
                    error = True if data.find('div', id='error') else False
      
                    if not error:
                        table = data.find('table', {'class': 'table_grid'})
                        if 'http://www.liberty4ever.com/downloads/view/' in str(table):
                            musicians, tracks = get_tracklist(table, name, img, musicians, tracks, person_type, main_url)
                            parsed.append(url)
                        else:
                            xml_links = ''
                            for td in data.findAll('td', {'class': 'windowbg', 'width': '10%'}):
                                img = td.find('img')
                                img = img['src'] if img else ''
                                
                                td2 = td.find_next('td', {'class': 'windowbg2'})
                                if td2:
                                    a = td2.find('a')
                                    a_href = a.get('href')
                                    a_txt = a.text.strip().replace(u'&',u'&amp;').replace(u'"',u'&quot;')

                                    xml_links += u'<a href="%s" name="%s" img="%s"></a>' % (a_href, a_txt, img)
                                    
                            if xml_links:
                                open('%s/dump_%s_artist_links2.xml' % (settings.API_DUMP_PATH, source.dump), 'a').write(str(xml_links.encode('utf-8')))
                    CompositionTrackTmp.objects.create(url=url, error=error)
                else:
                    CompositionTrackTmp.objects.create(url=url, error=True)
        return parsed, musicians, tracks   

    source = ImportSources.objects.get(url='http://web.archive.org/web/20110208000925/http://www.liberty4ever.com/downloads.html')

    main_url = 'http://web.archive.org'
    
    person_type = CompositionPersonType.objects.get(name='исполнение')
    parsed = list(CompositionTrackTmp.objects.all().values_list('url', flat=True))
    
    tracks = {}
    for i in Composition.objects.all().only('source_id', 'id').exclude(source_id=None):
        tracks[i.source_id] = i
        
    persons = {}
    for i in Person.objects.only('name', 'poster', 'id').filter(artist=True):
        persons[i.id] = i
    
    musicians = {}
    for i in NamePerson.objects.filter(status=4, person__pk__in=persons.keys()).values('name', 'person__pk'):
        obj = persons.get(i['person__pk'])
        musicians[i['name']] = obj
    
    with open('%s/dump_%s_artist_links.xml' % (settings.API_DUMP_PATH, source.dump), 'r') as f:
        xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")

    parsed, musicians, tracks = get_data(xml_data, musicians, tracks, parsed, person_type, main_url)
    
    time.sleep(1)
    
    try:
        with open('%s/dump_%s_artist_links2.xml' % (settings.API_DUMP_PATH, source.dump), 'r') as f:
            xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")

        parsed, musicians, tracks = get_data(xml_data, musicians, tracks, parsed, person_type, main_url)
    except IOError:
        pass
        
    return HttpResponse(str())
    
    
