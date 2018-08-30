# -*- coding: utf-8 -*- 

import os
import sys
#exit()
sys.path.append('/var/www/kinoinfo/data/www/kinoinfo')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_kinoinfo'
import settings_kinoinfo
from django.utils import datastructures
from base.models import *
from django.db import models
import urllib
import urllib2
import httplib2
import re
import datetime
import time
import cookielib
import operator

from django.conf import settings
from bs4 import BeautifulSoup
from release_parser.func import cron_success, get_imdb_id, give_me_cookie
import cookielib
import math
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from release_parser.func import get_imdb_id

root = settings.BUTTONS
root_old = "/var/www/kinoinfo/data/www/kinoinfo.ru/upload/_btn.copy"
BTN_LIMIT = 100


def start_update(root, startT):
    count = 0
    old = 0
    young = 0
    arr = []

    for path, subdirs, files in os.walk(root):
        for name in files:
            arr.append(name)
            count +=1
            fullName = os.path.join(path, name)
            st = os.stat(fullName) 
            fileAge = (time.time()-st.st_mtime) / 3600
            imdb = name.split('.')[0]

            if fileAge > 72:
                old +=1
            else:
                young +=1
  
    print root
    print "files {0}, t<72h: {1}, t>72h: {2}".format(count, young, old)

    endT = datetime.datetime.now()
    totalT = endT - startT 
    nowT = endT.strftime("%Y-%m-%d %H:%M:%S")

    with open("/var/www/kinoinfo/data/www/kinoinfo/ext2017/imdb_btn_chk.LOG", "a") as myfile:
        myfile.write(str(nowT) + " time: " + str(totalT) + " " + root + " " + " files compared: {0}, t<72h: {1}, t>72h: {2}".format(count, young, old) + "\n" )

    return arr



if __name__ == "__main__":
    count = 0
    startT = datetime.datetime.now()
    arr = start_update(root, startT)
    startT = datetime.datetime.now()
    arr_old = start_update(root_old, startT)
#    for i in arr_old:
#        if i in arr:
#            pass
#        else:
#            print i + "\n"
#            count += 1
#
#    print count

#============================================


    

    
