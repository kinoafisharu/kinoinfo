#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.zlat74ru import get_zlat74ru_schedules
from release_parser.kinosaturn import get_kinosaturn_schedules


get_kinosaturn_schedules()
#get_zlat74ru_schedules()
