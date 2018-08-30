#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import random
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils import simplejson as json
from django.db.models import Q
from django import db
from django.template.defaultfilters import date as tmp_date

from bs4 import BeautifulSoup
from base.models import *
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success, give_me_cookie


def cinemate_cc_login():
    source = ImportSources.objects.get(url='http://cinemate.cc/')
    
    opener = give_me_cookie()

    url = '%slogin/' % source.url

    req = opener.open(urllib2.Request(url))

    page = BeautifulSoup(req.read(), from_encoding="utf-8")

    login_form = page.find('form', id="login_form")

    if login_form:
        csrf = login_form.find('input', {'name': 'csrfmiddlewaretoken'})['value']

        login = 'movie_guzzler'
        passwd = 'P0mk67H2kq'

        values = urllib.urlencode({
            'csrfmiddlewaretoken': csrf,
            'username' : login,
            'password' : passwd,
        })

        # отправка формы авторизации
        url += '?next=/profile/%s/' % login
        
        try:
            req = opener.open(urllib2.Request(url, values))
        except urllib2.HTTPError, error:
            return {'source': source, 'opener': opener, 'error': error.read()}

    return {'source': source, 'opener': opener, 'error': ''}



def get_cinemate_cc_film(data, source, ignored, noffilms):
    flist = []
    for div in data.findAll('div', {'class': "movie-brief"}):
        h3 = div.find('h3')
        a = h3.find('a')
        film_url = a.get('href')
        film_id = int(film_url.replace('/movie/','').replace('/',''))
        film_name = a.text.encode('utf-8')
        film_slug = low(del_separator(film_name))

        if film_slug.decode('utf-8') not in ignored and film_id not in noffilms:
            full_url = '%s%s' % (source.url, film_url.lstrip('/'))
            film_year = int(h3.find('small').text.encode('utf-8').replace('(','').replace(')',''))

            next = False

            ul = div.find('ul')
            for link in ul.findAll('a'):
                a_txt = link.text.encode('utf-8').strip()
                if a_txt == 'Скачать':
                    next = True

            if next:
                flist.append({
                    'id': film_id,
                    'name': film_name,
                    'slug': film_slug,
                    'year': film_year,
                    'url': full_url,
                })
    return flist


def cinemate_cc_soon():
    '''
    login = cinemate_cc_login()
    if login['error']:
        return HttpResponse(str(login['error']))
    else:
        opener = login['opener']
        source = login['source']
    '''

    source = ImportSources.objects.get(url='http://cinemate.cc/')

    opener = give_me_cookie()

    ignored = get_ignored_films()

    data_nof_film = ''
    noffilms = []

    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[int(i.source_id)] = i
    fdict = get_all_source_films(source, source_films)

    send_msg = False

    for main_url in ('%smovies/soon' % source.url, '%smovies/cinema' % source.url):

        req = opener.open(urllib2.Request(main_url))

        data = BeautifulSoup(req.read(), from_encoding="utf-8")

        nav = data.find('div', {'class': "navigation"})
        nav_link = nav.findAll('a')[-1]
        last_page = int(nav_link.get('href').split('?page=')[-1])

        if last_page > 10:
            last_page = 10

        film_list = get_cinemate_cc_film(data, source, ignored, noffilms)

        for page in xrange(2, (last_page + 1)):
            time.sleep(random.uniform(1.0, 2.5))
            url = '%s?page=%s' % (main_url, page)
            try:
                req = opener.open(urllib2.Request(url))
                data = BeautifulSoup(req.read(), from_encoding="utf-8")
                film_list += get_cinemate_cc_film(data, source, ignored, noffilms)
            except urllib2.HTTPError: 
                pass


        for i in film_list:
            
            obj = films.get(i['id'])
            next_step = checking_obj(obj)
            
            if next_step:
                if obj:
                    kid = obj.kid
                else:
                    kid, info = film_identification(i['slug'], None, {}, {}, year=i['year'], source=source)
        
                objt = None
                if kid:
                    create_new, objt = unique_func(fdict, kid, obj)
                    if create_new:
                        objt = create_sfilm(i['id'], kid, source, i['name'], year=i['year'], txt=datetime.datetime.now().date(), extra='new')
                        films[i['id']] = objt
                        if not fdict.get(kid):
                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                        fdict[kid]['script_rel'].append(objt)
                        send_msg = True
                elif not obj:
                    data_nof_film += xml_noffilm(i['name'], i['slug'], None, None, i['id'], info, i['url'].encode('utf-8'), source.id)
                    noffilms.append(i['id'])
    
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'films', 'Фильмы в сети')

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




def cinemate_cc_get_links():
    source = ImportSources.objects.get(url='http://cinemate.cc/')

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)[:50]
    for i in source_films:
        films[int(i.source_id)] = i

    torrents = list(CinemateTorrents.objects.filter(film__source_id__in=films.keys()).values_list('go_link_id', flat=True))

    opener = give_me_cookie()

    for source_id, film in films.iteritems():

        url = '%smovie/%s/links/#tabs' % (source.url, source_id)
        req = opener.open(urllib2.Request(url))
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        table = data.find('div', {'class': "table"})
        for div in table.findAll('div', {'class': "row delimiter"}):
            td_div = div.findAll('div')
            tracker = td_div[2].text.strip().encode('utf-8')
            quality = td_div[3].text.strip().encode('utf-8')
            size = td_div[-1].text.strip().encode('utf-8')
            link_id = div.find('a', {'class': "icon_t download-link"}).get('href','').replace('/go/s/','').replace('/','')

            if link_id not in torrents:

                go_url = '%sgo/s/%s' % (source.url, link_id)
                go_req = opener.open(urllib2.Request(go_url))
                go_data = BeautifulSoup(go_req.read(), from_encoding="utf-8")

                main = go_data.find('div', {'class': "main"})

                a = main.find('a', rel="nofollow").get('href')

                CinemateTorrents.objects.create(
                    film = film,
                    go_link_id = link_id,
                    link = a,
                    tracker = tracker,
                    quality = quality,
                    file_size = size,
                )

        time.sleep(random.uniform(0.8, 1.2))

    cron_success('html', source.dump, 'links', 'Ссылки на трекеры')

# УДАЛИТЬ
@only_superuser
@never_cache
def cinemate_cc_test(request):

    source = ImportSources.objects.get(url='http://cinemate.cc/')

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
        source_url = u'http://cinemate.cc/movie/%s/' % i['obj'].source_id
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