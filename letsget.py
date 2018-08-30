import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo/base/templatetags')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_letsget'
os.environ['PYTHON_EGG_CACHE'] = '/var/www/kinoinfo/data/www/kinoinfo/temp/'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
