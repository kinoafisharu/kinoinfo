#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'


from release_parser.nowru import get_nowru_links, nowru_ident
from release_parser.iviru import get_ivi_file, ivi_ident
from release_parser.tvzavr import get_tvzavr_dump, tvzavr_ident

get_ivi_file()
ivi_ident()

get_tvzavr_dump()
tvzavr_ident()

get_nowru_links()
nowru_ident()


