#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.kinomonitor import get_kinomonitor_cities_and_cinemas, get_kinomonitor_films_and_schedules


get_kinomonitor_cities_and_cinemas()
get_kinomonitor_films_and_schedules()
