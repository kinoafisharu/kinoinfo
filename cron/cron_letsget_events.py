#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_letsget'


from letsgetrhythm.views import events_msg_sender

events_msg_sender()

