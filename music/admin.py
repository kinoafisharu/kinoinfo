#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
import os
from random import randrange
from collections import defaultdict

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.core.mail import get_connection, EmailMultiAlternatives
from django.utils.html import escape
from django.db.models import Q
from django.template.defaultfilters import date as tmp_date

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits, resize_image
from user_registration.views import get_usercard
from user_registration.func import *
from news.views import cut_description, create_news
from vladaalfimov.forms import *
from organizations.ajax import xss_strip2
from organizations.forms import OrganizationImageUploadForm, OrganizationImageSlideUploadForm
from kinoinfo_folder.func import low, del_separator, uppercase
from articles.views import pagination as pagi
from music.func import get_mp3_tags

@only_superuser
@never_cache
def admin_main(request):
    return render_to_response('music/admin_main.html', {}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def admin_media_del(request):
    if request.POST:
        if 'del' in request.POST and request.user.is_superuser:
            checker = request.POST.getlist('checker')
            for i in Mediafiles.objects.filter(pk__in=checker):
                path = '%s/%s' % (settings.MEDIA_ROOT, i.path)
                try: os.remove('%s/%s' % (settings.MEDIA_ROOT, i.path))
                except OSError: pass
                i.delete()
                
            ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
            return HttpResponseRedirect(ref)
    raise Http404


@only_superuser
@never_cache
def admin_media(request):
    
    char = ''

    if request.POST:
        char = request.POST.get('char')

    names = set(list(Mediafiles.objects.all().values_list('original_file_name', flat=True)))
    alphabet_filter = sorted(set([uppercase(i.encode('utf-8')).decode('utf-8')[0] for i in names]))
    
    if not char and alphabet_filter:
        char = request.session.get('filter_admin_music_char')
        if not char:
            char = alphabet_filter[0]

    data = Mediafiles.objects.select_related('profile').filter(original_file_name__istartswith=char)
    
    if not data:
        char = ''
    
    data_ids = [i.id for i in data]
    tags = {}
    
    for i in list(NewsTags.objects.filter(mediafiles__id__in=data_ids).values('mediafiles__id', 'name')):
        if tags.get(i['mediafiles__id']):
            tags[i['mediafiles__id']].append(i['name'])
        else:
            tags[i['mediafiles__id']] = [i['name']]
    
    
    content = []
    for i in data:
        itags = tags.get(i.id, [])
        content.append({'obj': i, 'tags': itags})
        
    request.session['filter_admin_music_char'] = char
    return render_to_response('music/admin_media.html', {'data': content, 'alphabet_filter': alphabet_filter, 'char': char, 'mtype': MUSIC_TYPE}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def admin_media_upload(request):
    '''
    import shutil
    
    if request.POST:
        mp3 = {'good': [], 'bad': []}
        
        files = request.FILES.getlist('files')
        
        for i in files:
            
            original_title = i.name
            file_format = low(i.name).split('.')[-1]
            
            if file_format == 'mp3':
                # генерация имени файла
                f_name = '%s.mp3' % sha1_string_generate(original_title.encode('utf-8'))
                
                # папка для временных файлов
                tmp_folder_path = '%s/mp3/tmp' % settings.MUSIC_PLAYER
                try: os.makedirs(tmp_folder_path)
                except OSError: pass
                
                # полный путь к временному файлу
                full_path = '%s/%s' % (tmp_folder_path, f_name)

                # записываем в БД
                db_path = full_path.replace(settings.MEDIA_ROOT, '')

                sign = sha1_string_generate()
                media_obj = Mediafiles.objects.create(sign=sign, path=db_path, profile=request.profile, original_file_name=original_title)

                # сохранение файла в папку
                with open(full_path, 'wb') as f:
                    f.write(i.read())

                # получение ID3 данных из mp3 файла
                fdata = get_mp3_tags(full_path)
                
                # получаю букву (название папки) исходя из названия композиции
                artist = fdata.get('artist')
                if artist:
                    slug = low(del_separator(artist.encode('utf-8')))
                else:
                    slug = low(del_separator(original_title.encode('utf-8')))
                    
                if slug:
                    folder_char = slug.decode('utf-8')[0]
                    folder_char = ord(folder_char)
                else:
                    folder_char = '-'
                
                # если нет папки (буквы), то создаем
                folder_path = '%s/mp3/%s' % (settings.MUSIC_PLAYER, folder_char)
                try: os.makedirs(folder_path)
                except OSError: pass
                
                # перемещаем временный файл в конечную папку (букву)
                shutil.move(full_path, folder_path)

                # обновляем запись в БД
                db_path = '%s/%s' % (folder_path.replace(settings.MEDIA_ROOT, ''), f_name)
                
                if artist:
                    media_obj.original_artist = artist
                    media_obj.original_album = fdata.get('album')
                    media_obj.original_title = fdata.get('title')
                    
                media_obj.bitrate = fdata.get('bitrate')
                media_obj.runtime = fdata.get('second')
                media_obj.size = fdata['size']
                media_obj.path = db_path
                media_obj.tmp = False
                media_obj.save()
                
                mp3['good'].append(original_title)
            else:
                mp3['bad'].append(original_title)
        
        request.session['music_upload_mp3'] = mp3
        return HttpResponseRedirect(reverse('admin_media_upload'))

    mp3 = request.session.get('music_upload_mp3')
    request.session['music_upload_mp3'] = {'good': [], 'bad': []}
    '''
    
    char = u'Нет'
    artist_char = ''
    artist_select = ''
    
    if request.POST:
        char = request.POST.get('char')
        artist_char = request.POST.get('artist_char')
        artist_select = request.POST.get('artist_select')
    
    
    # Фильтр по букве артиста
    artist_names = set(list(NamePerson.objects.filter(status=4, person__artist=True).values_list('name', flat=True)))
    artist_alphabet = sorted(set([uppercase(i.encode('utf-8').replace('-','')).decode('utf-8')[0] for i in artist_names]))
    
    if not artist_char and artist_alphabet:
        artist_char = request.session.get('filter_admin_track_art_char')
        if not artist_char:
            artist_char = artist_alphabet[0]
    
    artists = list(Person.objects.filter(name__name__istartswith=artist_char, name__status=4, artist=True).values('name__name', 'id').order_by('name__name'))

    if not artist_select:
        artist_select = artists[0]['id']


    
    # Фильтр по букве композиции
    names = set(list(Composition.objects.filter(compositionpersonrel__person__id=artist_select, name__status=2).values_list('name__name', flat=True)))
    alphabet_filter = sorted(set([uppercase(i.encode('utf-8')).decode('utf-8')[0] for i in names]))
    
    alphabet_filter.insert(0, u"Нет")
    

    filter = {'type__name': 'исполнение', 'person__id': artist_select, 'composition__name__status': 2}
    if char != u'Нет':
        filter['composition__name__name__istartswith'] = char
        
    data = list(CompositionPersonRel.objects.filter(**filter).values('composition__name__name', 'composition', 'person__name__name', 'person'))
    
    comp_list = []
    for i in data:
        track = '%s - %s' % (i['person__name__name'], i['composition__name__name'])
        comp_list.append({
            'cid': i['composition'],
            'pid': i['person'],
            'title': track,
        })
    
    if comp_list:
        comp_list = sorted(comp_list, key=operator.itemgetter('title'))
    else:
        char = ''
        
    request.session['filter_admin_track_char'] = char
    request.session['filter_admin_track_art_char'] = artist_char
    return render_to_response('music/admin_media_upload.html', {'data': comp_list, 'alphabet_filter': alphabet_filter, 'char': char, 'mtype': MUSIC_TYPE, 'artist_alphabet': artist_alphabet, 'artist_char': artist_char, 'artists': artists, 'artist_select': artist_select}, context_instance=RequestContext(request))


