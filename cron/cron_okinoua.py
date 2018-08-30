#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.okinoua import get_okinoua_links, get_okinoua_releases, get_okinoua_cities, get_okinoua_cinemas, get_okinoua_films, get_okinoua_schedules


get_okinoua_links()

get_okinoua_releases()

get_okinoua_cities()

get_okinoua_cinemas()

get_okinoua_films()

get_okinoua_schedules()
