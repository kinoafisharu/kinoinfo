#-*- coding: utf-8 -*- 
import urllib
import urllib2
import httplib2
import re
import datetime
import time
import cookielib
import operator
import requests

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup

from base.models import *
from api.func import resize_image
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser, md5_string_generate
from kinoinfo_folder.func import get_month_en, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from decors import timer
from release_parser.func import cron_success, get_imdb_id, give_me_cookie

        
@timer
def get_imdb_film_list():

    source = ImportSources.objects.get(url='http://www.imdb.com/')

    url = '%scalendar/?region=us' % source.url
    
    opener = give_me_cookie()
    req = opener.open(urllib2.Request(url))
    
    xml = ''
    ids = []
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        div = data.find('div', id="main")
        old_date = ''
        for h4 in div.findAll('h4'):
            release = h4.string.encode('utf-8')
            day, month, year = release.split()
            
            month = get_month_en(low(month))
            
            rel_date = '%s-%s-%s' % (year, month, day)

            xml += '<date v="%s">' % rel_date
                
            ul = h4.find_next('ul')
            
            for li in ul.findAll('li'):
                year = li.find('span', {'class': "year_type"}).string.encode('utf-8')
                if 'documentary' not in low(year):
                    year = re.findall(r'\d+', year)
                    if year:
                        details = li.find('i')
                        if details:
                            details = str(details).encode('utf-8').replace('<i>','').replace('</i>','')
                            details = details.replace('(','').replace(')','')
                        else:
                            details = ''
                            
                        if 'limited' not in low(details) and 'fest' not in low(details) or 'tv premiere' not in low(details):
                            film_name = li.a.string.encode('utf-8').replace('"', '&quot;').replace('&','&amp;')
                            film_slug = low(del_separator(film_name))
                            full_url = li.a.get('href').encode('utf-8')
                            imdb_id = full_url.replace('/title/tt', '').replace('/', '')
                        
                            xml += '<film n="%s" s="%s" y="%s" id="%s" d="%s" r="%s"></film>' % (film_name, film_slug, year[0], imdb_id, details, rel_date)
                            ids.append(imdb_id)
                    
            xml += '</date>'
    ids = ';'.join(set(ids))
    xml = '<data><ids value="%s">%s</ids></data>' % (ids, xml)

    create_dump_file('%s_film_list' % source.dump, settings.API_DUMP_PATH, xml)
    cron_success('html', source.dump, 'films_list', 'Список релизов')


def get_imdb_poster(url, name):
    obj = None
    resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method="GET")
    if content:
        poster_path = '%s/%s.jpg' % (settings.POSTERS_EN_PATH, name)
        
        with open(poster_path, 'wb') as f:
            f.write(content)

        resized = resize_image(1000, None, content, 1500)
        if resized:
            resized.save(poster_path)

        obj = Images.objects.create(
            file = poster_path.replace(settings.MEDIA_ROOT, ''),
            status = 0,
        )
    return obj




def parse_imdb(main_data, count, source, imdb, is_dump, images, country_data, genres_data, persons_data, productions, distr_objs, film_object, films, language, distr_nof_data, data_nof_persons, nof_distr, nof_persons, release_format, country_id, release):
    limits = {
        'G': 0,
        'PG': 6,
        'PG-13': 12,
        'R': 16,
        'NC-17': 18,
    }
    
    imdb = get_imdb_id(imdb)
    opener = give_me_cookie()
    url = '%stitle/tt%s/' % (source.url, imdb)
    try:
        #req = opener.open(urllib2.Request(url))
	req = requests.get(url)
    except urllib2.HTTPError:
        req = None
    film_obj = None
    if req.status_code == 200:
        data = BeautifulSoup(req.text, 'html.parser')
        
        #open('imdb.html','w').write(str(data))

        imdb = long(imdb)
        
        fname = main_data.get('fname')
        fslug = main_data.get('fslug')
        fyear = main_data.get('fyear')
        details = main_data.get('details','')
        
        new_interface = data.find('div', {'class': "title_block"})

        if not is_dump:
            # название
            if new_interface:
                #fname = data.find('h1', itemprop="name")
                fname = data.find('div', {'class': "title_block"}).find('h1')
                try:
                    fname.find('span').extract()
                except AttributeError: pass
                fname = fname.text.strip().encode('utf-8')
            else:
                h1 = data.find('h1', {'class': 'header'})
                fname = h1.find('span', itemprop="name").text.strip().encode('utf-8')

            fslug = low(del_separator(fname))
            
            # год
            if new_interface:
                year_tmp = data.find('title').text.replace(u' - IMDb','')
                # если такого вида 'The Expanse (2015)'
                year = re.findall(r'\(\d{4}\)$', year_tmp)
                if year:
                    fyear = year[0].replace('(','').replace(')','').strip()
                else:
                    # если такого вида 'The Expanse (TV Series 2015– )'
                    year = re.findall(r'\(.*\d{4}.*\)$', year_tmp)
                    if year:
                        year = re.findall(r'\d{4}', year[0].strip())
                        fyear = year[0] if year else fyear
                open('errors.txt','a').write('point2')
            else:
                year = h1.find('span', {'class': 'nobr'})
                if year:
                    if year.find('a'):
                        year = year.find('a').text.encode('utf-8').strip()
                    else:
                        year = year.text.encode('utf-8').replace('(','').replace(')','').split('–')[0].strip()

                    try:
                        fyear = int(year)
                    except ValueError:
                        fyear = int(year.split()[-1])
            
            # дата релиза
            if not release:
                url_release = '%sreleaseinfo' % url
                time.sleep(2)
                req_release = requests.get(url_release)
                if req_release.status_code == 200:
                    data_release = BeautifulSoup(req_release.text, 'html.parser')

                    table = data_release.find('table', id='release_dates')
                    if table:
                        for ttr in table.findAll('tr'):
                            tds = ttr.findAll('td')
                            td_country = tds[0].find('a').text.encode('utf-8').strip()
                            td_release = tds[1].text.encode('utf-8').strip()
                            td_details = tds[2].text.encode('utf-8').strip()
                            if td_country == 'USA' and '(' not in td_details:
                                try:
                                    td_day, td_month, td_year = td_release.split()
                                    td_month = get_month_en(low(td_month.encode('utf-8')))
                                    release = datetime.date(int(td_year), int(td_month), int(td_day))
                                except ValueError: pass
        # постер
        if new_interface:
            poster = data.find('div', {'class': 'poster'})
        else:
            poster = data.find('td', id="img_primary")
            if poster:
                poster = poster.find('div', {'class': 'image'})
        if poster:
            if new_interface:
                #poster = poster.find('img', itemprop="image").get('src').split('@._')[0]
                poster = poster.find('img').get('src').split('@._')[0]
            else:
            
                poster = poster.find('img').get('src').split('@._')[0]

            poster += '@._V1_SX640_SY720_.jpg'
            
            poster_name = 'poster__%s' % md5_string_generate('%s%s' % (poster, datetime.datetime.now()))
            
            while poster_name.decode('utf-8') in images:
                poster_name = 'poster__%s' % md5_string_generate('%s%s' % (poster, datetime.datetime.now()))
            
            images.append(poster_name.decode('utf-8'))
        else:
            poster = None
        # ограничения
        if new_interface:
            title_block = data.find('div', {'class': "title_block"})

	    limit = title_block.find('div', {'class': 'subtext'})
	    for key in limits.keys():
		if limit.text.find(key) != -1:
		    limit = limits.get(key)
		    break

            genres_tmp = [gen.text.encode('utf-8') for gen in title_block.findAll('span', itemprop="genre")]

            div_details = data.find('div', id="titleDetails")

            runtime = div_details.find('time')
        else:
            div = data.find('div', {'class': "infobar"})

            limit = div.find('span', itemprop="contentRating")
            if limit:
                limit = limit.get('content').encode('utf-8')
                limit = limits.get(limit)

            #genres_tmp = [gen.string.encode('utf-8') for gen in div.findAll('span', itemprop="genre")]
    	    for item in title_block.findAll('a'):
    	        if item.attrs['href'].find('genre') != -1:
    	                genres_tmp.append(item.text.encode('utf-8'))
    	    
            runtime = div.find('time', itemprop="duration")
        if runtime:
            runtime = runtime.text.strip().encode('utf-8')
            runtime = int(re.findall(r'\d+', runtime)[0])
        # рейтинг
        imdb_rate = data.find('div', {'class': 'imdbRating'})
        imdb_votes = None
        if imdb_rate:
            #imdb_rate = float(imdb_rate.text.encode('utf-8'))
            imdb_votes = int(imdb_rate.find('span', {'class': 'small'}).text.replace(',', ''))
            imdb_rate = float(imdb_rate.find('div', {'class': 'ratingValue'}).find('strong').find('span').text)
            #imdb_votes = data.find('span', itemprop="ratingCount")
            #imdb_votes = int(imdb_votes.text.encode('utf-8').replace(u' ', '').replace(u',', ''))
        # жанры
        genres = []
        if len(genres_tmp) == 1 and genres_tmp[0] == 'Crime':
            # детектив
            gen_obj = Genre.objects.get(name='детектив')
            genres.append(gen_obj)
        elif 'Action' in genres_tmp and 'Drama' in genres_tmp:
            # драму не импортируем
            for genr in genres_tmp:
                if genr != 'Drama':
                    gen_obj = genres_data.get(genr)
                    genres.append(gen_obj)
        elif 'Romance' in genres_tmp:
            if 'Comedy' in genres_tmp:
                # драму не импортируем
                for genr in genres_tmp:
                    if genr != 'Drama':
                        gen_obj = genres_data.get(genr)
                        genres.append(gen_obj)
            elif 'Drama' in genres_tmp:
                # мелодрама
                gen_obj = Genre.objects.get(name='мелодрама')
                genres.append(gen_obj)
                for genr in genres_tmp:
                    if genr != 'Drama' and genr != 'Romance':
                        gen_obj = genres_data.get(genr)
                        genres.append(gen_obj)
            else:
                for genr in genres_tmp:
                    gen_obj = genres_data.get(genr)
                    genres.append(gen_obj)
        else:
            for genr in genres_tmp:
                gen_obj = genres_data.get(genr)
                genres.append(gen_obj)
            
        if 'Horror' in genres_tmp:
            if not limit or limit < 16:
                limit = 16

        note = None
        if new_interface:
            persons = []
            persons_block = data.find('div', {'class': "plot_summary_wrapper"})
#            for pb in persons_block.findAll('span', itemprop="director"):
	    for pb in persons_block.findAll('div', {'class': 'credit_summary_item'}):
                pb_a = pb.find('a')
                pb_name = pb_a.text.encode('utf-8').strip()
                if pb_name:
                    pb_id = pb_a.get('href').split('?')[0]
                    pb_id = long(pb_id.replace('/name/nm', '').replace('/', ''))
                    persons.append({'name': pb_name, 'action': 3, 'status': 1, 'id': pb_id})
            
            for pb in persons_block.findAll('div', {'class': 'credit_summary_item'}):
#	     for pb in persons_block.findAll('div', {'class': 'credit_summary_item'}):
		pb_a = pb.find('a')
                pb_name = pb_a.text.encode('utf-8').strip()
                if pb_name:
                    pb_type = pb_a.next_sibling
                    if u'screenplay' in pb_type:
                        pb_id = pb_a.get('href').split('?')[0]
                        pb_id = long(pb_id.replace('/name/nm', '').replace('/', ''))
                        persons.append({'name': pb_name, 'action': 4, 'status': 1, 'id': pb_id})

#            for pb in persons_block.findAll('span', itemprop="actors"):
	    for pb in persons_block.findAll('div', {'class': 'credit_summary_item'}):
                pb_a = pb.find('a')
                pb_name = pb_a.text.encode('utf-8').strip()
                if pb_name:
                    pb_id = pb_a.get('href').split('?')[0]
                    pb_id = long(pb_id.replace('/name/nm', '').replace('/', ''))
                    persons.append({'name': pb_name, 'action': 1, 'status': 1, 'id': pb_id})

            budget_obj = None
            countries = []
            production = []
            for div in div_details.findAll('div', {'class': "txt-block"}):
                h4 = div.find('h4')
                if h4:
                    if h4.text == u'Country:':
                        for a in div.findAll('a'):
                            country_obj = country_data.get(a.text)
                            countries.append(country_obj)
                    elif h4.text == u'Budget:':
                        budget = div
                        budget.find('h4').extract()
                        budget.find('span').extract()
                        budget = budget.text.encode('utf-8').strip()
                        if '$' in budget or '€' in budget:
                            budget = budget.replace(' ', '').replace(',', '').replace('.', '')
                            
                            budget_sum = re.findall(r'\d+\s?', budget)[0]
                            if '$' in budget:
                                budget_cur = '$'
                            elif '€' in budget:
                                budget_cur = '€'
                            
                            if film_object and film_object['obj'].budget:
                                film_object['obj'].budget.budget = int(budget_sum)
                                film_object['obj'].budget.currency = budget_cur
                                film_object['obj'].budget.save()
                            else:
                                budget_obj = Budget.objects.create(
                                    budget = int(budget_sum),
                                    currency = budget_cur,
                                )
        else:
            budget_obj = None
            countries = []
            production = []
            persons = []
            for div in data.findAll('div', {'class': "txt-block"}):
                h4 = div.find('h4')
                if h4:
                    if h4.string == u'Country:':
                        for a in div.findAll('a'):
                            country_obj = country_data.get(a.string)
                            countries.append(country_obj)
                    elif h4.string == u'Budget:':
                        budget = div
                        budget.find('h4').extract()
                        budget.find('span').extract()
                        budget = budget.text.encode('utf-8').strip()
                        if '$' in budget or '€' in budget:
                            budget = budget.replace(' ', '').replace(',', '').replace('.', '')
                            
                            budget_sum = re.findall(r'\d+\s?', budget)[0]
                            if '$' in budget:
                                budget_cur = '$'
                            elif '€' in budget:
                                budget_cur = '€'
                            
                            if film_object and film_object['obj'].budget:
                                film_object['obj'].budget.budget = int(budget_sum)
                                film_object['obj'].budget.currency = budget_cur
                                film_object['obj'].budget.save()
                            else:
                                budget_obj = Budget.objects.create(
                                    budget = int(budget_sum),
                                    currency = budget_cur,
                                )
                    elif h4.string == u'Director:':
                        for d in div.findAll('a'):
                            d_name = d.find('span', itemprop="name")
                            if d_name:
                                d_name = d_name.string
                                d_id = d.get('href').split('?')[0]
                                d_id = long(d_id.replace('/name/nm', '').replace('/', ''))
                                persons.append({'name': d_name, 'action': 3, 'status': 1, 'id': d_id})
                    elif h4.string == u'Writers:':
                        for w in div.findAll('a'):
                            p_name = w.find('span', itemprop="name")
                            if p_name:
                                p_name = p_name.string
                                p_type = w.next_sibling
                                w_id = w.get('href').split('?')[0]
                                w_id = long(w_id.replace('/name/nm', '').replace('/', ''))
                                if u'screenplay' in p_type:
                                    persons.append({'name': p_name, 'action': 4, 'status': 1, 'id': w_id})
                    elif h4.string == u'Stars:':
                        for s in div.findAll('a'):
                            s_name = s.find('span', itemprop="name")
                            if s_name:
                                s_name = s_name.string
                                s_id = s.get('href').split('?')[0]
                                s_id = long(s_id.replace('/name/nm', '').replace('/',''))
                                persons.append({'name': s_name, 'action': 1, 'status': 1, 'id': s_id})

        distributors = []
        url2 = '%scompanycredits' % url
        time.sleep(1.5)
        req2 = requests.get(url2)
    	if req2.status_code == 200:
            #data2 = BeautifulSoup(req2.read(), from_encoding="utf-8")
            data2 = BeautifulSoup(req2.text, 'html.parser')
            distr_h4 = data2.find('h4', {'name': "distributors"})
            if distr_h4:
                ul = distr_h4.find_next("ul")
                for link in ul.findAll('a'):
                    distr_name = link.text.encode('utf-8')
                    if distr_name not in nof_distr:
                        distr_details = link.next_sibling.encode('utf-8').strip()
                        
                        if country_id == 1:
                            cntry = 'USA'
                        else:
                            cntry = 'France'

                        if cntry in distr_details and 'theatrical' in distr_details:
                            distr_year = re.findall(r'\d{4}', distr_details)
                            distr_year = distr_year[0] if distr_year else None
                            distributors.append({'year': distr_year, 'name': distr_name})

        distr_data = []
        if distributors:
            distributors = sorted(distributors, key=operator.itemgetter('year'))
            cur_year = distributors[0]['year']
            for distrib in distributors:
                if distrib['year'] == cur_year:
                    distr_slug = low(del_separator(distrib['name']))
                    distr_obj = distr_objs.get(distr_slug)
                    if distr_obj:
                        distr_data.append(distr_obj)
                    else:
                        distr_nof_data += '<distributor value="%s" slug="%s" alt="%s"></distributor>' % (distrib['name'].replace('&', '&amp;'), distr_slug, None)
                        nof_distr.append(distrib['name'])
        poster_obj = None
        if poster:
            time.sleep(1.5)
            poster_obj = get_imdb_poster(poster, poster_name)

        person_list = []
        for pe in persons:
            person_id = pe['id']
            person_obj = persons_data.get(person_id)
            if person_obj:
                person_list.append({'person': person_obj, 'st': pe['status'], 'act': pe['action']})
            else:
                if person_id not in nof_persons:
                    try:
                        person_name = pe['name'].decode('utf8').encode('utf-8')
                    except UnicodeEncodeError:
                        person_name = pe['name'].encode('utf-8')
                    person_slug = low(del_separator(person_name))
                    data_nof_persons += '<person name="%s" slug="%s" code="%s" name_alt="" slug_alt=""></person>' % (person_name, person_slug, person_id)
                    nof_persons.append(pe['id'])
        new = False
        if film_object:
            if not film_object['obj'].imdb_id:
                film_object['obj'].imdb_id = imdb
            if not film_object['obj'].budget and budget_obj:
                film_object['obj'].budget = budget_obj
            if film_object['obj'].runtime != runtime:
                film_object['obj'].runtime = runtime
            if film_object['obj'].imdb_votes != imdb_votes:
                film_object['obj'].imdb_votes = imdb_votes
                film_object['obj'].imdb_rate = imdb_rate
            if film_object['obj'].year != fyear:
                film_object['obj'].year = fyear
            film_object['obj'].save()
        else:
            film_obj = Films.objects.create(
                year = fyear,
                note = note,
                runtime = runtime,
                rated = limit,
                budget = budget_obj,
                imdb_id = imdb,
                imdb_rate = imdb_rate,
                imdb_votes = imdb_votes,
            )
            film_object = {'releases': [], 'obj': film_obj}
            new = True
        
        
            if is_dump:
                films[int(imdb)] = {'obj': film_obj, 'releases': []}
                
        
        if release and release not in film_object['releases']:
            rel_obj = FilmsReleaseDate.objects.create(
                release = release,
                note = details,
                format = release_format,
                country_id = country_id,
            )
            film_object['obj'].release.add(rel_obj)
        
            if is_dump:
                films[int(imdb)]['releases'].append(rel_obj.release)
        
        if not new:
            for img in film_object['obj'].images.filter(status=0):
                img_p = '%s%s' % (settings.MEDIA_ROOT, img.file)
                try:
                    os.remove(img_p)
                except OSError: pass
                film_object['obj'].images.remove(img)
                img.delete()
                
        if poster_obj:
            film_object['obj'].images.add(poster_obj)
        
        
        film_names = [
            {'name': fname, 'status': 1},
            {'name': fslug, 'status': 2},
        ]
        for f in film_names:
            name_obj, name_created = NameFilms.objects.get_or_create(
                name = f['name'].strip(),
                status = f['status'],
                language = language,
                defaults = {
                    'name': f['name'].strip(),
                    'status': f['status'],
                    'language': language,
                })
            
            for fn in film_object['obj'].name.all():
                if fn.status == f['status'] and fn.language == language:
                    film_object['obj'].name.remove(fn)
                    
            film_object['obj'].name.add(name_obj)
            
        for c in countries:
            if c:
                if new:
                    film_object['obj'].country.add(c)
                else:
                    if c not in film_object['obj'].country.all():
                        film_object['obj'].country.add(c)
            
        for g in genres:
            if g:
                if new:
                    film_object['obj'].genre.add(g)
                else:
                    if g not in film_object['obj'].genre.all():
                        film_object['obj'].genre.add(g)
            
        for pr in production:
            if pr:
                if new:
                    film_object['obj'].production.add(pr)
                else:
                    if pr not in film_object['obj'].production.all():
                        film_object['obj'].production.add(pr)
        
        for pers in person_list:
            rel_fp, rel_fp_created = RelationFP.objects.get_or_create(
                person = pers['person'],
                status_act_id = pers['st'],
                action_id = pers['act'],
                films = film_object['obj'],
                defaults = {
                    'person': pers['person'],
                    'status_act_id': pers['st'],
                    'action_id': pers['act'],
                    'films': film_object['obj'],
                })
        
        for dis_data in distr_data:
            if new:
                film_object['obj'].distributor.add(dis_data)
            else:
                if dis_data not in film_object['obj'].distributor.all():
                    film_object['obj'].distributor.add(dis_data)

        film_obj = film_object['obj']
        count += 1

    return count, film_obj, distr_nof_data, data_nof_persons, nof_distr, nof_persons
            

def create_film_by_imdb_id(imdb):

    distr_nof_data = ''
    data_nof_persons = ''
    nof_distr = []
    nof_persons = []

    source = ImportSources.objects.get(url='http://www.imdb.com/')
    film_object = {}
    films = {}

    genres_data = {}
    for i in Genre.objects.all():
        if i.name_en:
            genres_data[i.name_en] = i

    country_data = {}
    for i in Country.objects.all():
        if i.name_en:
            country_data[i.name_en] = i

    productions = {}
    for i in ProductionsCo.objects.all():
        productions[i.name] = i

    persons_data = {}
    for i in Person.objects.exclude(Q(iid=None) | Q(iid=0) | Q(kid=None)):
        persons_data[i.iid] = i

    distr_names = {}
    for i in NameDistributors.objects.filter(status=2, distributors__usa=True).values('distributors', 'name'):
        distr_names[int(i['distributors'])] = i['name'].encode('utf-8')

    distr_objs = {}
    for i in Distributors.objects.filter(usa=True):
        dname = distr_names.get(i.id, '')
        distr_objs[dname] = i

    images = list(Images.objects.all().values_list('file', flat=True))

    language = Language.objects.get(pk=2)

    count = 0
    release_format = '0'
    main_data = {}
    is_dump = False
    country_id = 1
    release = None
    check_imdb_rate = False
    
    try:
        film_obj = Films.objects.get(imdb_id=imdb)
        check_imdb_rate = True
    except Films.DoesNotExist:
        # создаем в БД киноинфо
        count, film_obj, distr_nof_data, data_nof_persons, nof_distr, nof_persons = parse_imdb(main_data, count, source, imdb, is_dump, images, country_data, genres_data, persons_data, productions, distr_objs, film_object, films, language, distr_nof_data, data_nof_persons, nof_distr, nof_persons, release_format, country_id, release)
        if film_obj:
            film_obj.generated = True
            film_obj.generated_dtime = datetime.datetime.now()
            film_obj.save()
    
    # создаем в БД киноафиши
    if check_imdb_rate:
        if film_obj and not film_obj.imdb_votes:
            opener = give_me_cookie()
            url = '%stitle/tt%s/' % (source.url, imdb)
            req = opener.open(urllib2.Request(url))

            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")

                imdb_rate = data.find('span', itemprop="ratingValue")
                imdb_votes = None
                if imdb_rate:
                    imdb_rate = float(imdb_rate.string)
                    imdb_votes = data.find('span', itemprop="ratingCount")
                    imdb_votes = int(imdb_votes.string.replace(u' ', '').replace(u',', ''))
    
                film_obj.imdb_votes = imdb_votes
                film_obj.imdb_rate = imdb_rate
                film_obj.save()
    
    from film.views import film_create_new_func
    ka_film = None
    if film_obj:
        name = NameFilms.objects.get(status=1, language__id=2, films__pk=film_obj.id).name
        
        ka_film = film_create_new_func(name, film_obj.year, 1, create=False)
        
        ka_film.idalldvd = film_obj.imdb_id
        ka_film.runtime = film_obj.runtime
        ka_film.imdb = film_obj.imdb_rate if film_obj.imdb_rate else 0
        ka_film.imdb_votes = film_obj.imdb_votes if film_obj.imdb_votes else 0
        ka_film.save()
        
        film_obj.kid = ka_film.id
        film_obj.save()

    return ka_film


def get_imdb_data(xml, is_dump, country_id=1, ids=[], upd=False, film_kid=None):
    distr_nof_data = ''
    data_nof_persons = ''
    nof_distr = []
    nof_persons = []

    source = ImportSources.objects.get(url='http://www.imdb.com/')
    film_object = {}
    films = {}
    
    
    if is_dump:
        with open('%s/dump_%s_film_list.xml' % (settings.API_DUMP_PATH, source.dump), 'r') as f:
            xml = BeautifulSoup(f.read(), from_encoding="utf-8")
    
        ids = xml.find('ids').get('value').split(';')
        ids = [int(i) for i in ids]
        
        for i in Films.objects.filter(imdb_id__in=ids):
            films[int(i.imdb_id)] = {'obj': i}
            films[int(i.imdb_id)]['releases'] = [j.release for j in i.release.all()]
        
    else:
        xml = BeautifulSoup(xml, from_encoding="utf-8")
        
        film_object = {}
        if ids:
            try:
                film_object = Films.objects.get(imdb_id=ids[0])
                film_object = {'obj': film_object, 'releases': [i.release for i in film_object.release.all()]}
            except Films.DoesNotExist: pass
        

    genres_data = {}
    for i in Genre.objects.all():
        if i.name_en:
            genres_data[i.name_en] = i

    country_data = {}
    for i in Country.objects.all():
        if i.name_en:
            country_data[i.name_en] = i

    productions = {}
    for i in ProductionsCo.objects.all():
        productions[i.name] = i

    persons_data = {}
    for i in Person.objects.exclude(Q(iid=None) | Q(iid=0) | Q(kid=None)):
        persons_data[i.iid] = i

    
    distr_names = {}
    for i in NameDistributors.objects.filter(status=2, distributors__usa=True).values('distributors', 'name'):
        distr_names[int(i['distributors'])] = i['name'].encode('utf-8')

    distr_objs = {}
    for i in Distributors.objects.filter(usa=True):
        dname = distr_names.get(i.id, '')
        distr_objs[dname] = i


    images = list(Images.objects.all().values_list('file', flat=True))

    language = Language.objects.get(pk=2)

    count = 0
    good = 0
    for i in xml.findAll('film'):
        fname = i['n'].encode('utf-8')
        fslug = i['s'].encode('utf-8')
        fyear = i['y'].encode('utf-8')
        imdb = i['id'].encode('utf-8')
        details = i['d'].encode('utf-8')
        
        main_data = {
            'fname': fname,
            'fslug': fslug,
            'fyear': fyear,
            'details': details,
        }
        
        if details:
            tmp_det = low(details)
            if 'fest' in tmp_det:
                release_format = '1'
            elif 'limit' in tmp_det:
                release_format = '2'
            elif 'dvd' in tmp_det:
                release_format = '3'
            elif 'blu-ray' in tmp_det:
                release_format = '4'
            elif 'internet' in tmp_det:
                release_format = '5'
            elif '3-d' in tmp_det:
                release_format = '6'
            elif 'tv premiere' in tmp_det:
                release_format = '8'
            else:
                release_format = '7'
        else:
            release_format = '0'
            
        release = None
        if i['r']:        
            year, month, day = i['r'].split('-')
            release = datetime.date(int(year), int(month), int(day))
        
        if is_dump:
            film_object = films.get(int(imdb))
        
        parse = False
        if film_object:
            if not upd:
                if release and release not in film_object['releases']:
                    rel_obj = FilmsReleaseDate.objects.create(
                        release = release,
                        note = details,
                        format = release_format,
                        country_id = country_id,
                    )
                    film_object['obj'].release.add(rel_obj)
            else:
                parse = True
                
        else:
            parse = True
            
        if parse:
            count, film_obj, distr_nof_data, data_nof_persons, nof_distr, nof_persons = parse_imdb(main_data, count, source, imdb, is_dump, images, country_data, genres_data, persons_data, productions, distr_objs, film_object, films, language, distr_nof_data, data_nof_persons, nof_distr, nof_persons, release_format, country_id, release)
            if film_obj:
                good += 1

            if count == 100: #!!!!!!!!!!!!!
                break

                        
        time.sleep(2)

    #RelationFP.objects.filter(films__imdb_id=None).delete()
    #Films.objects.filter(imdb_id=None).delete()
    
    return data_nof_persons, distr_nof_data, source.dump, good
        

@timer
def get_imdb_film():
    
    data_nof_persons, distr_nof_data, dump, good = get_imdb_data(None, True, 1)
    
    create_dump_file('%s_nof_person' % dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_persons)
    create_dump_file('%s_nof_distributor' % dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % distr_nof_data)
    cron_success('html', dump, 'films_data', 'Данные релизов')



@timer
def imdb_film_ident():
    source = ImportSources.objects.get(url='http://www.imdb.com/')
    
    films = Films.objects.filter(kid=None)
    films_ids = [i.imdb_id for i in films]

    exist_films = Film.objects.using('afisha').filter(idalldvd__in=films_ids)
    exist_ids = {}
    for i in exist_films:
        exist_ids[i.idalldvd] = i.id

    data_nof_film = ''
    
    for i in films:
        name = None
        for j in i.name.filter(status=1, language__id=2):
            name = j.name.encode('utf-8')
            
        slug = low(del_separator(name))
        
        kid = exist_ids.get(long(i.imdb_id))
        
        if kid:
            i.kid = kid
            i.save()
        else:
            full_url = '%stitle/tt%s/' % (source.url, i.imdb_id)
            data_nof_film += xml_noffilm(name, slug, None, None, i.imdb_id, 'Фильм не найден', full_url.encode('utf-8'), source.id)
            
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'films_ident', 'Идентификация')
    


@only_superuser
@never_cache
def imdb_film_show(request):
    
    filmsdata = Films.objects.select_related('budget').all().order_by('-id')[:100]
    
    txt = ''
    for films in filmsdata:
        name = films.name.filter(status=1)[0]
        txt += '<h2><a href="http://www.imdb.com/title/tt%s/">%s (%s)</a></h2>' % (films.imdb_id, name.name.encode('utf-8'), films.year)
        
        for i in films.images.all():
            txt += '<img src="%s%s" width="240" /><br />' % (settings.MEDIA_URL, i.file.encode('utf-8'))
            
        country = ''
        for i in films.country.all():
            if country:
                country += ', '
            country += i.name.encode('utf-8')
            
        txt += country
        txt += '<br />'
        
        genre = ''
        for i in films.genre.all():
            if genre:
                genre += ', '
            genre += i.name.encode('utf-8')
        
        txt += genre
        txt += '<br />'
        
        if films.runtime:
            txt += '%s min<br />' % films.runtime
        
        if films.budget:
            txt += '%s %s<br />' % (films.budget.budget, films.budget.currency.encode('utf-8'))
        
        if films.rated:
            txt += '+%s<br />' % films.rated
        
        
        rel = ''
        for i in films.release.all():
            if rel:
                rel += ', '
            rel += '%s' % i.release
            if i.format != '0':
                f = '%s' % i.get_format_display().encode('utf-8')
                if i.format == '1' or i.format == '7':
                    f += ' - %s' % i.note.encode('utf-8')
                rel += ' (%s)' % f
            
        txt += rel
        txt += '<br />'
        
        if films.imdb_rate:
            txt += 'Rate: %s; Votes: %s<br />' % (films.imdb_rate, films.imdb_votes)
        
        pr = ''
        for i in films.distributor.all():
            if pr:
                pr += ', '
            for j in i.name.filter(status=1):
                pr += '%s' % j.name.encode('utf-8')
            
        txt += pr
        txt += '<br /><br />'
        
        fp = RelationFP.objects.select_related('person', 'action', 'status_act').filter(films=films)
        
        for i in fp:
            pname = ''
            for j in i.person.name.filter(status=1, language__id=2):
                pname = j.name.encode('utf-8')
                
            txt += '%s (%s, %s)<br />' % (pname, i.status_act, i.action)
        
        txt += '<hr /><br />'
        
    return HttpResponse(str(txt))
    #return render_to_response('release_parser/kinoinfo_import_info.html', {'p': p, 'page': page}, context_instance=RequestContext(request))  
    
    

def imdb_searching(query, exact=False):
    params = {
        'q': query,
        's': 'tt',
    }
    
    if exact:
        params['exact'] = 'true'
        
    body = urllib.urlencode(params)
    
    url = 'http://www.imdb.com/find?%s' % body
    
    resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url)
    
    result = []
    
    count = 0
    
    current_year = datetime.datetime.now().year
    
    from_year = current_year - 2
    to_year = current_year + 2

    if resp['status'] == '200':
        data = BeautifulSoup(content, "html5lib", from_encoding="utf-8")
        
        table = data.find('table', {'class': 'findList'})

        if table:

            for tr in table.findAll('tr'):
                td = tr.find('td', {'class': "result_text"})
                
                year = td.text.encode('utf-8')
                year = re.findall('\(\d+\)', year)
                if year:
                    year = int(year[0].replace('(','').replace(')','').strip())

                go = True
                if exact:
                    go = True if year >= from_year and year <= to_year else False

                if go and year:
                    count += 1
                    
                    a = td.find('a')
                    
                    aka = td.find('i')
                    aka = aka.string.encode('utf-8') if aka else ''  
                    
                    link = a.get('href').split('?')[0]
                    title = a.text.encode('utf-8')
                    
                    opener = give_me_cookie()
                    url2 = 'http://www.imdb.com%s' % link
                    req = opener.open(urllib2.Request(url2))
                    
                    imdb_id = int(link.replace('/title/tt', '').replace('/',''))
                    
                    persons = []
                    
                    if req.getcode() == 200:
                        data2 = BeautifulSoup(req.read(), "html5lib", from_encoding="utf-8")

                        #h1 = data2.find('h1', {'class': "header"})
                        #year = h1.find('span', {'class': "nobr"}).text.encode('utf-8').replace('(','').replace(')','')
                        
                        for div in data2.findAll('div', {'class': "txt-block"}):
                            h4 = div.find('h4')
                            if h4 and h4.string == u'Director:':
                                for d in div.findAll('a'):
                                    d_name = d.find('span', itemprop="name")
                                    if d_name:
                                        persons.append(d_name.string)
                    
                    result.append({'title': title, 'persons': persons, 'link': link, 'year': year, 'aka': aka, 'id': imdb_id})
        
                    if count == 5:
                        break
    
    return result




def imdb_person_searching(query):
    params = {
        'q': query,
        's': 'nm',
    }

    body = urllib.urlencode(params)
    
    url = 'http://www.imdb.com/find?%s' % body
    
    resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url)
    
    result = []
    count = 0

    if resp['status'] == '200':
        data = BeautifulSoup(content, "html5lib", from_encoding="utf-8")
        
        table = data.find('table', {'class': 'findList'})
        for tr in table.findAll('tr'):
            td = tr.find('td', {'class': "result_text"})

            a = td.find('a')

            link = a.get('href').split('?')[0]
            title = a.text.encode('utf-8')
            small = td.find('small')
            details = small.text.strip().encode('utf-8') if small else ''

            imdb_id = int(link.replace('/name/nm', '').replace('/',''))
            
            result.append({'title': title, 'link': link, 'details': details, 'id': imdb_id})

            count += 1
            if count == 8:
                break
    
    return result

def imdb_person_data(id):

    url = 'http://www.imdb.com/name/nm%s/bio' % id
    
    resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url)
    
    result = {'bio': '', 'birth': '', 'place': '', 'country': '', 'poster': ''}

    if resp['status'] == '200':
        data = BeautifulSoup(content, "html5lib", from_encoding="utf-8")

        table = data.find('table', id="overviewTable")

        birth_day = 0
        birth_month = 0
        birth_year = 0

        if table:
            trs = table.findAll('tr')

            for a in trs[0].findAll('a'):
                href = a.get('href').encode('utf-8')

                if '?birth_monthday' in href:
                    birth_day, birth_month = a.text.strip().split()
                    birth_month = get_month_en(low(birth_month))
                elif '?birth_year' in href:
                    birth_year = a.text.encode('utf-8')
                elif '?birth_place' in href:
                    result['place'] = a.text.encode('utf-8')
                    result['country'] = a.text.split(',')[-1].split('[')[0].strip()


        if birth_day and birth_month and birth_year:
            result['birth'] = datetime.date(int(birth_year), int(birth_month), int(birth_day))

        bio_block = data.find('a', {'name': 'mini_bio'}).find_next('p')
        if bio_block:
            result['bio'] = bio_block.text.strip().encode('utf-8')
    

        poster = data.find('img', {'class': 'poster'})
        if poster:
            poster = poster.get('src').split('._V1_')[0]
            poster += '._V1_SX640_SY720_.jpg'
            
            result['poster'] = poster

    return result
