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
from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file
from user_registration.func import only_superuser
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, xml_noffilm, get_ignored_films
from decors import timer
from release_parser.func import cron_success

@timer
def get_nowru_links():
    '''
    Получение urls фильмов
    '''
    source = ImportSources.objects.get(url='http://www.now.ru/')
    
    login = 'afisha'
    password = 'y8p29T4AQO6S'
    main_url = 'https://www.now.ru/embed-api/content-list?login=%s&password=%s' % (login, password)
    
    nowru_data = Nowru.objects.all()
    nowru_data_dict = {}
    for i in nowru_data:
        nowru_data_dict[i.nowru_id] = i
        
    req = urllib.urlopen(main_url)
    if req.getcode() == 200:
        links = BeautifulSoup(req.read(), from_encoding="utf-8")
        
        for index, i in enumerate(links.findAll('item')):
            id = i.get('id')
            idec = i.get('idec')
            proj_id = i.get('project_id')
            regions = i.get('regions')

            nowru_obj = nowru_data_dict.get(int(id))
            if nowru_obj and nowru_obj.regions != regions:
                nowru_obj.regions = regions
                nowru_obj.save()

            if not proj_id and not nowru_obj:
                url = '%s&login=%s&password=%s' % (i['info_url'], login, password)
                #url = 'https://www.now.ru/embed-api/content-info?idec=PR248480&id=1005892&format=xml&login=afisha&password=y8p29T4AQO6S' ###
                
                film_req = urllib.urlopen(url)
                if film_req.getcode() == 200:
                    film = BeautifulSoup(film_req.read(), from_encoding="utf-8")
                    
                    if film.find('now_item'):
                        if not film.now_item.get('error'):
                            kinopoisk_id = film.now_item.kinopoisk_id.string
                            url_web = film.now_item.now_url.string
                            name_ru = film.now_item.findAll('title')[1].string.encode('utf-8')
                            name_en = film.now_item.findAll('title_orig')[1].string.encode('utf-8')
                            
                            name_ru = name_ru.replace('<![CDATA[','').replace('[CDATA[','').replace(']]>','').replace(']]','')
                            name_en = name_en.replace('<![CDATA[','').replace('[CDATA[','').replace(']]>','').replace(']]','')
                            
                            year = film.now_item.year.string
                            url_poster = film.now_item.poster_url.string
                            url_image = film.now_item.image_url.string
                            url_player = film.now_item.embed_url.string
                            player_code = str(film.now_item.embed_src.text).replace('[CDATA[', '').replace(']]>', '></iframe>')

                            Nowru.objects.create(
                                nowru_id = id,
                                idec = idec, 
                                kinopoisk_id = kinopoisk_id,
                                regions = regions,
                                name_ru = name_ru,
                                name_en = name_en,
                                year = year,
                                player_code = player_code,
                                url_api = url,
                                url_web = url_web,
                                url_poster = url_poster,
                                url_image = url_image,
                                url_player = url_player,
                            )
                        
                    # на каждом 60 обращении к источнику делаю паузу в 2 секунды
                    if (index + 1) % 60 == 0:
                        time.sleep(2.0)
    cron_success('xml', source.dump, 'links', 'Ссылки на плееры')


@timer
def nowru_ident():
    source = ImportSources.objects.get(url='http://www.now.ru/')
    ignored = get_ignored_films()
    
    data_nof_film = ''
    nowru_data = Nowru.objects.filter(kid=None)
    
    for i in nowru_data:
        name_ru_slug = low(del_separator(i.name_ru.encode('utf-8')))
        if name_ru_slug.decode('utf-8') not in ignored:
            name_en_slug = low(del_separator(i.name_en.encode('utf-8')))
            kid, info = film_identification(name_ru_slug, name_en_slug, {}, {}, year=i.year, source=source)
            if kid:
                i.kid = kid
                i.save()
            else:
                if 'slug="%s"' % name_ru_slug not in data_nof_film:
                    name_ru = i.name_ru.encode('utf-8')
                    name_en = i.name_en.encode('utf-8')
                    data_nof_film += xml_noffilm(name_ru, name_ru_slug, name_en, name_en_slug, i.nowru_id, info, None, source.id)
                
    create_dump_file('%s_nof_film' % source.dump, settings.NOF_DUMP_PATH, '<data>%s</data>' % data_nof_film)
    cron_success('xml', source.dump, 'players', 'Онлайн плееры')


@timer
def nowru_player_to_kinoafisha():
    source = ImportSources.objects.get(url='http://www.now.ru/')
    
    nowru_data = Nowru.objects.exclude(kid=None)
    nowru_ids = [i.kid for i in nowru_data]
    
    ivi_data = SourceFilms.objects.exclude(kid__in=set(nowru_ids)).filter(source_obj__url="http://antipiracy.ivi.ru/")
    ivi_ids = [i.kid for i in ivi_data]
    
    nowru_ivi = nowru_ids + ivi_ids
    
    megogo_data = MovieMegogo.objects.exclude(Q(afisha_id=0) | Q(afisha_id=None) | Q(afisha_id__in=set(nowru_ivi)))
    megogo_ids = [i.afisha_id for i in megogo_data]
    
    nowru_ivi_megogo = set(nowru_ivi + megogo_ids)
    
    afisha_code = FilmsCodes.objects.using('afisha').exclude(player='').filter(film__id__in=nowru_ivi_megogo)
    
    afisha_code_dict = {}
    for i in afisha_code:
        afisha_code_dict[i.film_id] = i
    

    for ind, data in enumerate((nowru_data, ivi_data, megogo_data)):
        for i in data:
            # now.ru
            if ind == 0:
                kid = i.kid
                player = i.player_code
            elif ind == 1:
                kid = i.kid
                player = i.text
            # megogo
            elif ind == 2:
                kid = i.afisha_id
                player = '<iframe width="607" height="360" \
                        src="http://megogo.net/e/%s" frameborder="0" \
                        allowfullscreen></iframe>' % i.megogo_id
            
            if kid:
                afisha_obj = afisha_code_dict.get(kid)
                if afisha_obj:
                    afisha_obj.player = player
                    afisha_obj.save()
                else:
                    FilmsCodes.objects.using('afisha').create(
                        film_id = kid,
                        player = player,
                    )
    cron_success('export', source.dump, 'players', 'Онлайн плееры')



@only_superuser
@never_cache
def nowru_test_show(request):
    nowru_data = Nowru.objects.exclude(kid=None).order_by('-year')
    '''
    data = ''
    for i in nowru_data:
        data += '<b>now.ru id</b>: %s, <b>idec</b>: %s, <b>kinopoisk id</b>: %s, <b>kid</b>: %s<br />' % (i.nowru_id, i.idec, i.kinopoisk_id, i.kid)
        data += '%s / %s (%s). Regions: %s<br />' % (i.name_ru, i.name_en, i.year, i.regions)
        data += '%s<br /><br /><br />' % i.player_code
    '''
    data = u'Всего: %s<br /><br />' % nowru_data.count()
    for i in nowru_data:
        data += u'%s / %s (%s)<br />' % (i.name_ru, i.name_en, i.year)
    
    return HttpResponse(data)

