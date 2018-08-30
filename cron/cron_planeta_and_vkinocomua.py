#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.planeta_kino import get_planeta_cities_cinemas, get_planeta_films, get_planeta_schedules
from release_parser.vkinocomua import get_vkinocomua_cities_and_cinemas, get_vkinocomua_films_and_schedules

get_planeta_cities_cinemas()
get_planeta_films()
get_planeta_schedules()

#get_vkinocomua_cities_and_cinemas()
#get_vkinocomua_films_and_schedules()

