#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.kinometro import kinometro_films_pages, film_kinometro_ident

# ~51.00 min

#kinometro_films_pages() # ~50.00 min
#film_kinometro_ident() # ~1.00 min


