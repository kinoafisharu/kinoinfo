#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.luxor import get_luxor_cinemas, get_luxor_films, get_luxor_schedules
from release_parser.yovideo import get_yovideo

# ~20 sec
get_luxor_cinemas()
get_luxor_films()
get_luxor_schedules()

# ~40 sec
get_yovideo()
