#-*- coding: utf-8 -*- 
import datetime
import time
import operator
from os import listdir
import json
import collections

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.contrib.humanize.templatetags.humanize import intcomma

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from user_registration.func import only_superuser, org_peoples
from user_registration.views import get_usercard, get_user
from kinoinfo_folder.func import del_separator, low
from release_parser.views import create_name_distr
from release_parser.func import get_file_modify_datetime
from release_parser.forms import ImportSourcesForm, ActionsPriceListForm
from articles.views import pagination as pagi


@only_superuser
@never_cache
def kinoafisha_admin_main(request):
    return render_to_response('release_parser/kinoafisha_admin.html', context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_parsers_info(request, typedata):
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    sources_data = []
    
    sources = ImportSources.objects.all()
    sources_dict = {}
    for i in sources:
        sources_dict[i.dump] = i.source
            
    for f in listdir(settings.SUCCESS_LOG_PATH):
        type, source, filename = f.replace('.xml', '').split('__')
        if '~' not in filename and type == typedata:
            file = open('%s/%s' % (settings.SUCCESS_LOG_PATH, f), 'r')
            data = BeautifulSoup(file.read(), from_encoding="utf-8")
            file.close()
            
            s = sources_dict.get(source)

            modify_date = get_file_modify_datetime(settings.SUCCESS_LOG_PATH, f)
            modify_date = modify_date + datetime.timedelta(hours=4) # + 4 часа для России
            modify_date = modify_date.date()
            
            info = data.data.string.encode('utf-8')
            
            error_flag = False if today == modify_date else True
            
            if source == 'nowru' and typedata != 'export':
                error_flag = False if today == modify_date or yesterday == modify_date else True
        
            sources_data.append({'source': s, 'title': info, 'error': error_flag, 'modify_date': modify_date})
            
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    p, page = pagi(page, sorted(sources_data, key=operator.itemgetter('source')), 15)
    return render_to_response('release_parser/parsers_info.html', {'p': p, 'page': page, 'today': today, 'yesterday': yesterday, 'type': typedata}, context_instance=RequestContext(request))



def admin_identification_status(obj):
    sources_data = []
    today = datetime.datetime.now().date()
    yesterday = today - datetime.timedelta(days=1)
    
    error_status = []
    
    sources = ImportSources.objects.all()
    for i in sources:
        try:
            file_name = '%s_nof_%s' % (i.dump, obj)
            file = 'dump_%s.xml' % file_name
            modify_date = get_file_modify_datetime(settings.NOF_DUMP_PATH, file)
            modify_date = modify_date + datetime.timedelta(hours=4) # + 4 часа для России
            modify_date = modify_date.date()
            error_flag = False if today == modify_date else True
            dump = open('%s/%s' % (settings.NOF_DUMP_PATH, file), 'r')
            dump_data = BeautifulSoup(dump.read(), from_encoding="utf-8")
            dump.close()
            
            if i.dump == 'kinometro':
                nof_data = len(set(i['slug'] for i in dump_data.findAll(obj)))
            else:
                nof_data = len(dump_data.findAll(obj))
                
            if i.dump in ('yovideo', 'top250'):
                if i.dump == 'yovideo':
                    s_url = 'http://www.yo-video.net/'
                else:
                    s_url = 'http://top250.info/'
                nof_data = SourceFilms.objects.filter(source_obj__url=s_url, kid=None).count()
            
            sources_data.append({'source': i.source, 'dump': file_name, 'error': error_flag, 'modify_date': modify_date, 'nof_data': nof_data})
            error_status.append(nof_data)
        except OSError: pass
    
    error = True if sum([i for i in error_status]) else False
    return sources_data, error, today, yesterday


def identification_info(request, obj):
    sources_data, error, today, yesterday = admin_identification_status(obj)
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, sources_data, 15)

    return {'p': p, 'page': page, 'today': today, 'yesterday': yesterday, 'obj': obj}
    
     
@only_superuser
@never_cache
def admin_identification_info(request, obj):
    data = identification_info(request, obj)
    return render_to_response('release_parser/objects_info.html', data, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_kinoinfo_import_info(request):
    data = [
        {'status': 0, 'cron': True, 'source': 'Киноафиша', 'links': (
            ('Страны', 'kinoafisha_country_import'),
            ('Города', 'kinoafisha_city_import'),
            ('Кинотеатры', 'kinoafisha_cinema_import'),
            ('Кинотеатры 2', 'kinoafisha_cinema2_import'),
            ('Оценки кинотеатров', 'kinoafisha_cinema_rates_import'),
            ('Залы', 'kinoafisha_hall_import'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Киноафиша', 'links': (
            ('Дистр', 'kinoafisha_distributor_import'),
            ('Жанры', 'kinoafisha_genres_import'),
            ('Фильмы', 'kinoafisha_films_import'),
            ('Бюджеты', 'kinoafisha_budget_import'),
            ('Сборы США', 'kinoafisha_usa_gathering_import'),
            ('Статусы и типы', 'kinoafisha_statusact_and_actions'),
            ('Персоны', 'kinoafisha_persons_import'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Киноафиша', 'links': (
            ('Связи персон с фильмами', 'kinoafisha_persons_rel'),
            ('Сеансы', 'kinoafisha_schedules_import'),
            ('Оценки', 'integral_rate'),
            ('Рецензии', 'kinoafisha_reviews_import'),
            ('Новости', 'kinoafisha_news_import'),
            ('Отзывы', 'kinoafisha_opinions_import'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Kinohod.ru', 'links': (
            ('Города', 'get_kinohod_cities'),
            ('Кинотеаты', 'get_kinohod_cinemas'),
            ('Фильмы', 'get_kinohod_films'),
            ('Сеансы', 'get_kinohod_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Okinoua.ru', 'links': (
            ('Ссылки на релизы', 'get_okinoua_links'),
            ('Релизы', 'get_okinoua_releases'),
            ('Города', 'get_okinoua_cities'),
            ('Кинотеаты', 'get_okinoua_cinemas'),
            ('Фильмы', 'get_okinoua_films'),
            ('Сеансы', 'get_okinoua_schedules'),
            )
        },
        {'status': 1, 'cron': False, 'source': 'Okinoua.ru', 'links': (
            ('Релизы и дистрибьюторы', u'get_okinoua_distributors'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Rambler.ru', 'links': (
            ('IndexFile', 'get_rambler_indexfile'),
            ('Города', 'get_rambler_cities'),
            ('Кинотеаты', 'get_rambler_cinemas'),
            ('Фильмы', 'get_rambler_films'),
            ('Сеансы', 'get_rambler_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Планета Кино IMAX', 'links': (
            ('Города и Кинотеатры', 'get_planeta_cities_cinemas'),
            ('Фильмы', 'get_planeta_films'),
            ('Сеансы', 'get_planeta_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Megamag.by', 'links': (
            ('Сеансы', 'get_megamag'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'CMC/Kinobit', 'links': (
            ('Дамп сеансов', 'get_kinobit_dump'),
            ('Города', 'get_kinobit_cities'),
            ('Кинотеаты', 'get_kinobit_cinemas'),
            ('Фильмы', 'get_kinobit_films'),
            ('Сеансы', 'get_kinobit_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Кинометро', 'links': (
            ('Импорт релизов', 'kinometro_films_pages'),
            ('Идентификация релизов и дистрибьюторов', 'film_kinometro_ident'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Now.ru', 'links': (
            ('Онлайн плееры', 'get_nowru_links'),
            ('Идентифик. фильмов', 'nowru_ident'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Kino-teatr.ua', 'links': (
            ('Укр. фильмы и персоны', 'get_kinoteatrua_films_and_persons'),
            ('Сеансы', 'get_kinoteatrua_schedules'),
            ('Укр. постеры', 'get_kinoteatrua_posters'),
            ('Укр. релизы', 'get_kinoteatrua_releases'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Кинотеатр Этаж', 'links': (
            ('Сеансы', 'get_etaj_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Афиша в Сургуте', 'links': (
            ('Кинотеатры', 'get_surkino_cinemas'),
            ('Сеансы', 'get_surkino_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Кинотеатр Б-Класс', 'links': (
            ('Сеансы', 'get_kinobklass_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Синема-АРТ-Холл', 'links': (
            ('Сеансы', 'get_cinemaarthall_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Златоуст Космос', 'links': (
            ('Сеансы', 'get_zlat74ru_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Александров Сатурн', 'links': (
            ('Сеансы', 'get_kinosaturn_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Запад 24', 'links': (
            ('Сеансы', 'get_zapad24ru'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Мичуринск Октябрь', 'links': (
            ('Сеансы', 'get_michurinskfilm_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Балаково Мир, Россия', 'links': (
            ('Сеансы', 'get_ktmir_and_ktrussia_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Мир Луксор, Атал', 'links': (
            ('Сеансы', 'get_luxor_chuvashia_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Нефтекамск Арсенал', 'links': (
            ('Сеансы', 'get_arsenalclub_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Сеть Иллюзион', 'links': (
            ('Сеансы', 'get_illuzion_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'VKino.com.ua', 'links': (
            ('Города и кинотеатры', 'get_vkinocomua_cities_and_cinemas'),
            ('Фильмы и сеансы', 'get_vkinocomua_films_and_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Люксор', 'links': (
            ('Города и кинотеатры', 'get_luxor_cinemas'),
            ('Фильмы', 'get_luxor_films'),
            ('Сеансы', 'get_luxor_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Cinema 5', 'links': (
            ('Сеансы', 'get_cinema5_schedules'),
            )
        },
        {'status': 1, 'cron': False, 'source': 'KinoBusiness', 'links': (
            ('Кассовые сборы России', 'get_kinobusiness_ru'),
            ('Кассовые сборы США', 'get_kinobusiness_usa'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Курс валют', 'links': (
            ('USD-RUR, AUD-RUR, NZD-RUR', 'get_currency_rate'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Сеть Монитор', 'links': (
            ('Города и кинотеатры', 'get_kinomonitor_cities_and_cinemas'),
            ('Фильмы и сеансы', 'get_kinomonitor_films_and_schedules'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Rutracker.org', 'links': (
            ('Топики', 'get_rutracker_topics'),
            ('Закрытые', 'get_rutracker_topics_closed'),
            ),
        },
        {'status': 1, 'cron': False, 'source': 'Megogo', 'links': (
            ('Загрузить файл', 'movie_online_main_admin'),
            ('Парсить файл', 'parse_data_file'),
            ('Идент. фильмов', 'parse_data_identification'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Ivi.ru', 'links': (
            ('Файл', 'get_ivi_file'),
            ('Идент. фильмов', 'ivi_ident'),
            ),
        },
        {'status': 1, 'cron': False, 'source': 'IMDb', 'links': (
            ('Файл', 'get_imdb_film_list'),
            ('Релизы в США', 'get_imdb_film'),
            ('Идентификация', 'imdb_film_ident'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'RottenTomatoes', 'links': (
            ('Фильмы/Рейтинг', 'get_rottentomatoes_films'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'YoVideo', 'links': (
            ('Франц. релизы', 'get_yovideo'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Top250', 'links': (
            ('Фильмы', 'get_top250'),
            ('Награды', 'get_top250_awards'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'TVzavr', 'links': (
            ('Дамп', 'get_tvzavr_dump'),
            ('Фильмы/Плееры', 'tvzavr_ident'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Ореанда и Спартак', 'links': (
            ('Фильмы и сеансы', 'get_oreanda_and_spartak'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Kino.ru', 'links': (
            ('Фильмы и отзывы', 'get_kino_ru'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Cinemaplex', 'links': (
            ('Релизы', 'get_cinemaplex'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Cinemate.cc', 'links': (
            ('Фильмы в сети', 'cinemate_cc_soon'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'ПремьерЗал', 'links': (
            ('Города', 'get_premierzal_cities'),
            ('Кинотеатры', 'get_premierzal_cinemas'),
            ('Фильмы и Сеансы', 'get_premierzal_schedules'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'Mail.ru', 'links': (
            ('Релизы', 'get_mailru_soon'),
            ),
        },
        {'status': 1, 'cron': True, 'source': 'KinoMagnat', 'links': (
            ('Сеансы', 'get_kinomagnat_schedules'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'KinoBoomer', 'links': (
            ('Сеансы', 'get_kinoboomer_schedules'),
            )
        },
    ]
    
    data = sorted(data, key=operator.itemgetter('status'))
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, data, 15)
    
    return render_to_response('release_parser/kinoinfo_import_info.html', {'p': p, 'page': page}, context_instance=RequestContext(request))  


@only_superuser
@never_cache
def admin_kinoafisha_import_info(request):
    data = [
        {'status': 0, 'cron': True, 'source': 'CMC/Kinobit', 'links': (
            ('Сеансы', 'kinobit_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinobit_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Планета-Кино IMAX', 'links': (
            ('Сеансы', 'planeta_schedules_export_to_kinoafisha'),
            (u'Лог', 'planeta_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Киноход', 'links': (
            ('Сеансы', 'kinohod_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinohod_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Megamag.by', 'links': (
            ('Сеансы', 'megamag_schedules_export_to_kinoafisha'),
            (u'Лог', 'megamag_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Rambler', 'links': (
            ('Сеансы', 'rambler_schedules_export_to_kinoafisha'),
            (u'Лог', 'rambler_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Кинотеатр Этаж', 'links': (
            ('Сеансы', 'etaj_schedules_export_to_kinoafisha'),
            (u'Лог', 'etaj_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Кинотеатр Б-Класс', 'links': (
            ('Сеансы', 'kinobklass_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinobklass_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Афиша в Сургуте', 'links': (
            ('Сеансы', 'surkino_schedules_export_to_kinoafisha'),
            (u'Лог', 'surkino_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Синема-АРТ-Холл', 'links': (
            ('Сеансы', 'cinemaarthall_schedules_export_to_kinoafisha'),
            (u'Лог', 'cinemaarthall_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Златоуст Космос', 'links': (
            ('Сеансы', 'zlat74ru_schedules_export_to_kinoafisha'),
            (u'Лог', 'zlat74ru_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Александров Сатурн', 'links': (
            ('Сеансы', 'kinosaturn_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinosaturn_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Запад 24', 'links': (
            ('Сеансы', 'zapad24ru_schedules_export_to_kinoafisha'),
            (u'Лог', 'zapad24ru_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Мичуринск Октябрь', 'links': (
            ('Сеансы', 'michurinskfilm_schedules_export_to_kinoafisha'),
            (u'Лог', 'michurinskfilm_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Kino-teatr.ua', 'links': (
            ('Сеансы', 'kinoteatrua_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinoteatrua_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Балаково Мир, Россия', 'links': (
            ('Сеансы', 'ktmir_and_ktrussia_schedules_export_to_kinoafisha'),
            (u'Лог Мир', 'ktmir_schedules_export_to_kinoafisha_log'),
            (u'Лог Россия', 'ktrussia_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Мир Луксор, Атал', 'links': (
            ('Сеансы', 'luxor_chuvashia_schedules_export_to_kinoafisha'),
            (u'Лог', 'luxor_chuvashia_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Нефтекамск Арсенал', 'links': (
            ('Сеансы', 'arsenalclub_schedules_export_to_kinoafisha'),
            (u'Лог', 'arsenalclub_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Сеть Иллюзион', 'links': (
            ('Сеансы', 'illuzion_schedules_export_to_kinoafisha'),
            (u'Лог', 'illuzion_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'VKino.com.ua', 'links': (
            ('Сеансы', 'vkinocomua_schedules_export_to_kinoafisha'),
            (u'Лог', 'vkinocomua_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Люксор', 'links': (
            ('Сеансы', 'luxor_schedules_export_to_kinoafisha'),
            (u'Лог', 'luxor_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Cinema 5', 'links': (
            ('Сеансы', 'cinema5_schedules_export_to_kinoafisha'),
            (u'Лог', 'cinema5_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Now.ru, Megogo, Ivi', 'links': (
            ('Онлайн плееры', u'nowru_player_to_kinoafisha'),
            )
        },
        {'status': 1, 'cron': False, 'source': 'Kinometro', 'links': (
            ('Хронометраж и копии', u'runtime_copy_to_kinoafisha'),
            ('Даты релизов', u'kinoafisha_release_update'),
            )
        },
        {'status': 1, 'cron': False, 'source': 'Cinemaplex', 'links': (
            ('Даты релизов', u'kinoafisha_cinemaplex_release_update'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Сеть Монитор', 'links': (
            ('Сеансы', 'kinomonitor_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinomonitor_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'Ореанда и Спартак', 'links': (
            ('Сеансы', 'oreanda_and_spartak_schedules_export_to_kinoafisha'),
            (u'Лог 1', 'yalta_oreanda_export_to_kinoafisha_log'),
            (u'Лог 2', 'yalta_spartak_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'ПремьерЗал', 'links': (
            ('Сеансы', 'premierzal_schedules_export_to_kinoafisha'),
            (u'Лог', 'premierzal_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'KinoMagnat', 'links': (
            ('Сеансы', 'kinomagnat_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinomagnat_schedules_export_to_kinoafisha_log'),
            )
        },
        {'status': 1, 'cron': True, 'source': 'KinoBoomer', 'links': (
            ('Сеансы', 'kinoboomer_schedules_export_to_kinoafisha'),
            (u'Лог', 'kinoboomer_schedules_export_to_kinoafisha_log'),
            )
        },
    ]
        
    data = sorted(data, key=operator.itemgetter('status'))
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, data, 15)
    return render_to_response('release_parser/kinoafisha_import_info.html', {'p': p, 'page': page}, context_instance=RequestContext(request))  


@only_superuser
@never_cache
def admin_api_import_info(request):
    sources_data = []
    
    years_list = ['1990', '1990_1999', '2000_2009', '2010_2011'] + map(str, range(2012, datetime.date.today().year + 1))
    f = []
    for i in ('film', 'film_v3_', 'film_v4_'):
        for j in years_list:
            f.append('%s%s' % (i, j))
    
    sources_dict = {
        'Сеансы': [
            'schedule',
            'schedule_v2',
            'schedule_v4',
         ],
        'Фильмы': [
            'genre_dir',
            'films_name',
            'imdb_rate',
            'movie_reviews',
            'film_posters',
            'film_trailers',
            'allfilms',
        ],
        'Персоны': [
            'persons',
        ],
        'Кинотеатры': [
            'cinema',
            'hall',
            'hall_dir',
        ],
        'Города': [
            'city_dir',
            'metro_dir',
        ],
        'Спец.методы': [
            'screens',
            'screens_v2',
            'imovie',
            'theater',
            'releases_ua',
        ],
    }

    sources_dict['Фильмы'] = sources_dict['Фильмы'] + f

    for k, v in sources_dict.iteritems():
        for i in v:
            data = {}
            try:
                modify_date = get_file_modify_datetime(settings.API_DUMP_PATH, 'dump_%s.xml' % i)
                modify_date = modify_date + datetime.timedelta(hours=4) # + 4 часа для России
            except OSError:
                modify_date = None
                
            if '0' in i:
                param = i.replace('film_v3_','').replace('film_v4_','').replace('film','')
                if '_v3_' in i:
                    get = '?version=3'
                elif '_v4_' in i:
                    get = '?version=4'
                i = 'film'
            else:
                param = ''
                get = ''
                
            data = {'category': k, 'name': i, 'modify': modify_date, 'dump': 'dump_%s' % i, 'param': param, 'get': get}

            sources_data.append(data)
    
    sources_data = sorted(sources_data, key=operator.itemgetter('category'), reverse=True)
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, sources_data, 15)
    return render_to_response('release_parser/api_import_info.html', {'p': p, 'page': page}, context_instance=RequestContext(request)) 


@only_superuser
@never_cache
def edit_city_names_relations(request):
    '''
    Редактор связей, город - название
    '''
    cities = City.objects.all()
    cities_list = {}
    cities_dict = {}
    
    for i in cities:
        for n in i.name.all():
            if n.status == 1:
                cities_list[i.id] = {'name': n.name.strip(), 'id': i.id, 'obj': i}
            
            if cities_dict.get(i.id):
                cities_dict[i.id].append({'name': n.name.strip(), 'id': n.id, 'status': n.status})
            else:
                cities_dict[i.id] = [{'name': n.name.strip(), 'id': n.id, 'status': n.status}]
    
    cities = sorted(cities_list.values(), key=operator.itemgetter('name'))

    name_id = request.POST.get('cities')
    if name_id:
        names = cities_dict.get(int(name_id))
        
        request.session['filter_edit_city_names_relations__city'] = name_id
    else:
        name_id = request.session.get('filter_edit_city_names_relations__city', cities[0]['id'])
        names = cities_dict.get(int(name_id))

    if 'rel_del' in request.POST:
        checker = request.POST.getlist('checker')
        for i in checker:
            try:
                name = NameCity.objects.get(pk=i)
                cities_list[int(name_id)]['obj'].name.remove(name)
            except NameCity.DoesNotExist: pass
        return HttpResponseRedirect(reverse('edit_city_names_relations'))

    if 'genitive' in request.POST:
        genitive = request.POST.get('genitive_text')
        if genitive:
            name, created = NameCity.objects.get_or_create(
                name = genitive, 
                status = 3, 
                defaults = {
                    'name': genitive,
                    'status': 3,
                })
            if name not in cities_list[int(name_id)]['obj'].name.all():
                cities_list[int(name_id)]['obj'].name.add(name)
        return HttpResponseRedirect(reverse('edit_city_names_relations'))
        
    return render_to_response('release_parser/city_names_relations.html', {'cities': cities, 'names': names, 'name_id': int(name_id)}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def edit_cinema_relations(request):
    '''
    Редактор связей кинотеатр - название
    '''
    cities = City.objects.all()
    cities_list = []
    
    for i in cities:
        for n in i.name.all():
            if n.status == 1:
                cities_list.append({'name': n.name.strip(), 'kid': i.kid })
            
    cities = sorted(cities_list, key=operator.itemgetter('name'))

    city = None
    names_rel = None
    cinema = None

    if request.POST:
        city = int(request.POST.get('city'))
        if request.POST.get('cinema'):
            cinema = int(request.POST.get('cinema'))
            try:
                cinema_obj = Cinema.objects.get(code=cinema, city__kid=city)
            except:
                cinema = None
        if request.POST.get('rel_del'):
            checker = request.POST.getlist('checker')
            for i in checker:
                try:
                    name = NameCinema.objects.get(pk=i)
                    cinema_obj.name.remove(name)
                except NameCinema.DoesNotExist: pass
            return HttpResponseRedirect(reverse('edit_cinema_relations'))
    
    if not city:
        city = cities[0]['kid']
    
    cinemas = Cinema.objects.filter(city__kid=city)
    
    cinemas_list = []
    cinemas_names = {}
    for i in cinemas:
        cinemas_names[i.code] = []
        for n in i.name.all():
            if n.status == 1:
                cinemas_list.append({'name': n.name.strip(), 'kid': i.code })
            cinemas_names[i.code].append(n)
    
    if cinemas:
        cinemas = sorted(cinemas_list, key=operator.itemgetter('name'))
        if not cinema:
            cinema = cinemas[0]['kid']

    names_rel = cinemas_names.get(cinema)
    return render_to_response('release_parser/cinema_relations.html', {'cinemas': cinemas, 'cities': cities, 'city': city, 'cinema': cinema, 'names_rel': names_rel}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def notfoundcinemas_temp(request):
    obj = NotFoundCinemasRelations.objects.filter(city=None)
    for i in obj:
        cin = Cinema.objects.get(code=i.kid)
        i.city = cin.city
        i.save()
    return HttpResponse(str())

@only_superuser
@never_cache
def edit_cinema_relations_alter_names(request):
    '''
    Редактор связей, установленных вручную для кинотеатров
    '''
    if request.POST:
        checker = request.POST.getlist('checker')
        NotFoundCinemasRelations.objects.filter(pk__in=checker).delete()
        return HttpResponseRedirect(reverse('edit_cinema_relations_alter_names'))
    
    kids = list(NotFoundCinemasRelations.objects.all().values_list('kid', flat=True))
    
    cinemas = Movie.objects.using('afisha').select_related('city').filter(pk__in=set(kids))
    cinemas_dict = {}
    for i in cinemas:
        cinemas_dict[i.id] = {'name': i.name, 'city': i.city.name}
        
    cinemas_alt = NotFoundCinemasRelations.objects.all()
    cinemas_alt_list = []
    for i in cinemas_alt:
        name = cinemas_dict.get(i.kid)
        cinema_name, city_name = (name['name'], name['city']) if name else (None, None)
        cinemas_alt_list.append(
            {'id': i.id, 'kid': i.kid, 'name': cinema_name, 'city': city_name, 'alt_name': i.name}
        )
        
    cinemas = sorted(cinemas_alt_list, key=operator.itemgetter('name'))
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, cinemas, 15)
    
    return render_to_response('release_parser/cinema_relations_alt_names.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def edit_films_relations_alter_names(request):
    '''
    Редактор связей, установленных вручную для фильмов 
    '''
    if request.POST:
        checker = request.POST.getlist('checker')
        NotFoundFilmsRelations.objects.filter(pk__in=checker).delete()
        return HttpResponseRedirect(reverse('edit_films_relations_alter_names'))
    
    kids = list(NotFoundFilmsRelations.objects.all().values_list('kid', flat=True))
    films = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__id__in=set(kids), type=2, status=1)

    films_dict = {}
    for i in films:
        films_dict[i.film_id_id] = {'name': i.name, 'year': i.film_id.year}
        
    films_alt = NotFoundFilmsRelations.objects.all()
    films_alt_list = []
    for i in films_alt:
        name = films_dict.get(i.kid)
        film_name, year = (name['name'], name['year']) if name else (None, None)
        films_alt_list.append(
            {'id': i.id, 'kid': i.kid, 'name': film_name, 'year': year, 'alt_name': i.name}
        )
        
    films = sorted(films_alt_list, key=operator.itemgetter('name'))
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, films, 15)
    return render_to_response('release_parser/film_relations_alt_names.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def edit_releases_relations(request):
    filter = {}
    year = None
    if request.POST:
        year = request.POST.get('year')
        if year:
            year = int(year)
            year_next = year + 1
            year_dt = datetime.date(year, 1, 1)
            year_next_dt = datetime.date(year_next, 1, 1)
            filter = {'release__release_date__gte': year_dt, 'release__release_date__lt': year_next_dt}
            
        # разрываем связь и связываем с найденным
        if 'create_relations' in request.POST:
            film = request.POST.get('nof_data')
            new_rel = request.POST.get('film')
            
            if film and new_rel:
                SubscriptionRelease.objects.filter(release__film_kid=film).delete()
                ReleasesRelations.objects.filter(film_kid=film).update(film_kid=new_rel)

            return HttpResponseRedirect(reverse('edit_releases_relations'))

    years = list(ReleasesRelations.objects.all().values_list('release__release_date', flat=True))
    years = sorted(set([i.year for i in years if i]), reverse=True)
    
    if not year:
        year = request.session.get('filter_edit_releases_relations__year', list(years)[0])
        year_next = year + 1
        year_dt = datetime.date(year, 1, 1)
        year_next_dt = datetime.date(year_next, 1, 1)
        filter = {'release__release_date__gte': year_dt, 'release__release_date__lt': year_next_dt}
    
    releases = ReleasesRelations.objects.select_related('release').filter(**filter)
    films_kids = list(ReleasesRelations.objects.filter(**filter).values_list('film_kid', flat=True))
    films = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__id__in=set(films_kids), type=2, status=1)
    
    films_dict = {}
    for i in films:
        films_dict[i.film_id_id] = i
    
    #releases_dict = {}
    #for i in releases:
    #    releases_dict[i.film_kid] = i

    films_list = []
    for i in releases:
        name = films_dict.get(i.film_kid)
        films_list.append({'film': name, 'release': i, 'name': i.release.name_ru})

    #films_list = []
    #for i in films:
    #    release = releases_dict.get(i.film_id_id)
    #    films_list.append({'film': i, 'release': release, 'name': release.release.name_ru})
    
    films = sorted(films_list, key=operator.itemgetter('name'))
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, films, 15)

    request.session['filter_edit_releases_relations__year'] = year
    return render_to_response('release_parser/edit_releases_relations.html', {'p': p, 'page': page, 'years': years, 'year': year}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_city_nof_list(request, method, dump):
    '''
    Форма для ненайденных городов/кинотеатров/залов
    '''
    xml_file = 'dump_%s.xml' % dump
    count = 0
    f = {}
    kid = ''
    # чтение из xml
    try:
        xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
        xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
        xml_nof.close()
        for i in xml_nof_data.findAll(method):
            # формирую данные для вывода в форму
            name = i['name'].encode('utf-8').replace('&', '&amp;')
            slug = i['slug'].encode('utf-8')
            info = i.get('info', '')
            if method == 'cinema':
                kid = i['city_kid'].encode('utf-8')
            if method == 'hall':
                kid = i['cinema_kid'].encode('utf-8')
            key = '%s @ %s @ %s' % (name, slug, kid)
            if method == 'hall':
                key = '%s @ %s @ %s @ %s' % (name, slug, i['id'].encode('utf-8'), kid)
            if method != 'city':
                if method == 'cinema':
                    value = '%s @ %s' % (name, i['city'].encode('utf-8'))
                else:
                    value = '%s @ %s @ %s' % (name, i['cinema'].encode('utf-8'), i['city'].encode('utf-8'))
            else:
                value = name
            if not f.get(key):
                f[key] = {'value': value, 'key': key, 'info': info}
                count += 1
    except IOError: pass
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    if f:
        f = sorted(f.values())
        p, page = pagi(page, f, 12)

    countries = []
    cities_names = []
    cinemas = []
    if method == 'cinema':
        city_filter = {'status': 1, 'city__country__id': 2}
        countries = Country.objects.filter(city__name__status=1).distinct('pk').order_by('name')
        cities_names = list(NameCity.objects.filter(**city_filter).order_by('name').values('id', 'city__id', 'name', 'city__kid'))
    elif method == 'hall':
        cinemas = {}
        cinemas_ids = []

        for i in list(NameCinema.objects.filter(status=1).values('name', 'cinema__code')):
            cinemas[i['cinema__code']] = {'name': i['name'], 'id': i['cinema__code']}
            cinemas_ids.append(i['cinema__code'])

        for i in list(NameCity.objects.filter(status=1, city__cinema__code__in=cinemas_ids).values('name', 'city__cinema__code')):
            cinemas[i['city__cinema__code']]['city'] = i['name']

        cinemas = sorted(cinemas.values(), key=operator.itemgetter('name'))

    return render_to_response('release_parser/admin_city_cinema_hall_nof_list2.html', {'count': count, 'cinemas': cinemas, 'method': method, 'dump': dump, 'p': p, 'page': page, 'countries': countries, 'cities_names': cities_names}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_city_cinema_nof(request, method, dump):
    '''
    Обработка ненайденных городов/кинотеатров
    '''
    if request.POST:
        nof_data = request.POST.get('nof_data')
        data = request.POST.get('data')

        xml_file = 'dump_%s.xml' % dump
        try:
            # чтение из xml
            xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
            xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
            xml_nof.close()
            # получение данных для связи между собой
            nof = nof_data.split(' @ ')
            nof_name = nof[0]
            nof_slug = nof[1]
            
            city = ''
            next = False

            if data:
                # получаю объект для связи
                model1, model2 = (City, NameCity) if method == 'city' else (Cinema, NameCinema)
                if method == 'city':
                    try:
                        obj = model1.objects.get(pk=data)
                    except model1.DoesNotExist:
                        return HttpResponse(str('На kinoinfo нет такого города. Импортируйте все города с киноафиши.'))
                else:
                    try:
                        obj = model1.objects.get(code=data)
                    except model1.DoesNotExist:
                        return HttpResponse(str('На kinoinfo нет такого кинотеатра. Импортируйте все кинотеатры с киноафиши.'))
                next = True
            elif request.POST.get('ignore'):
                next = True
                    
            if next:
                # удаление обрабатываемого элемента из xml файла
                for i in xml_nof_data.find_all(method, slug=nof_slug):
                    i.extract()
                
                names = [
                    {'name': nof_name, 'status': 0}, 
                    {'name': nof_slug, 'status': 2}
                ]
                if request.POST.get('kid_sid'):
                    city = nof[2]
                    city_obj = City.objects.get(kid=city)
                    if method == 'cinema':
                        nof_obj, nof_created = NotFoundCinemasRelations.objects.get_or_create(
                            name=nof_slug,
                            city=city_obj,
                            defaults={
                                'kid': data, 
                                'name': nof_slug,
                                'city': city_obj,
                            })
                elif request.POST.get('rel'):
                    # создаю объект названия, если не создан, и связываю, если нет связи
                    for i in names:
                        name_obj, created = model2.objects.get_or_create(
                            name=i['name'], 
                            status=i['status'], 
                            defaults={
                                'name': i['name'], 
                                'status': i['status']
                            })
                        if name_obj not in obj.name.all():
                            obj.name.add(name_obj)
                elif request.POST.get('ignore'):
                    # в игнор
                    with open('%s/dump_ignore_cinemas.xml' % settings.API_DUMP_PATH, 'r') as f:
                        ignore_xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
                    
                    ignored_cinemas = [i.get('name') for i in ignore_xml_data.findAll('cinema')]

                    ignore_txt = ''
                    if nof_slug not in ignored_cinemas:
                        ignore_txt = '<cinema name="%s__%s"></cinema>' % (nof_slug.encode('utf-8'), nof[2].encode('utf-8'))
                    
                    xml_data = str(ignore_xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
                    xml_data = '<data>%s%s</data>' % (xml_data, ignore_txt)
                    create_dump_file('ignore_cinemas', settings.API_DUMP_PATH, xml_data)


            # запись изменений в файл
            xml_nof = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
            create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof)
        except IOError: pass
    return HttpResponseRedirect(reverse("admin_city_nof_list2", kwargs={'method': method, 'dump': dump}))


@only_superuser
@never_cache
def admin_hall_nof(request, method, dump):

    '''
    Обработка ненайденных залов
    '''
    if request.POST:
        nof_data = request.POST.get('nof_data')
        data = request.POST.get('data')
        if data:
            xml_file = 'dump_%s.xml' % dump
            try:
                # чтение из xml
                xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
                xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
                xml_nof.close()
                # получение данных для связи между собой
                nof = nof_data.split(' @ ')
                nof_name = nof[0]
                nof_slug = nof[1]
                nof_id = nof[2]

                # получаю объект для связи
                try:
                    obj = Hall.objects.get(pk=data)
                except Hall.DoesNotExist:
                    return HttpResponse(str('На kinoinfo нет такого зала. Импортируйте все залы с киноафиши.'))
                
                # удаление обрабатываемого элемента их xml файла
                for i in xml_nof_data.find_all('hall', id=nof_id):
                    i.extract()   
                    
                names = [
                    {'name': nof_name, 'status': 0}, 
                    {'name': nof_slug, 'status': 2}
                ]
                
                # создаю объект названия, если не создан, и связываю, если нет связи
                for i in names:
                    if i['name'] != 'None':
                        name_obj, created = NameHall.objects.get_or_create(name=i['name'], status=i['status'], defaults={'name': i['name'], 'status': i['status']})
                        
                        if name_obj not in obj.name.all():
                            obj.name.add(name_obj)

                # запись изменений в файл
                xml_nof_data = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
                create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof_data)
            except IOError: pass
    return HttpResponseRedirect(reverse("admin_city_nof_list2", kwargs={'method': method, 'dump': dump}))

@only_superuser
@never_cache
def admin_films_nof(request, dump):
    '''
    Обработка ненайденных фильмов
    '''
    if request.POST:
        xml_file = 'dump_%s.xml' % dump
            
        nof_film = request.POST.get('nof_data')
        film = request.POST.get('film')
        
        if film or request.POST.get('ignore'):
            try:
                # чтение из xml
                xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
                if dump == 'kinometro_nof_film':
                    xml_nof_data = BeautifulSoup(xml_nof.read(), 'html.parser')
                else:
                    xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")

                xml_nof.close()
                
                # получение данных для связи между собой
                nof_film_name_ru, nof_film_name_en = nof_film.split(' @ ')
                source_id = 0

                if nof_film_name_ru:
                    for i in xml_nof_data.findAll('film', slug_ru=nof_film_name_ru):
                        source_id = i.get('source', 0)
                        i.extract()
                else:
                    for i in xml_nof_data.find_all('film', slug=nof_film_name_en):
                        source_id = i.get('source', 0)
                        i.extract()
                
                # если устанавливается связь
                if request.POST.get('kid_sid'):
                    film_name = nof_film_name_ru
                    if dump == 'kinometro_nof_film':
                        film_name = nof_film_name_ru if nof_film_name_ru else nof_film_name_en
                    
                    source_obj = None
                    if source_id:
                        source_obj = ImportSources.objects.get(pk=source_id)

                    obj, created = NotFoundFilmsRelations.objects.get_or_create(
                        name = film_name,
                        kid = film,
                        source_obj = source_obj,
                        defaults={
                            'kid': film, 
                            'name': film_name,
                            'source_obj': source_obj,
                        })
                # если создается альт. название
                elif request.POST.get('rel'):
                    # создание объекта связи, источника с альт.названием фильма 
                    kif, created = KIFilmRelations.objects.get_or_create(kid=film, defaults={'kid': film})
                    film_name_list = [nof_film_name_ru, nof_film_name_en]
                    for i in film_name_list:
                        if i:
                            # создание альт. названия
                            nf, created = NameFilms.objects.get_or_create(name=i, defaults={'name': i, 'status': 2})
                            # установка связи
                            if nf not in kif.name.all():
                                kif.name.add(nf)
                else:
                    with open('%s/dump_ignore_films.xml' % settings.API_DUMP_PATH, 'r') as f:
                        ignore_xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
                    
                    ignored_films = [i.get('name') for i in ignore_xml_data.findAll('film')]
                    ignore_film = nof_film_name_ru if nof_film_name_ru else nof_film_name_en
                    
                    ignore_txt = ''
                    if ignore_film not in ignored_films:
                        ignore_txt = '<film name="%s"></film>' % ignore_film.encode('utf-8')
                    
                    xml_data = str(ignore_xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
                    xml_data = '<data>%s%s</data>' % (xml_data, ignore_txt)
                    create_dump_file('ignore_films', settings.API_DUMP_PATH, xml_data)
                
                # запись изменений в файл
                xml_nof = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
                create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof)

            except IOError: pass
    return HttpResponseRedirect(reverse("admin_film_nof_list", kwargs={'dump': dump}))



@only_superuser
@never_cache
def admin_films_nof_v2(request, dump):
    nof_film = request.POST.get('nof_data')
    film = request.POST.get('film')
    
    if film or request.POST.get('ignore'):
        film_obj = SourceFilms.objects.get(pk=nof_film)
        
        # если устанавливается связь
        if request.POST.get('kid_sid'):
            film_obj.kid = film
            film_obj.save()
            
            obj, created = NotFoundFilmsRelations.objects.get_or_create(
                name = nof_film,
                defaults = {
                    'kid': film, 
                    'name': low(del_separator(film_obj.name.encode('utf-8'))),
                })
        # если создается альт. название
        elif request.POST.get('rel'):
            film_obj.kid = film
            film_obj.save()
            
            # создание объекта связи, источника с альт.названием фильма 
            kif, created = KIFilmRelations.objects.get_or_create(kid=film, defaults={'kid': film})
            film_name_list = [low(del_separator(film_obj.name.encode('utf-8')))]
            for i in film_name_list:
                if i:
                    # создание альт. названия
                    nf, created = NameFilms.objects.get_or_create(name=i, defaults={'name': i, 'status': 2})
                    # установка связи
                    if nf not in kif.name.all():
                        kif.name.add(nf)
        # если в игнор
        else:
            with open('%s/dump_ignore_films.xml' % settings.API_DUMP_PATH, 'r') as f:
                ignore_xml_data = BeautifulSoup(f.read(), from_encoding="utf-8")
            
            ignored_films = [i.get('name') for i in ignore_xml_data.findAll('film')]
            
            ignore_txt = ''
            ignore_film = low(del_separator(film_obj.name.encode('utf-8')))
            if ignore_film not in ignored_films:
                ignore_txt = '<film name="%s"></film>' % ignore_film
            
            film_obj.delete()
            
            xml_data = str(ignore_xml_data).replace('<html><head></head><body><data>','').replace('</data></body></html>','')
            xml_data = '<data>%s%s</data>' % (xml_data, ignore_txt)
            create_dump_file('ignore_films', settings.API_DUMP_PATH, xml_data)
    
    return HttpResponseRedirect(reverse("admin_film_nof_list", kwargs={'dump': dump}))


@only_superuser
@never_cache
def admin_film_nof_list_v2(request, dump):
    if dump == 'yovideo_nof_film':
        source_url = 'http://www.yo-video.net/'
    elif dump == 'top250_nof_film':
        source_url = 'http://top250.info/'
        
    films = SourceFilms.objects.filter(kid=None, source_obj__url=source_url)
    count = films.count()
    
    films_list = []
    for i in films:
        slug = low(del_separator(i.name.encode('utf-8')))
        
        url, img, director, year = (None, None, None, None)
        if i.text:
            url, img, director, year = i.text.split(';')
        
        films_list.append({
            'slug': slug, 
            'name': i.name, 
            'url': url,
            'id': i.id, 
            'alt': i.name_alter,
            'img': img, 
            'director': director, 
            'year': year,
        })
    

    films_list = sorted(films_list, key=operator.itemgetter('name'))
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    
    if count:
        p, page = pagi(page, films_list, 12)
    
    countries = Country.objects.all().order_by('name')
    limits = (0, 13, 16, 18, 21)
        
    return render_to_response('release_parser/admin_film_nof_list_v2.html', {'p': p, 'page': page, 'count': count, 'dump': dump, 'countries': countries, 'limits': limits}, context_instance=RequestContext(request))
    



@only_superuser
@never_cache
def admin_film_doubles_sources_list(request):
    sources = ImportSources.objects.all().exclude(url__in=("http://www.kinoafisha.ru/", "http://rutracker.org/"))
    
    data = []
    for i in sources:
        count = SourceFilms.objects.filter(source_obj=i, kid=None, rel_double=True, rel_ignore=False).count()
        
        if i.url == 'http://www.kinometro.ru/':
            count = ReleasesRelations.objects.filter(rel_double=True, rel_ignore=False).count()
            
        if count:
            data.append({'id': i.id, 'name': i.source, 'count': count})
    
    data = sorted(data, key=operator.itemgetter('name'))
    
    return render_to_response('release_parser/admin_film_doubles_sources_list.html', {'data': data}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def admin_film_doubles_list(request, id):
    
    if request.POST:
        nof_film = request.POST.get('nof_data')
        film = request.POST.get('film')
        source_id = request.POST.get('source')
        
        if source_id == '2':
            film_obj = ReleasesRelations.objects.get(pk=nof_film)
        else:
            film_obj = SourceFilms.objects.get(pk=nof_film)
        
            
        if 'ignore' in request.POST:
            film_obj.rel_ignore = True
        elif 'kid_sid' in request.POST:
            if source_id == '2':
                film_obj.film_kid = film
            else:
                film_obj.kid = film
        
        film_obj.rel_profile = request.profile
        film_obj.rel_dtime = datetime.datetime.now()
        film_obj.rel_double = False
        
        film_obj.save()
        return HttpResponseRedirect(reverse("admin_film_doubles_list", kwargs={'id': id}))
    
    source = ImportSources.objects.get(pk=id)
    
    data = []
    
    if source.url == 'http://www.kinometro.ru/':
        for i in ReleasesRelations.objects.select_related('release').filter(rel_double=True, rel_ignore=False):
            url = 'http://www.kinometro.ru/release/card/id/%s' % i.release.film_id
            name = u'%s / %s' % (i.release.name_ru, i.release.name_en)
            data.append({'id': i.id, 'name': name, 'url': url})
    else:
        for i in SourceFilms.objects.filter(source_obj=source, kid=None, rel_double=True, rel_ignore=False):
            url = ''
            if i.source_obj.url == 'http://ktmir.ru/':
                url = '%s/' % i.source_id.replace('http:ktmir.rufilms', 'http://ktmir.ru/films/')
            elif i.source_obj.url == 'http://kt-russia.ru/':
                url = '%s/' % i.source_id.replace('http:kt-russia.rufilms', 'http://kt-russia.ru/films/')
            elif i.source_obj.url == 'http://megamag.by/':
                url = 'http://kinoteatr.megamag.by/newsdesk_info.php?newsdesk_id=%s' % i.source_id
            elif i.source_obj.url == 'http://kino-teatr.ua/':
                url = 'http://kino-teatr.ua/film/%s.phtml' % i.source_id
            elif i.source_obj.url == 'http://etaj.mega74.ru/':
                url = 'http://etaj.mega74.ru/kino/list/films_%s.html' % i.source_id
            elif i.source_obj.url == 'http://www.rambler.ru/':
                url = 'http://kassa.rambler.ru/movie/%s' % i.source_id
            elif i.source_obj.url == 'http://kinohod.ru/':
                url = 'http://kinohod.ru/movie/%s/' % i.source_id
            elif i.source_obj.url == 'http://surkino.ru/':
                url = 'http://surkino.ru/?film=%s' % i.source_id
            elif i.source_obj.url == 'http://cinemaarthall.ru/':
                url = 'http://cinemaarthall.ru/page/kino/films/%s/' % i.source_id
            elif i.source_obj.url == 'http://www.zlat74.ru/':
                url = 'http://www.zlat74.ru/movies/%s' % i.source_id
            elif i.source_obj.url == 'http://kino-bklass.ru/':
                url = 'http://kino-bklass.ru/films/%s/' % i.source_id
            elif i.source_obj.url == 'http://www.michurinsk-film.ru/':
                url = 'http://www.michurinsk-film.ru/film/item/%s' % i.source_id
            elif i.source_obj.url == 'http://luxor.chuvashia.com/':
                url = 'http://luxor.chuvashia.com/films.aspx?id=%s' % i.source_id
            elif i.source_obj.url == 'http://vkino.com.ua/':
                url = 'http://vkino.com.ua/show/%s/about' % i.source_id
            elif i.source_obj.url == 'http://www.rottentomatoes.com/':
                url = 'http://www.rottentomatoes.com/%s' % i.source_id
            elif i.source_obj.url == 'http://www.yo-video.net/':
                url = 'http://www.yo-video.net%s' % i.source_id
            elif i.source_obj.url == 'http://www.tvzavr.ru/':
                url = i.extra
                
            data.append({'id': i.id, 'name': i.name, 'url': url})
    
    data = sorted(data, key=operator.itemgetter('name'))
    
    return render_to_response('release_parser/admin_film_doubles_list.html', {'data': data, 'source': source}, context_instance=RequestContext(request))




@only_superuser
@never_cache
def admin_film_nof_list(request, dump):
    '''
    Форма для ненайденных фильмов
    '''
    if dump in ('yovideo_nof_film', 'top250_nof_film'):
        return admin_film_nof_list_v2(request, dump)
    
    xml_file = 'dump_%s.xml' % dump
        
    count = 0
    f = {}
    distr = []

    try:
        xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
        xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
        xml_nof.close()
        for i in xml_nof_data.findAll('film'):
            name_ru = i['name_ru'].encode('utf-8').replace('&', '&amp;')
            slug_ru = i['slug_ru'].encode('utf-8')
            name = i['name'].encode('utf-8').replace('&', '&amp;')
            slug = i['slug'].encode('utf-8')
            code = i.get('code')
            if code:
                code = code.encode('utf-8')
                if dump == 'kinometro_nof_film':
                    code = int(code)
            url = i.url['value'] if i.url else None
            
            info = None
            kid = None
            
            if dump not in ('cmc_nof_films', 'planeta_nof_films'):
                info_temp = i.info['value'].split(' / ') if i.info else None
                info, kid = (info_temp[0], info_temp[1]) if len(info_temp) > 1 else (info_temp[0], None)

            key = '%s @ %s' % (slug_ru, slug)
            value = '%s @ %s' % (name_ru, name)
            if not f.get(key):
                if dump not in ('cmc_nof_films', 'planeta_nof_films'):
                    distr = [{'name': d['value'], 'kid': d['kid']} for d in i.findAll('distributor')]
                    
                f[key] = {'name': value, 'key': key, 'info': info, 'kid': kid, 'url': url, 'distr': distr, 'code': code}
                count += 1
    except IOError: pass
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    
    if f:
        sort_field, reverse = ('code', True) if dump in (u'raspishi_nof_film',) else ('name', False)
        f = sorted(f.values(), key=operator.itemgetter(sort_field), reverse=reverse)
        p, page = pagi(page, f, 12)
    
    countries = None
    limits = ()
    if dump in ('imdb_nof_film', 'yovideo_nof_film'):
        countries = Country.objects.all().order_by('name')
        limits = (0, 13, 16, 18, 21)
    
    return render_to_response('release_parser/admin_film_nof_list2.html', {'p': p, 'page': page, 'count': count, 'dump': dump, 'countries': countries, 'limits': limits}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_country_nof_list(request, dump):
    '''
    Форма для ненайденных стран
    '''
    xml_file = 'dump_%s.xml' % dump
    count = 0
    f = {}
    try:
        xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
        xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
        xml_nof.close()
        for i in xml_nof_data.findAll('country'):
            name = i['name'].encode('utf-8').replace('&', '&amp;')
            f[name] = {'name': name, 'key': name, 'value': name}
            count += 1
    except IOError: pass
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    
    if f:
        f = sorted(f.values(), key=operator.itemgetter('name'))
        p, page = pagi(page, f, 12)
    
    return render_to_response('release_parser/admin_countries_nof_list.html', {'p': p, 'page': page, 'count': count, 'dump': dump}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_country_nof(request, dump):
    '''
    Обработка ненайденных стран
    '''
    if request.POST:
        nof_data = request.POST.get('nof_data')
        data = request.POST.get('data')

        if data:
            xml_file = 'dump_%s.xml' % dump
            try:
                # чтение из xml
                xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
                xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
                xml_nof.close()
                
                # удаление обрабатываемого элемента их xml файла
                xml_nof_data.find('country', {'name': nof_data}).extract()
                
                if request.POST.get('kid_sid'):
                    obj = Country.objects.get(kid=data)
                    if obj.name_en != nof_data:
                        obj.name_en == nof_data
                        obj.save()
                
                # запись изменений в файл
                xml_nof_data = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
                create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof_data)
            except IOError: pass
    return HttpResponseRedirect(reverse("admin_country_nof_list", kwargs={'dump': dump}))



@only_superuser
@never_cache
def admin_person_nof_list(request, dump):
    '''
    Форма для ненайденных персон
    '''
    xml_file = 'dump_%s.xml' % dump 
    count = 0
    f = {}

    try:
        xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'a+')
        xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
        xml_nof.close()
        for i in xml_nof_data.findAll('person'):
            name = i['name'].encode('utf-8').replace('&', '&amp;')
            slug = i['slug'].encode('utf-8')
            code = i['code'].encode('utf-8')

            key = '%s @ %s' % (code, slug)
            if not f.get(key):
                f[key] = {'name': name, 'key': key, 'code': code}
                count += 1
    except IOError: pass
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    
    if f:
        f = sorted(f.values(), key=operator.itemgetter('name'))
        p, page = pagi(page, f, 12)
    
    return render_to_response('release_parser/admin_person_nof_list.html', {'p': p, 'page': page, 'count': count, 'dump': dump}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_person_nof(request, dump):
    '''
    Обработка ненайденных персон
    '''
    if request.POST:
        nof_data = request.POST.get('nof_data')
        data = request.POST.get('data')
        
        if data:
            xml_file = 'dump_%s.xml' % dump
            try:
                # чтение из xml
                xml_nof = open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r')
                xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
                xml_nof.close()

                p_code, p_slug = nof_data.split(' @ ')

                # удаление обрабатываемого элемента их xml файла
                xml_nof_data.find('person', code=p_code).extract()
                
                if request.POST.get('kid_sid'):
                    obj, created = NotFoundPersonsRelations.objects.get_or_create(
                        name=p_slug,
                        defaults={
                            'kid': data, 
                            'name': p_slug,
                        })
                else:
                    # получаю объект для связи
                    person = Person.objects.get(kid=data)
                    
                    lang_name = 'Русский'
                    
                    if dump == 'kinoteatrua_nof_person':
                        lang_name = 'Украинский'
                    elif dump == 'imdb_nof_person':
                        lang_name = 'Английский'
                        
                    lang = Language.objects.get(name=lang_name)
                    
                    name_obj, name_created = NamePerson.objects.get_or_create(
                        name = p_slug, 
                        status = 2, 
                        language = lang, 
                        defaults = {
                            'name': p_slug, 
                            'status': 2, 
                            'language': lang,
                        })
                    if name_obj not in person.name.all():
                        person.name.add(name_obj)

                # запись изменений в файл
                xml_nof_data = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
                create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof_data)
            except IOError: pass
    return HttpResponseRedirect(reverse("admin_person_nof_list", kwargs={'dump': dump}))


def distr_create(country_id, name):
    country_obj = Country.objects.get(pk=country_id)
    usa = True if country_obj.name == 'США' else False

    slug = low(del_separator(name.encode('utf-8')))

    obj = None
    try:
        Distributors.objects.get(name__name=slug, name__status=2, country=country_obj, usa=usa)
    except Distributors.DoesNotExist:
        obj = Distributors.objects.create(country=country_obj, usa=usa)

        for i in ({'name': name, 'status': 1}, {'name': slug, 'status': 2}):
            name_obj, name_created = NameDistributors.objects.get_or_create(
                name = i['name'],
                status = i['status'],
                defaults = {
                    'name': i['name'],
                    'status': i['status'],
                })
            obj.name.add(name_obj)

        if usa:
            afisha_obj = Company.objects.using('afisha').create(
                name = name,
                name_en = name
            )
        else:
            afisha_obj = Prokat.objects.using('afisha').create(
                name = name,
                country_id = country_obj.kid,
                address = '',
                phone = '',
                url = '',
                mail = '',
                comment = ''
            )
        obj.kid = afisha_obj.id
        obj.save()
    return obj


@only_superuser
@never_cache
def admin_distributor_list(request, country):
    '''
    Список дистрибьюторов
    '''
    if request.POST:
        if 'del' in request.POST:
            checker = request.POST.getlist('checker')
            distrs = Distributors.objects.filter(pk__in=checker)
            usa_ids = []
            prokat_ids = []
            for i in distrs:
                if i.usa:
                    usa_ids.append(i.kid)
                else:
                    prokat_ids.append(i.kid)

            Company.objects.using('afisha').filter(pk__in=usa_ids).delete()
            Prokat.objects.using('afisha').filter(pk__in=prokat_ids).delete()
            distrs.delete()

            return HttpResponseRedirect(reverse("distributor_list", kwargs={'country': country}))
        else:
            country = request.POST.get('country_filter', country)

            distributor_name = request.POST.get('distributor_name', '').strip()
            distributor_country = request.POST.get('distributor_country')

            if distributor_name and distributor_country:
                distr_create(distributor_country, distributor_name)

                return HttpResponseRedirect(reverse("distributor_list", kwargs={'country': country}))

    distr = NameDistributors.objects.filter(status=1, distributors__country__id=country).order_by('name').values('name', 'distributors__id', 'distributors__country', 'distributors__country__name')

    countries = list(Country.objects.filter(distributors__id__gt=0).order_by('name').distinct('id').values('id', 'name'))

    all_countries = list(Country.objects.all().order_by('name').values('id', 'name'))

    return render_to_response('release_parser/distributor_list.html', {'status': 'distr', 'content': distr, 'all_countries': all_countries, 'countries': countries, 'country': int(country)}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_distributor_nof_list(request, dump):
    '''
    Список ненайденных дистрибьюторов
    '''
    xml_file = 'dump_%s.xml' % dump
    
    with open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r') as f:
        xml_nof_data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    distr_list = []
    distr = Distributors.objects.all()
    for i in distr:
        for j in i.name.all():
            if j.status == 1:
                distr_list.append({'id': i.id, 'name': j.name, 'country': i.country})
    d = {}
    count = 0
    for i in xml_nof_data.findAll('distributor'):
        d[i['value']] = {'slug': i['slug'], 'alt': i['alt'], 'key': i['value']}
        count += 1
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = (None, page)
    
    if d:
        d = sorted(d.values())
        p, page = pagi(page, d, 12)
    
    countries = Country.objects.all().order_by('name')

    return render_to_response('release_parser/admin_distributor_nof_list2.html', {'countries': countries, 'p': p, 'page': page, 'distr': distr_list, 'count': count, 'dump': dump}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_distributor_nof(request, dump):
    '''
    Обрабока ненайденных дистрибьюторов
    '''
    if request.POST:
        xml_file = 'dump_%s.xml' % dump
        nof_distr = request.POST.get('nof_data')
        if nof_distr:
            # открытие файла с данными
            with open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r') as xml_nof:
                xml_nof_data = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
            # создание связи с основным дистр.
            if 'rel' in request.POST:
                distr = request.POST['distr']
                distributor = Distributors.objects.get(pk=distr)
                data = xml_nof_data.find('distributor', value=nof_distr)
                create_name_distr(nof_distr.replace('&', '&amp;'), 0, distributor)
                alt = data['alt']
                if alt and alt != 'None':
                    create_name_distr(alt.replace('&', '&amp;'), 0, distributor)
            else:
                country = request.POST.get('country')
                distr_create(country, nof_distr)

            # удаление записи из xml файла ненайденных
            xml_nof_data.find('distributor', value=nof_distr).extract()

            xml_nof_data = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
            create_dump_file(dump, settings.NOF_DUMP_PATH, xml_nof_data)

    return HttpResponseRedirect(reverse("admin_distributor_nof_list", kwargs={'dump': dump}))


@only_superuser
@never_cache
def films_doubles_relations(request):
    '''
    sources = ImportSources.objects.all().exclude(url__in=("http://www.kinoafisha.ru/", "http://rutracker.org/"))
    sources_dict = {}
    for i in sources:
        sources_dict[i.id] = {'obj': i, 'doubles': []}

    for k, v in sources_dict.iteritems():
        doubles = []
        films = {}
        for i in SourceFilms.objects.filter(source_obj__id=k).exclude(Q(kid=None) | Q(kid=0)):
            if films.get(i.kid):
                films[i.kid].append(i)
                doubles.append(i.kid)
            else:
                films[i.kid] = [i]
        
        #return HttpResponse(str(films.values()))
        
        for i in set(doubles):
            v['doubles'].append({'kid': i, 'films': films[i]})
            
            for j in films[i]:
                j.kid = None
                j.rel_double = True
                j.save()
    '''
    km_doubles = []
    km_films = {}
    for i in ReleasesRelations.objects.select_related('release').all():

        if km_films.get(i.film_kid):
            km_films[i.film_kid].append(i)
            km_doubles.append(i.film_kid)
        else:
            km_films[i.film_kid] = [i]
    
    ReleasesRelations.objects.filter(film_kid__in=set(km_doubles)).update(rel_double = True)
    return HttpResponse(str())
    return render_to_response('release_parser/admin_films_doubles.html', {'data': sources_dict.values()}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def admin_sources_editor(request):
    '''
    Редактор источников
    '''
    sources = ImportSources.objects.all()
    
    source_id = None
    if request.POST:
        form = ImportSourcesForm(request.POST)
        source_id = request.POST.get('source_id')
        if source_id:
            source_id = int(source_id)
        if 'create' in request.POST or 'save' in request.POST or 'delete' in request.POST:
            if 'create' in request.POST and form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('admin_sources_editor'))
            else:
                
                if 'save' in request.POST and form.is_valid():
                    source = get_object_or_404(ImportSources, pk=source_id)
                    source.source = form.cleaned_data['source']
                    source.url = form.cleaned_data['url']
                    code = form.cleaned_data['code'] if form.cleaned_data['code'] else None
                    dump = form.cleaned_data['dump'] if form.cleaned_data['dump'] else None
                    source.code = code
                    source.dump = dump
                    source.save()
                    return HttpResponseRedirect(reverse('admin_sources_editor'))
                elif 'delete' in request.POST:
                    source = get_object_or_404(ImportSources, pk=source_id)
                    source.delete()
                    return HttpResponseRedirect(reverse('admin_sources_editor'))
            
    else:
        form = ImportSourcesForm()
        
    sources_list = []
    for i in sources:
        sources_list.append({'id': i.id, 'source': i.source, 'url': i.url, 'code': i.code, 'dump': i.dump})
        if source_id and int(source_id) == i.id:
            initial = {'source': i.source, 'url': i.url, 'code': i.code, 'dump': i.dump}
            form = ImportSourcesForm(initial=initial)

    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, sources_list, 15)

    return render_to_response('release_parser/admin_sources_editor.html', {'form': form, 'p': p, 'page': page, 'source_id': source_id}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def admin_delete_source_data(request):
    if request.POST:
        source_id = request.POST.get('sources')
        source_obj = get_object_or_404(ImportSources, pk=source_id)
        SourceCities.objects.filter(source_obj=source_obj).delete()
        SourceCinemas.objects.filter(source_obj=source_obj).delete()
        SourceFilms.objects.filter(source_obj=source_obj).delete()
        SourceHalls.objects.filter(source_obj=source_obj).delete()
        SourceSchedules.objects.filter(source_obj=source_obj).delete()
        return HttpResponseRedirect(reverse("admin_delete_source_data"))
    sources = ImportSources.objects.all().values('id', 'source')
    return render_to_response('release_parser/admin_delete_source_data.html', {'sources': sources}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def edit_source_films_relations(request):
    films_names = list(SourceFilms.objects.all().values_list('name', flat=True).distinct('name'))
    alphabet_filter = sorted(set([low(del_separator(i.encode('utf-8'))).decode('utf-8')[0] for i in films_names]))
    
    char = None

    if request.POST:
        char = request.POST.get('char')
        if request.POST.get('kid_sid'):
            checker = request.POST.getlist('checker')
            film_kid = request.POST.get('film')
            if checker and film_kid:
                SourceFilms.objects.filter(pk__in=checker).update(kid=film_kid)
                return HttpResponseRedirect(request.get_full_path())
                
    if not char:
        char = request.session.get('filter_source_films_rel__char', alphabet_filter[0])
    
    films = SourceFilms.objects.filter(name__istartswith=char)
    kids = set([i.kid for i in films])
    
    afisha_films = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__id__in=kids, status=1, type=2)
    afisha_films_dict = {}
    for i in afisha_films:
        afisha_films_dict[i.film_id_id] = i
    
    films_list = []
    for i in films:
        af = afisha_films_dict.get(i.kid)
        films_list.append({'name': i.name, 'af': af, 'kf': i})
        
    films_list = sorted(films_list, key=operator.itemgetter('name'))
        
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, films_list, 10)
    
    request.session['filter_source_films_rel__char'] = char
    return render_to_response('release_parser/edit_source_films_relations.html', {'alphabet_filter': alphabet_filter, 'p': p, 'page': page, 'char': char}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def admin_source_releases_show(request):
    today = datetime.date.today()
    releases = SourceReleases.objects.filter(release__gte=today, source_obj__url='http://www.okino.ua/').order_by('release')
    
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, releases, 10)
    return render_to_response('release_parser/source_releases_show.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def actions_pricelist(request):
    groups = ACTION_OBJ_CHOICES
    
    group = None
    if request.POST:
        group = request.POST.get('group')
        
    if not group:
        group = request.session.get('filter_actions_pricelist__group', '0')
        
    request.session['filter_actions_pricelist__group'] = group
    
    actions = ActionsPriceList.objects.filter(group=group)

    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, actions, 12)
    return render_to_response('release_parser/actions_pricelist.html', {'p': p, 'page': page, 'groups': groups, 'group': group}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def edit_actions_pricelist(request, id):
    actions = get_object_or_404(ActionsPriceList, pk=id)
    
    if request.POST:
        form = ActionsPriceListForm(request.POST)
        if form.is_valid():
            actions.title = form.cleaned_data['title']
            actions.price = form.cleaned_data['price']
            actions.price_edit = form.cleaned_data['price_edit']
            actions.price_delete = form.cleaned_data['price_delete']
            actions.allow = form.cleaned_data['allow']
            actions.group = form.cleaned_data['group']
            actions.project = form.cleaned_data['project']
            actions.user_group = form.cleaned_data['user_group']
            actions.save()
            return HttpResponseRedirect(reverse('actions_pricelist'))
    else:
        form = ActionsPriceListForm(initial={
            'title': actions.title,
            'price': actions.price,
            'price_edit': actions.price_edit,
            'price_delete': actions.price_delete,
            'group': actions.group,
            'user_group': actions.user_group,
            'allow': actions.allow,
            'project': actions.project,
        })
        
    return render_to_response('release_parser/edit_actions_pricelist.html', {'form': form}, context_instance=RequestContext(request))    


@only_superuser
@never_cache
def add_actions_pricelist(request):

    if request.POST:
        form = ActionsPriceListForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('actions_pricelist'))

    else:
        form = ActionsPriceListForm(initial={
            'price': 0,
            'price_edit': 0,
            'price_delete': 0,
            'allow': True,
        })
        
    return render_to_response('release_parser/edit_actions_pricelist.html', {'form': form}, context_instance=RequestContext(request))    


@only_superuser
@never_cache
def paid_actions_list(request, id, all=None):
    
    group = None
    if request.POST:
        group = request.POST.get('user_group')
        
        checker = request.POST.getlist('checker')
        if checker:
            actions = PaidActions.objects.select_related('profile', 'action').filter(pk__in=checker, action__group=id)
            if request.POST.get('pay'):
                for i in actions:
                    number = int(request.POST.get('number_%s' % i.id))
                    i.allow = True
                    i.number = number
                    i.save()

                    if i.action_id not in (1, 2, 16, 17, 18):

                        interface = i.profile.personinterface
                        if i.act == '1':
                            price = i.action.price
                        elif i.act == '2':
                            price = i.action.price_edit
                        elif i.act == '3':
                            price = i.action.price_delete

                        interface.money += float((float(price) * number))
                        interface.save()
            elif request.POST.get('del'):
                for i in actions:
                    if i.action_id in (1, 2, 16, 17, 18):
                        interface = i.profile.personinterface
                        if i.act == '1':
                            price = i.action.price
                        elif i.act == '2':
                            price = i.action.price_edit
                        elif i.act == '3':
                            price = i.action.price_delete

                        interface.money -= float(price)
                        interface.save()

                    i.ignore = True
                    i.save()
            return HttpResponseRedirect(reverse('paid_actions_list', kwargs={'id': id}))
    
    groups = {
        '1': {'id': '1', 'name': 'Суперюзеры', 'filter': {'profile__user__is_superuser': True}}, 
        '2': {'id': '2', 'name': 'Aвторизованные', 'filter': {'profile__user__is_superuser': False}},
        '3': {'id': '3', 'name': 'Остальные', 'filter': {'profile__accounts': None}},
    }
    
    filter = {}
    if all != 'all':
        filter = {'action__allow': True, 'allow': False, 'ignore': False}
    
    filter['action__group'] = id
    filter['future'] = False
    
    if not group:
        group = request.session.get('filter_paid_actions__group', '1')
        
    request.session['filter_paid_actions__group'] = group
    
    group = groups.get(group)

    filter = dict(filter.items() + group['filter'].items())
    if group['id'] == '2':
        actions = PaidActions.objects.select_related('profile', 'action').exclude(profile__accounts=None).filter(**filter).order_by('-dtime')
    else:
        actions = PaidActions.objects.select_related('profile', 'action').filter(**filter).order_by('-dtime')
    
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, actions, 30)
    
    
    profiles = set([i.profile for i in p.object_list])
    peoples = org_peoples(profiles)
    
    objs_ids = [i.object for i in p.object_list if i.object and i.object.isdigit()]
    objs_dict = {}
    if objs_ids:
        if id == '3': # фильм
            films = FilmsName.objects.using('afisha').filter(film_id__id__in=objs_ids, status=1, type__in=(1, 2))
            for i in films:
                if objs_dict.get(str(i.film_id_id)):
                    if not objs_dict[str(i.film_id_id)]['ntype']:
                        objs_dict[str(i.film_id_id)] = {'name': i.name, 'id': i.film_id_id, 'ntype': True}
                else:
                    ntype = True if i.type == 2 else False
                    objs_dict[str(i.film_id_id)] = {'name': i.name, 'id': i.film_id_id, 'ntype': ntype}
                    
        elif id == '2': # персона
            persons = list(NamePerson.objects.filter(person__pk__in=objs_ids, status=1, language__id=1).values('person__id', 'name', 'person__kid'))
            for i in persons:
                objs_dict[str(i['person__id'])] = {'name': i['name'], 'id': i['person__kid']}
    
    actions_list = []
    for i in p.object_list:
        obj = objs_dict.get(i.object, {'name': 'Не найден в БД', 'id': ''})
        user = None
        for j in peoples:
            if j['id'] == i.profile.user_id:
                user = j
        actions_list.append({'obj': i, 'name': obj['name'], 'id': obj['id'], 'user': user})

    return render_to_response('release_parser/paid_actions_list.html', {'p': p, 'page': page, 'all': all, 'groups': groups, 'group': group, 'actions_list': actions_list, 'id': id}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def get_user_page_info(request, id):
    profile = get_object_or_404(Profile, user__id=id)
    card = get_usercard(profile.user)
    p_accounts = card['accounts']
    folder = profile.folder
    return render_to_response('user/user_page_info.html', {'p_accounts': p_accounts, 'card': card, 'id': id, 'folder': folder}, context_instance=RequestContext(request))


# STATISTICS

@only_superuser
@never_cache
def buy_ticket_statistics(request):
    data = BuyTicketStatistic.objects.select_related('film', 'cinema', 'cinema__city').all()
    count = data.count()
    
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, data, 10)
    return render_to_response('release_parser/buy_ticket_statistic.html', {'p': p, 'page': page, 'count': count}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def boxoffice_relations(request, id):
    next = request.session.get('boxoffice__next')
    obj = BoxOffice.objects.get(pk=id)
    
    if request.POST:
        box = BoxOffice.objects.filter(kid=obj.kid)
        
        # связь с новым дистрибьютором
        if request.POST.get('create_relations'):
            distrib = request.POST.get('distributor')
            distrib_obj = Distributors.objects.get(pk=distrib)
            for i in box:
                i.distributor.add(distrib_obj)
        # удаление связи
        elif request.POST.get('del_relations'):
            distr_temp = request.POST.get('object')
            distrib_obj = Distributors.objects.get(pk=distr_temp)
            for i in box:
                i.distributor.remove(distrib_obj)
            
        return HttpResponseRedirect('')
    
    distr = Distributors.objects.all()
    distr_list = []
    for i in distr:
        for n in i.name.all():
            if n.status == 1:
                distr_list.append({'name': n.name, 'id': i.id})
                
    distributors = sorted(distr_list, key=operator.itemgetter('name'))
    
    return render_to_response('release_parser/boxoffice_relations.html', {'id': id, 'obj': obj, 'next': next, 'distributors': distributors}, context_instance=RequestContext(request))


def boxoffice_func(request, country, admin=False):
#    bug = ofc76
    weekends = list(BoxOffice.objects.filter(country__name=country).values_list('date_to', flat=True).order_by('date_to').distinct('date_to'))
#     import sys
#    for i in weekends:
#        print >>sys.stderr, i    

    weekend = None
    distributor = None
    
    sort_sumall = request.GET.get('sumall')
    sort_sumwee = request.GET.get('sumwee')
    sort_sumavg = request.GET.get('sumavg')
    sort_audavg = request.GET.get('audavg')

    if sort_sumwee:
        sort_field = 'week_sum'
        url_param = 'sumwee'
        value = sort_sumwee
    elif sort_sumall:
        sort_field = 'all_sum'
        url_param = 'sumall'
        value = sort_sumall
    elif sort_sumavg:
        sort_field = 'week_sum_avg'
        url_param = 'sumavg'
        value = sort_sumavg
    elif sort_audavg:
        sort_field = 'week_audience_avg'
        url_param = 'audavg'
        value = sort_audavg
    else:
        sort_field = 'week_sum'
        url_param = 'sumwee'
        value = 1

    try:
        value = int(value)
    except ValueError:
        value = 1
    
    value, sort_reverse = (0, True) if value else (1, False)

    if request.POST and request.user.is_superuser:
        weekend = request.POST.get('weekend')
        if weekend:
            day, month, year = weekend.split('.')
            weekend = datetime.date(int(year), int(month), int(day))
            
        distributor = request.POST.get('distributor')
        if distributor and distributor != 'all':
            distributor = int(distributor)
            
        if request.POST.get('edit_relations'):
            id = request.POST.get('object')
            next = request.get_full_path()
            request.session['boxoffice__next'] = next
            return {'redirect': True, 'param': id}
            #return HttpResponseRedirect(reverse("boxoffice_relations", kwargs={'id': id}))
            
    if not weekend and weekends:
        if admin:
            weekend = request.session.get('filter_boxoffice__weekend', sorted(weekends, reverse=True)[0])
        else:
            weekend = sorted(weekends, reverse=True)[0]
            
    filter = {'date_to': weekend, 'country__name': country}
    if not distributor:
        if admin:
            distributor = request.session.get('filter_boxoffice__distributor')
        
    box = BoxOffice.objects.filter(**filter).order_by('-week_sum')

    distributors_data = Distributors.objects.filter(box_office__id__in=[o.id for o in box], name__status=1)
    distributors_id = [o.id for o in distributors_data]

    box_to_distributors = collections.defaultdict(list)
    for o in distributors_data.values('box_office__id', 'id', 'kid'):
        box_to_distributors[o['box_office__id']].append(o)

    name_distributors = collections.defaultdict(list)
    for o in NameDistributors.objects.filter(
                distributors__id__in=distributors_id, status=1).values('distributors__id', 'id', 'name'):
        name_distributors[o['distributors__id']].append(o)

    distributor_filter = []
    distributors = {}
    distributors_names = {}
    kid = []

    for i in box:
        kid.append(i.kid)
        distrib = []
        for distr in box_to_distributors[i.id]:
            for dname in name_distributors[distr['id']]:
                distrib.append(dname['name'])
                distributors[distr['kid']] = {'id': distr['id'], 'kid': distr['kid'], 'name': dname['name']}
                if distributor and distributor != 'all' and distributor == distr['kid']:
                    distributor_filter.append(i.id)
            distributors_names[i.id] = ' / '.join(distrib)

    films = FilmsName.objects.using('afisha').filter(film_id__id__in=set(kid), status=1, type=2)
    films_dict = {}
    for i in films:
        films_dict[i.film_id_id] = i.name

    box_list = []
    for i in box:
        if not distributor_filter or distributor_filter and i.id in distributor_filter:
            name = films_dict.get(i.kid)
            
            distrib = distributors_names.get(i.id)
            
            all_audience, week_audience = (float(i.all_audience), i.week_audience) if i.all_audience else (0, 0)
            
            week_audience_avg = 0
            
            screens = i.screens if i.screens else 0
            
            if all_audience and not week_audience:
                week_audience = int(float(i.week_sum) / (float(i.all_sum) / all_audience))
                
                week_audience_avg = week_audience / screens if screens else 0

            days = i.days if i.days else ''


            week_sum_avg = i.week_sum / screens if screens else 0
            data = {
                'name': name,
                'distrib': distrib,
                'week_audience': week_audience,
                'all_audience': all_audience,
                'week_audience_avg': week_audience_avg,
                'week_sum': i.week_sum,
                'all_sum': i.all_sum,
                'week_sum_avg': week_sum_avg,
                'screens': screens,
                'days': days,
                'kid': i.kid,
                'id': i.id,
            }
            box_list.append(data)
    
        
    box_list = sorted(box_list, key=operator.itemgetter(sort_field), reverse=sort_reverse)
    box_list_placed = []
    for ind, i in enumerate(box_list):
        i['place'] = ind + 1
        i['week_audience'] = intcomma(int(i['week_audience'])).replace(',', ' ')
        i['all_audience'] = intcomma(int(i['all_audience'])).replace(',', ' ')
        i['week_audience_avg'] = intcomma(int(i['week_audience_avg'])).replace(',', ' ')
        i['week_sum'] = intcomma(int(i['week_sum'])).replace(',', ' ')
        i['all_sum'] = intcomma(int(i['all_sum'])).replace(',', ' ')
        i['week_sum_avg'] = intcomma(int(i['week_sum_avg'])).replace(',', ' ')
        i['screens'] = intcomma(int(i['screens'])).replace(',', ' ')
        box_list_placed.append(i)

    distributors = sorted(distributors.values(), key=operator.itemgetter('name'))
    
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    items = 15
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        items = 500
        
    p, page = pagi(page, box_list_placed, items)
    
    if admin:
        request.session['filter_boxoffice__distributor'] = distributor
        request.session['filter_boxoffice__weekend'] = weekend
    
    data = {'p': p, 'page': page, 'weekends': weekends, 'weekend': weekend, 'distributors': distributors, 'distributor': distributor, 'url_param': url_param, 'value': value}
    return data


@only_superuser
@never_cache
def boxoffice_admin(request, country):
    country_name = None
    if country == 'russia':
        country_name = 'Россия'
    if country == 'usa':
        country_name = 'США'
    
    if country_name:
        data = boxoffice_func(request, country_name, True)
        if data.get('redirect'):
            return HttpResponseRedirect(reverse("boxoffice_relations", kwargs={'id': data['param']}))
        data['country'] = country
        return render_to_response('release_parser/boxoffice.html', data, context_instance=RequestContext(request))
    else:
        raise Http404
    
    
@only_superuser
@never_cache
def boxoffice_del(request, country):
    if request.POST:
        ids = request.POST.getlist('checker')
        if ids:
            BoxOffice.objects.filter(pk__in=ids).delete()
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    raise Http404


@only_superuser
@never_cache
def edit_source_cinemas_relations(request):
    sources_ids = list(SourceCinemas.objects.all().values_list('source_obj', flat=True).distinct('source_obj'))
    sources = ImportSources.objects.filter(pk__in=sources_ids)
    
    source = None
    if request.POST:
        source = request.POST.get('source')
        if source:
            source = int(source)
            
        if 'kid_sid' in request.POST:
            new_cin = request.POST.get('data')
            cur_cin = request.POST.get('nof_data')
            if cur_cin and new_cin:
                cin_id = cur_cin.split(' @ ')[0]
                cin_obj = SourceCinemas.objects.get(pk=cin_id)
                new_cin_obj = Cinema.objects.get(code=new_cin)
                cin_obj.cinema = new_cin_obj 
                cin_obj.save()
                
            return HttpResponseRedirect(reverse("source_cinemas_relations"))
            
    if not source:
        source = request.session.get('filter_edit_source_cinemas__source', sources[0].id)
    
    cinemas = SourceCinemas.objects.select_related('city', 'cinema').filter(source_obj__id=source)
    
    cinemas_dict = {}
    for i in cinemas:
        cinemas_dict[i.cinema.code] = i
        
    afisha_cinemas = Movie.objects.using('afisha').select_related('city').filter(pk__in=cinemas_dict.keys())
    cinema_list = []
    for i in afisha_cinemas:
        obj = cinemas_dict.get(i.id)
        cinema_list.append({'afisha': i, 'source': obj, 'city_name': obj.city.name})
    
    cinema_list = sorted(cinema_list, key=operator.itemgetter('city_name'))
    
    page = request.GET.get('page')   
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, cinema_list, 12)
    
    request.session['filter_edit_source_cinemas__source'] = source
    return render_to_response('release_parser/edit_source_cinemas_relations.html', {'p': p, 'page': page, 'sources': sources, 'source': source}, context_instance=RequestContext(request))
    

@only_superuser
@never_cache
def admin_city_statistics(request):
    today = datetime.date.today()
    sources = ImportSources.objects.all()
    sources_dict = {}
    for i in sources:
        sources_dict[i.id] = i

    afisha = {}
    filter = {}
    char = None
    country = None
    source = None
    alphabet_filter = []
    cities_list = []
    '''
    request.session['filter_city_statistics__country'] = None
    request.session['filter_city_statistics__char'] = None
    request.session['filter_city_statistics__source'] = None
    return HttpResponse(str())
    '''
    afisha_cities = AfishaCity.objects.using('afisha').select_related('country').filter(country__name__in=('Россия', 'Беларусь', 'Украина'))

    for i in afisha_cities:
        if afisha.get(i.country_id):
            afisha[i.country_id]['city'].append(i)
            afisha[i.country_id]['count'] += 1
        else:
            afisha[i.country_id] = {'name': i.country.name, 'city': [i], 'count': 1}
    
    # список первых букв названий городов
    for i in afisha.values():
        for j in i['city']:
            alphabet_filter.append(j.name[0])
    alphabet_filter = sorted(set(alphabet_filter))
    
    countries_ids = sorted(afisha.keys())
    filter = {'country__id__in': countries_ids}
    
    if request.POST:
        source = request.POST.get('source')
        if source != 'all' and source != 'no':
            source = int(source)
            
        country = request.POST.get('country')
        if country != 'all':
            country = int(country)
            
        char = request.POST.get('char')
    

    if not country:
        country = request.session.get('filter_city_statistics__country')
        # temp
        if country == 'no':
            country = None
    if country and country != 'all':
        filter['country__id'] = country

    if not char:
        char = request.session.get('filter_city_statistics__char')
        # temp
        if char == 'no':
            char = None
    if char and char != 'all':
        filter['name__istartswith'] = char


    if not source:
        source = request.session.get('filter_city_statistics__source')

    f = {'dtime__gte': today}
    if source and source != 'no' and source != 'all':
        s = sources_dict.get(source)
        if s:
            f['source_obj__id'] = s.id
        myfilter = 'cinema__cinema__city__kid'

        # получаю список городов у источника
        cities = list(SourceSchedules.objects.filter(**f).distinct(myfilter).values_list(myfilter, flat=True))

        
        # получю массив данных о городах у источника
        for i in afisha.values():
            for j in i['city']:
                if j.id in cities:
                    cities_list.append(j.id)

        filter['pk__in'] = set(cities_list)

    # выборка городов
    cities = AfishaCity.objects.using('afisha').select_related('country').filter(**filter).values('id', 'name', 'country__name')

    cities_ids = {}
    for i in cities:
        cities_ids[i['id']] = i
        cities_ids[i['id']]['equals'] = 0
        cities_ids[i['id']]['not_equals'] = 0
        cities_ids[i['id']]['not_equals_cities'] = []
    
    source_cities = SourceCities.objects.select_related('city', 'source_obj').filter(source_obj__in=sources_dict.values(), city__kid__in=cities_ids.keys()).order_by('name')

    for i in source_cities:
        city = cities_ids.get(i.city.kid)
        if city:
            if city['name'] == i.name.encode('utf-8'):
                cities_ids[i.city.kid]['equals'] += 1
            else:
                cities_ids[i.city.kid]['not_equals'] += 1
                cities_ids[i.city.kid]['not_equals_cities'].append({'name': i.name, 'source': i.source_obj.source})
    
    # если фильтр 'Нет источника'
    if source == 'no':
        cities_ids2 = {} 
        for k, v in cities_ids.iteritems():
            if not v['not_equals'] and not v['equals']:
                cities_ids2[k] = v
        cities_ids = cities_ids2

    cities = sorted(cities_ids.values(), key=operator.itemgetter('name'))
    amount = afisha

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, cities, 12)
    
    # переменные в сессию
    request.session['filter_city_statistics__country'] = country
    request.session['filter_city_statistics__char'] = char
    request.session['filter_city_statistics__source'] = source
    return render_to_response('release_parser/admin_city_statistics.html', {'p': p, 'page': page, 'alphabet_filter': alphabet_filter, 'char': char, 'amount': amount, 'afisha': afisha, 'country': country, 'sources': sources_dict, 'source': source, 'sources_dict': sources_dict}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_cinemas_statistics(request):
    today = datetime.date.today()
    
    sources = ImportSources.objects.all()
    sources_dict = {}
    for i in sources:
        sources_dict[i.id] = i

    afisha = {}
    filter = {}
    char = None
    city = None
    source = None
    network = None
    session = None
    alphabet_filter = []
    cinemas_list = []
    counter = {}
    networks = {}

    timer_list = []
    timer = time.time()

    afisha_cinemas = list(
        Movie.objects.using('afisha').filter(
            city__country__name__in=('Россия', 'Беларусь', 'Украина')
        ).values(
            'id', 'name', 'city', 'city__country', 'city__country__name',
            'set_field', 'set_field__name', 'city__name'))

    for i in afisha_cinemas:
        if not afisha.get(i['city']):
            afisha[i['city']] = {
                'name': i['city__name'],
                'cinema': [],
                'count': 0,
                'city_id': i['city'],
                'set': i['set_field']}
        afisha[i['city']]['cinema'].append(i)
        afisha[i['city']]['count'] += 1

        if not counter.get(i['city__country']):
            counter[i['city__country']] = {'name': i['city__country__name'], 'count': 0}
        counter[i['city__country']]['count'] += 1

        if i['set_field'] > 0 and not networks.get(i['set_field']):
            networks[i['set_field']] = {'id': i['set_field'], 'name': i['set_field__name']}

    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()

    # список первых букв названий кинотеатров 
    for i in afisha.values():
        for j in i['cinema']:
            alphabet_filter.append(j['name'].encode('utf-8').decode('utf-8')[0])

    alphabet_filter = sorted(set(alphabet_filter))
    
    cities_ids = sorted(afisha.keys())
    filter = {'city__id__in': cities_ids}
    
    if request.POST:
        source = request.POST.get('source')
        if source != 'all' and source != 'no':
            source = int(source)
            
        city = request.POST.get('city')
        if city != 'all':
            city = int(city)
            
        char = request.POST.get('char')
        
        session = request.POST.get('session')
        if session != 'all':
            session = int(session)
        
        network = request.POST.get('network')
        if network != 'all':
            network = int(network)

    if not city:
        city = request.session.get('filter_cinema_statistics__city')

    if city and city != 'all':
        filter['city__id'] = city

    if not char:
        char = request.session.get('filter_cinema_statistics__char')

    if char and char != 'all':
        filter['name__istartswith'] = char

    if network and network != 'all':
        filter['set_field__id'] = network

    if session is None:
        session = request.session.get('filter_cinema_statistics__session', 'all')

    if not source:
        source = request.session.get('filter_cinema_statistics__source')
      
    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()

    f = {'dtime__gte': today}
    if source and source != 'no' and source != 'all':
        s = sources_dict.get(source)
        if s:
            f['source_obj__id'] = s.id
        myfilter = 'cinema__cinema__code'

        # получаю список кинотеатров у источника
        cinemas = list(SourceSchedules.objects.filter(**f).distinct(myfilter).values_list(myfilter, flat=True))
        
        # получю массив данных о кинотеатрах у источника
        for i in afisha.values():
            for j in i['cinema']:
                if j['id'] in cinemas:
                    cinemas_list.append(j['id'])

        filter['pk__in'] = set(cinemas_list)


    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()

    schedule_filter = {'schedule_id__movie_id__id__in': set(cinemas_list)} if cinemas_list else {}
    
    schedules = AfishaSession.objects.using('afisha').select_related('schedule_id').filter(Q(schedule_id__date_from__gte=today) | Q(schedule_id__date_from__lt=today) & Q(schedule_id__date_to__gte=today)).filter(**schedule_filter)

    cinemas_schedules = {}
    for i in schedules:
        date_from = i.schedule_id.date_from
        date_to = i.schedule_id.date_to
        delta = date_to - date_from
        days = delta.days + 1
        
        if cinemas_schedules.get(i.schedule_id.movie_id_id):
            cinemas_schedules[i.schedule_id.movie_id_id]['sessions'] += days
            cinemas_schedules[i.schedule_id.movie_id_id]['dates'].append(date_to)
        else:
            cinemas_schedules[i.schedule_id.movie_id_id] = {'sessions': days, 'dates': [date_to]}

    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()

    # выборка кинотеатров
    cinemas = Movie.objects.using('afisha').select_related('city').filter(**filter).values('id', 'name', 'city__name')

    cinemas_ids = {}
    for i in cinemas:
        cinemas_ids[i['id']] = i
        cinemas_ids[i['id']]['equals'] = 0
        cinemas_ids[i['id']]['not_equals'] = 0
        cinemas_ids[i['id']]['not_equals_cinemas'] = []
        cinemas_ids[i['id']]['sessions'] = 0
        cinemas_ids[i['id']]['date'] = ''
    

    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()

    source_cinemas = SourceCinemas.objects.select_related('cinema', 'source_obj').filter(source_obj__in=sources_dict.values(), cinema__code__in=cinemas_ids.keys()).order_by('name')

    for i in source_cinemas:
        cinema = cinemas_ids.get(i.cinema.code)
        sessions = cinemas_schedules.get(i.cinema.code)

        if sessions:
            cinemas_ids[i.cinema.code]['date'] = sorted(sessions['dates'], reverse=True)[0]
            cinemas_ids[i.cinema.code]['sessions'] = sessions['sessions']
            
        if session == 0:
            cinemas_ids.pop(i.cinema.code)
            cinema = None

        if cinema:
            if cinema['name'] == i.name.encode('utf-8'):
                cinemas_ids[i.cinema.code]['equals'] += 1
            else:
                cinemas_ids[i.cinema.code]['not_equals'] += 1
                cinemas_ids[i.cinema.code]['not_equals_cinemas'].append({'name': i.name, 'source': i.source_obj.source})
    
    timer = '%5.2f' % (time.time()-timer)
    timer_list.append(timer)
    timer = time.time()
    
    if session == 1:
        del_sess = [k for k, v in cinemas_ids.iteritems() if not v['sessions']]
        for i in del_sess:
            del cinemas_ids[i]
    
    # если фильтр 'Нет источника'
    if source == 'no':
        cinemas_ids2 = {} 
        for k, v in cinemas_ids.iteritems():
            if not v['not_equals'] and not v['equals']:
                cinemas_ids2[k] = v
        cinemas_ids = cinemas_ids2

    cinemas = sorted(cinemas_ids.values(), key=operator.itemgetter('name'))
    afisha = sorted(afisha.values(), key=operator.itemgetter('name'))
    networks = sorted(networks.values(), key=operator.itemgetter('name'))
    amount = counter

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, cinemas, 12)
    
    # переменные в сессию
    request.session['filter_cinema_statistics__city'] = city
    request.session['filter_cinema_statistics__char'] = char
    request.session['filter_cinema_statistics__source'] = source
    request.session['filter_cinema_statistics__session'] = session

    timer = '%5.2f' % (time.time() - timer)
    timer_list.append(timer)

    #return HttpResponse(str(timer_list))
    return render_to_response('release_parser/admin_cinema_statistics.html', {'p': p, 'page': page, 'alphabet_filter': alphabet_filter, 'char': char, 'amount': amount, 'afisha': afisha, 'city': city, 'sources': sources_dict, 'source': source, 'sources_dict': sources_dict, 'networks': networks, 'network': network, 'session': session, 'timer_list': timer_list}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def comments_moderator(request):
    '''
    Пакетное удаление сообщений, блокировка по ID и IP
    '''
    reader_type = ('8', '9', '10')

    if request.POST:
        news_ids = set(request.POST.getlist('checker'))
        ofilter = {}

        if 'del_msg' in request.POST or 'date_filter' in request.POST or 'user_id_del_filter' in request.POST:
            if 'del_msg' in request.POST:
                ofilter = {'news__pk__in': news_ids} if news_ids else {}
            elif 'user_id_del_filter' in request.POST:
                user_id = request.POST.get('user_id_del')
                if user_id:
                    ofilter = {'news__autor__user__id': user_id.strip()}
            else:
                dfrom = request.POST.get('date_from')
                dto = request.POST.get('date_to')
                if dfrom and dto:
                    dfrom = '%s 00:00:00' % dfrom.strip()
                    dto = '%s 23:59:59' % dto.strip()
                    ofilter = {'news__dtime__gte': dfrom, 'news__dtime__lte': dto, 'news__reader_type__in': reader_type}

            orgnews = []
            news = []

            if ofilter:
                for i in OrganizationNews.objects.filter(**ofilter):
                    if i.news.reader_type == '8':
                        ntype = 'отзыв'
                    elif i.news.reader_type == '9':
                        ntype = 'вопрос'
                    elif i.news.reader_type == '10':
                        ntype = 'комментарий'

                    ActionsLog.objects.create(
                        profile=request.profile,
                        object='1',
                        action='3',
                        object_id=i.organization_id,
                        attributes=ntype,
                        site=request.current_site,
                    )

                    orgnews.append(i.id)
                    news.append(i.news_id)

                OrganizationNews.objects.filter(pk__in=orgnews).delete()
                News.objects.filter(pk__in=news).delete()
        else:
            who = request.profile
            if news_ids:
                users_ban = set([i.autor for i in News.objects.filter(pk__in=news_ids)])

                if 'lock_id' in request.POST:
                    for i in users_ban:
                        obj, created = BannedUsersAndIPs.objects.get_or_create(
                            profile=i,
                            defaults={
                                'profile': i,
                                'who': who,
                            })
                if 'lock_ip' in request.POST:
                    ip_addresses = set(list(Interface.objects.filter(profile__in=users_ban).values_list('ip_address', flat=True)))
                    for i in ip_addresses:
                        obj, created = BannedUsersAndIPs.objects.get_or_create(
                            ip=i,
                            defaults={
                                'ip': i,
                                'who': who,
                            })

        return HttpResponseRedirect(reverse("comments_moderator"))

    banned_users = {'profiles': [], 'ips': []}
    for i in BannedUsersAndIPs.objects.all():
        if i.profile:
            banned_users['profiles'].append(i.profile_id)
        else:
            banned_users['ips'].append(i.ip)

    data = []
    related = ['news', 'news__autor', 'organization', 'organization__domain']

    yalta = OrganizationNews.objects.select_related(*related).filter(news__reader_type__in=reader_type, organization__buildings__city__name__name="Ялта").distinct('pk')
    orsk = OrganizationNews.objects.select_related(*related).filter(news__reader_type__in=reader_type, organization__buildings__city__name__name="Орск").distinct('pk')
    #other = OrganizationNews.objects.select_related(*related).filter(news__reader_type__in=reader_type).exclude(organization__domain__domain="vsetiinter.net")

    profiles = []
    for i in [yalta, orsk]:
        for j in i:
            profiles.append(j.news.autor)
            
    ips = {}
    for i in Interface.objects.filter(profile__in=set(profiles)).values('profile', 'ip_address'):
        if not ips.get(i['profile']):
            ips[i['profile']] = []
        if i['ip_address'] not in ips[i['profile']]:
            ips[i['profile']].append(i['ip_address'])

    
    for obj in [(yalta, 'yalta'), (orsk, 'orsk')]:
        for i in obj[0]:

            #if obj[1] in ('yalta', 'orsk'):
            url = 'http://%s.vsetiinter.net/%s' % (obj[1], i.organization.uni_slug)
            #else:
            #    url = '%s/%s' % (i.organization.domain, i.organization.uni_slug)
            

            if i.news.autor_id in banned_users['profiles']:
                banned = True
            else:
                user_ips = ips.get(i.news.autor_id, [])
                banned_ips = [uip for uip in user_ips if uip in banned_users['ips']]
                banned = True if len(user_ips) and len(user_ips) == len(banned_ips) else False
                    
                
            
            data.append({
                'news_title': i.news.title,
                'news_type': i.news.get_reader_type_display,
                'news_time': i.news.dtime,
                'news_id': i.news.id,
                'news_user_id': i.news.autor.user_id, 
                'org_url': url, 
                'org_name': i.organization.name,
                'banned': banned,
            })

    data = sorted(data, key=operator.itemgetter('news_time'), reverse=True)

    return render_to_response('release_parser/admin_comments_moderator.html', {'data': data}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def get_subscriptions_users(request):
    '''
    Список с фильтрами подписавшихся на релиз юзеров
    '''
    def clear_my_sess_param():
        #request.session['subr_emails'] = ''
        request.session['subr_cities'] = ''
        request.session['subr_films'] = ''
        request.session['subr_notified'] = ''
        request.session['date_from'] = ''
        request.session['date_to'] = ''

    subr = SubscriptionRelease.objects.select_related('release', 'release__release', 'profile', 'profile__user')

    films_id = []
    for i in subr:
        film_kid = i.release.film_kid if i.release else i.kid
        films_id.append(film_kid)
    films_id = set(films_id)

    films_names = FilmsName.objects.using('afisha').filter(film_id__id__in=films_id, status=1, type=2)
    films_names_dict = {}
    for i in films_names:
        if not films_names_dict.get(i.film_id_id):
            films_names_dict[i.film_id_id] = i.name

    films = {}
    #emails = []
    user_cities = []
    all_users = []
    notified = []
    for i in subr:
        film_kid = i.release.film_kid if i.release else i.kid

        film_name = films_names_dict.get(film_kid)
        #emails.append(i.profile.user.email)
        user_cities.append(i.profile.person.city_id)
        all_users.append(i.profile)
        notified.append(i.notified)
        if not films.get(film_kid):
            films[film_kid] = {'kid': film_kid, 'name': film_name}

    all_users = len(set(all_users))

    user_cities_dict = {}
    cit = City.objects.filter(pk__in=set(user_cities))
    for i in cit:
        for j in i.name.all():
            if j.status == 1:
                user_cities_dict[i.id] = j.name

    sess_value = ''
    #sel_email = None
    sel_date_from = None
    sel_date_to = None
    date_from = ''
    date_to = ''

    my_filter = {}

    if request.POST:
        clear_my_sess_param()

    #if request.POST.get('subr_emails'):
    #    sess_value = request.POST['subr_emails']
    #    my_filter['profile__user__email'] = sess_value
    #    request.session['subr_emails'] = sess_value
    if request.POST.get('subr_cities'):
        sess_value = int(request.POST['subr_cities'])
        my_filter['profile__person__city__id'] = sess_value
        request.session['subr_cities'] = sess_value
    if request.POST.get('subr_films'):
        sess_value = int(request.POST['subr_films'])
        #my_filter['release__film_kid'] = sess_value
        request.session['subr_films'] = sess_value
    if request.POST.get('subr_notified'):
        sess_value = request.POST['subr_notified']
        my_filter['notified'] = True if request.POST['subr_notified'] == 'True' else False
        request.session['subr_notified'] = sess_value
    if request.POST.get('date_btn'):
        sel_date_from = request.POST['subr_date_from'].split('-') if request.POST['subr_date_from'] else None
        sel_date_to = request.POST['subr_date_to'].split('-') if request.POST['subr_date_to'] else None
        try:
            if sel_date_from:
                date_from = datetime.datetime(int(sel_date_from[2]), int(sel_date_from[1]), int(sel_date_from[0]))
                my_filter['dtime__gte'] = date_from
            if sel_date_to:
                date_to = datetime.datetime(int(sel_date_to[2]), int(sel_date_to[1]), int(sel_date_to[0]), 23, 59, 59)
                my_filter['dtime__lte'] = date_to
        except (IndexError, ValueError): pass
        if date_from:
            request.session['date_from'] = date_from
            date_from = '%s-%s-%s' % ('{0:0=2d}'.format(date_from.day), '{0:0=2d}'.format(date_from.month), date_from.year)
        if date_to:
            request.session['date_to'] = date_to
            date_to = '%s-%s-%s' % ('{0:0=2d}'.format(date_to.day), '{0:0=2d}'.format(date_to.month), date_to.year)

    if not sess_value:
    #    if request.session.get('subr_emails'):
    #        sess_value = request.session['subr_emails']
    #        my_filter['profile__user__email'] = sess_value
        if request.session.get('subr_cities'):
            sess_value = request.session['subr_cities']
            my_filter['profile__person__city__id'] = sess_value
        if request.session.get('subr_films'):
            sess_value = request.session['subr_films']
            #my_filter['release__film_kid'] = sess_value
        if request.session.get('subr_notified'):
            sess_value = request.session['subr_notified']
            my_filter['notified'] = True if request.session['subr_notified'] == 'True' else False
        if request.session.get('date_to') or request.session.get('date_from'):
            if request.session.get('date_to'):
                date_t = request.session['date_to']
                date_to = '%s-%s-%s' % ('{0:0=2d}'.format(date_t.day), '{0:0=2d}'.format(date_t.month), date_t.year)
                my_filter['dtime__lte'] = date_t
            if request.session.get('date_from'):
                date_f = request.session['date_from']
                date_from = '%s-%s-%s' % ('{0:0=2d}'.format(date_f.day), '{0:0=2d}'.format(date_f.month), date_f.year)
                my_filter['dtime__gte'] = date_f

    if my_filter:
        if request.session.get('subr_films'):
            subr = SubscriptionRelease.objects.select_related('release', 'release__release', 'profile', 'profile__user').filter(Q(release__film_kid=sess_value) | Q(kid=sess_value), **my_filter)
        else:
            subr = SubscriptionRelease.objects.select_related('release', 'release__release', 'profile', 'profile__user').filter(**my_filter)

    subr_list = []
    for i in subr:
        film_kid = i.release.film_kid if i.release else i.kid
        film_name = films_names_dict.get(film_kid)
        subr_list.append({'email': i.profile.user.email, 'user_id': i.profile.user_id, 'city': i.profile.person.city_id, 'kid': film_kid, 'name': film_name, 'dtime': i.dtime, 'notified': i.notified})

    #emails = set(emails)
    notified = set(notified)

    if subr_list:
        subr_list = sorted(subr_list, key=operator.itemgetter('email'))
    if films:
        films = sorted(films.values(), key=operator.itemgetter('name'))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, subr_list, 15)

    return render_to_response('release_parser/subscriptions_users.html', {'p': p, 'page': page, 'cities': user_cities_dict, 'films': films, 'notified': notified, 'date_from': date_from, 'date_to': date_to, 'sess_value': sess_value, 'all_users': all_users}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def subscriptions_feeds(request):
    date_from = ''
    date_to = ''
    feed = None
    my_filter = {}

    data = SubscriptionFeeds.objects.select_related('profile').all()
    feeds = {}
    all_users = []
    for i in data:
        feeds[i.type] = {'type': i.type, 'name': i.get_type_display()}
        all_users.append(i.profile)

    all_users = len(set(all_users))

    if request.POST:
        request.session['subscriptions_feeds__date_from'] = ''
        request.session['subscriptions_feeds__date_to'] = ''
        feed = request.POST.get('feed')

    if request.POST.get('date_btn'):
        sel_date_from = request.POST['subr_date_from'].split('-') if request.POST['subr_date_from'] else None
        sel_date_to = request.POST['subr_date_to'].split('-') if request.POST['subr_date_to'] else None
        try:
            if sel_date_from:
                date_from = datetime.datetime(int(sel_date_from[2]), int(sel_date_from[1]), int(sel_date_from[0]))
                my_filter['dtime__gte'] = date_from
            if sel_date_to:
                date_to = datetime.datetime(int(sel_date_to[2]), int(sel_date_to[1]), int(sel_date_to[0]), 23, 59, 59)
                my_filter['dtime__lte'] = date_to
        except (IndexError, ValueError):
            pass
        if date_from:
            request.session['subscriptions_feeds__date_from'] = date_from
            date_from = '%s-%s-%s' % ('{0:0=2d}'.format(date_from.day), '{0:0=2d}'.format(date_from.month), date_from.year)
        if date_to:
            request.session['subscriptions_feeds__date_to'] = date_to
            date_to = '%s-%s-%s' % ('{0:0=2d}'.format(date_to.day), '{0:0=2d}'.format(date_to.month), date_to.year)
    else:
        if request.session.get('subscriptions_feeds__date_to') or request.session.get('subscriptions_feeds__date_from'):
            if request.session.get('subscriptions_feeds__date_to'):
                date_t = request.session['subscriptions_feeds__date_to']
                date_to = '%s-%s-%s' % ('{0:0=2d}'.format(date_t.day), '{0:0=2d}'.format(date_t.month), date_t.year)
                my_filter['dtime__lte'] = date_t
            if request.session.get('subscriptions_feeds__date_from'):
                date_f = request.session['subscriptions_feeds__date_from']
                date_from = '%s-%s-%s' % ('{0:0=2d}'.format(date_f.day), '{0:0=2d}'.format(date_f.month), date_f.year)
                my_filter['dtime__gte'] = date_f

    feeds = sorted(feeds.values())
    if not feed:
        feed = feeds[0]['type']

    my_filter['type'] = feed

    data = SubscriptionFeeds.objects.filter(**my_filter)

    users = [{'user_id': i.profile.user_id, 'dtime': i.dtime} for i in data]

    users = sorted(users, key=operator.itemgetter('dtime'))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, users, 15)

    return render_to_response('release_parser/subscriptions_feeds.html', {'p': p, 'page': page, 'feeds': feeds, 'feed': feed, 'users': users, 'all_users': all_users, 'date_from': date_from, 'date_to': date_to}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def kinometro_films_pages_log(request):
    '''
    Лог парсера релизов кинометро
    '''
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    releases = Releases.objects.all().order_by('id')
    p, page = pagi(page, releases, 17)
    return render_to_response('release_parser/kinometro_films_log.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def rutracker_topics(request):
    source = ImportSources.objects.get(url='http://rutracker.org/')

    films = SourceFilms.objects.filter(source_obj=source)

    films_kids = set([i.kid for i in films])

    names = FilmsName.objects.using('afisha').filter(film_id__id__in=films_kids, status=1, type=2)
    names_dict = {}
    for i in names:
        names_dict[i.film_id_id] = i.name

    films_list = []
    for i in films:
        name = names_dict.get(i.kid)
        dtime = None
        if i.text:
            d, t = i.text.split()
            year, month, day = d.split('-')
            hour, minute, sec = t.split(':')
            dtime = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(sec))
        films_list.append({'source': i, 'kinoafisha': name, 'dtime': dtime})

    films_list = sorted(films_list, key=operator.itemgetter('dtime'), reverse=True)

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, films_list, 17)
    return render_to_response('release_parser/rutracker_topics.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def persons_parental_names(request):
    ids = list(RelationFP.objects.filter(action__name='режиссер').values_list('person', flat=True))

    names = list(NamePerson.objects.filter(person__id__in=ids).exclude(status=2).values('id', 'status', 'language', 'name', 'person__id', 'person__iid', 'person__kid'))

    names_dict = {}
    for i in names:
        if not names_dict.get(i['person__id']):
            if i['person__iid']:
                person_url = 'http://www.imdb.com/name/nm%s/' % i['person__iid']
            else:
                person_url = 'http://www.kinoafisha.ru/index.php3?id5=%s&status=5' % i['person__kid']

            names_dict[i['person__id']] = {
                'ru': '',
                'en': '',
                'parent': '',
                'pid': i['person__id'],
                'ru_id': '',
                'parent_id': '',
                'person_url': person_url,
            }

        if i['status'] == 1:
            if i['language'] == 1:
                names_dict[i['person__id']]['ru'] = i['name']
                names_dict[i['person__id']]['ru_id'] = i['id']
            elif i['language'] == 2:
                names_dict[i['person__id']]['en'] = i['name']
        elif i['status'] == 3:
            names_dict[i['person__id']]['parent'] = i['name']
            names_dict[i['person__id']]['parent_id'] = i['id']

    names_dict = sorted(names_dict.values(), key=operator.itemgetter('ru'))

    return render_to_response('release_parser/persons_parental_names.html', {'data': names_dict}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def edit_reviews_list_without_rate(request):
    kids = set(list(FilmsVotes.objects.filter(rate_1=0).values_list('kid', flat=True)))

    films = FilmsName.objects.using('afisha').only("film_id", "name").filter(film_id__id__in=kids, type__in=(1, 2), status=1)

    films_dict = {}
    for i in films:
        if not films_dict.get(i.film_id_id):
            films_dict[i.film_id_id] = {'name_en': None, 'name_ru': None, 'id': i.film_id_id, 'year': i.film_id.year}
        if i.type == 2:
            films_dict[i.film_id_id]['name_ru'] = i.name.strip()

    films = sorted(films_dict.values(), key=operator.itemgetter('year'), reverse=True)

    count = (len(films))

    return render_to_response('release_parser/reviews_list_without_rate.html', {'data': films, 'count': count}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_actions(request):
    return render_to_response('release_parser/admin_actions.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_person_actions(request):
    log = ActionsLog.objects.select_related('profile').filter(object=2).order_by('-dtime')

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, log, 15)

    persons_ids = set([i.object_id for i in p.object_list])
    persons = Person.objects.filter(pk__in=persons_ids)

    persons_dict = {}
    kids = []
    for i in persons:
        persons_dict[i.id] = i.kid
        kids.append(i.kid)

    names = list(NamePerson.objects.filter(person__kid__in=kids, language__id=1, status=1).values('name', 'person__id'))
    names_dict = {}
    for i in names:
        names_dict[i['person__id']] = i['name']

    logs = []
    for i in p.object_list:
        kid = persons_dict.get(i.object_id)
        name = names_dict.get(i.object_id)
        logs.append({'log': i, 'kid': kid, 'name': name})

    return render_to_response('person/actions.html', {'p': p, 'page': page, 'logs': logs}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_create_user(request):
    return render_to_response('release_parser/admin_create_user.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def language_test(request):
    return render_to_response('release_parser/language_test.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def source_opinions_set_rate(request):
    excl = 0
    if request.POST:
        if 'rate_filter' in request.POST:
            rate_filter = request.POST.get('rate_filter')
            if rate_filter:
                excl = int(rate_filter)

        if 'op_edit' in request.POST:
            op_id = request.POST.get('op_id')
            txt = request.POST.get('note')
            obj = NewsFilms.objects.get(pk=op_id)
            msg = obj.message
            msg.text = txt
            msg.save()
            return HttpResponseRedirect(reverse('source_opinions_set_rate'))

    if excl:
        filmsnews = NewsFilms.objects.select_related('message', 'message__autor').filter(message__visible=True, source_obj__url="http://www.kino.ru/").exclude(rate=None)
    else:
        filmsnews = NewsFilms.objects.select_related('message', 'message__autor').filter(message__visible=True, rate=None, source_obj__url="http://www.kino.ru/")

    kids = set([i.kid for i in filmsnews])
    films = {}
    for i in FilmsName.objects.using('afisha').filter(film_id__id__in=kids, status=1, type=2):
        films[i.film_id_id] = i.name

    authors = set([i.message.autor for i in filmsnews])
    authors_dict = org_peoples(authors, True)

    opinions_list = []
    for i in filmsnews:

        txt = BeautifulSoup(i.message.text, from_encoding="utf-8").text

        author = authors_dict.get(i.message.autor.user_id)

        nick = 'Аноним'
        if author:
            nick = author['nickname'] if author['nickname'] else author['short_name']

        film_name = films.get(i.kid, '')

        opinions_list.append({
            'date': i.message.dtime,
            'nick': nick,
            'txt': txt,
            'id': i.id,
            'rate': i.rate,
            'rate_1': i.rate_1,
            'rate_2': i.rate_2,
            'rate_3': i.rate_3,
            'kid': i.kid,
            'name': film_name
        })

    opinions_list = sorted(opinions_list, key=operator.itemgetter('date'), reverse=True)

    count = len(opinions_list)

    return render_to_response('release_parser/source_opinions_set_rate.html', {'data': opinions_list, 'count': count, 'excl': str(excl)}, context_instance=RequestContext(request))


@only_superuser
@never_cache 
def admin_afisha_cinemas(request):
    orgs = Organization.objects.filter(kid__gt=0).order_by('name')
    return render_to_response('release_parser/admin_afisha_cinemas.html', {'data': orgs}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_generated_films(request):
    films = Films.objects.filter(generated=True, kid__gt=0).order_by('-generated_dtime')

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, films, 25)

    films_ids = [i.kid for i in p.object_list]

    names = FilmsName.objects.using('afisha').filter(type__in=(1, 2), status=1, film_id__id__in=films_ids).values('type', 'name', 'film_id')

    names_dict = {}
    for i in names:
        if not names_dict.get(i['film_id']):
            names_dict[i['film_id']] = {1: None, 2: None}
        names_dict[i['film_id']][i['type']] = i['name']

    films_list = []
    for i in p.object_list:
        name = names_dict.get(i.kid)
        films_list.append({'kid': i.kid, 'name': name, 'year': i.year, 'dtime': i.generated_dtime})

    films_list = sorted(films_list, key=operator.itemgetter('dtime'), reverse=True)

    return render_to_response('release_parser/admin_generated_films.html', {'data': films_list, 'page': page, 'p': p}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_seo_mainpage(request):
    current_site = request.current_site

    site_file = '%s/%s__mainpage.json' % (settings.SEO_PATH, current_site.domain)

    if request.POST:
        keys = request.POST.get('keys', '').strip()
        descr = request.POST.get('descr', '')
        tags = request.POST.get('tags_cloud_arr', '')

        tags_list = []
        for i in tags.split(';'):
            if i:
                tag_name, tag_size, tag_link = i.split('~')
                tags_list.append({'name': tag_name.strip(), 'size': tag_size, 'link': tag_link})

        data = {
            "keywords": keys,
            "description": descr,
            "tags": tags_list,
        }

        with open(site_file, 'w') as f:
            json.dump(data, f)

        return HttpResponseRedirect(reverse('admin_seo_mainpage'))

    try:
        with open(site_file, 'r') as f:
            data = json.loads(f.read())
    except IOError:
        with open(site_file, 'w') as f:
            data = {
                "keywords": '',
                "description": '',
                "tags": [],
            }
            json.dump(data, f)

    return render_to_response('release_parser/admin_seo_mainpage.html', {'data': data}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_adv_statistics(request):
    data = []

    banners = SiteBanners.objects.select_related('country').filter(deleted=False).order_by('-id')

    count_banners = banners.count()
    spent_sum = 0

    banners_ids = []
    profiles = []

    for i in banners:
        banners_ids.append(i.id)
        if i.user:
            profiles.append(i.user)

    sites = {}
    for i in DjangoSite.objects.filter(sitebanners__pk__in=banners_ids, sitebanners__btype='2').values('sitebanners__pk', 'domain'):
        if not sites.get(i['sitebanners__pk']):
            sites[i['sitebanners__pk']] = []
        sites[i['sitebanners__pk']].append(i['domain'])

    clicks = {'model': SiteBannersClicks, 'data': {}}
    views = {'model': SiteBannersViews, 'data': {}}

    for item in (clicks, views):
        for i in item['model'].objects.select_related('profile', 'banner', 'banner__user').filter(banner__pk__in=banners_ids):
            if not item['data'].get(i.banner_id):
                item['data'][i.banner_id] = {}

            try:
                item_date = i.dtime.date()
            except AttributeError:
                item_date = i.dtime

            if not item['data'][i.banner_id].get(item_date):
                item['data'][i.banner_id][item_date] = []

            if i.profile:
                uid = i.profile.user_id
                profiles.append(i.profile)
            else:
                uid = None

            item['data'][i.banner_id][item_date].append({'profile': uid, 'dtime': i.dtime})

    clicks = clicks['data']
    views = views['data']

    peoples = org_peoples(set(profiles), True)

    for item in (clicks, views):
        for banner, value in item.iteritems():
            for k, v in value.iteritems():
                for i in v:
                    user_obj = peoples.get(i['profile'])
                    if user_obj:
                        i['user'] = user_obj['id']
                        i['name'] = user_obj['name']
                    else:
                        i['user'] = ''
                        i['name'] = u'Не найден'

    countries = {}
    for i in list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name')):
        countries[i['id']] = {'id': i['id'], 'name': i['name'], 'cities': []}

    cities_all = {}
    for i in list(NameCity.objects.filter(status=1, city__country__id__in=countries.keys()).order_by('name').values('id', 'city__id', 'name', 'city__country')):
        countries[i['city__country']]['cities'].append(i)
        cities_all[i['city__id']] = i['name']

    def get_count(data, id):
        count = 0
        xdata = data.get(id, {})
        xdata = collections.OrderedDict(sorted(xdata.items()))
        for k, v in xdata.iteritems():
            count += len(v)
        return count, xdata

    for i in banners:
        author = {'id': '', 'name': None}
        if i.user:
            author = peoples.get(i.user.user_id, {'id': '', 'name': None})

        if not author['id'] and i.date_to:
            author['name'] = 'Старый формат'

        country_name, country_id = (i.country.name, i.country.id) if i.country else (u'ВСЕ', '0')
        city_name, city_id = (u'ВСЕ', '')
        cities_in_country = 0
        if int(country_id):
            cities_in_country = len(countries[country_id]['cities'])
            cities = list(i.cities.all().values_list('pk', flat=True))
            if cities and cities_in_country > len(cities):
                cnames = ''
                for ind, j in enumerate(cities):
                    city_obj = cities_all.get(j, '')
                    if ind < 3:
                        if cnames:
                            cnames += ', '
                        cnames += city_obj
                    if city_id:
                        city_id += ','
                    city_id += str(j)
                city_name = cnames + '...' if cnames and len(cities) > 3 else cnames

        click, clicks_data = get_count(clicks, i.id)
        view, views_data = get_count(views, i.id)

        ctr = (float(click) / float(i.views)) * 100 if click and i.views else 0.0
        ctr = '%2.2f' % ctr

        spent_sum += i.spent

        sites_list = sites.get(i.id, [])

        data.append({
            'author_id': author['id'],
            'author_name': author['name'],
            'country': country_name,
            'city': city_name,
            'clicks': click,
            'clicks_data': clicks_data,
            'obj': i,
            'ctr': ctr,
            'views': view,
            'views_data': views_data,
            'sites': sites_list,
        })

    return render_to_response('release_parser/admin_adv_statistics.html', {'data': data, 'count_banners': count_banners, 'spent_sum': spent_sum}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def online_player(request):
    return render_to_response('release_parser/online_player_test.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def user_nicknames(request):
    export = request.GET.get('export')

    profiles_dict = {}

    for i in Profile.objects.select_related('person').filter(auth_status=True, person__pk__gt=0, kid__gt=0):
        profiles_dict[i.kid] = i

    peoples = org_peoples(profiles_dict.values(), True)

    users = RegisteredUsers.objects.using('afisha').filter(pk__in=profiles_dict.keys())

    html = u'%s<br /><table><th>Киноафиша</th><th>Киноинфо</th>' % users.count()
    for i in users:
        profile = profiles_dict.get(i.id)

        user_data = peoples.get(profile.user_id)

        user_data_nick = user_data.get('nickname')
        user_data_nick = user_data_nick if user_data_nick else None

        style = ''
        if i.nickname != user_data_nick:
            if export:
                profile.user.first_name = i.nickname
                profile.user.save()
                user_data_nick = i.nickname
            else:
                style = 'style="color: red;"'

        html += u'<tr>'
        html += u'<td>%s</td><td><a %s href="http://kinoinfo.ru/user/profile/%s/" target="_blank">%s</a></td>' % (i.nickname, style, profile.user_id, user_data_nick)
        html += u'</tr>'

    if export:
        return HttpResponseRedirect(reverse('user_nicknames'))

    html += u'</table><br /><a href="?export=1">Экспорт никнэймов Киноафиша -> Киноинфо</a>'

    return HttpResponse(html)


@only_superuser
@never_cache
def user_nicknames_doubles(request):
    profiles_dict = {}

    for i in Profile.objects.select_related('person').filter(person__pk__gt=0).exclude(user__first_name=''):
        profiles_dict[i.kid] = i

    peoples = org_peoples(profiles_dict.values(), True)

    doubles = {}
    for i in peoples.values():
        if not doubles.get(i['nickname']):
            doubles[i['nickname']] = 0
        doubles[i['nickname']] += 1

    html = u'%s<br /><table><th>Ник</th><th>Кол-во</th>' % len(doubles.keys())
    for k, v in doubles.iteritems():
        html += u'<tr>'
        html += u'<td>%s</td><td>%s</td>' % (k, v)
        html += u'</tr>'

    html += u'</table>'

    return HttpResponse(html)


@only_superuser
@never_cache
def opinions_rate_converter(request):
    for i in NewsFilms.objects.filter(rate_1=0, rate__gt=0):
        if i.rate == 2:
            i.rate_1 = 1
            i.rate_2 = 1
            i.rate_3 = 1
        elif i.rate == 3:
            i.rate_1 = 2
            i.rate_2 = 2
            i.rate_3 = 2
        elif i.rate == 4:
            i.rate_1 = 2
            i.rate_2 = 2
            i.rate_3 = 3
        elif i.rate == 5:
            i.rate_1 = 3
            i.rate_2 = 3
            i.rate_3 = 3
        i.save()

    return HttpResponse(str('OK'))


@only_superuser
@never_cache
def image_optimizer(request):
    return render_to_response('release_parser/image_optimizer.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def create_system_user(request):
    try:
        user = User.objects.get(last_name='SYSTEM')
    except User.DoesNotExist:
        user = get_user()
        user.last_name = 'SYSTEM'
        user.save()
    return HttpResponse(str('OK'))


@only_superuser
@never_cache
def get_table_size(request):
    from django.db import connection

    cursor = connection.cursor()

    txt = ''
    for table in ('base_sourceschedules', 'base_sessionsafisharelations', 'django_session'):
        query = '''SELECT table_name "{0}", Round(Sum(data_length + index_length) / 1024 / 1024, 1)
        FROM information_schema.tables WHERE table_schema="{1}" AND table_name="{2}";'''
        query = query.format(table, settings.DATABASES['default']['NAME'], table)
        cursor.execute(query)
        txt += u'Таблица %s = %s MB<br />' % cursor.fetchone()

    return HttpResponse(str(txt.encode('utf-8')))
