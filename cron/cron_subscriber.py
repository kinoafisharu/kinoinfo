#!/usr/bin/python

import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoafisha'


from user_registration.views import subscriber_blog_sender, subscriber_comments_sender, adv_notification_sender

subscriber_blog_sender()

subscriber_comments_sender()

adv_notification_sender()
