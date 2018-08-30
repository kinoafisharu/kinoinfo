#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.rutracker import get_rutracker_topics, get_rutracker_topics_closed
from release_parser.oreanda_and_spartak import get_oreanda_and_spartak


# ~1 min
get_oreanda_and_spartak()

get_rutracker_topics()
get_rutracker_topics_closed()


