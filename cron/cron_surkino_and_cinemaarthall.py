#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.surkino import get_surkino_cinemas, get_surkino_schedules
from release_parser.cinemaarthall import get_cinemaarthall_schedules

# ~1 min
get_surkino_cinemas()
get_surkino_schedules()
get_cinemaarthall_schedules()




