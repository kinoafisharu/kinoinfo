# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from release_parser.views import *
from release_parser.kinobit_cmc import *
from release_parser.okinoua import *
from release_parser.kinohod import *
from release_parser.nowru import *
from release_parser.rambler import *
from release_parser.megamag import *
from release_parser.planeta_kino import *
from release_parser.kinoteatrua import *
from release_parser.etaj import *
from release_parser.surkino import *
from release_parser.kinobklass import *
from release_parser.cinemaarthall import *
from release_parser.zlat74ru import *
from release_parser.kinosaturn import *
from release_parser.zapad24ru import *
from release_parser.kinobusiness import *
from release_parser.currencyrate import *
from release_parser.michurinskfilm import *
from release_parser.ktmir_and_ktrussia import *
from release_parser.luxor_chuvashia import *
from release_parser.arsenalclub import *
from release_parser.illuzion import *
from release_parser.luxor import *
from release_parser.vkinocomua import *
from release_parser.cinema5 import *
from release_parser.kinomonitor import *
from release_parser.kinometro import *
#from organizations.parser import get_orsk_organizations #get_0654_organizations, get_bigyalta_organizations
from movie_online.parser import *
from movie_online.IR import integral_rate
from release_parser.rutracker import *
from release_parser.iviru import *
from release_parser.imdb import *
from release_parser.rottentomatoes import *
from release_parser.yovideo import *
from release_parser.top250 import *
from release_parser.clickatell import *
from release_parser.tvzavr import *
from release_parser.oreanda_and_spartak import *
from release_parser.kino_ru import *
from release_parser.liberty4ever import *
from release_parser.cinemaplex import *
from release_parser.cinemate_cc import *
from release_parser.premierzal import *
from release_parser.mailru import *
from release_parser.kinomagnat import *
from release_parser.kinoboomer import *
#from release_parser.kinozal_tv import *

from api.cron_func import *
from user_registration.views import user_deposit
from release_parser.memoirs import get_all_story

urlpatterns = patterns('',
    # график кинорелизов для посетителей
    url(r'^$', 'release_parser.views.film_list_form_ajax', name='releases_ajax'),
    url(r'^(?P<id>\d+)/$', 'release_parser.views.film_list_form_ajax', name='releases_ajax'),

    # скачивание дампов
    url(r'^download/(?P<method>\w+)/$', 'release_parser.views.parser_download', name='parser_download'),

    # список ненайденных фильмов с фильтрами (релизы)
    url(r'^film/list_form/$', 'release_parser.views.film_list_form', name='film_list_form'),
    
    # добавление дистрибьюторов
    url(r'^distributor/add/$', 'release_parser.views.distributor_add', name='distributor_add'),
    # редактирование дистрибьюторов
    url(r'^distributor/edit/(?P<id>\d+)/$', 'release_parser.views.distributor_edit', name='distributor_edit'),
    # удаление дистрибьюторов
    url(r'^distributor/delete/(?P<id>\d+)/$', 'release_parser.views.distributor_delete', name='distributor_delete'),
    # удаление связи с именем дистрибьюторов
    url(r'^distributor/del_name/(?P<org_id>\d+)/(?P<name_id>\d+)/$', 'release_parser.views.distributor_delete_name', name='distributor_delete_name'),

    # список названий дистрибьюторов
    url(r'^org_name/list/$', 'release_parser.views.org_name_list', name='org_name_list'),
    # добавление названий дистрибьюторов
    url(r'^org_name/add/$', 'release_parser.views.add_org_name', name='add_org_name'),
    # редактирование названий дистрибьюторов
    url(r'^org_name/edit/(?P<id>\d+)/$', 'release_parser.views.edit_org_name', name='edit_org_name'),
    # удаление названий дистрибьюторов
    url(r'^org_name/delete/(?P<id>\d+)/$', 'release_parser.views.delete_org_name', name='delete_org_name'),

    # список стран
    url(r'^country/list/$', 'release_parser.views.country_list', name='country_list'),
    # список городов
    url(r'^city/list/$', 'release_parser.views.city_list_in_db', name='city_list_in_db'),
    
    url(r'^okinoua_schedules_list/$', 'release_parser.okinoua.okinoua_schedules_list', name='okinoua_schedules_list'),
    url(r'^get_okinoua_distributors/$', 'release_parser.okinoua.get_okinoua_distributors', name='get_okinoua_distributors'),
    
    # лог экспорта CMC на киноафишу
    url(r'^kinobit_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'cmc_export_to_kinoafisha_log'}, name='kinobit_schedules_export_to_kinoafisha_log'),
    # лог экспорта Kinohod на киноафишу
    url(r'^kinohod_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinohod_export_to_kinoafisha_log'}, name='kinohod_schedules_export_to_kinoafisha_log'),
    # лог экспорта Megamag на киноафишу
    url(r'^megamag_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'megamag_export_to_kinoafisha_log'}, name='megamag_schedules_export_to_kinoafisha_log'),
    # лог экспорта Rambler на киноафишу
    url(r'^rambler_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'rambler_export_to_kinoafisha_log'}, name='rambler_schedules_export_to_kinoafisha_log'),
    # лог экспорта Планета-Кино на киноафишу
    url(r'^planeta_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'planeta_export_to_kinoafisha_log'}, name='planeta_schedules_export_to_kinoafisha_log'),
    # лог экспорта Кинотеатр Этаж на киноафишу
    url(r'^etaj_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'etaj_export_to_kinoafisha_log'}, name='etaj_schedules_export_to_kinoafisha_log'),
    # лог экспорта Кинотеатр Б-Класс на киноафишу
    url(r'^kinobklass_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinobklass_export_to_kinoafisha_log'}, name='kinobklass_schedules_export_to_kinoafisha_log'),
    # лог экспорта Афиша в Сургуте на киноафишу
    url(r'^surkino_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'surkino_export_to_kinoafisha_log'}, name='surkino_schedules_export_to_kinoafisha_log'),
    # лог экспорта Синема-АРТ-Холл на киноафишу
    url(r'^cinemaarthall_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'cinemaarthall_export_to_kinoafisha_log'}, name='cinemaarthall_schedules_export_to_kinoafisha_log'),
    # лог экспорта Златоуст Космос на киноафишу
    url(r'^zlat74ru_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'zlat74ru_export_to_kinoafisha_log'}, name='zlat74ru_schedules_export_to_kinoafisha_log'),
    # лог экспорта Александров Сатурн на киноафишу
    url(r'^kinosaturn_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinosaturn_export_to_kinoafisha_log'}, name='kinosaturn_schedules_export_to_kinoafisha_log'),
    # лог экспорта Запад 24 на киноафишу
    url(r'^zapad24ru_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'zapad24ru_export_to_kinoafisha_log'}, name='zapad24ru_schedules_export_to_kinoafisha_log'),
    # лог экспорта Мичуринск Октябрь на киноафишу
    url(r'^michurinskfilm_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'michurinskfilm_export_to_kinoafisha_log'}, name='michurinskfilm_schedules_export_to_kinoafisha_log'),
    # лог экспорта Kino-teatr.ua на киноафишу
    url(r'^kinoteatrua_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinoteatrua_export_to_kinoafisha_log'}, name='kinoteatrua_schedules_export_to_kinoafisha_log'),
    # лог экспорта ktmir.ru на киноафишу
    url(r'^ktmir_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'ktmir_export_to_kinoafisha_log'}, name='ktmir_schedules_export_to_kinoafisha_log'),
    # лог экспорта ktmir.ru на киноафишу
    url(r'^ktrussia_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'ktrussia_export_to_kinoafisha_log'}, name='ktrussia_schedules_export_to_kinoafisha_log'),
    # лог экспорта luxor.chuvashia.com на киноафишу
    url(r'^luxor_chuvashia_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'luxor_chuvashia_export_to_kinoafisha_log'}, name='luxor_chuvashia_schedules_export_to_kinoafisha_log'),
    # лог экспорта arsenal-club.com на киноафишу
    url(r'^arsenalclub_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'arsenalclub_export_to_kinoafisha_log'}, name='arsenalclub_schedules_export_to_kinoafisha_log'),
    # лог экспорта www.illuzion.ru на киноафишу
    url(r'^illuzion_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'illuzion_export_to_kinoafisha_log'}, name='illuzion_schedules_export_to_kinoafisha_log'),
    # лог экспорта vkino.com.ua на киноафишу
    url(r'^vkinocomua_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'vkinocomua_export_to_kinoafisha_log'}, name='vkinocomua_schedules_export_to_kinoafisha_log'),
    # лог экспорта luxor.ru на киноафишу
    url(r'^luxor_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'luxor_export_to_kinoafisha_log'}, name='luxor_schedules_export_to_kinoafisha_log'),
    # лог экспорта cinema5.ru на киноафишу
    url(r'^cinema5_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'cinema5_export_to_kinoafisha_log'}, name='cinema5_schedules_export_to_kinoafisha_log'),
    # лог экспорта kinomonitor.ru на киноафишу
    url(r'^kinomonitor_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinomonitor_export_to_kinoafisha_log'}, name='kinomonitor_schedules_export_to_kinoafisha_log'),
    # лог экспорта Ореанда и Спартак на киноафишу
    url(r'^yalta_oreanda_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'yalta_oreanda_export_to_kinoafisha_log'}, name='yalta_oreanda_export_to_kinoafisha_log'),
    url(r'^yalta_spartak_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'yalta_spartak_export_to_kinoafisha_log'}, name='yalta_spartak_export_to_kinoafisha_log'),
    # лог экспорта kinomonitor.ru на киноафишу
    url(r'^premierzal_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'premierzal_export_to_kinoafisha_log'}, name='premierzal_schedules_export_to_kinoafisha_log'),
    # лог экспорта kinomagnat на киноафишу
    url(r'^kinomagnat_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinomagnat_export_to_kinoafisha_log'}, name='kinomagnat_schedules_export_to_kinoafisha_log'),
    # лог экспорта kinoboomer на киноафишу
    url(r'^kinoboomer_schedules_export_to_kinoafisha_log/$', 'release_parser.schedules.schedules_export_to_kinoafisha_log', {'dump': 'kinoboomer_export_to_kinoafisha_log'}, name='kinoboomer_schedules_export_to_kinoafisha_log'),


    # Экспорт хронометраж и копии в Киноафишу
    url(r'^runtime_copy_to_kinoafisha/$', 'release_parser.views.runtime_copy_to_kinoafisha', name='runtime_copy_to_kinoafisha'),
    

    # дубли на киноафише
    url(r'^equal_cmc_kinoafisha/$', 'release_parser.schedules.equal_cmc_kinoafisha', name='equal_cmc_kinoafisha'),    

    # Обработка ненайденных фильмов с фильтрами !!! удалить
    url(r'^film/cmc/list_form/$', 'release_parser.schedules.cmc_film_list_form', name='cmc_film_list_form'),
    
    # Обновление дат релизов на Киноафише
    url(r'^kinoafisha_release_update/$', 'release_parser.views.kinoafisha_release_update', name='kinoafisha_release_update'),
    url(r'^kinoafisha_cinemaplex_release_update/$', 'release_parser.views.kinoafisha_cinemaplex_release_update', name='kinoafisha_cinemaplex_release_update'),

    # Список идентифицированных фильмов от now.ru
    url(r'^nowru_test_show/$', 'release_parser.nowru.nowru_test_show', name='nowru_test_show'),

    url(r'^kinobusiness_export_to_kinoafisha/(?P<country_name>\w+)/$', 'release_parser.kinobusiness.kinobusiness_export_to_kinoafisha', name='kinobusiness_export_to_kinoafisha'),

    # ЗАПУСК МЕТОДОВ CRON ВРУЧНУЮ
    # парсинг kinometro.ru
    #url(r'^cron/kinometro_ru/$', 'release_parser.views.create', {'method': kinometro_ru}, name='kinometro_ru_parser'),
    # парсинг film.ru
    #url(r'^cron/film_ru/$', 'release_parser.views.create', {'method': film_ru}, name='film_ru_parser'),
    # Рассылка уедомлений вручную
    url(r'^cron/mass_email_sender/$', 'release_parser.views.create', {'method': mass_email_sender}, name='mass_email_sender'),
    # Парсер городов киноход вручную
    url(r'^cron/get_kinohod_cities/$', 'release_parser.views.create', {'method': get_kinohod_cities}, name='get_kinohod_cities'),
    # Парсер кинотеатров киноход вручную
    url(r'^cron/get_kinohod_cinemas/$', 'release_parser.views.create', {'method': get_kinohod_cinemas}, name='get_kinohod_cinemas'),
    # Парсер фильмов киноход вручную
    url(r'^cron/get_kinohod_films/$', 'release_parser.views.create', {'method': get_kinohod_films}, name='get_kinohod_films'),
    # Парсер сеансов киноход вручную
    url(r'^cron/get_kinohod_schedules/$', 'release_parser.views.create', {'method': get_kinohod_schedules}, name='get_kinohod_schedules'),
    # Получение ссылок от now.ru
    url(r'^cron/get_nowru_links/$', 'release_parser.views.create', {'method': get_nowru_links}, name='get_nowru_links'),
    # Идентификация фильмов от now.ru
    url(r'^cron/nowru_ident/$', 'release_parser.views.create', {'method': nowru_ident}, name='nowru_ident'),
    # Получение индексного файла rambler
    url(r'^cron/get_rambler_indexfile/$', 'release_parser.views.create', {'method': get_rambler_indexfile}, name='get_rambler_indexfile'),
    # Парсер городов rambler
    url(r'^cron/get_rambler_cities/$', 'release_parser.views.create', {'method': get_rambler_cities}, name='get_rambler_cities'),
    # Парсер кинотеатров rambler
    url(r'^cron/get_rambler_cinemas/$', 'release_parser.views.create', {'method': get_rambler_cinemas}, name='get_rambler_cinemas'),
    # Парсер фильмов rambler
    url(r'^cron/get_rambler_films/$', 'release_parser.views.create', {'method': get_rambler_films}, name='get_rambler_films'),
    # Парсер сеансов rambler
    url(r'^cron/get_rambler_schedules/$', 'release_parser.views.create', {'method': get_rambler_schedules}, name='get_rambler_schedules'),
    # Получить ссылки на релизы okino.ua
    url(r'^cron/get_okinoua_links/$', 'release_parser.views.create', {'method': get_okinoua_links}, name='get_okinoua_links'),
    # Получить города с okino.ua
    url(r'^cron/get_okinoua_cities/$', 'release_parser.views.create', {'method': get_okinoua_cities}, name='get_okinoua_cities'),
    # Получить укр.релизы от okino.ua
    url(r'^cron/get_okinoua_releases/$', 'release_parser.views.create', {'method': get_okinoua_releases}, name='get_okinoua_releases'),
    # Получить укр.кинотеатры от okino.ua
    url(r'^cron/get_okinoua_cinemas/$', 'release_parser.views.create', {'method': get_okinoua_cinemas}, name='get_okinoua_cinemas'),
    # Получить укр.фильмы от okino.ua
    url(r'^cron/get_okinoua_films/$', 'release_parser.views.create', {'method': get_okinoua_films}, name='get_okinoua_films'),
    # Получить укр.сеансы от okino.ua
    url(r'^cron/get_okinoua_schedules/$', 'release_parser.views.create', {'method': get_okinoua_schedules}, name='get_okinoua_schedules'),
    # Идентификация фильмов от распиши.рф для метода API - Релизы Украины
    url(r'^cron/raspishi_relations/$', 'release_parser.views.create', {'method': raspishi_relations}, name='raspishi_relations'),
    # Парсер релизов кинометро
    url(r'^cron/kinometro_films_pages/$', 'release_parser.views.create', {'method': kinometro_films_pages}, name='kinometro_films_pages'),
    # Парсер megamag.by
    url(r'^cron/get_megamag/$', 'release_parser.views.create', {'method': get_megamag}, name='get_megamag'),
    # Парсер городов и кинотеатров planeta-kino
    url(r'^cron/get_planeta_cities_cinemas/$', 'release_parser.views.create', {'method': get_planeta_cities_cinemas}, name='get_planeta_cities_cinemas'),
    # Парсер фильмов planeta-kino
    url(r'^cron/get_planeta_films/$', 'release_parser.views.create', {'method': get_planeta_films}, name='get_planeta_films'),
    # Парсер сеансов planeta-kino
    url(r'^cron/get_planeta_schedules/$', 'release_parser.views.create', {'method': get_planeta_schedules}, name='get_planeta_schedules'),
    # СМС/Kinobit
    url(r'^cron/get_kinobit_dump/$', 'release_parser.views.create', {'method': get_kinobit_dump}, name='get_kinobit_dump'),
    url(r'^cron/get_kinobit_cities/$', 'release_parser.views.create', {'method': get_kinobit_cities}, name='get_kinobit_cities'),
    url(r'^cron/get_kinobit_cinemas/$', 'release_parser.views.create', {'method': get_kinobit_cinemas}, name='get_kinobit_cinemas'),
    url(r'^cron/get_kinobit_films/$', 'release_parser.views.create', {'method': get_kinobit_films}, name='get_kinobit_films'),
    url(r'^cron/get_kinobit_schedules/$', 'release_parser.views.create', {'method': get_kinobit_schedules}, name='get_kinobit_schedules'),
    # Kino-tear.ua
    url(r'^cron/get_kinoteatrua_films_and_persons/$', 'release_parser.views.create', {'method': get_kinoteatrua_films_and_persons}, name='get_kinoteatrua_films_and_persons'),
    url(r'^cron/get_kinoteatrua_posters/$', 'release_parser.views.create', {'method': get_kinoteatrua_posters}, name='get_kinoteatrua_posters'),
    url(r'^cron/get_kinoteatrua_schedules/$', 'release_parser.views.create', {'method': get_kinoteatrua_schedules}, name='get_kinoteatrua_schedules'),
    url(r'^cron/get_kinoteatrua_releases/$', 'release_parser.views.create', {'method': get_kinoteatrua_releases}, name='get_kinoteatrua_releases'),
    # etaj.mega74.ru
    url(r'^cron/get_etaj_schedules/$', 'release_parser.views.create', {'method': get_etaj_schedules}, name='get_etaj_schedules'),
    # surkino.ru
    url(r'^cron/get_surkino_cinemas/$', 'release_parser.views.create', {'method': get_surkino_cinemas}, name='get_surkino_cinemas'),
    url(r'^cron/get_surkino_schedules/$', 'release_parser.views.create', {'method': get_surkino_schedules}, name='get_surkino_schedules'),
    # kino-bklass.ru
    url(r'^cron/get_kinobklass_schedules/$', 'release_parser.views.create', {'method': get_kinobklass_schedules}, name='get_kinobklass_schedules'),
    # cinemaarthall.ru
    url(r'^cron/get_cinemaarthall_schedules/$', 'release_parser.views.create', {'method': get_cinemaarthall_schedules}, name='get_cinemaarthall_schedules'),
    # идентификация фильмов кинометро
    url(r'^cron/film_kinometro_ident/$', 'release_parser.views.create', {'method': film_kinometro_ident}, name='film_kinometro_ident'),
    # www.zlat74.ru
    url(r'^cron/get_zlat74ru_schedules/$', 'release_parser.views.create', {'method': get_zlat74ru_schedules}, name='get_zlat74ru_schedules'),
    # www.kinosaturn.ru
    url(r'^cron/get_kinosaturn_schedules/$', 'release_parser.views.create', {'method': get_kinosaturn_schedules}, name='get_kinosaturn_schedules'),
    # zapad24.ru
    url(r'^cron/get_zapad24ru/$', 'release_parser.views.create', {'method': get_zapad24ru}, name='get_zapad24ru'),
    # www.kinobusiness.com
    #url(r'^cron/get_kinobusiness/$', 'release_parser.views.create', {'method': get_kinobusiness}, name='get_kinobusiness'),
    url(r'^cron/get_kinobusiness_ru/$', 'release_parser.kinobusiness.get_kinobusiness_russia', name='get_kinobusiness_russia'),
    url(r'^cron/get_kinobusiness_usa/$', 'release_parser.kinobusiness.get_kinobusiness_usa', name='get_kinobusiness_usa'),
    url(r'^cron/temp_kinobusiness_upd/$', 'release_parser.views.create', {'method': temp_kinobusiness_upd}, name='temp_kinobusiness_upd'),
    # cbrf.magazinfo.ru, www.finanz.ru
    url(r'^cron/get_currency_rate/$', 'release_parser.views.create', {'method': get_currency_rate}, name='get_currency_rate'),
    # www.michurinsk-film.ru
    url(r'^cron/get_michurinskfilm_schedules/$', 'release_parser.views.create', {'method': get_michurinskfilm_schedules}, name='get_michurinskfilm_schedules'),
    # ktmir.ru и kt-russia.ru
    url(r'^cron/get_ktmir_and_ktrussia_schedules/$', 'release_parser.views.create', {'method': get_ktmir_and_ktrussia_schedules}, name='get_ktmir_and_ktrussia_schedules'),
    # luxor.chuvashia.com
    url(r'^cron/get_luxor_chuvashia_schedules/$', 'release_parser.views.create', {'method': get_luxor_chuvashia_schedules}, name='get_luxor_chuvashia_schedules'),
    # arsenal-club.com
    url(r'^cron/get_arsenalclub_schedules/$', 'release_parser.views.create', {'method': get_arsenalclub_schedules}, name='get_arsenalclub_schedules'),
    # www.illuzion.ru
    url(r'^cron/get_illuzion_schedules/$', 'release_parser.views.create', {'method': get_illuzion_schedules}, name='get_illuzion_schedules'),
    # luxor
    url(r'^cron/get_luxor_cinemas/$', 'release_parser.views.create', {'method': get_luxor_cinemas}, name='get_luxor_cinemas'),
    url(r'^cron/get_luxor_films/$', 'release_parser.views.create', {'method': get_luxor_films}, name='get_luxor_films'),
    url(r'^cron/get_luxor_schedules/$', 'release_parser.views.create', {'method': get_luxor_schedules}, name='get_luxor_schedules'),
    # vkino.com.ua
    url(r'^cron/get_vkinocomua_cities_and_cinemas/$', 'release_parser.views.create', {'method': get_vkinocomua_cities_and_cinemas}, name='get_vkinocomua_cities_and_cinemas'),
    url(r'^cron/get_vkinocomua_films_and_schedules/$', 'release_parser.views.create', {'method': get_vkinocomua_films_and_schedules}, name='get_vkinocomua_films_and_schedules'),
    # cinema5.ru
    url(r'^cron/get_cinema5_schedules/$', 'release_parser.views.create', {'method': get_cinema5_schedules}, name='get_cinema5_schedules'),
    # kinomonitor.ru
    url(r'^cron/get_kinomonitor_cities_and_cinemas/$', 'release_parser.views.create', {'method': get_kinomonitor_cities_and_cinemas}, name='get_kinomonitor_cities_and_cinemas'),
    url(r'^cron/get_kinomonitor_films_and_schedules/$', 'release_parser.views.create', {'method': get_kinomonitor_films_and_schedules}, name='get_kinomonitor_films_and_schedules'),
    # rutracker.org
    url(r'^cron/get_rutracker_topics/$', 'release_parser.views.create', {'method': get_rutracker_topics}, name='get_rutracker_topics'),
    url(r'^cron/get_rutracker_topics_closed/$', 'release_parser.views.create', {'method': get_rutracker_topics_closed}, name='get_rutracker_topics_closed'),
    # ivi.ru
    url(r'^cron/get_ivi_file/$', 'release_parser.views.create', {'method': get_ivi_file}, name='get_ivi_file'),
    url(r'^cron/ivi_ident/$', 'release_parser.views.create', {'method': ivi_ident}, name='ivi_ident'),
    # imdb.com
    url(r'^cron/get_imdb_film_list/$', 'release_parser.views.create', {'method': get_imdb_film_list}, name='get_imdb_film_list'),
    url(r'^cron/get_imdb_film/$', 'release_parser.views.create', {'method': get_imdb_film}, name='get_imdb_film'),
    url(r'^cron/imdb_film_ident/$', 'release_parser.views.create', {'method': imdb_film_ident}, name='imdb_film_ident'),
    url(r'^imdb_film_show/$', 'release_parser.imdb.imdb_film_show', name='imdb_film_show'),
    # rottentomatoes.com
    url(r'^cron/get_rottentomatoes_films/$', 'release_parser.views.create', {'method': get_rottentomatoes_films}, name='get_rottentomatoes_films'),
    url(r'^rottentomatoes_demo/$', 'release_parser.rottentomatoes.rottentomatoes_demo', name='rottentomatoes_demo'),
    # www.yo-video.net
    url(r'^cron/get_yovideo/$', 'release_parser.views.create', {'method': get_yovideo}, name='get_yovideo'),
    # top250.info
    url(r'^cron/get_top250/$', 'release_parser.views.create', {'method': get_top250}, name='get_top250'),
    url(r'^cron/get_top250_awards/$', 'release_parser.views.create', {'method': get_top250_awards}, name='get_top250_awards'),
    # tvzavr.ru
    url(r'^cron/get_tvzavr_dump/$', 'release_parser.views.create', {'method': get_tvzavr_dump}, name='get_tvzavr_dump'),
    url(r'^cron/tvzavr_ident/$', 'release_parser.views.create', {'method': tvzavr_ident}, name='tvzavr_ident'),
    # oreanda_and_spartak
    url(r'^cron/get_oreanda_and_spartak/$', 'release_parser.views.create', {'method': get_oreanda_and_spartak}, name='get_oreanda_and_spartak'),
    # kino.ru
    url(r'^cron/get_kino_ru/$', 'release_parser.views.create', {'method': get_kino_ru}, name='get_kino_ru'),
    # liberty4ever
    url(r'^cron/get_liberty4ever_cat/$', 'release_parser.views.create', {'method': get_liberty4ever_cat}, name='get_liberty4ever_cat'),
    url(r'^cron/get_liberty4ever_artist/$', 'release_parser.views.create', {'method': get_liberty4ever_artist}, name='get_liberty4ever_artist'),
    url(r'^cron/get_liberty4ever_track/$', 'release_parser.views.create', {'method': get_liberty4ever_track}, name='get_liberty4ever_track'),
    # cinemaplex
    url(r'^cron/get_cinemaplex/$', 'release_parser.views.create', {'method': get_cinemaplex_releases}, name='get_cinemaplex_releases'),
    # cinemate.cc
    url(r'^cron/cinemate_cc_soon/$', 'release_parser.views.create', {'method': cinemate_cc_soon}, name='cinemate_cc_soon'),
    url(r'^cron/cinemate_cc_get_links/$', 'release_parser.views.create', {'method': cinemate_cc_get_links}, name='cinemate_cc_get_links'),
    # www.premierzal.ru
    url(r'^cron/get_premierzal_cities/$', 'release_parser.views.create', {'method': get_premierzal_cities}, name='get_premierzal_cities'),
    url(r'^cron/get_premierzal_cinemas/$', 'release_parser.views.create', {'method': get_premierzal_cinemas}, name='get_premierzal_cinemas'),
    url(r'^cron/get_premierzal_schedules/$', 'release_parser.views.create', {'method': get_premierzal_schedules}, name='get_premierzal_schedules'),
    # mail.ru
    url(r'^cron/get_mailru_soon/$', 'release_parser.views.create', {'method': get_mailru_soon}, name='get_mailru_soon'),
    url(r'^cron/get_mailru_test/$', 'release_parser.mailru.get_mailru_test', name='get_mailru_test'),
    # kinomagnat
    url(r'^cron/get_kinomagnat_schedules/$', 'release_parser.views.create', {'method': get_kinomagnat_schedules}, name='get_kinomagnat_schedules'),
    # kinoboomer
    url(r'^cron/get_kinoboomer_schedules/$', 'release_parser.views.create', {'method': get_kinoboomer_schedules}, name='get_kinoboomer_schedules'),

    # kinozal.tv Трекер
    #url(r'^cron/get_kinozal_tv/$', 'release_parser.views.create', {'method': get_kinozal_tv}, name='get_kinozal_tv'),



    # ИМПОРТ ИЗ STORY
    url(r'^cron/get_all_story/$', 'release_parser.views.create', {'method': get_all_story}, name='get_all_story'),
    
    # ИМПОРТ ИЗ КИНОАФИШИ через cron
    # импорт стран из киноафиши
    url(r'^cron/kinoafisha_country_import/$', 'release_parser.views.create', {'method': kinoafisha_country_import}, name='kinoafisha_country_import'),
    # импорт городов из киноафиши
    url(r'^cron/kinoafisha_city_import/$', 'release_parser.views.create', {'method': kinoafisha_city_import}, name='kinoafisha_city_import'),
    # импорт метро из киноафиши
    url(r'^cron/kinoafisha_metro_import/$', 'release_parser.views.create', {'method': kinoafisha_metro_import}, name='kinoafisha_metro_import'),
    # импорт сети кинотеатров из киноафиши
    url(r'^cron/kinoafisha_cinemacircuit_import/$', 'release_parser.views.create', {'method': kinoafisha_cinemacircuit_import}, name='kinoafisha_cinemacircuit_import'),
    # импорт основных дистрибьюторов из киноафиши
    url(r'^cron/kinoafisha_distributor_import/$', 'release_parser.views.create', {'method': kinoafisha_distributor_import}, name='kinoafisha_distributor_import'),
    # импорт кинотеатров из киноафиши
    url(r'^cron/kinoafisha_cinema_import/$', 'release_parser.views.create', {'method': kinoafisha_cinema_import}, name='kinoafisha_cinema_import'),
    # импорт кинотеатров2 из киноафиши
    url(r'^cron/kinoafisha_cinema2_import/$', 'release_parser.views.create', {'method': kinoafisha_cinema2_import}, name='kinoafisha_cinema2_import'),
    # импорт оценок для кинотеатров из киноафиши
    url(r'^cron/kinoafisha_cinema_rates_import/$', 'release_parser.views.create', {'method': kinoafisha_cinema_rates_import}, name='kinoafisha_cinema_rates_import'),
    # импорт залов из киноафиши
    url(r'^cron/kinoafisha_hall_import/$', 'release_parser.views.create', {'method': kinoafisha_hall_import}, name='kinoafisha_hall_import'),
    # импорт персон из киноафиши
    url(r'^cron/kinoafisha_persons_import/$', 'release_parser.views.create', {'method': kinoafisha_persons_import}, name='kinoafisha_persons_import'),
    # импорт фильмов из киноафиши
    url(r'^cron/kinoafisha_films_import/$', 'release_parser.views.create', {'method': kinoafisha_films_import}, name='kinoafisha_films_import'),
    # импорт сеансов из киноафиши
    url(r'^cron/kinoafisha_schedules_import/$', 'release_parser.views.create', {'method': kinoafisha_schedules_import}, name='kinoafisha_schedules_import'),
    url(r'^cron/kinoafisha_schedules_booking_import/$', 'release_parser.views.create', {'method': kinoafisha_schedules_booking_import}, name='kinoafisha_schedules_booking_import'),
    
    url(r'^cron/kinoinfo_ua_releases_import/$', 'release_parser.views.create', {'method': kinoinfo_ua_releases_import}, name='kinoinfo_ua_releases_import'),
    
    
    # импорт бюджетов фильмов
    url(r'^cron/kinoafisha_budget_import/$', 'release_parser.views.create', {'method': kinoafisha_budget_import}, name='kinoafisha_budget_import'),
    # импорт жанров фильмов
    url(r'^cron/kinoafisha_genres_import/$', 'release_parser.views.create', {'method': kinoafisha_genres_import}, name='kinoafisha_genres_import'),
    # импорт статусов и типов персон
    url(r'^cron/kinoafisha_statusact_and_actions/$', 'release_parser.views.create', {'method': kinoafisha_statusact_and_actions}, name='kinoafisha_statusact_and_actions'),
    # импорт кассовых сборов сша
    url(r'^cron/kinoafisha_usa_gathering_import/$', 'release_parser.views.create', {'method': kinoafisha_usa_gathering_import}, name='kinoafisha_usa_gathering_import'),
    # импорт рецензий
    url(r'^cron/kinoafisha_reviews_import/$', 'release_parser.views.create', {'method': kinoafisha_reviews_import}, name='kinoafisha_reviews_import'),
    # импорт фильмов v2
    url(r'^cron/kinoafisha_films_import_v2/$', 'release_parser.views.create', {'method': kinoafisha_films_import_v2}, name='kinoafisha_films_import_v2'),
    # импорт связи между персоной и фильмом
    url(r'^cron/kinoafisha_persons_rel/$', 'release_parser.views.create', {'method': kinoafisha_persons_rel}, name='kinoafisha_persons_rel'),
    # импорт отзывов на фильмы
    url(r'^cron/kinoafisha_opinions_import/$', 'release_parser.views.create', {'method': kinoafisha_opinions_import}, name='kinoafisha_opinions_import'),
    # импорт новостных статей
    url(r'^cron/kinoafisha_news_import/$', 'release_parser.views.create', {'method': kinoafisha_news_import}, name='kinoafisha_news_import'),
    


    # ЭКСПОРТ В КИНОАФИШУ через cron
    # экспорт Планета-Кино репертуаров в киноафишу
    url(r'^cron/planeta_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': planeta_schedules_export_to_kinoafisha}, name='planeta_schedules_export_to_kinoafisha'),
    # экспорт Rambler репертуаров в киноафишу
    url(r'^cron/rambler_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': rambler_schedules_export_to_kinoafisha}, name='rambler_schedules_export_to_kinoafisha'),
    # экспорт CMC репертуаров в киноафишу
    url(r'^cron/kinobit_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinobit_schedules_export_to_kinoafisha}, name='kinobit_schedules_export_to_kinoafisha'),
    # экспорт Kinohod репертуаров в киноафишу
    url(r'^cron/kinohod_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinohod_schedules_export_to_kinoafisha}, name='kinohod_schedules_export_to_kinoafisha'),
    # экспорт Megamag репертуаров в киноафишу
    url(r'^cron/megamag_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': megamag_schedules_export_to_kinoafisha}, name='megamag_schedules_export_to_kinoafisha'),
    # экспорт плееров от now.ru на киноафишу
    url(r'^cron/nowru_player_to_kinoafisha/$', 'release_parser.views.create', {'method': nowru_player_to_kinoafisha}, name='nowru_player_to_kinoafisha'),
    # экспорт CinemaArtHall репертуаров в киноафишу
    url(r'^cron/cinemaarthall_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': cinemaarthall_schedules_export_to_kinoafisha}, name='cinemaarthall_schedules_export_to_kinoafisha'),
    # экспорт Кинотеатр Этаж репертуаров в киноафишу
    url(r'^cron/etaj_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': etaj_schedules_export_to_kinoafisha}, name='etaj_schedules_export_to_kinoafisha'),
    # экспорт Кинотеатр Б-Класс репертуаров в киноафишу
    url(r'^cron/kinobklass_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinobklass_schedules_export_to_kinoafisha}, name='kinobklass_schedules_export_to_kinoafisha'),
    # экспорт Афиша в Сургуте репертуаров в киноафишу
    url(r'^cron/surkino_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': surkino_schedules_export_to_kinoafisha}, name='surkino_schedules_export_to_kinoafisha'),
    # экспорт Златоуст Космос репертуаров в киноафишу
    url(r'^cron/zlat74ru_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': zlat74ru_schedules_export_to_kinoafisha}, name='zlat74ru_schedules_export_to_kinoafisha'),
    # экспорт Александров Сатурн репертуаров в киноафишу
    url(r'^cron/kinosaturn_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinosaturn_schedules_export_to_kinoafisha}, name='kinosaturn_schedules_export_to_kinoafisha'),
    # экспорт Запад 24 репертуаров в киноафишу
    url(r'^cron/zapad24ru_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': zapad24ru_schedules_export_to_kinoafisha}, name='zapad24ru_schedules_export_to_kinoafisha'),
    # экспорт Мичуринск Октябрь репертуаров в киноафишу
    url(r'^cron/michurinskfilm_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': michurinskfilm_schedules_export_to_kinoafisha}, name='michurinskfilm_schedules_export_to_kinoafisha'),
    # экспорт Kino-teart.ua репертуаров в киноафишу
    url(r'^cron/kinoteatrua_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinoteatrua_schedules_export_to_kinoafisha}, name='kinoteatrua_schedules_export_to_kinoafisha'),
    # экспорт ktmir.ru и kt-russia.ru репертуаров в киноафишу
    url(r'^cron/ktmir_and_ktrussia_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': ktmir_and_ktrussia_schedules_export_to_kinoafisha}, name='ktmir_and_ktrussia_schedules_export_to_kinoafisha'),
    # экспорт luxor.chuvashia.com репертуаров в киноафишу
    url(r'^cron/luxor_chuvashia_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': luxor_chuvashia_schedules_export_to_kinoafisha}, name='luxor_chuvashia_schedules_export_to_kinoafisha'),
    # экспорт arsenal-club.com репертуаров в киноафишу
    url(r'^cron/arsenalclub_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': arsenalclub_schedules_export_to_kinoafisha}, name='arsenalclub_schedules_export_to_kinoafisha'),
    # экспорт www.illuzion.ru репертуаров в киноафишу
    url(r'^cron/illuzion_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': illuzion_schedules_export_to_kinoafisha}, name='illuzion_schedules_export_to_kinoafisha'),
    # экспорт vkino.com.ua репертуаров в киноафишу
    url(r'^cron/vkinocomua_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': vkinocomua_schedules_export_to_kinoafisha}, name='vkinocomua_schedules_export_to_kinoafisha'),
    # экспорт luxor.ru репертуаров в киноафишу
    url(r'^cron/luxor_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': luxor_schedules_export_to_kinoafisha}, name='luxor_schedules_export_to_kinoafisha'),
    # экспорт cinema5.ru репертуаров в киноафишу
    url(r'^cron/cinema5_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': cinema5_schedules_export_to_kinoafisha}, name='cinema5_schedules_export_to_kinoafisha'),
    # экспорт kinomonitor.ru репертуаров в киноафишу
    url(r'^cron/kinomonitor_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinomonitor_schedules_export_to_kinoafisha}, name='kinomonitor_schedules_export_to_kinoafisha'),
    # экспорт Ореанда и Спартак репертуаров в киноафишу
    url(r'^cron/oreanda_and_spartak_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': oreanda_and_spartak_schedules_export_to_kinoafisha}, name='oreanda_and_spartak_schedules_export_to_kinoafisha'),
    # экспорт premierzal репертуаров в киноафишу
    url(r'^cron/premierzal_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': premierzal_schedules_export_to_kinoafisha}, name='premierzal_schedules_export_to_kinoafisha'),
    # экспорт kinomagnat.com.ua репертуаров в киноафишу
    url(r'^cron/kinomagnat_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinomagnat_schedules_export_to_kinoafisha}, name='kinomagnat_schedules_export_to_kinoafisha'),
    # экспорт kinoboomer.com.ua репертуаров в киноафишу
    url(r'^cron/kinoboomer_schedules_export_to_kinoafisha/$', 'release_parser.views.create', {'method': kinoboomer_schedules_export_to_kinoafisha}, name='kinoboomer_schedules_export_to_kinoafisha'),
    


    # ЗАПУСК ДАМПОВ ДЛЯ API через cron
    url(r'^cron/api_dump_schedules/$', 'release_parser.views.create', {'method': cron_dump_schedules}, name='api_dump_schedules'),
    url(r'^cron/api_dump_cinemas/$', 'release_parser.views.create', {'method': cron_dump_cinemas}, name='api_dump_cinemas'),
    url(r'^cron/api_dump_films/$', 'release_parser.views.create', {'method': cron_dump_films}, name='api_dump_films'),
    url(r'^cron/api_dump_persons/$', 'release_parser.views.create', {'method': cron_dump_persons}, name='api_dump_persons'),
    url(r'^cron/api_dump_halls/$', 'release_parser.views.create', {'method': cron_dump_halls}, name='api_dump_halls'),
    url(r'^cron/api_dump_city_dir/$', 'release_parser.views.create', {'method': cron_dump_city_dir}, name='api_dump_city_dir'),
    url(r'^cron/api_dump_hall_dir/$', 'release_parser.views.create', {'method': cron_dump_hall_dir}, name='api_dump_hall_dir'),
    url(r'^cron/api_dump_genre_dir/$', 'release_parser.views.create', {'method': cron_dump_genre_dir}, name='api_dump_genre_dir'),
    url(r'^cron/api_dump_metro_dir/$', 'release_parser.views.create', {'method': cron_dump_metro_dir}, name='api_dump_metro_dir'),
    url(r'^cron/api_dump_theater/$', 'release_parser.views.create', {'method': cron_dump_theater}, name='api_dump_theater'),
    url(r'^cron/api_dump_screens/$', 'release_parser.views.create', {'method': cron_dump_screens}, name='api_dump_screens'),
    url(r'^cron/api_dump_imovie/$', 'release_parser.views.create', {'method': cron_dump_imovie}, name='api_dump_imovie'),
    url(r'^cron/api_dump_films_name/$', 'release_parser.views.create', {'method': cron_dump_films_name}, name='api_dump_films_name'),
    url(r'^cron/api_dump_imdb_rate/$', 'release_parser.views.create', {'method': cron_dump_imdb_rate}, name='api_dump_imdb_rate'),
    url(r'^cron/api_dump_movie_reviews/$', 'release_parser.views.create', {'method': cron_dump_movie_reviews}, name='api_dump_movie_reviews'),
    url(r'^cron/api_dump_film_posters/$', 'release_parser.views.create', {'method': cron_dump_film_posters}, name='api_dump_film_posters'),
    url(r'^cron/api_dump_film_trailers/$', 'release_parser.views.create', {'method': cron_dump_film_trailers}, name='api_dump_film_trailers'),
    url(r'^cron/api_dump_releases_ua/$', 'release_parser.views.create', {'method': cron_dump_releases_ua}, name='api_dump_releases_ua'),


    # Логи выполнения cron заданий для kinohod
    url(r'^cron_log/kinohod_cities/$', 'release_parser.views.cron_log', {'log': 'kinohod_cities'}, name='cron_log_kinohod_cities'),
    url(r'^cron_log/kinohod_cinemas/$', 'release_parser.views.cron_log', {'log': 'kinohod_cinemas'}, name='cron_log_kinohod_cinemas'),
    url(r'^cron_log/kinohod_films/$', 'release_parser.views.cron_log', {'log': 'kinohod_films'}, name='cron_log_kinohod_films'),
    url(r'^cron_log/kinohod_schedules/$', 'release_parser.views.cron_log', {'log': 'kinohod_schedules'}, name='cron_log_kinohod_schedules'),
    url(r'^cron_log/kinohod_export/$', 'release_parser.views.cron_log', {'log': 'kinohod_export'}, name='cron_log_kinohod_export'),
    
    
    # Организации
    # 0654.com.ua
    #url(r'^cron/get_0654_organizations/$', 'release_parser.views.create', {'method': get_0654_organizations}, name='get_0654_organizations'),
    # bigyalta.info
    #url(r'^cron/get_bigyalta_organizations/$', 'release_parser.views.create', {'method': get_bigyalta_organizations}, name='get_bigyalta_organizations'),
    #url(r'^cron/get_orsk_organizations/$', 'release_parser.views.create', {'method': get_orsk_organizations}, name='get_orsk_organizations'),

    # отправка смс
    url(r'^cron/clickatell_send_msg/$', 'release_parser.views.create', {'method': clickatell_send_msg}, name='clickatell_send_msg'),

    # Интегральная оценка "Оценки киномэтров"
    url(r'^cron/integral_rate/$', 'movie_online.debug.create', {'method': integral_rate}, name='integral_rate'),

    url(r'^cron/user_deposit/$', 'release_parser.views.create', {'method': user_deposit}, name='user_deposit'),
    

)


