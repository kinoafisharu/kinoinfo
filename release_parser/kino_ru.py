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
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success
from user_registration.views import get_user

@timer
def get_kino_ru():

    current_site = DjangoSite.objects.get(domain='kinoinfo.ru')

    REG_YEAR = re.compile(r'\d{4}\sгод.')
    REG_DATETIME = re.compile(r'\s?\-\s\d{2}\:\d{2}\:\d{2}\s\d{2}\s.*\s\d{4}')

    ignored = get_ignored_films()
    
    data_nof_film = ''
    noffilms = []

    source = ImportSources.objects.get(url='http://www.kino.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    users = {}
    for i in SourceUsers.objects.select_related('profile').filter(source_obj=source):
        users[i.source_id] = i
    
    text_ids = list(NewsFilms.objects.filter(source_obj=source).values_list('source_id', flat=True))
    
    forum_dict = {}

    urls = (source.url, '%safisha/page/2' % source.url, '%safisha/page/3' % source.url)
    
    for url in urls:
        # фильмы
        req = urllib.urlopen(url)
        if not req.getcode() == 200:
            time.sleep(7)
            req = urllib.urlopen(url)
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")

            for article in data.findAll('article', {'class': "post"}):
                
                film_url = article.find('a', {'class': 'h2'})

                film_id = film_url.get('href')
                full_url = u'%s%s' % (source.url, film_id.lstrip('/'))

                film_id = film_id.replace('/film/','')
                
                film_name = film_url.text.strip().encode('utf-8')
                film_slug = low(del_separator(film_name))
                
                info_country = article.find('div', {'class': 'info-country'})
                year = int(info_country.findAll('a')[-1].text.strip())

                comments_exist = article.find('div', {'class': 'comments'})

                if comments_exist and film_id.encode('utf-8') not in noffilms and film_slug.decode('utf-8') not in ignored:
                    forum_href = '%s/comments' % full_url
                    obj = films.get(film_id)
                    next_step = checking_obj(obj)
                    
                    if next_step:
                        if obj:
                            kid = obj.kid
                        else:
                            kid, info = film_identification(film_slug, None, {}, {}, year=year, source=source)
                
                        objt = None
                        if kid:
                            create_new, objt = unique_func(fdict, kid, obj)
                            if create_new:
                                objt = create_sfilm(film_id, kid, source, film_name, year=year)
                                films[film_id] = objt
                                if not fdict.get(kid):
                                    fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                fdict[kid]['script_rel'].append(objt)
                        elif not obj:
                            data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id.encode('utf-8'), info, full_url.encode('utf-8'), source.id)
                            noffilms.append(film_id.encode('utf-8'))
                
                        if objt:
                            forum_dict[film_id] = {'obj': objt, 'href': forum_href}

        # отзывы и авторы
        for k, v in forum_dict.iteritems():
            req = urllib.urlopen(v['href'])
            if not req.getcode() == 200:
                time.sleep(7)
                req = urllib.urlopen(v['href'])

            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")

                for post in data.findAll('div', {'class': 'post-comment'}):
                    user_data = post.find('a', {'class': 'login_name'})
                    if user_data:

                        user_name = user_data.text.strip().encode('utf-8')
                        user_id = user_data.get('href').replace('/user/','')

                        user_obj = users.get(user_id)
                        if user_obj:
                            profile = user_obj.profile
                        else:
                            new_user = get_user()
                            new_user.first_name = user_name
                            new_user.save()
                            profile = Profile.objects.get(user=new_user)
                            user_obj = SourceUsers.objects.create(
                                source_id = user_id,
                                source_obj = source,
                                profile = profile,
                            )
                            users[user_id] = user_obj

                        date_comment = post.find('div', {'class': 'date-comment'})
                        com_time, com_date = date_comment.findAll('a')

                        com_day, com_month, com_year = com_date.text.encode('utf-8').strip().split()
                        com_month = get_month(com_month)
                        com_hour, com_minute = com_time.text.encode('utf-8').split(':')

                        com_dtime = datetime.datetime(int(com_year), int(com_month), int(com_day), int(com_hour), int(com_minute), 0)

                        text_id = com_time.get('href').replace('/film/%s/comments/' % k,'')

                        text = post.find('div', {'class': 'text-comment'}).text.encode('utf-8').strip()

                        if text_id not in text_ids:
             
                            news = News.objects.create(
                                title = '',
                                text = text,
                                visible = True,
                                autor = profile,
                                autor_nick = 1,
                                site = current_site,
                                subdomain = 0,
                                reader_type = '8',
                            )

                            news.dtime = com_dtime
                            news.save()

                            NewsFilms.objects.create(
                                kid = v['obj'].kid,
                                message = news,
                                source_id = text_id,
                                source_obj = source,
                            )

                            text_ids.append(text_id)
                                    

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'films', 'Фильмы и отзывы')
