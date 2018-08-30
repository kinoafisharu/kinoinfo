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
BTN_LIMIT = 100

def get_imdb_rate(imdb):
    imdb_votes = None
    imdb_rate = None
    imdb = get_imdb_id(imdb)
    opener = give_me_cookie()
    url = 'http://www.imdb.com/title/tt%s/' %  imdb
    try:
        req = opener.open(urllib2.Request(url))
    except urllib2.HTTPError:
        req = None
        print "http  error"
    if req:
        data = BeautifulSoup(req.read(), from_encoding="utf-8")
        # рейтинг
        imdb_rate = data.find('span', itemprop="ratingValue")
        
        if imdb_rate:
            imdb_rate = float(imdb_rate.text.encode('utf-8'))
            imdb_votes = data.find('span', itemprop="ratingCount")
            imdb_votes = int(imdb_votes.text.encode('utf-8').replace(u' ', '').replace(u',', ''))
    
    return imdb_rate, imdb_votes



def update_kinoafisha_button(imdb_id, rate, votes):
    idents = {
        0: 72,
        1: 72,
        2: 69,
        3: 66,
        4: 63,
        5: 62,
        6: 60,
        7: 60,
    }
    
#    # получаем рейтинг IMDb от киноафиши
#    rate = film.imdb if film.imdb else 0
#    votes = film.imdb_votes if film.imdb_votes else 0
#    imdb = get_imdb_id(film.idalldvd)
    imdb = imdb_id
    votes = votes if votes  else 0
    rate = rate if rate  else 0
    
    # подготавливаем изображния к работе
    img = Image.open("%s/base/images/tbut.png" % settings.STATIC_ROOT)
    star0 = Image.open("%s/base/images/star0.png" % settings.STATIC_ROOT)
    star1 = Image.open("%s/base/images/star1.png" % settings.STATIC_ROOT)
    
    # получаем ширину и высоту изображения "звездочка"
    star_w, star_h = star0.size
    
    # округляем рейтинг
    rounded_rate = int(math.ceil(float(str(rate).replace(',','.')))) if rate else 0
    
    # на изображение ставим звездочки по рейтингу
    place = 0
    for i in range(1, 11):
        star = star1 if i <= rounded_rate else star0
        img.paste(star, (place, 27))
        place += star_w

    rate = str(rate)
    votes = str(votes)

    # подготавливаем жирный и обычный шрифт Roboto
    font_bold = ImageFont.truetype("%s/base/fonts/Roboto-Black.ttf" % settings.STATIC_ROOT, 15)
    font_light = ImageFont.truetype("%s/base/fonts/Roboto-Light.ttf" % settings.STATIC_ROOT, 9)
    
    # на изображение пишем рейтинг и кол-во голосов
    ident = idents.get(len(votes), 60)
    background = ImageDraw.Draw(img)
    background.text((63, -2), rate, (165, 42, 42), font=font_bold)
    background.text((ident, 15), votes, (0, 0, 0), font=font_light)

    # создаем, если нет папку, с именем - первая цифра id IMDB
    folder = str(imdb)[0]
    folder_path = '%s/%s' % (settings.BUTTONS, folder)
    try: os.makedirs(folder_path)
    except OSError: pass
    
    # сохраняем кнопку
    output_name = '%s.png' % imdb
    output_path = '%s/%s' % (folder_path, output_name)
    path = output_path.replace(settings.MEDIA_ROOT, '/upload')
    img.save(output_path)



def start_update(startT):
    global root
    count = 0
    old = 0
    young = 0
    errors = 0
    updated = 0

    for path, subdirs, files in os.walk(root):
        if old >= BTN_LIMIT:
            break
        for name in files:
            count +=1
            if old >= BTN_LIMIT:
                break
            fullName = os.path.join(path, name)
            st = os.stat(fullName) 
            fileAge = (time.time()-st.st_mtime) / 3600
            imdb = name.split('.')[0]


            if fileAge > 72:
          #      print "{0} -> id:{1} (updated {2:.1f} hour ego) ".format(fullName, imdb, fileAge)
                old +=1
                rate, votes = get_imdb_rate(imdb)
          #      print fullName  + " -> " + imdb + " " + str(rate) + "/" + str(votes) + "(updates " + str(fileAge) + " hour ago)"                
                try:
                    update_kinoafisha_button(imdb, rate, votes)
                    updated +=1
          #          print "* button updated!!! *"
                except:
                    errors +=1
                    print "error btn create"
            else:
                young +=1

  #  print "files {0}, <72h: {1}, >72h: {2}".format(count, young, old)

    endT = datetime.datetime.now()
    totalT = endT - startT 
    nowT = endT.strftime("%Y-%m-%d %H:%M:%S")

    with open("/var/www/kinoinfo/data/www/kinoinfo/ext2017/imdb_btn_upd.LOG", "a") as myfile:
        myfile.write(str(nowT) + " time: " + str(totalT) + " files compared: {0}, t<72h: {1}, t>72h: {2}, updated: {3}".format(count, young, old, updated) + ", errors:" + str(errors) +"\n" )




if __name__ == "__main__":
    startT = datetime.datetime.now()
    start_update(startT)


#============================================


    

    
