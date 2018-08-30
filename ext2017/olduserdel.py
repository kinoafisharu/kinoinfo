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

startT = datetime.datetime.now()


pofileArray = Profile.objects.order_by('user__last_login').all()[130:125000]
count = 0
yearAgo = datetime.datetime.now() - datetime.timedelta(days=367)
#print len(pofileArray)
for pr in pofileArray:
    if pr.user.last_login < yearAgo and pr.user.email == '':
#         print('n={0} l={1} e={2} '.format(pr.user.username, pr.user.last_login, pr.user.email))
         pr.user.delete()
         pr.personinterface.delete()
         pr.delete() 
         count += 1

endT = datetime.datetime.now()

totalT = endT - startT 
nowT = endT.strftime("%Y-%m-%d %H:%M:%S")

with open("/var/www/kinoinfo/data/www/kinoinfo/ext2017/olduserdel.LOG", "a") as myfile:
    myfile.write(str(nowT) + " time: " + str(totalT) + " record: " + str(count) + "\n" )

