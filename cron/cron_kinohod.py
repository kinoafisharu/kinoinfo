#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.kinohod import get_kinohod_cities, get_kinohod_cinemas, get_kinohod_films, get_kinohod_schedules

# ~57.00 min

get_kinohod_cities() # ~0.05 min
get_kinohod_cinemas() # ~0.45 min
get_kinohod_films() # ~1.30 min
get_kinohod_schedules() # ~55.00 min



