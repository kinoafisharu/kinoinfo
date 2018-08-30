#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.kinobit_cmc import get_kinobit_dump, get_kinobit_cities, get_kinobit_cinemas, get_kinobit_films, get_kinobit_schedules



get_kinobit_dump()

get_kinobit_cities()

get_kinobit_cinemas()

get_kinobit_films()

get_kinobit_schedules()



