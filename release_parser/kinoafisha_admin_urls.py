# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^notfci/$', 'release_parser.kinoafisha_admin.notfoundcinemas_temp', name='notfoundcinemas_temp'),

    # главная страница
    url(r'^$', 'release_parser.kinoafisha_admin.kinoafisha_admin_main', name='kinoafisha_admin_main'),

    # парсинг
    url(r'^parser/(?P<typedata>\w+)/$', 'release_parser.kinoafisha_admin.admin_parsers_info', name='admin_parsers_info'),

    # идентификация
    url(r'^objects/(?P<obj>\w+)/$', 'release_parser.kinoafisha_admin.admin_identification_info', name='admin_identification_info'),

    # запись
    url(r'^import/kinoinfo/$', 'release_parser.kinoafisha_admin.admin_kinoinfo_import_info', name='admin_kinoinfo_import_info'),
    url(r'^import/kinoafisha/$', 'release_parser.kinoafisha_admin.admin_kinoafisha_import_info', name='admin_kinoafisha_import_info'),
    url(r'^import/api/$', 'release_parser.kinoafisha_admin.admin_api_import_info', name='admin_api_import_info'),

    # редактирование
    url(r'^edit/cinema_relations/$', 'release_parser.kinoafisha_admin.edit_cinema_relations', name='edit_cinema_relations'),

    url(r'^edit/cinema_relations_alter_names/$', 'release_parser.kinoafisha_admin.edit_cinema_relations_alter_names', name='edit_cinema_relations_alter_names'),

    url(r'^edit/city_names_relations/$', 'release_parser.kinoafisha_admin.edit_city_names_relations', name='edit_city_names_relations'),

    url(r'^edit/films_relations_alter_names/$', 'release_parser.kinoafisha_admin.edit_films_relations_alter_names', name='edit_films_relations_alter_names'),

    url(r'^edit/source_films_relations/$', 'release_parser.kinoafisha_admin.edit_source_films_relations', name='edit_source_films_relations'),

    url(r'^edit/releases_relations/$', 'release_parser.kinoafisha_admin.edit_releases_relations', name='edit_releases_relations'),

    url(r'^edit/source_cinemas_relations/$', 'release_parser.kinoafisha_admin.edit_source_cinemas_relations', name='source_cinemas_relations'),

    url(r'^edit/reviews_list_without_rate/$', 'release_parser.kinoafisha_admin.edit_reviews_list_without_rate', name='reviews_list_without_rate'),

    # Платные действия
    url(r'^actions_pricelist/$', 'release_parser.kinoafisha_admin.actions_pricelist', name='actions_pricelist'),
    url(r'^edit/actions_pricelist/(?P<id>\w+)/$', 'release_parser.kinoafisha_admin.edit_actions_pricelist', name='edit_actions_pricelist'),
    url(r'^add/actions_pricelist/$', 'release_parser.kinoafisha_admin.add_actions_pricelist', name='add_actions_pricelist'),

    url(r'^paid_actions_list/(?P<id>\w+)/(?P<all>\w+)/$', 'release_parser.kinoafisha_admin.paid_actions_list', name='paid_actions_list'),
    url(r'^paid_actions_list/(?P<id>\w+)/$', 'release_parser.kinoafisha_admin.paid_actions_list', name='paid_actions_list'),

    url(r'^get_user_page_info/(?P<id>\d+)/$', 'release_parser.kinoafisha_admin.get_user_page_info', name='get_user_page_info'),

    url(r'^source_releases_show/$', 'release_parser.kinoafisha_admin.admin_source_releases_show', name='admin_source_releases_show'),

    # Лог парсера релизов кинометро
    url(r'^kinometro_films_pages_log/$', 'release_parser.kinoafisha_admin.kinometro_films_pages_log', name='kinometro_films_pages_log'),

    # Список подписавшихся юзеров
    url(r'^get_subscriptions_users/$', 'release_parser.kinoafisha_admin.get_subscriptions_users', name='get_subscriptions_users'),

    # список дистрибьюторов
    url(r'^distributor/list/(?P<country>\d+)/$', 'release_parser.kinoafisha_admin.admin_distributor_list', name='distributor_list'),

    # редактор источников
    url(r'^sources/$', 'release_parser.kinoafisha_admin.admin_sources_editor', name='admin_sources_editor'),

    # статистика
    url(r'^stat/cities/$', 'release_parser.kinoafisha_admin.admin_city_statistics', name='admin_city_statistics'),
    url(r'^stat/cinemas/$', 'release_parser.kinoafisha_admin.admin_cinemas_statistics', name='admin_cinemas_statistics'),
    url(r'^stat/buy_ticket/$', 'release_parser.kinoafisha_admin.buy_ticket_statistics', name='admin_buy_ticket_statistics'),

    # кинотеатры Киноафиши
    url(r'^afisha/cinemas/$', 'release_parser.kinoafisha_admin.admin_afisha_cinemas', name='admin_afisha_cinemas'),

    # удаление всех дынных источника
    url(r'^delete/sources/$', 'release_parser.kinoafisha_admin.admin_delete_source_data', name='admin_delete_source_data'),

    # подписки на rss
    url(r'^subscriptions_feeds/$', 'release_parser.kinoafisha_admin.subscriptions_feeds', name='subscriptions_feeds'),

    # rutracker topics
    url(r'^rutracker_topics/$', 'release_parser.kinoafisha_admin.rutracker_topics', name='rutracker_topics'),    

    # кассовые сборы
    url(r'^boxoffice/(?P<country>\w+)/$', 'release_parser.kinoafisha_admin.boxoffice_admin', name='boxoffice_admin'),
    url(r'^boxoffice_relations/(?P<id>\w+)/$', 'release_parser.kinoafisha_admin.boxoffice_relations', name='boxoffice_relations'),
    url(r'^boxoffice/(?P<country>\w+)/del/$', 'release_parser.kinoafisha_admin.boxoffice_del', name='boxoffice_del'),

    url(r'^nof/cch/(?P<method>\w+)/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_city_nof_list', name='admin_city_nof_list2'),
    url(r'^ident/cch/(?P<method>\w+)/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_city_cinema_nof', name='admin_city_cinema_nof2'),

    url(r'^ident/hall/(?P<method>\w+)/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_hall_nof', name='admin_hall_nof'),

    # Форма для ненайденных фильмов
    url(r'^nof/films/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_film_nof_list', name='admin_film_nof_list'),
    url(r'^ident/film/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_films_nof', name='admin_films_nof'),
    url(r'^ident/film/v2/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_films_nof_v2', name='admin_films_nof_v2'),

    # Форма для ненайденных стран
    url(r'^nof/country/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_country_nof_list', name='admin_country_nof_list'),
    url(r'^ident/country/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_country_nof', name='admin_country_nof'),

    # Форма для ненайденных дистрибьюторов
    url(r'^nof/distr/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_distributor_nof_list', name='admin_distributor_nof_list'),
    url(r'^ident/distr/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_distributor_nof', name='admin_distributor_nof'),

    # Форма для ненайденных персон
    url(r'^nof/person/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_person_nof_list', name='admin_person_nof_list'),
    url(r'^ident/person/(?P<dump>\w+)/$', 'release_parser.kinoafisha_admin.admin_person_nof', name='admin_person_nof'),

    # Movie_online
    (r'^online/', include('movie_online.admin_urls')),

    # редактор имен режиссеров
    url(r'^persons_parental_names/$', 'release_parser.kinoafisha_admin.persons_parental_names', name='persons_parental_names'),

    # создать юзера
    #url(r'^create_user/$', 'release_parser.kinoafisha_admin.admin_create_user', name='admin_create_user'),

    url(r'^films_doubles/$', 'release_parser.kinoafisha_admin.films_doubles_relations', name='films_doubles'),
    url(r'^films_doubles/sources/$', 'release_parser.kinoafisha_admin.admin_film_doubles_sources_list', name='admin_film_doubles_sources_list'),
    url(r'^films_doubles/source/(?P<id>\d+)/$', 'release_parser.kinoafisha_admin.admin_film_doubles_list', name='admin_film_doubles_list'),

    url(r'^language_test/$', 'release_parser.kinoafisha_admin.language_test', name='language_test'),

    url(r'^image_optimizer/$', 'release_parser.kinoafisha_admin.image_optimizer', name='admin_image_optimizer'),

    # ДЕЙСТВИЯ
    url(r'^actions/$', 'release_parser.kinoafisha_admin.admin_actions', name='admin_actions'),
    # действия над персонами
    url(r'^persons/actions/$', 'release_parser.kinoafisha_admin.admin_person_actions', name='admin_person_actions'),
    # организации
    (r'^organization/', include('organizations.admin_urls')),

    # сгенерированные фильмы
    url(r'^generated_films/$', 'release_parser.kinoafisha_admin.admin_generated_films', name='admin_generated_films'),

    # модератор комментов, отзывов, вопросов
    url(r'^comments_moderator/$', 'release_parser.kinoafisha_admin.comments_moderator', name='comments_moderator'),
    # оценка для отзывов на фильм от источников
    url(r'^opinions_set_rate/$', 'release_parser.kinoafisha_admin.source_opinions_set_rate', name='source_opinions_set_rate'),
    # тест онлайн плеера
    url(r'^online_player/$', 'release_parser.kinoafisha_admin.online_player', name='online_player'),
    # конвертер оценок для отзывов 2-5 = 3-9
    url(r'^opinions_rate_converter/$', 'release_parser.kinoafisha_admin.opinions_rate_converter', name='opinions_rate_converter'),

    url(r'^user_nicknames/$', 'release_parser.kinoafisha_admin.user_nicknames', name='user_nicknames'),
    url(r'^user_nicknames_doubles/$', 'release_parser.kinoafisha_admin.user_nicknames_doubles', name='user_nicknames_doubles'),

    url(r'^adv/statistics/$', 'release_parser.kinoafisha_admin.admin_adv_statistics', name='admin_adv_statistics'),

    # SEO
    url(r'^seo/main/$', 'release_parser.kinoafisha_admin.admin_seo_mainpage', name='admin_seo_mainpage'),

    # Создание системного юзера - SYSTEM
    url(r'^create_system_user/$', 'release_parser.kinoafisha_admin.create_system_user', name='create_system_user'),

    # размер таблицы сеансов
    url(r'^get/size/table/schedules/$', 'release_parser.kinoafisha_admin.get_table_size', name='admin_get_table_size'),

)
