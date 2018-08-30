#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.kinoteatrua import get_kinoteatrua_films_and_persons, get_kinoteatrua_posters, get_kinoteatrua_schedules, get_kinoteatrua_releases


# ~55 min
get_kinoteatrua_films_and_persons()
get_kinoteatrua_posters()
get_kinoteatrua_releases()
get_kinoteatrua_schedules()



