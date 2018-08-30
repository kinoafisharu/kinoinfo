#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.zapad24ru import get_zapad24ru
from release_parser.michurinskfilm import get_michurinskfilm_schedules

get_zapad24ru()
get_michurinskfilm_schedules()
