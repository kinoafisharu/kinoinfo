#-*- coding: utf-8 -*- 
import urllib
import datetime

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache

from bs4 import BeautifulSoup
from base.models import *
from user_registration.func import only_superuser
from decors import timer
from release_parser.func import cron_success



@timer
def get_currency_rate():

    source = ImportSources.objects.get(url='http://cbrf.magazinfo.ru/')
    
    data = [
        {
        'url': '%srur/USD' % source.url,
        'cur_1': '4', # рубль
        'cur_2': '1', # доллар
        },
        {
        'url': '%srur/AUD' % source.url,
        'cur_1': '4', # рубль
        'cur_2': '3', # австр.доллар
        },
    ]
    
    for i in data:
        req = urllib.urlopen(i['url'])
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            table = data.find('table', border="1", cellspacing="0", cellpadding="5")
            tr = table.findAll('tr', limit=2)
            td = tr[1].findAll('td') 
            cur_day, cur_month, cur_year = td[0].text.split('.')
            cur_date = datetime.datetime(int(cur_year), int(cur_month), int(cur_day))
            value = td[1].text.encode('utf-8')

            obj, created = CurrencyRate.objects.get_or_create(
                currency = i['cur_1'],
                by_currency = i['cur_2'],
                defaults = {
                    'currency': i['cur_1'],
                    'by_currency': i['cur_2'],
                    'country_id': 2,
                    'date': cur_date,
                    'value': value,
                })
            
            if obj:
                obj.value = value
                obj.date = cur_date
                obj.save()
    
        get_currency_rate_NZD()

    cron_success('html', source.dump, 'currency_rate', 'Курс валют') 



#@timer
def get_currency_rate_NZD():

    cur_date = datetime.datetime.today().date()

    source_url = 'http://www.finanz.ru/'
    
    data = [
        {
        'url': '%svalyuty/NZD-RUB' % source_url,
        'cur_1': '4', # рубль
        'cur_2': '6', # НЗ доллар
        },
    ]
    
    for i in data:
        req = urllib.urlopen(i['url'])
        if req.getcode() == 200:
            data = BeautifulSoup(req.read(), from_encoding="utf-8")
            data = data.find('div', {'class': "pricebox content_box"})
            data = data.find('div', {'class': "content"})
            data = data.findAll('table', limit=1)[0]

            value = data.findAll('th', limit=1)[0].text.encode('utf-8').replace('RUB','').replace(',','.').strip()

            obj, created = CurrencyRate.objects.get_or_create(
                currency = i['cur_1'],
                by_currency = i['cur_2'],
                defaults = {
                    'currency': i['cur_1'],
                    'by_currency': i['cur_2'],
                    'country_id': 2,
                    'date': cur_date,
                    'value': value,
                })
            
            if obj:
                obj.value = value
                obj.date = cur_date
                obj.save()
