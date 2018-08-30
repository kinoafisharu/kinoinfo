#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
import os

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.utils.html import escape
from django.db.models import Q

from unidecode import unidecode
import eyed3

from base.models import *


def get_file_size_func(filepath):
    filesize = ''
    try:
        filesize = os.path.getsize(filepath)
        if filesize < 1048576:
            filesize = '%.2f KB' % (float(filesize)/1024)
        else:
            filesize = '%.2f MB' % (float(filesize)/(1024*1024))
    except (OSError, IOError): pass
    return filesize


def get_mp3_tags(file):
    
    audiofile = eyed3.load(file)
    
    runtime = str(datetime.timedelta(seconds=audiofile.info.time_secs))
    rhour, rminute, rsec = runtime.split(':')
    
    if int(rhour):
        runtime = '%s:%s:%s' % (rhour, rminute, rsec)
    else:
        runtime = '%s:%s' % (rminute, rsec)
        
    size = get_file_size_func(file)
        
    data = {
        'artist': None, 
        'album': None, 
        'title': None, 
        'bitrate': audiofile.info.bit_rate_str, 
        'second': runtime, 
        'size': size,
    }
    if audiofile.tag:
        data['artist'] = audiofile.tag.artist
        data['album'] = audiofile.tag.album
        data['title'] = audiofile.tag.title
    return data
    
        
