#-*- coding: utf-8 -*- 
from django.utils import simplejson
from django.shortcuts import render_to_response
from dajaxice.decorators import dajaxice_register
from api.func import *
from user_registration.views import *

@dajaxice_register
def cout_mains(request):
    return render_to_response('api_main.html')