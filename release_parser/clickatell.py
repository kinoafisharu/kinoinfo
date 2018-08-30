#-*- coding: utf-8 -*- 
import urllib
import urllib2
import httplib2
import re
import datetime
import time

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q

from bs4 import BeautifulSoup
from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, cinema_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, afisha_dict
from decors import timer
from release_parser.func import cron_success


def clickatell_send_sms(to, text):
    url = 'http://api.clickatell.com/http/sendmsg?user=%s&password=%s&api_id=%s' % (
        settings.CLICKATELL_USER,
        settings.CLICKATELL_PSWD,
        settings.CLICKATELL_API_ID
    )
    
    url += '&to=%s&text=%s' % (to, text)
    
    resp, content = httplib2.Http().request(url, method='GET')
    if resp['status'] == '200':
        return content
    else:
        return resp


def clickatell_get_sms_status(id):
    url = 'http://api.clickatell.com/http/querymsg?user=%s&password=%s&api_id=%s&apimsgid=%s' % (
        settings.CLICKATELL_USER,
        settings.CLICKATELL_PSWD,
        settings.CLICKATELL_API_ID,
        id,
    )
    
    statuses = {
        '001': (False, 'Message unknown'),
        '002': (False, 'Message queued'),
        '003': (True, 'Delivered to gateway'),
        '004': (True, 'Received by recipient'),
        '005': (False, 'Error with message'),
        '006': (False, 'User cancelled message delivery'),
        '007': (False, 'Error delivering message'),
        '008': (True, 'OK'),
        '009': (False, 'Routing error'),
        '010': (False, 'Message expired'),
        '011': (False, 'Message queued for later delivery'),
        '012': (False, 'Out of credit'),
        '014': (False, 'Maximum MT limit exceeded'),

    }
    
    resp, content = httplib2.Http().request(url, method='GET')
    if resp['status'] == '200':
        status = re.findall(ur'Status: \d+', content)
        status = status[0].replace(u'Status: ', '').strip()
        status = statuses.get(status.encode('utf-8'))
        return status
    else:
        return resp




#@timer
def clickatell_send_msg():
    to = '61400558398'
    text = 'Ot M.Ivanova'
    result = clickatell_send_sms(to, text)
    
    #id = 'd486bde39abe5e080ffca6faf84279d7'
    #reuslt = clickatell_get_sms_status(id)
    
    return HttpResponse(str(result))





        
