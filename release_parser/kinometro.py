#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import random


from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django import db

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, distributor_identification, xml_noffilm, get_ignored_films, language_identify
from decors import timer
from release_parser.func import cron_success
from release_parser.kinobit_cmc import checking_obj, unique_func, sfilm_clean


def get_all_kinometro_films(sfilms=[]):
    fdict = {}
    if not sfilms:
        sfilms = ReleasesRelations.objects.select_related('release').all()
    for i in sfilms:
        if not fdict.get(i.film_kid):
            fdict[i.film_kid] = {'editor_rel': [], 'script_rel': []}
        if i.rel_dtime:
            fdict[i.film_kid]['editor_rel'].append(i)
        else:
            fdict[i.film_kid]['script_rel'].append(i)
    return fdict


def get_kinometro_data(data):

    REG = re.compile(r'\(.*?\)')
    
    div = data.find('div', {'class': 'c11'})
    film_name = div.find('p', {'class': 'ftitle'}).text.strip().encode('utf-8')
    
    f_name_details = REG.findall(film_name)
    details = ''
    if f_name_details:
        for i in f_name_details:
            try:
                if str(i) not in details:
                    details += str(i).decode('utf-8')
            except (UnicodeDecodeError, TypeError): pass
                
    film_name = REG.sub('', film_name)
    
    # разбор названий фильмов в теге
    f_name = film_name.split('/')
    if len(f_name) == 2:
        f_name_ru, f_name_en = (f_name[0], f_name[1])
    elif len(f_name) > 2:
        f_name_ru, f_name_en = language_identify(f_name)
    else:
        f_name_ru, f_name_en = (f_name[0], '')
        
    f_name_ru = f_name_ru.replace(' ', '').replace('"', "'").strip().decode('utf-8')
    f_name_en = f_name_en.replace(' ', '').replace('"', "'").strip().decode('utf-8')
    
    distr_name = None
    distr_id = None
    release = None
    runtime = None
    copies = None

    for tr in div.table.tbody.find_all('tr'):
        td = tr.find_all('td')
        # получение дистрибьютора
        if td[0].text.encode('utf-8') == 'Дистрибьютор:':
            distr = td[1].text.encode('utf-8').split('/')
            distr_name1, distr_name2 = (distr[0].strip().decode('utf-8'), distr[1].strip().decode('utf-8')) if len(distr) > 1 else (distr[0].strip().decode('utf-8'), None)
            tag_a = td[1].findAll('a')
            if len(tag_a) > 1:
                distr_id1, distr_id2 = (tag_a[0].get('href'), tag_a[1].get('href'))
            elif len(tag_a) < 1:
                distr_id1, distr_id2 = (None, None)
            elif len(tag_a) == 1:
                t = td[1].prettify().split(' /')
                d_id = tag_a[0].get('href')
                distr_id1 = None
                distr_id2 = None
                if len(t) > 1:
                    if d_id in t[0]:
                        distr_id1 = d_id
                    elif d_id in t[1]:
                        distr_id2 = d_id
                else:
                    distr_id1 = d_id
            if distr_id1:
                distr_id1 = distr_id1.replace('/distributor/show/id/','').encode('utf-8')
            if distr_id2:
                distr_id2 = distr_id2.replace('/distributor/show/id/','').encode('utf-8')
        # получение даты релиза
        elif td[0].text.encode('utf-8') == 'Дата начала проката в России:':
            release = td[1].text.strip().encode('utf-8')
        # получение хронометража
        elif td[0].text.encode('utf-8') == 'Хронометраж:':
            runtime = td[1].text.strip().encode('utf-8').replace(' минут', '').replace(' минуты', '').replace('~', '')
        # получение кол-ва копий
        elif td[0].text.encode('utf-8') == 'Количество копий:':
            copies = td[1].text.strip().encode('utf-8').replace('~', '')
            
    if release:
        release = REG.sub('', release).strip()
        day, month, year = release.split('.')
        release = datetime.date(int(year), int(month), int(day))
    
    return f_name_ru, f_name_en, details, release, distr_name1, distr_name2, distr_id1, distr_id2, copies, runtime
    

@timer
def kinometro_films_pages_OLD():

    source = ImportSources.objects.get(url='http://www.kinometro.ru/')
    
    today = datetime.date.today()
    last_month = today - datetime.timedelta(days=25)
    
    releases = Releases.objects.filter(release_date__gte=last_month)

    xml_for_delete = ''
    ignore_urls = []
    
    for ind, i in enumerate(releases):
        req = urllib.urlopen(i.url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            
            f_name_ru, f_name_en, details, release, distr_name1, distr_name2, distr_id1, distr_id2, copies, runtime = get_kinometro_data(data)

            i.name_ru = f_name_ru
            i.name_en = f_name_en
            i.details = details
            i.release_date = release
            i.distributor1 = distr_name1
            i.distributor1_id = distr_id1
            i.distributor2 = distr_name2
            i.distributor2_id = distr_id2
            i.copies = copies
            i.runtime = runtime
            i.save()

        elif req.getcode() == 404:
            # несущесвующий/удаленный id у источника
            xml_for_delete += '<film name_ru="%s" name_en="%s" release_id="%s" url="%s"></film>' % (i.name_ru, i.name_en, i.id, i.url)
        
        ignore_urls.append(i.url)
        
        if ind % 50 == 0:
            time.sleep(random.uniform(1.0, 3.0))

    req_main = urllib.urlopen('%srelease' % source.url)
    if req_main.getcode() == 200:
        count = 0
        page_data = BeautifulSoup(req_main.read(), from_encoding="utf-8")
        table = page_data.find('table', {'class': 'sr_tbl'})
        for tr in table.findAll('tr'):
            link = tr.findAll('a', limit=1)
            if link:
                url_part = link[0].get('href').lstrip('/')
                film_id = url_part.replace('release/card/id/','')
                url = '%s%s' % (source.url, url_part)
                if url.decode('utf-8') not in ignore_urls:
                    count += 1
                    req2 = urllib.urlopen(url)
                    if req2.getcode() == 200:
                        page = BeautifulSoup(req2.read(), from_encoding="utf-8")
                        
                        f_name_ru, f_name_en, details, release, distr_name1, distr_name2, distr_id1, distr_id2, copies, runtime = get_kinometro_data(page)
                        
                        if release:
                            Releases.objects.create(
                                name_ru = f_name_ru, 
                                name_en = f_name_en,
                                details = details,
                                film_id = film_id,
                                url = url,
                                release_date = release,
                                distributor1 = distr_name1,
                                distributor1_id = distr_id1,
                                distributor2 = distr_name2,
                                distributor2_id = distr_id2,
                                copies = copies,
                                runtime = runtime,
                            )
                        
                            
                    if count % 50 == 0:
                        time.sleep(random.uniform(1.0, 3.0))
    
    create_dump_file('release_film_for_delete', settings.API_DUMP_PATH, xml_for_delete.encode('utf-8'))
    cron_success('html', source.dump, 'releases', 'Релизы')
    


@timer
def kinometro_films_pages():
    
    rel = set(list(ReleasesRelations.objects.all().values_list('release', flat=True)))
    Releases.objects.exclude(pk__in=rel).delete()
    
    source = ImportSources.objects.get(url='http://www.kinometro.ru/')
    
    today = datetime.date.today()
    last_month = today - datetime.timedelta(days=25)
    
    releases_new = Releases.objects.filter(release_date__gte=last_month)
    releases_all = set(list(Releases.objects.all().values_list('film_id', flat=True)))
    releases_all = [int(i) for i in releases_all]

    xml_for_delete = ''
    ignore_urls = []
    
    for ind, i in enumerate(releases_new):
        if i.film_id not in ignore_urls:
            req = urllib.urlopen(i.url)
            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")
                
                f_name_ru, f_name_en, details, release, distr_name1, distr_name2, distr_id1, distr_id2, copies, runtime = get_kinometro_data(data)

                i.name_ru = f_name_ru
                i.name_en = f_name_en
                i.details = details
                if release:
                    i.release_date = release
                i.distributor1 = distr_name1
                i.distributor1_id = distr_id1
                i.distributor2 = distr_name2
                i.distributor2_id = distr_id2
                i.copies = copies
                i.runtime = runtime
                i.save()
                
            elif req.getcode() == 404:
                # несущесвующий/удаленный id у источника
                xml_for_delete += '<film name_ru="%s" name_en="%s" release_id="%s" url="%s"></film>' % (i.name_ru, i.name_en, i.id, i.url)
        
            ignore_urls.append(int(i.film_id))
        
            if ind % 50 == 0:
                time.sleep(random.uniform(1.0, 3.0))
    
    id = None
    
    req_main = urllib.urlopen(source.url)
    if req_main.getcode() == 200:
        page_data = BeautifulSoup(req_main.read(), from_encoding="utf-8")
        main = page_data.findAll('table', {'class': 'relprev'})
        main = main[1]
        a = main.findAll('a', limit=1)[0]
        id = int(a.get('href').replace('/release/card/id/',''))
    
    
    if id:
        range_to = id - 9000
        count = 0
        for i in sorted(xrange(range_to, id + 1), reverse=True):
            url = '%srelease/card/id/%s' % (source.url, i)
            
            if i not in releases_all:
                count += 1
                
                req2 = urllib.urlopen(url)
                if req2.getcode() == 200:
                    page = BeautifulSoup(req2.read(), from_encoding="utf-8")
                    
                    f_name_ru, f_name_en, details, release, distr_name1, distr_name2, distr_id1, distr_id2, copies, runtime = get_kinometro_data(page)
                    
                    if release:
                        Releases.objects.create(
                            name_ru = f_name_ru, 
                            name_en = f_name_en,
                            details = details,
                            film_id = i,
                            url = url,
                            release_date = release,
                            distributor1 = distr_name1,
                            distributor1_id = distr_id1,
                            distributor2 = distr_name2,
                            distributor2_id = distr_id2,
                            copies = copies,
                            runtime = runtime,
                        )
                    
                if count % 50 == 0:
                    time.sleep(random.uniform(1.0, 3.0))
                    
    create_dump_file('release_film_for_delete', settings.API_DUMP_PATH, xml_for_delete.encode('utf-8'))
    cron_success('html', source.dump, 'releases', 'Релизы')

def sfilm_clean_kinometro():
    dict = {}
    for_delete = []
    for i in ReleasesRelations.objects.select_related('release').all():
        if dict.get(i.release.film_id):
            for_delete.append(i.id)
        else:
            dict[i.release.film_id] = i
    ReleasesRelations.objects.filter(pk__in=for_delete).delete()
    
    dict = {}
    for_delete = []
    for i in Releases.objects.all():
        if dict.get(i.film_id):
            for_delete.append(i.id)
        else:
            dict[i.film_id] = i
    Releases.objects.filter(pk__in=for_delete).delete()


@timer
def film_kinometro_ident():
    '''
    Идентификация фильмов кинометро
    '''
    source = ImportSources.objects.get(url='http://www.kinometro.ru/')

    xml_nof_data = ''
    distr_nof_data = ''
    nof_distributors = []
    noffilms = []
    
    sfilm_clean_kinometro()
    
    ignored = get_ignored_films()
    
    films = {}
    source_films = ReleasesRelations.objects.select_related('release').all()
    for i in source_films:
        films[i.release.film_id] = i
        
    fdict = get_all_kinometro_films(source_films)

    exe_releases = list(ReleasesRelations.objects.all().values_list('release', flat=True))
    releases = Releases.objects.exclude(id__in=exe_releases)

    for release in releases:
        # получение, приведение к нужному виду названий фильмов
        film_name_ru = release.name_ru.encode('utf-8')
        film_name_en = release.name_en.encode('utf-8')
        slug_name_ru = low(del_separator(del_screen_type(film_name_ru)))
        slug_name_en = low(del_separator(del_screen_type(film_name_en)))
        
        if not slug_name_ru:
            slug_name_ru = slug_name_en
            film_name_ru = film_name_en
        else:
            if not slug_name_en:
                slug_name_en = slug_name_ru
                film_name_en = film_name_ru
        
        # получаю данные дистрибьюторов, привожу к нужному виду, получаю объект дистрибьютор для иднтифик. фильма
        dlist = []
        distr_dict = [
            {'name': release.distributor1, 'id': release.distributor1_id},
            {'name': release.distributor2, 'id': release.distributor2_id}
        ]
        distr_temp_data = ''
        distr_data = ''
        for i in distr_dict:
            if i['name']:
                
                distr_name = i['name'].encode('utf-8').replace('&', '&amp;')
                distr_alt = i['id'].encode('utf-8').replace('&', '&amp;') if i['id'] else ''
                distr_slug = low(del_separator(distr_name))
                distr_temp_data += '<distributor value="%s" code="%s" kid=""></distributor>' % (
                    distr_name, distr_alt
                )
                distr, status = distributor_identification(distr_name, distr_slug)
                if distr:
                    dlist.append(distr.kid)
                    kid = distr.kid if distr.kid else 0
                    distr_data += '<distributor value="%s" code="%s" kid="%s"></distributor>' % (
                        distr_name, distr_alt, kid
                    )
                else:
                    if distr_slug.decode('utf-8') not in nof_distributors:
                        distr_nof_data += '<distributor value="%s" slug="%s" alt="%s"></distributor>' % (
                            distr_name, distr_slug, distr_alt
                        )
                        nof_distributors.append(distr_slug.decode('utf-8'))
        
        if not distr_data:
            distr_data = distr_temp_data

        ru_ignore = False
        if slug_name_ru.decode('utf-8') in ignored:
            ru_ignore = True
        en_ignore = False
        if slug_name_en.decode('utf-8') in ignored:
            en_ignore = True
        
        if not ru_ignore and not en_ignore:
            nof_flag = True
            if dlist:
                # определяем фильтры для дальнейшей выборки
                d1, d2 = (dlist[0], dlist[1]) if len(dlist) > 1 else (dlist[0], None)

                film_id = release.film_id
                
                if film_id not in noffilms:
                
                    obj = films.get(film_id)
                    
                    next_step = checking_obj(obj)
                    
                    if next_step:
                        skip = False
                        if obj:
                            kid = obj.release.film_kid
                        else:
                            try:
                                kid, info = film_identification(slug_name_ru, slug_name_en, d1, d2, source=source)
                            except db.backend.Database._mysql.OperationalError:
                                skip = True
                    
                        if not skip:
                            objt = None
                            if kid:
                                create_new, objt = unique_func(fdict, kid, obj, kinometro=True)
                                if create_new:

                                    new = ReleasesRelations.objects.create(
                                        film_kid = kid,
                                        release = release,
                                        distributor_kid = dlist[0],
                                        rel_dtime = datetime.datetime.now(),
                                    )
                                    
                                    films[film_id] = new
                            elif not obj:
                                xml_nof_data += xml_noffilm(film_name_ru, slug_name_ru, film_name_en, slug_name_en, release.film_id, info, release.url.encode('utf-8'), source.id)
                                noffilms.append(film_id)

            else:
                info = 'Нет такого дистрибьютора'
                xml_nof_data += xml_noffilm(film_name_ru, slug_name_ru, film_name_en, slug_name_en, release.film_id, info, release.url.encode('utf-8'))
    
    create_dump_file('%s_nof_distributor' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % distr_nof_data)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % xml_nof_data)
    
    cron_success('html', source.dump, 'releases', 'Идентификация фильмов и дистр.')




