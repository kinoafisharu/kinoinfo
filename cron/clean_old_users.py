#!/usr/bin/python
import datetime
import os
import sys

sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'

DAYS = 30


def clean_old_users():
    from django.contrib.auth.models import User

    User.objects.filter(
        last_login__lte=datetime.datetime.now()-datetime.timedelta(days=DAYS),
        email='',
        first_name='',
        last_name=''
    ).delete()


clean_old_users()

