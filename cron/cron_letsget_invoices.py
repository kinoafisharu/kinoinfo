#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_letsget'


from letsgetrhythm.views import invoice_msg_sender

invoice_msg_sender()

