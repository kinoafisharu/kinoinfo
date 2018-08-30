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



@never_cache
def main(request):
    names = set(list(NamePerson.objects.filter(status=4, person__artist=True).values_list('name', flat=True)))
    alphabet_filter = sorted(set([uppercase(i.encode('utf-8').replace('-','')).decode('utf-8')[0] for i in names]))
    return render_to_response('music/main.html', {'alphabet_filter': alphabet_filter}, context_instance=RequestContext(request))


@never_cache
def artist_list(request, char):
    
    names = set(list(NamePerson.objects.filter(status=4, person__artist=True).values_list('name', flat=True)))
    alphabet = sorted(set([low(i.encode('utf-8').replace('-','')).decode('utf-8')[0] for i in names]))
    
    if low(char.encode('utf-8')).decode('utf-8') not in alphabet:
        char = alphabet[0]
    
    filter = {'name__name__istartswith': char, 'name__status': 4, 'artist': True}
    
    data = list(Person.objects.filter(**filter).values('name__name', 'id').order_by('name__name'))

    return render_to_response('music/artist_list.html', {'data': data, 'char': char}, context_instance=RequestContext(request))


@never_cache
def artist(request, id):
    try:
        person = Person.objects.select_related('country').get(pk=id, artist=True)
    except IndexError:
        raise Http404
    
    artist_name = NamePerson.objects.filter(person__pk=id, status=4)[0]
    
    form = OrganizationImageUploadForm()

    if request.POST:
        if request.user.is_superuser or request.is_admin:
            if 'artist_poster_add' in request.POST:
                if 'file' in request.FILES:
                
                    form = OrganizationImageUploadForm(request.POST, request.FILES)
                    if form.is_valid():

                        file_format = low(request.FILES['file'].name)
                        img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif)$', file_format)
                        if img_format:
                            
                            file_name = '%s_%s.%s' % (id, md5_string_generate(id), img_format[0])
                            poster_path = '%s/%s' % (settings.PERSONS_IMGS, file_name)
                            poster_path_db = poster_path.replace(settings.MEDIA_ROOT, '')

                            try:
                                img = Images.objects.get(status='0', person__pk=id)
                                created = False
                            except Images.DoesNotExist:
                                img = Images.objects.create(status='0')
                                created = True
                                
                            if img.file:
                                img_del = '%s%s' % (settings.MEDIA_ROOT, img.file)
                                os.remove(img_del)

                            file_obj = request.FILES['file'].read()
                            
                            with open(poster_path, 'wb') as f:
                                f.write(file_obj)
                        
                            resized = resize_image(1000, None, file_obj, 1500)
                            if resized:
                                resized.save(poster_path)

                            img.file = poster_path_db
                            img.save()
                        
                            if created:
                                person.poster.add(img)
                                
            elif 'artist_poster_del' in request.POST:
                img = Images.objects.filter(status='0', person__pk=id)
                if img:
                    img = img[0]
                    img_del = '%s%s' % (settings.MEDIA_ROOT, img.file)
                    os.remove(img_del)
                    img.delete()
            
        return HttpResponseRedirect(reverse('artist', kwargs={'id': id}))
        
    
    born_txt = 'дата основания' if person.is_group else 'дата рождения'
    
    sex = (
        (0, 'Нет'),
        (1, 'М'),
        (2, 'Ж'),
    )
    
    country = []
    if request.user.is_superuser:
        country = list(Country.objects.all().order_by('name').values('id', 'name'))

    images = {'main': None, 'second': [], 'slides': []}
    for i in Images.objects.filter(person__pk=id):
        if i.status == '0':
            images['main'] = i.file
        elif i.status == '1':
            images['second'].append(i.file)
        elif i.status == '2':
            images['slides'].append(i.file)

    members = []
    for i in person.musician.all():
        members.append(i.id)

    return render_to_response('music/artist.html', {'artist': person, 'sex': sex, 'country': country, 'born_txt': born_txt, 'images': images, 'form': form, 'artist_name': artist_name, 'members': members}, context_instance=RequestContext(request))


@never_cache
def composition_list(request, id):
    try:
        person = list(Person.objects.filter(pk=id, name__status=4, artist=True).values('name__name', 'id'))[0]
    except IndexError:
        raise Http404
    
    compositions_ids = list(CompositionPersonRel.objects.filter(person__id=id, type__name='исполнение').values_list('composition', flat=True))

    compositions = list(Composition.objects.filter(pk__in=compositions_ids, name__status=2).values('name__name', 'id').order_by('name__name'))

    return render_to_response('music/composition_list.html', {'artist': person, 'compositions': compositions}, context_instance=RequestContext(request))


@never_cache
def composition(request, id, comp_id):
    try:
        person = list(Person.objects.filter(pk=id, name__status=4, artist=True).values('name__name', 'id'))[0]
    except IndexError:
        raise Http404
    
    try:
        comp = list(CompositionPersonRel.objects.filter(person__id=id, composition__id=comp_id, type__name='исполнение').values_list('composition', flat=True))[0]
    except IndexError:
        raise Http404
    
    composition = Composition.objects.get(pk=comp)
    
    name = CompositionName.objects.get(status=2, composition=composition)
    
    mediafiles = composition.media.all()
    
    data_ids = [i.id for i in mediafiles]
    tags = {}
    
    for i in list(NewsTags.objects.filter(mediafiles__id__in=data_ids).values('mediafiles__id', 'name')):
        if tags.get(i['mediafiles__id']):
            tags[i['mediafiles__id']].append(i['name'])
        else:
            tags[i['mediafiles__id']] = [i['name']]

    content = []
    for i in mediafiles:
        itags = tags.get(i.id, [])
        content.append({'obj': i, 'tags': itags})

    return render_to_response('music/composition.html', {'artist': person, 'composition': composition, 'mediafiles': content, 'name': name, 'mtype': MUSIC_TYPE}, context_instance=RequestContext(request))


@never_cache
def track_download(request):
    if request.POST:
        if request.user.is_superuser:
            sign = request.POST.get('id')
            
            if sign:
                try:
                    obj = Mediafiles.objects.get(sign=sign)
                except Mediafiles.DoesNotExist:
                    pass
                else:

                    filename = BeautifulSoup(obj.original_file_name, from_encoding="utf-8").text.encode('utf-8')
                    
                    domain = request.current_site.domain
                    
                    with open('%s%s' % (settings.MEDIA_ROOT.rstrip('/'), obj.path), 'r') as f:
                        file_obj = f.read()
                        
                    response = HttpResponse(file_obj, mimetype='audio/mpeg')
                    response['Content-Disposition'] = 'attachment; filename=%s [%s].mp3' % (filename, domain)
                    return response

    raise Http404

