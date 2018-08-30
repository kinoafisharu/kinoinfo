#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.megamag import get_megamag
from release_parser.rambler import get_rambler_indexfile, get_rambler_cities, get_rambler_cinemas, get_rambler_films, get_rambler_schedules

# ~30 min
get_rambler_indexfile()
get_rambler_cities()
get_rambler_cinemas()
get_rambler_films()
get_rambler_schedules() 

# ~10 min
get_megamag() 




