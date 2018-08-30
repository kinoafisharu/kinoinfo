#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.cinemaplex import get_cinemaplex_releases

# ~0.30 min
get_cinemaplex_releases()


