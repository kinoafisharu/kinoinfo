#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.ktmir_and_ktrussia import get_ktmir_and_ktrussia_schedules
from release_parser.luxor_chuvashia import get_luxor_chuvashia_schedules

# ~2 min
get_luxor_chuvashia_schedules()
get_ktmir_and_ktrussia_schedules()

