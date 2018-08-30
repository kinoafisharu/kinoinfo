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

from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup

from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, distributor_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success



@timer
def get_cinemaplex_releases():
    ignored = get_ignored_films()

    distr_nof_data = ''
    data_nof_film = ''
    noffilms = []
    nof_distributors = []
    distributors = {}

    source = ImportSources.objects.get(url='http://cinemaplex.ru/')
    sfilm_clean(source)
    
    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)
    
    today = datetime.datetime.today()

    url = '%s2013/01/30/release-schedule.html' % source.url
    
    '''
    with open('cinemaplex.htm','r') as f:
        main = BeautifulSoup(f.read(), from_encoding="utf-8")

    if main:
    '''

    req = urllib.urlopen(url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")

        main = data.find('div', {'class': 'post-entry'})
        main = main.find('tbody')
        
        release_date = None

        for tr in main.findAll('tr'):
            
            all_td = tr.findAll('td')

            if len(all_td) == 1:
                if all_td[0].text.strip():
                    try:
                        release_first, release_last = all_td[0].text.encode('utf-8').split('—')
                    except ValueError:
                        try:
                            release_first, release_last = all_td[0].text.encode('utf-8').split('–')
                        except ValueError:
                            release_first, release_last = all_td[0].text.encode('utf-8').split('-')

                    release_first = release_first.replace('\xc2\xa0','').strip()

                    try:
                        release_first = int(release_first)
                    except ValueError:
                        release_last = release_first
                        release_first = release_first.split()[0].strip()


                    release_month = release_last.strip().split()[1]
                    release_day = int(release_first)
                    release_month = int(get_month(release_month))

                    past_month_range = []
                    for m in [1, 2, 3, 4]:
                        past_dates = today - relativedelta(months=+m)
                        past_month_range.append(past_dates.month)

                    if release_month in past_month_range or (release_month == today.month and release_day <= today.day):
                        release_date = None
                    else:
                        release_year = today.year if release_month >= today.month else today.year + 1
                        release_date = datetime.date(release_year, release_month, release_day)
            elif release_date:
                film_name = all_td[0].text.encode('utf-8').strip()
                distributor = all_td[1].text.encode('utf-8').replace('&', '&amp;').split(',')[0].strip()
                #copies = all_td[2].text.encode('utf-8').strip()
                runtime = all_td[3].text.encode('utf-8').strip()
                #genres = all_td[5].text.encode('utf-8').strip()
                #limits = all_td[7].text.encode('utf-8').strip()
                try:
                    details = all_td[8].text.encode('utf-8').strip()
                except IndexError:
                    details = ''

                f_name = film_name.split('/')
                if len(f_name) == 2:
                    f_name_ru, f_name_en = (f_name[0].strip(), f_name[1].strip())
                else:
                    f_name_ru, f_name_en = (f_name[0].strip(), f_name[0].strip())
                    
                film_slug_ru = low(del_separator(f_name_ru))
                film_slug_en = low(del_separator(f_name_en))
                film_slug = low(del_separator(film_name))
                film_id = film_slug
                full_url = None

                
                
                '''
                current_release_date = re.findall(r'с\s\d+\.\d+', details)
                if current_release_date:
                    current_release_day = current_release_date[0].replace('с ','').split('.')[0]
                    current_release_date = datetime.date(int(release_date.year), int(release_date.month), int(current_release_day))
                else:
                    current_release_date = release_date
                '''
                if film_slug_ru:
                    if film_id not in noffilms and film_slug_ru.decode('utf-8') not in ignored:
                    
                        # дистрибьютор
                        distributor_slug = low(del_separator(distributor))
                        distributor_kid = distributors.get(distributor_slug)

                        if not distributor_kid and distributor_slug.decode('utf-8') not in nof_distributors:
                            distr, status = distributor_identification(distributor, distributor_slug)
                            if distr:
                                distributor_kid = distr.kid if distr.kid else None
                                distributors[distributor_slug] = distributor_kid
                            else:
                                distr_nof_data += '<distributor value="%s" slug="%s" alt="%s"></distributor>' % (
                                    distributor, distributor_slug, ''
                                )
                                nof_distributors.append(distributor_slug.decode('utf-8'))


                        if distributor_kid:        

                            obj = films.get(film_id.decode('utf-8'))
                            next_step = checking_obj(obj)
                            
                            if next_step:
                                if obj:
                                    kid = obj.kid
                                else:
                                    kid, info = film_identification(film_slug_ru, film_slug_en, distributor_kid, {}, source=source)
                        
                                objt = None
                                if kid:
                                    create_new, objt = unique_func(fdict, kid, obj)
                                    if create_new:
                                        objt = create_sfilm(film_id, kid, source, f_name_ru)
                                        films[film_id.decode('utf-8')] = objt
                                        if not fdict.get(kid):
                                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                        fdict[kid]['script_rel'].append(objt)
                                elif not obj:
                                    data_nof_film += xml_noffilm(f_name_ru, film_slug_ru, f_name_en, film_slug_en, film_id, info, full_url, source.id)
                                    noffilms.append(film_id)
                                

                                if objt:
                                    sr_obj, sr_created = SourceReleases.objects.get_or_create(
                                        film = objt,
                                        source_obj = source,
                                        defaults = {
                                            'film': objt,
                                            'distributor': distributor,
                                            'source_obj': source,
                                            'release': release_date,
                                        })
                                    if not sr_created:
                                        if sr_obj.release != release_date:
                                            sr_obj.release = release_date
                                            sr_obj.save()


                                    runtime = runtime.replace('-','').strip()
                                    if runtime:
                                        runtime = runtime.split("'")[0].split('’')[0]
                                        runtime = runtime.replace("'", '').replace('’', '')

                                        extra = '%s' % runtime
                                        if objt.extra != extra:
                                            objt.extra = extra
                                            objt.save()
                        else:
                            info = 'Нет такого дистрибьютора'
                            data_nof_film += xml_noffilm(f_name_ru, film_slug_ru, f_name_en, film_slug_en, film_id, info, full_url, source.id)
                            noffilms.append(film_id)
                
    create_dump_file('%s_nof_distributor' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % distr_nof_data)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'releases', 'Релизы') 

