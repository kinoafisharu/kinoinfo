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
from unidecode import unidecode

from base.models import *
from kinoinfo_folder.func import del_separator, low
from release_parser.kinobit_cmc import get_source_data, afisha_dict
from release_parser.decors import timer
from base.func import org_build_create, get_org_street


REG_HOUSE = re.compile(r'\d+\/*-?\s?[а-яА-Я]?')
REG_PHONE = re.compile(r'\+?\d*?\(\d+\)?\d+')




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
    

#@timer
def get_orsk_organizations():
    
    source = ImportSources.objects.get(url='http://www.orgpage.ru/')

    org_phones = OrganizationPhones.objects.filter(organization__source_obj=source)
    phones_objs = {}
    for i in org_phones:
        phones_objs[i.phone] = i
    
    org_tags = OrganizationTags.objects.all()
    tags_objs = {}
    for i in org_tags:
        tags_objs[i.name] = i

    org_streets = Street.objects.all()
    org_streets_dict = {}
    for i in org_streets:
        org_streets_dict[i.slug.encode('utf-8')] = i
    
    source_ids = list(Organization.objects.filter(source_obj=source).values_list('source_id', flat=True))

    city_name = 'Орск'

    city = City.objects.get(name__name=city_name, name__status=1)
    '''
    # 1
    urls = [
        'http://www.orgpage.ru/орск_и_городской_округ_орск/администрация,_органы_исполнительной_власти/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/бизнес/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/досуг/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/жкх_и_благоустройство/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/культура/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/магазины/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/медицина/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/наука/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/образование/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/общественные_организации/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/посольства/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/промышленность/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/ремонт/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/организации_социального_комплекса/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/строительство/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/оптовая_торговля,_поставка_оборудования/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/транспорт/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/туризм_и_отдых/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/управление_и_контроль/',
        'http://www.orgpage.ru/орск_и_городской_округ_орск/услуги/',
    ]
    
    xml = ''
    
    count = 0
    for url in urls:
        req = urllib.urlopen(url)
        count += 1
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            try:
                div = data.find('div', {'class': 'r_alphabet'})
                for link in div.findAll('li'):
                    name = link.a.text.encode('utf-8')
                    link = link.a.get('href').encode('utf-8')
                    xml += '<url link="%s" name="%s"></url>' % (link, name)
            except AttributeError: pass
            
        if count % 5 == 0:
            time.sleep(random.uniform(1.0, 3.0))
            
    open('organizations_orsk.xml', 'w').write(str('<data>%s</data>' % xml))
    '''
    
    '''
    # 2
    with open('%s/organizations_orsk.xml' % settings.API_DUMP_PATH, 'r') as f:
        data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    xml = ''
    count = 0
    for i in data.findAll('url'):
        url = '%s?order=date&onpage=100' % i['link'].encode('utf-8')
        tag = i['name'].encode('utf-8')
        
        req = urllib.urlopen(url)
        count += 1
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            for a in data.findAll('a', {'class': 'name'}):
                name = a.text.encode('utf-8').replace('"', "'")
                link = a.get('href').encode('utf-8')
                
                xml += '<url link="%s" name="%s" tag="%s"></url>' % (link, name, tag)

        if count % 10 == 0:
            time.sleep(random.uniform(1.0, 3.0))
            
    open('organizations_orsk2.xml', 'w').write(str('<data>%s</data>' % xml))
    '''
    
    '''
    # 3
    with open('%s/organizations_orsk2.xml' % settings.API_DUMP_PATH, 'r') as f:
        data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    orgs = {}
    
    for i in data.findAll('url'):
        url = i['link'].encode('utf-8')
        name = i['name'].encode('utf-8')
        tag = i['tag'].encode('utf-8')
    
        if orgs.get(url):
            orgs[url]['tag'].append(tag)
        else:
            orgs[url] = {'tag': [tag], 'name': name, 'url': url}
    
    xml = ''
    
    for i in orgs.values():
        xml += '<url name="%s" url="%s">' % (i['name'], i['url'])
        for t in i['tag']:
            xml += '<tag name="%s"></tag>' % t
        xml += '</url>'

    open('organizations_orsk3.xml', 'w').write(str('<data>%s</data>' % xml))
    '''
    
    with open('%s/organizations_orsk3.xml' % settings.API_DUMP_PATH, 'r') as f:
        data = BeautifulSoup(f.read(), from_encoding="utf-8")
    
    count = 0
    for i in data.findAll('url'):
        count += 1
        
        url = i['url'].encode('utf-8')
        title = i['name'].encode('utf-8')
        
        uni = unidecode(i['name'])
        uni = re.findall(ur'[a-z0-9]+', low(uni))
        uni = '-'.join(uni) if uni else ''

        source_id = url.replace('http://www.orgpage.ru/орск_и_городской_округ_орск/', '').decode('utf-8')

        if source_id not in source_ids:
            req = urllib.urlopen(url)
            
            if req.getcode() == 200:
                data = BeautifulSoup(req.read(), from_encoding="utf-8")
                address = data.find('span', itemprop='streetAddress')
                if address:
                    address = address.text.encode('utf-8')
                    street_name, street_type, house = get_org_street(address.decode('utf-8'))
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
                        phones = []
                        for ph in data.findAll('span', itemprop='telephone'):
                            ph = ph.text.encode('utf-8').replace(' ','').replace('-','').replace('–','')
                            phone = REG_PHONE.findall(ph)
                            
                            if phone:
                                phone = phone[0].replace('(','').replace(')','')
                                phone = phone.decode('utf-8')
                                phone_obj = phones_objs.get(phone)
                                if not phone_obj:
                                    phone_obj = OrganizationPhones.objects.create(phone=phone)
                                    phones_objs[phone] = phone_obj
                                phones.append(phone_obj)
                                
                        site = None
                        site_block = data.find('li', id='list_sites')
                        if site_block:
                            site = site_block.find('a', itemprop='url')
                            if site:
                                site = site.text.encode('utf-8')
                        
                        email = None
                        email = data.find('span', itemprop='email')
                        if email:
                            email = email.text.encode('utf-8')


                        # МЕТКИ (КАТЕГОРИИ, ТЕГИ)
                        tags = []
                        for cat in i.findAll('tag'):
                            category_name = cat['name']
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
                        
                        org_obj.uni_slug = '%s-%s' % (uni, org_obj.id)
                        org_obj.save()
                        
                        for j in phones:
                            org_obj.phones.add(j)
                        
                        for j in tags:
                            org_obj.tags.add(j)
                        
                        org_obj.buildings.add(building_obj)
                        
                        source_ids.append(source_id)

        if count % 10 == 0:
            time.sleep(random.uniform(1.0, 3.0))
    
    return HttpResponse(str())



#@timer
def orsk_streets_fix(request):
    
    source = ImportSources.objects.get(url='http://www.orgpage.ru/')
    
    orgs = list(Organization.objects.filter(source_obj=source).values_list('id', flat=True))
    
    builds = Building.objects.select_related('street').filter(organization__id__in=orgs)
    
    
    for ind, i in enumerate(builds):
        if ind not in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19):
            st_type = i.street.name
            st = st_type
            
            street_name = st_type
            street_type = '1'

            #return HttpResponse(str(st_type.encode('utf-8')))

            if u'Набережная' in st_type or u'набережная' in st_type:
                street_name = st.encode('utf-8').replace('Набережная', '').replace('набережная', '').strip()
                street_type = '4'
            elif u'шоссе' in st_type or u'ш.' in st_type:
                street_name = st.encode('utf-8').replace('шоссе', '').replace('ш.', '').strip()
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
            elif u'пер.' in st_type or u'переулок' in st_type or u'Пер.' in st_type:
                street_name = st.encode('utf-8').replace('пер.', '').replace('Пер.', '').replace('переулок', '').strip()
                street_type = '2'
            elif u'пр-кт' in st_type or u'проспект' in st_type or u'Пр.' in st_type or u'просп.' in st_type:
                street_name = st.encode('utf-8').replace('пр-кт', '').replace('проспект', '').replace('Пр.', '').replace('просп.', '').strip()
                street_type = '6'
            elif u'ул.' in st_type or u'улица' or u'Ул.' in st_type:
                street_name = st.encode('utf-8').replace('ул.', '').replace('Ул.', '').replace('улица','').strip()
                street_type = '1'
                
            street_name = street_name.replace('ул.', '').replace('улица','').replace('Ул.', '').strip()
            
            name_slug = low(del_separator(street_name))
            
            i.street.name = street_name
            i.street.slug = name_slug
            i.street.type = street_type
            i.street.save()
            
    return HttpResponse(str())


#@timer
def org_slufy_names(request):
    orgs = Organization.objects.all()
    
    for i in orgs:
        lo = low(i.name.encode('utf-8'))
        name_slug = re.findall(ur'[a-zа-я0-9]', lo.decode('utf-8'))
        name_slug = ''.join(name_slug) if name_slug else ''
        i.slug = name_slug
        i.save()
        
    return HttpResponse(str())

