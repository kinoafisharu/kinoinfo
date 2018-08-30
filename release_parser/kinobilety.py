#-*- coding: utf-8 -*- 
import urllib
import urllib2
import re
import datetime
import time
import json

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt

from dateutil.relativedelta import relativedelta
from bs4 import BeautifulSoup

from base.models import *
from api.views import create_dump_file
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from release_parser.views import film_identification, distributor_identification, xml_noffilm, get_ignored_films
from release_parser.kinobit_cmc import get_source_data, create_sfilm, get_all_source_films, unique_func, checking_obj, sfilm_clean
from decors import timer
from release_parser.func import cron_success, give_me_cookie


@csrf_exempt
@never_cache
def main(request):
	data = str(request)
	return HttpResponse(json.dumps({}), content_type='application/json')
	row = str(request.REQUEST)

	data = '%s ***** %s ***** %s' % (data, row, request.FILES)

	d = str(datetime.datetime.now()).replace(' ', '')

	f = open('%s/%s_data.txt' % (settings.KINOBILETY_PATH, d), 'w')
	f.write(data)
	f.close()

	return HttpResponse(json.dumps({'err': [{"message":"Только POST запросы!"}]}, ensure_ascii=False), mimetype='application/json')
	return HttpResponse(json.dumps({}), content_type='application/json')
	'''

	apikey = request.GET.get('apikey')
	theater = request.GET.get('theater')

	if apikey and theater:
		opener = give_me_cookie()

		#url = 'http://erp.kinobilety.net/sync-films.php?theater=%s&apikey=%s' % (apikey, theater)
		#url = 'http://st.kinobilety.net/sync-films.php?theater=%s&apikey=%s' % (apikey, theater)
		url = 'http://kinobilety.net/sync-films.php?theater=%s&apikey=%s' % (apikey, theater)

		req = opener.open(urllib2.Request(url))
		return HttpResponse(str(req.read()))
		#return HttpResponse(json.dumps({}), content_type='application/json')
	else:
		return HttpResponse(json.dumps({'err': [{"message":"Нет параметра apikey или theatre"}]}, ensure_ascii=False), mimetype='application/json')
	'''
	
	'''
	if request.POST:
		data = str(request.POST)
		with open('%s/data.json' % settings.KINOBILETY_PATH, 'w') as f:
			f.write(data)
		return HttpResponse(json.dumps({}), content_type='application/json')
	else:
		return HttpResponse(json.dumps({'err': [{"message":"Только POST запросы!"}]}, ensure_ascii=False), mimetype='application/json')
	'''

    

