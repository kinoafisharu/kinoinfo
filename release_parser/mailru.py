#-*- coding: utf-8 -*- 
import urllib2
import re
import datetime
import time
import random

from django.http import HttpResponse
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache
from django.conf import settings

from dateutil.relativedelta import relativedelta

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import del_separator, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success, give_me_cookie


#@timer
def get_mailru_soon():
    data_nof_film = ''
    noffilms = []

    ignored = get_ignored_films()

    source = ImportSources.objects.get(url='https://afisha.mail.ru/')
    sfilm_clean(source)

    films = {}
    source_films = SourceFilms.objects.filter(source_obj=source)
    for i in source_films:
        films[i.source_id] = i
    fdict = get_all_source_films(source, source_films)

    today = datetime.datetime.today()

    dates = list(map((lambda x: today.date() + relativedelta(months=x)), xrange(1, 13)))
    dates.insert(0, today.date())

    for d in dates:

        main_url = '%scinema/soon/%s/%s/' % (source.url, d.year, d.month)

        opener = give_me_cookie()
        #headers = {
        #    'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.2.2; en-us; Nexus 7 Build/JDQ39E) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30 CyanogenMod/10.1.3/grouper',
        #}
        #opener.addheaders = headers.items()

        try:
            req = opener.open(urllib2.Request(main_url))
        except urllib2.HTTPError:
            req = None

        if req:
            data = BeautifulSoup(req.read(), "html.parser")
            for block in data.findAll('div', {'class': 'premiere__date'}):
                day = block.find('div', {'class': 'premiere__date__mday'}).text
                if day:
                    release_date = datetime.date(d.year, d.month, int(day))

                    for item in block.findAll('div', {'class': 'clearin'}):
                        a = item.find('div', {'class': 'itemevent__head__name'}).find('a')
                        film_name = a.text.strip().encode('utf-8')
                        film_slug = low(del_separator(film_name))
                        href = a.get('href')
                        film_id = href.replace('/cinema/movies/','').replace('/', '').encode('utf-8')
                        full_url = '%s%s' % (source.url, href.lstrip('/'))
                        details = item.find('div', {'class': 'itemevent__head__info'}).text.encode('utf-8')
                        year = re.findall(r'\/\d{4}\/', details)
                        if year:
                            year = int(year[0].replace('/', ''))

                        if film_id not in noffilms and film_slug.decode('utf-8') not in ignored:

                            obj = films.get(film_id.decode('utf-8'))
#OFC76 path from U+2009|e2 80 89|THIN SPACE
#in film name
                            film_slug = film_slug.decode("utf-8").replace(u"\u2009", '').encode("utf-8")
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
                                        objt = create_sfilm(film_id, kid, source, film_name)
                                        films[film_id.decode('utf-8')] = objt
                                        if not fdict.get(kid):
                                            fdict[kid] = {'editor_rel': [], 'script_rel': []}
                                        fdict[kid]['script_rel'].append(objt)
                                elif not obj:
                                    data_nof_film += xml_noffilm(film_name, film_slug, None, None, film_id, info, full_url.encode('utf-8'), source.id)
                                    noffilms.append(film_id)

                                if objt:
                                    sr_obj, sr_created = SourceReleases.objects.get_or_create(
                                        film=objt,
                                        source_obj=source,
                                        defaults={
                                            'film': objt,
                                            'source_obj': source,
                                            'release': release_date,
                                        })
                                    if sr_created:

                                        try:
                                            req = opener.open(urllib2.Request(full_url))
                                        except urllib2.HTTPError:
                                            req = None

                                        if req:
                                            data = BeautifulSoup(req.read(), "html.parser")
                                            movie_pic = data.find('div', {'class': 'movieabout__info__left'})
                                            pic = None
                                            if movie_pic:
                                                pic = movie_pic.find('a', {'data-module': 'Gallery'}).get('href')

                                            txt = None
                                            movie_txt = data.find('div', {'class': 'movieabout__info__descr__txt'})
                                            if movie_txt:
                                                txt = movie_txt.text.strip().encode('utf-8')

                                            if pic or txt:
                                                objt.text = txt
                                                objt.extra = pic
                                                objt.save()

                                        time.sleep(random.uniform(1.0, 1.5))
                                    else:
                                        if sr_obj.release != release_date:
                                            sr_obj.release = release_date
                                            sr_obj.save()

        time.sleep(random.uniform(1.0, 2.0))

    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('html', source.dump, 'films', 'Релизы')


@never_cache
def get_mailru_test(request):
    from api.views import film_poster2
    from news.views import cut_description

    source = ImportSources.objects.get(url='https://afisha.mail.ru/')

    html = u'''
        <link rel="stylesheet" href="http://kinoinfo.ru/static/base/css/style.css" type="text/css" media="screen" />
        <table class="modern_tbl">
        <tr>
            <th>Релиз</th>
            <th></th>
            <th>Фильм</th>
            <th>Аннотация</th>
            <th>Постер</th>
            <th>Источник</th>
        </tr>'''

    kids = list(SourceReleases.objects.filter(source_obj=source).values_list('film__kid', flat=True))

    descriptions = {}
    for i in list(Film.objects.using('afisha').filter(pk__in=kids).values('pk', 'description')):
        if i['description']:
            d = cut_description(i['description'], True, 200)
            descriptions[i['pk']] = d

    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue__in=kids)
    posters = {}
    for p in poster_obj:
        if posters.get(p.objpkvalue):
            posters[p.objpkvalue].append(p)
        else:
            posters[p.objpkvalue] = [p]

    for i in list(SourceReleases.objects.filter(source_obj=source).values('release', 'film__source_id', 'film__extra', 'film__text', 'film__kid', 'film__name').order_by('release')):
        poster = posters.get(i['film__kid'], [])
        poster_path = film_poster2(poster, 'small')

        mailru_pic = ''
        if i['film__extra']:
            mailru_pic = u'<a href="%s" target="_blank"><img src="%s" width="100" /></a>' % (i['film__extra'], i['film__extra'])

        mailru_link = u'<a href="%scinema/movies/%s/" target="_blank">перейти</a>' % (source.url, i['film__source_id'])

        kinoinfo_link = u'<a href="http://kinoinfo.ru/film/%s/" target="_blank">%s</a>' % (i['film__kid'], i['film__name'])
        kinoinfo_pic = u'<div style="width: 100px; height: 150px; background: #CCC;"></div>'
        if poster_path:
            kinoinfo_pic = u'<img src="%s" width="100" />' % poster_path

        kinoinfo_pic = u'<a href="http://posters.kinoafisha.ru/loadtrailers18/detalfilms.php?id=%s&ix=5507931&act=posters&profile=%s" target="_blank">%s</a>' % (i['film__kid'], request.user.id, kinoinfo_pic)

        desc = descriptions.get(i['film__kid'], '')
        if desc:
            desc = u'<div style="background: #e5ffe5;">%s</div>' % desc

        txt = i['film__text'] if i['film__text'] else ''
        html += u'''<tr>
            <td>%s</td>
            <td>%s</td>
            <td>%s</td>
            <td>%s%s</td>
            <td>%s</td>
            <td>%s</td>
            </tr>''' % (i['release'], kinoinfo_pic, kinoinfo_link, desc, txt, mailru_pic, mailru_link)

    html += u'</table>'

    return HttpResponse(str(html.encode('utf-8')))
