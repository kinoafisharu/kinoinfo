#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.etaj import get_etaj_schedules
from release_parser.kinobklass import get_kinobklass_schedules


get_etaj_schedules()
get_kinobklass_schedules()




