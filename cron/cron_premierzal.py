#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.premierzal import get_premierzal_cities, get_premierzal_cinemas, get_premierzal_schedules

# ~12.00 min
get_premierzal_cities()
get_premierzal_cinemas()
get_premierzal_schedules()


