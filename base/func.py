#-*- coding: utf-8 -*-
import re

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext

from base.models import *

REG_HOUSE = re.compile(r'\d+\/*-?\s?[а-яА-Я]?')


def org_build_create(house, city, street_obj, path=''):
    build, created = Building.objects.get_or_create(
        number = house,
        city = city,
        street = street_obj,
        defaults = {
            'number': house,
            'city': city,
            'street': street_obj,
            'path': path,
        }
    )
    return build
    
    

def get_org_street(addr):

    street_name = ''
    street_type = ''
    house = ''
    
    addr = addr.split(',')
    if len(addr) > 1:
        st = addr[0].strip()
        ho = addr[1].strip()
        st_type = st
        
        
        house = REG_HOUSE.findall(ho)
        if house:
            house = ''.join(house).replace('//', '/')
        else:
            house = REG_HOUSE.findall(st)
            if house:
                house = ''.join(house).replace('//', '/')
                st = ho
        
        if house:
            house = re.sub(r'\/$', '', house).strip()
        
        if len(house) > 5:
            house = house.split()[0]

        #if re.findall(r'\d+', st):
        #    street_name = ''
        #    street_type = ''
        #    house = ''
        #else:
        if u'Набережная' in st_type or u'набережная' in st_type:
            street_name = st.encode('utf-8').replace('Набережная', '').replace('набережная', '').strip()
            street_type = '4'
        elif u'шоссе' in st_type:
            street_name = st.encode('utf-8').replace('шоссе', '').strip()
            street_type = '5'
        elif u'пл.' in st_type or u'площадь' in st_type or u'Площадь' in st_type or u'плщ.' in st_type:
            street_name = st.encode('utf-8').replace('площадь', '').replace('пл.', '').replace('плщ.', '').replace('Площадь', '').strip()
            street_type = '3'
        elif u'проезд' in st_type or u'Проезд' in st_type:
            street_name = st.encode('utf-8').replace('проезд', '').replace('Проезд', '').strip()
            street_type = '7'
        elif u'Парк' in st_type or u'парк' in st_type:
            street_name = st.encode('utf-8').replace('парк', '').replace('Парк', '').strip()
            street_type = '10'
        elif u'ул.' in st_type or u'улица' or u'Ул.' in st_type:
            street_name = st.encode('utf-8').replace('ул.', '').replace('Ул.', '').replace('улица','').strip()
            street_type = '1'
        elif u'пер.' in st_type or u'переулок' in st_type:
            street_name = st.encode('utf-8').replace('пер.', '').replace('переулок', '').strip()
            street_type = '2'
        elif u'пр-кт' in st_type or u'проспект' in st_type or u'пр-т' in st_type or u'просп.' in st_type:
            street_name = st.encode('utf-8').replace('пр-кт', '').replace('проспект', '').replace('просп.', '').strip()
            street_type = '6'
        elif u'км.' in st_type or u' км ' in st_type:
            street_name = st.encode('utf-8').replace('км.', '').replace(' км ', '').strip()
            street_type = '12'
        elif u'микрорайон' in st_type or u' мкр' in st_type:
            street_name = st.encode('utf-8').replace('микрорайон', '').replace(' мкр', '').strip()
            street_type = '13'
        elif u'тупик' in st_type:
            street_name = st.encode('utf-8').replace('тупик', '').strip()
            street_type = '11'
        elif u'квл' in st_type or u'квартал' in st_type or u'кварт.' in st_type:
            street_name = st.encode('utf-8').replace('квл', '').replace('квартал', '').replace('кварт.', '').strip()
            street_type = '14'

        street_name = street_name.replace('ул.', '').replace('улица','').strip()
    return street_name, street_type, house
    
    
def create_kinoafisha_button(film, imdb_id):
    import math
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
    from release_parser.func import get_imdb_id
    
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
    
    # получаем рейтинг IMDb от киноафиши
    rate = film.imdb if film.imdb else 0
    votes = film.imdb_votes if film.imdb_votes else 0
    imdb = get_imdb_id(film.idalldvd)
    
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
    
    if imdb_id:
        url = 'http://www.imdb.com/title/tt%s/' % imdb
    else:
        url = 'http://kinoafisha.ru/film/%s/' % film.id
        
    code = '[url=%s][img]http://kinoafisha.ru/upload/btn/%s/%s[/img][/url]' % (url, folder, output_name)
    
    return {'name': output_name, 'output_path': output_path, 'path': path, 'code': code}
    
    
