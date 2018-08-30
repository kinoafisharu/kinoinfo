#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import random

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings

from bs4 import BeautifulSoup
from base.models import *
from kinoinfo_folder.func import del_separator, low
from release_parser.kinobit_cmc import get_source_data, afisha_dict
from decors import timer

REG_HOUSE = re.compile(r'\d+\/*-?\s?[а-яА-Я]?')
REG_PHONE = re.compile(r'\+?\d+?\(\d+\)?\d+')


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
        
        if re.findall(r'\d+', st):
            street_name = ''
            street_type = ''
            house = ''
        else:
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
            elif u'ул.' in st_type or u'улица' in st_type:
                street_name = st.encode('utf-8').replace('ул.', '').replace('улица','').strip()
                street_type = '1'
            elif u'пер.' in st_type or u'переулок' in st_type:
                street_name = st.encode('utf-8').replace('пер.', '').replace('переулок', '').strip()
                street_type = '2'
            street_name = street_name.replace('ул.', '').replace('улица','').strip()
    return street_name, street_type, house


def org_build_create(house, city, street_obj):
    build, created = Building.objects.get_or_create(
        number = house,
        city = city,
        street = street_obj,
        defaults = {
            'number': house,
            'city': city,
            'street': street_obj,
        }
    )
    return build
    
    
@timer
def get_0654_organizations():
   
    source = ImportSources.objects.get(url='http://m.0654.com.ua/')

    org_phones = OrganizationPhones.objects.filter(organization__source_obj=source)
    phones_objs = {}
    for i in org_phones:
        phones_objs[i.phone] = i
    
    org_tags = OrganizationTags.objects.filter(organization__source_obj=source)
    tags_objs = {}
    for i in org_tags:
        tags_objs[i.name] = i
    
    org_streets = Street.objects.all()
    org_streets_dict = {}
    for i in org_streets:
        org_streets_dict[i.slug.encode('utf-8')] = i
    
    
    source_ids = list(Organization.objects.filter(source_obj=source).values_list('source_id', flat=True))

    city_name = 'Ялта'

    city = City.objects.get(name__name=city_name, name__status=1)

    with open('%s/organizations.xml' % settings.API_DUMP_PATH, 'r') as f:
        data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    temp = {}
    
    count = 0
    for i in data.findAll('url'):
        count += 1
        
        url = i['value'].encode('utf-8')
        source_id = url.replace('http://m.0654.com.ua/catalog/full/', '').decode('utf-8')

        if source_id not in source_ids:
            req = urllib.urlopen(url)
            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")
                
                phones_temp = []
                phones = []
                streets = []
                tags = []
                email = None
                site = None
                
                # НАЗВАНИЕ
                title = data.find('h2').text.encode('utf-8').split('	')[0].strip()
                
                # ОПИСАНИЕ
                description = str(data.find('div', {'class': 'discription'})).replace('<div class="discription">', '').replace('</div>', '').strip()
                
                if not description:
                    description = None
                
                # АДРЕСА
                address = data.find('a', {'class': 'addr'})
                if address:
                    # если несколько адресов
                    address_temp = address.string.encode('utf-8').split(';')
                    for addr in address:
                        
                        street_name, street_type, house = get_org_street(addr)

                        if street_type:
                            if street_name:
                                street_slug = low(del_separator(street_name))
                                street_obj = org_streets_dict.get(street_slug)
                                if not street_obj:
                                    street_obj = Street.objects.create(name=street_name, slug=street_slug, type=street_type)
                                    org_streets_dict[street_slug] = street_obj
                            else:
                                street_obj = None
                                house = None
                                
                            building_obj = org_build_create(house, city, street_obj)
                            streets.append(building_obj)
                else:
                    building_obj = org_build_create(None, city, None)
                    streets.append(building_obj)
                    street_type = True
                
                if street_type:
                    # ТЕЛЕФОНЫ, САЙТ, МЭЙЛ
                    table = data.find('table', {'class': 'har'})
                    
                    for tr in table.findAll('tr'):
                        td = tr.findAll('td', limit=2)
                        if td[0].string == u'Телефон':
                            phones_temp = td[1].div.string.encode('utf-8')
                            phones_temp = phones_temp.replace(' ','').replace('-','').replace('–','').split(';')
                        elif td[0].string == u'Email адрес':
                            email = td[1].div.a.string.encode('utf-8')
                        elif td[0].string == u'Сайт':
                            site = td[1].div.a.string.encode('utf-8')
                    
                    for phone in phones_temp:
                        phone = REG_PHONE.findall(phone)
                        if phone:
                            phone = phone[0].decode('utf-8')
                            phone_obj = phones_objs.get(phone)
                            if not phone_obj:
                                phone_obj = OrganizationPhones.objects.create(phone=phone)
                                phones_objs[phone] = phone_obj
                            phones.append(phone_obj)
                    
                    
                    # МЕТКИ (КАТЕГОРИИ, ТЕГИ)
                    for cat in i.findAll('cat'):
                        category_name = cat['value']
                        category_obj = tags_objs.get(category_name)
                        if not category_obj:
                            category_obj = OrganizationTags.objects.create(name=category_name)
                            tags_objs[category_name] = category_obj
                        tags.append(category_obj)
                    
                    
                    org_obj = Organization.objects.create(
                        name = title,
                        site = site,
                        email = email,
                        note = description,
                        source_obj = source,
                        source_id = source_id,
                    )
                    
                    for j in phones:
                        org_obj.phones.add(j)
                    
                    for j in tags:
                        org_obj.tags.add(j)
                    
                    for j in streets:
                        org_obj.buildings.add(j)
                    
                    source_ids.append(source_id)
                    
                    if count % 10 == 0:
                        time.sleep(random.uniform(1.0, 3.0))

    return HttpResponse(str('finish'))
    

@timer
def get_bigyalta_organizations():
    REG_ADDR = re.compile(r'Адрес\:\s?.+')
    REG_TEL = re.compile(r'Телефон\:\s?.+')
    REG_MAIL = re.compile(r'E-mail\:\s?.+')
    REG_SITE = re.compile(r'Сайт\:\s?.+')
    
    source = ImportSources.objects.get(url='http://www.bigyalta.info/')

    org_phones = OrganizationPhones.objects.filter(organization__source_obj=source)
    phones_objs = {}
    for i in org_phones:
        phones_objs[i.phone] = i
    
    org_tags = OrganizationTags.objects.filter(organization__source_obj=source)
    tags_objs = {}
    for i in org_tags:
        tags_objs[i.name] = i
    
    org_streets = Street.objects.all()
    org_streets_dict = {}
    for i in org_streets:
        org_streets_dict[i.slug.encode('utf-8')] = i
    
    
    source_ids = list(Organization.objects.filter(source_obj=source).values_list('source_id', flat=True))

    city_name = 'Ялта'

    city = City.objects.get(name__name=city_name, name__status=1)
    
    with open('%s/organizations_bigyalta.xml' % settings.API_DUMP_PATH, 'r') as f:
        data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    count = 0
    for i in data.findAll('url'):
        count += 1
        
        url = i['value'].encode('utf-8')
        title = i['name'].encode('utf-8')
        
        source_id = url.replace('http://www.bigyalta.info/business/index.php?show=', '').decode('utf-8')

        if source_id not in source_ids:
            req = urllib.urlopen(url)
            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")
                div = data.find('div', style='float:left; width:670px; padding-right:10px;')
                div = div.text.encode('utf-8')
                
                addr = REG_ADDR.findall(div)
                if addr:
                    addr = addr[0].replace('Адрес:', '').replace('Ялта,', '').strip()
                    
                    street_name, street_type, house = get_org_street(addr.decode('utf-8'))
                    
                    if street_type:
                        if street_name:
                            street_slug = low(del_separator(street_name))
                            street_obj = org_streets_dict.get(street_slug)
                            if not street_obj:
                                street_obj = Street.objects.create(name=street_name, slug=street_slug, type=street_type)
                                org_streets_dict[street_slug] = street_obj
                        else:
                            street_obj = None
                            house = None
                            
                        building_obj = org_build_create(house, city, street_obj)
                        

                        # ТЕЛЕФОНЫ, САЙТ, МЭЙЛ
                        phones_temp = REG_TEL.findall(div)
                        
                        email = REG_MAIL.findall(div)
                        if email:
                            email = email[0].replace('E-mail:','').strip()
                            if not email:
                                email = None
                            
                        site = REG_SITE.findall(div)
                        if site:
                            site = site[0].replace('Сайт:','').strip()
                            if not site:
                                site = None
                            
                        phones = []
                        if phones_temp:
                            phones_temp = phones_temp[0].replace('Телефон:','').replace(' ','').replace('-','').replace('–','')
                            
                            phone = REG_PHONE.findall(phones_temp)
                            if phone:
                                phone = phone[0].decode('utf-8')
                                phone_obj = phones_objs.get(phone)
                                if not phone_obj:
                                    phone_obj = OrganizationPhones.objects.create(phone=phone)
                                    phones_objs[phone] = phone_obj
                                phones.append(phone_obj)

                        # МЕТКИ (КАТЕГОРИИ, ТЕГИ)
                        tags = []
                        for cat in i.findAll('tag'):
                            category_name = cat['value']
                            category_obj = tags_objs.get(category_name)
                            if not category_obj:
                                category_obj = OrganizationTags.objects.create(name=category_name)
                                tags_objs[category_name] = category_obj
                            tags.append(category_obj)
                        
                        
                        org_obj = Organization.objects.create(
                            name = title,
                            site = site,
                            email = email,
                            note = None,
                            source_obj = source,
                            source_id = source_id,
                        )
                        
                        for j in phones:
                            org_obj.phones.add(j)
                        
                        for j in tags:
                            org_obj.tags.add(j)
                        
                        org_obj.buildings.add(building_obj)
                        
                        source_ids.append(source_id)

        if count % 10 == 0:
            time.sleep(random.uniform(1.0, 3.0))
                        
    return HttpResponse(str('finish'))
    
    
    
