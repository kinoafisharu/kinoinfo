#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoafisha'


from user_registration.views import subscriber_comments_author_blog_sender

subscriber_comments_author_blog_sender()

