#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.kinomagnat import get_kinomagnat_schedules
from release_parser.kinoboomer import get_kinoboomer_schedules

# ~0.20 min
get_kinomagnat_schedules()
get_kinoboomer_schedules()

