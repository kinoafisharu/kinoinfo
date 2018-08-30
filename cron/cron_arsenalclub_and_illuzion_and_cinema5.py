#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.arsenalclub import get_arsenalclub_schedules
from release_parser.illuzion import get_illuzion_schedules
from release_parser.cinema5 import get_cinema5_schedules

get_arsenalclub_schedules()
get_illuzion_schedules()
get_cinema5_schedules()
