#-*- coding: utf-8 -*- 
import urllib
import re
import datetime
import time
import operator
import random

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.conf import settings

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import del_separator, low
from release_parser.views import film_identification, xml_noffilm,\
    distributor_identification, get_ignored_films
from decors import timer
from release_parser.func import cron_success
from django.shortcuts import render_to_response



@timer
def temp_kinobusiness_upd():
    bo = BoxOffice.objects.all()
    for i in bo:
        bx_id = '%s%s%s' % (i.source_id, i.date_from, i.date_to)
        i.bx_id = bx_id
        i.save()


# @never_cache
def get_kinobusiness(request, country_data):
    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='http://www.kinobusiness.com/')
    country = Country.objects.get(name=country_data['ru'])

    bx_ids = list(BoxOffice.objects.filter(country=country).values_list(
        'bx_id', flat=True))

    films = BoxOffice.objects.filter(country=country).distinct('kid')
    films_dict = {}
    for i in films:
        films_dict[i.source_id] = i.kid

    data_nof_films = ''
    data_nof_distr = ''
    noffilms = []
    nofdistr = []

    if country_data['en'] == 'usa':
        main_url = '%skassa_world_prokata/kassa-usa/' % source.url
        add = ''
    else:
        main_url = '%skassovye_sbory/weekend/' % source.url
        add = 'usd/'

    req = urllib.urlopen(main_url)
    if req.getcode() == 200:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")

        div = data.find('div', {'class': 'table-responsive'})
        data = div.findAll('table', limit=1)[0]

        # data = data.find('table', {'class': "table table-striped table-hover calendar_year ned"})
        tr = data.findAll('tr', limit=2)[1]
        a = tr.findAll('a')[0].get('href').lstrip('/')

        req = urllib.urlopen('%s%s%s' % (source.url, a, add))
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")

            date = data.find('h1', {'class': 'film__title'})
            date = date.find('small').text.encode('utf-8')

            to_day, to_month, to_year = re.findall(
                r'\-\s[\d+\.?]+', date)[0].replace('- ', '').split('.')
            date_to = datetime.date(int(to_year), int(to_month), int(to_day))
            date_from = date_to - datetime.timedelta(days=3)

            counter = 0
            main = data.find('table', id="krestable")

            for index, tr in enumerate(main.findAll('tr')):
                if index != 0:

                    if country_data['en'] == 'usa':
                        trs = tr.findAll('td', limit=5)
                        film_name = trs[2].text.strip().encode('utf-8')
                        film_name_orig = trs[3].text.strip().encode('utf-8')
                        a = trs[2].find('a')
                    else:
                        trs = tr.findAll('td', limit=5)
                        film_name = trs[3].text.strip().encode('utf-8')
                        film_name_orig = trs[4].text.strip().encode('utf-8')
                        a = trs[3].find('a')

                    url = a.get('href').encode('utf-8') if a else None

                    film_name = film_name.replace('*', '')

                    film_slug = low(del_separator(film_name))
                    film_slug_orig = low(del_separator(film_name_orig))

                    full_url = ''
                    if url:
                        full_url = '%s%s' % (source.url, url.lstrip('/'))
                        full_url = full_url.encode('utf-8')

                    film_id = film_slug.decode('utf-8')
                    film_slug_orig = film_slug_orig.decode('utf-8')

                    bx_id = '%s%s%s%s%s' % (
                        film_id, film_slug_orig, date_from,
                        date_to, country_data['dump'])
                    if bx_id not in bx_ids:
                        distributors = []
                        week_audience = None

                        td = tr.findAll('td')

                        if country_data['en'] == 'usa':
                            distributors = td[4].text
                            week_sum = int(float(td[5].text.replace(
                                u' ', '').replace(u',', u'.')))
                            screens = int(float(td[7].text.replace(
                                u' ', '').replace(u',', u'.').replace(u'-', u'0')))
                            all_sum = int(float(td[9].text.replace(
                                u' ', '').replace(u',', u'.')))
                            days = int(float(td[11].text.replace(
                                u' ', '').replace(u',', u'.'))) * 7
                            all_audience = None
                        else:
                            distributors = td[5].text
                            week_sum = int(float(td[6].text.replace(
                                u' ', '').replace(u',', u'.')))
                            screens = int(float(td[8].text.replace(
                                u' ', '').replace(u',', u'.').replace(u'-', u'0')))
                            days = int(float(td[10].text.replace(
                                u' ', '').replace(u',', u'.')))
                            all_sum = int(float(td[11].text.replace(
                                u' ', '').replace(u',', u'.')))
                            all_audience = td[12].text.replace(
                                u' ', '').replace(u',', u'.')
                            all_audience = int(float(all_audience)) if all_audience else None

                        if distributors:
                            distributors = distributors.encode(
                                'utf-8').replace('*', '').split('/')
                        else:
                            distributors = []

                        dlist = []
                        for dname in distributors:
                            dname = dname.strip().replace('&', '&amp;')
                            dname_slug = low(del_separator(dname))
                            if dname_slug not in nofdistr:
                                distr, status = distributor_identification(
                                    dname, dname_slug)
                                if distr:
                                    dlist.append(distr)
                                else:
                                    data_nof_distr += '<distributor value="%s" slug="%s" alt="%s"></distributor>' % (dname.replace('&', '&amp;'), dname_slug, None)
                                    nofdistr.append(dname_slug)

                        if dlist:
                            if film_id not in noffilms and film_slug.decode('utf-8') not in ignored:
                                film_obj = films_dict.get(film_id)
                                if not film_obj:
                                    '''
                                    req2 = urllib.urlopen(full_url)
                                    if req2.getcode() == 200:
                                        counter += 1
                                        data2 = BeautifulSoup(req2.read())
                                        film_details = data2.find('table', {'class': 'news-detail'})
                                        year = None
                                        for p in film_details.findAll('p'):
                                            if p.b:
                                                year_tag = p.b.string.encode('utf-8').strip()
                                                if year_tag == 'Год:':
                                                    year = re.findall(r'\d+', p.text.encode('utf-8').strip())[0]
                                        if year:
                                    '''
                                    d1, d2 = (dlist[0].kid, dlist[1].kid) if len(dlist) > 1 else (dlist[0].kid, None)
                                    kid, info = film_identification(
                                        film_slug, None, d1, d2, source=source)
                                    if kid:
                                        film_obj = kid
                                        films_dict[film_id] = kid
                                    else:
                                        data_nof_films += xml_noffilm(
                                            film_name, film_slug, None, None,
                                            film_id.encode('utf-8'), info,
                                            full_url, source.id)
                                        noffilms.append(film_id)

                                if film_obj:
                                    boxoffice = BoxOffice.objects.create(
                                        bx_id=bx_id,
                                        source_id=film_id,
                                        source_obj=source,
                                        name=film_name,
                                        kid=film_obj,
                                        screens=screens,
                                        date_from=date_from,
                                        date_to=date_to,
                                        week_sum=week_sum,
                                        all_sum=all_sum,
                                        week_audience=week_audience,
                                        all_audience=all_audience,
                                        days=days,
                                        country=country,
                                    )
                                    for i in dlist:
                                        boxoffice.distributor.add(i)

                                    bx_ids.append(bx_id)

                        if counter % 3 == 0:
                            time.sleep(random.uniform(1.0, 3.0))

    create_dump_file('%s_nof_distributor' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_distr)
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_films)
    cron_success('html', source.dump, 'boxoffice%s' % country_data['dump'], 'Кассовые сборы %s' % country_data['ru'])
    return HttpResponseRedirect(reverse("boxoffice_admin", kwargs={'country': country_data['en']}))


@never_cache
def get_kinobusiness_russia(request):
    country_data = {'ru': 'Россия', 'en': 'russia', 'dump': ''}
    try:
        return get_kinobusiness(request, country_data)
    except:
        raise Http404()


@never_cache
def get_kinobusiness_usa(request):
    country_data = {'ru': 'США', 'en': 'usa', 'dump': '_usa'}
    try:
        return get_kinobusiness(request, country_data)
    except Exception as (e):
        error = str(e) 
        text = ''' В процедуре get_kinobusiness_usa возникла ошибка. Возможно сайт-донор не предоставил корректный ответ'''
        return render_to_response('error.html', {'text': text, 'error': error}, context_instance=RequestContext(request))
#        raise Http404()


@only_superuser
@never_cache
def kinobusiness_export_to_kinoafisha(request, country_name):
    if country_name == 'usa':
        country_n = 'США'
    else:
        country_n = 'Россия'

    current_year = datetime.date.today().year
    past_three_year = current_year - 2
    box_date = datetime.date(past_three_year, 1, 1)
    gathering = Gathering.objects.using('afisha').filter(
        friday_date__gte=box_date)

    gathering_list = []
    for i in gathering:
        key = '%s%s%s%s' % (
            i.film_id, i.friday_date, i.sunday_date, country.id)
        gathering_list.append(key)

    country = AfishaCountry.objects.using('afisha').get(name=country_n)

    boxoffice = BoxOffice.objects.filter(country__name=country_n)

    box_dates = {}
    for i in boxoffice:

        all_audience, week_audience = (float(i.all_audience), i.week_audience) if i.all_audience else (0, 0)

        if all_audience and not week_audience:
            week_audience = int(
                float(i.week_sum) / (float(i.all_sum) / all_audience))

        box_data = {
            'date_from': i.date_from,
            'date_to': i.date_to,
            'week_sum': i.week_sum,
            'all_sum': i.all_sum,
            'week_audience': week_audience,
            'all_audience': all_audience,
            'name': i.name,
            'kid': i.kid,
            'screens': i.screens,
            'country': country.id
        }
        if box_dates.get(i.date_from):
            box_dates[i.date_from].append(box_data)
        else:
            box_dates[i.date_from] = [box_data]

    box = []
    for k, v in box_dates.iteritems():
        for place, i in enumerate(sorted(v, key=operator.itemgetter('week_sum'), reverse=True)):
            i['place'] = place + 1
            week = datetime.date(
                i['date_to'].year,
                i['date_to'].month,
                i['date_to'].day).isocalendar()[1]
            i['num'] = week
            key = '%s%s%s%s' % (
                i['kid'], i['date_from'], i['date_to'], i['country'])
            if key not in gathering_list:
                box.append(i)

    if request.GET.get('save'):
        for i in box:
            Gathering.objects.using('afisha').create(
                week_num=i['num'],
                friday_date=i['date_from'],
                sunday_date=i['date_to'],
                place=i['place'],
                film_id=i['kid'],
                period_gathering=i['week_sum'],
                total_gathering=i['all_sum'],
                country=country,
                date_from=i['week_audience'],
                date_to=i['all_audience'],
                day_in_rent=i['screens'],
            )
        return HttpResponseRedirect(reverse(
            "kinobusiness_export_to_kinoafisha",
            kwargs={'country_name': country_name}))

    # temp
    boxx_dates = {}
    for i in box:
        if boxx_dates.get(i['date_to']):
            boxx_dates[i['date_to']].append(i)
        else:
            boxx_dates[i['date_to']] = [i]

    xxx = '<br />'
    if not boxx_dates:
        xxx = 'Нет данных для записи'

    for k, v in boxx_dates.iteritems():
        xxx += '<br /><b>%s</b><br />' % k
        xxx += '<table border="1"><th>Place</th><th>Film</th><th>Week num</th><th>Sum week</th><th>Sum all</th><th>Audience Week</th><th>Audience Sum</th><th>Screens</th>'
        for place, i in enumerate(sorted(v, key=operator.itemgetter('week_sum'), reverse=True)):
            xxx += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (i['place'], i['name'].encode('utf-8'), i['num'], i['week_sum'], i['all_sum'], i['week_audience'], i['all_audience'], i['screens'])
        xxx += '</table>'

    if boxx_dates:
        xxx += '<br /><a href="/releases/kinobusiness_export_to_kinoafisha/?save=1">Записать в БД</a>'
    return HttpResponse(str(xxx))
