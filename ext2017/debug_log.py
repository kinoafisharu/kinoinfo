import os
import sys
#exit()
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo/base/templatetags')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'
os.environ['PYTHON_EGG_CACHE'] = '/var/www/kinoinfo/data/www/kinoinfo/temp/'


import django.core.handlers.wsgi

import settings_kinoinfo
from django.utils import datastructures
from base.models import *
from django.db import models
import datetime

from settings_kinoafisha import KINOAFISHA_EXT


def debug_kino_log(text):
    fileName = '{0}/{1}.json'.format(KINOAFISHA_EXT, 'debug_kino.LOG')
    with open(fileName, 'a') as outfile:
        outfile.write(str(text) + "\n")



