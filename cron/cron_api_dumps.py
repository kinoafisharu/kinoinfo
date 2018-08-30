#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from api.cron_func import *

# ~20 min
cron_dump_schedules()
cron_dump_schedules_v2()
cron_dump_schedules_v4()
cron_dump_screens()
cron_dump_films()
cron_dump_films_v3()
cron_dump_films_v4()
cron_dump_imovie()
cron_dump_persons()
cron_dump_films_name()
cron_dump_imdb_rate()
cron_dump_movie_reviews()
cron_dump_film_posters()
cron_dump_film_trailers()
cron_dump_cinemas()
cron_dump_theater()
#cron_dump_releases_ua()
cron_dump_halls()
cron_dump_city_dir()
cron_dump_hall_dir()
cron_dump_genre_dir()
cron_dump_metro_dir()



