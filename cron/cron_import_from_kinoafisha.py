#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.views import kinoafisha_country_import, kinoafisha_city_import, kinoafisha_distributor_import, kinoafisha_cinema_import, kinoafisha_hall_import, kinoafisha_persons_import, kinoafisha_films_import,  kinoafisha_schedules_import, kinoafisha_budget_import, kinoafisha_genres_import, kinoafisha_statusact_and_actions, kinoafisha_usa_gathering_import, kinoafisha_reviews_import, kinoafisha_films_import_v2, kinoafisha_persons_rel, kinoafisha_cinema2_import, kinoafisha_cinema_rates_import, kinoafisha_news_import, kinoafisha_opinions_import, kinoinfo_ua_releases_import
from movie_online.IR import integral_rate

# ~12 min
kinoafisha_country_import()
kinoafisha_city_import()
kinoafisha_distributor_import()
kinoafisha_cinema_import()
kinoafisha_cinema2_import()
kinoafisha_cinema_rates_import()
kinoafisha_hall_import()
kinoafisha_genres_import()
kinoafisha_statusact_and_actions()
kinoafisha_persons_import()
kinoafisha_films_import()
kinoafisha_films_import_v2()
kinoafisha_persons_rel()
kinoafisha_usa_gathering_import()
kinoafisha_schedules_import()
kinoafisha_news_import()
kinoafisha_opinions_import()
kinoafisha_reviews_import()
kinoinfo_ua_releases_import()

integral_rate() # ~4

kinoafisha_budget_import()




