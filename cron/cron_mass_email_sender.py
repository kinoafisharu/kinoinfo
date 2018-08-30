#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

from release_parser.views import mass_email_sender
from release_parser.currencyrate import get_currency_rate

mass_email_sender()

#get_currency_rate()

