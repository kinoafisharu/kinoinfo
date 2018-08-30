# -*- coding: utf-8 -*- 
import operator
import datetime
import time

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.conf import settings

from dajaxice.decorators import dajaxice_register

from base.models import *
from kinoinfo_folder.func import low, del_separator, uppercase
from user_registration.func import *

@never_cache
@dajaxice_register
def get_track(request, id):
    #try:
        f = Mediafiles.objects.only('path').get(sign=id)
        path = '%s%s' % (settings.MEDIA_URL.rstrip('/'), f.path)
        swf = '%sbase/js/player/uppod.swf' % settings.STATIC_URL
        style = '%splayer/st/audio197-782-mini.txt' % settings.MEDIA_URL
        flash = {'major': 10, 'minor': 0, 'release': 0}
        width = 220
        height = 22
        
        return simplejson.dumps({'swf': swf, 'path': path, 'style': style, 'width': width, 'height': height, 'flash': flash})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@never_cache
@dajaxice_register
def set_track_name(request, id, title, mtype, tags):
    try:
        if request.user.is_superuser and title.strip():
            f = Mediafiles.objects.get(sign=id)
            f.original_file_name = title.strip()
            f.mtype = mtype
            f.save()
            
            for i in f.tags.all():
                f.tags.remove(i)
            
            for tag in tags:
                tag = tag.strip()
                if tag:
                    obj, created = NewsTags.objects.get_or_create(name=tag, defaults={'name': tag})
                    f.tags.add(obj)
        
            mtype_txt = f.get_mtype_display()

            return simplejson.dumps({'title': title, 'id': id, 'mtype': mtype_txt})
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def get_rel(request, id):
    #try:
        if request.user.is_superuser:

            #obj = Media

            comp = list(CompositionPersonRel.objects.filter(type__name='исполнение', person__name__status=4, person__artist=True, composition__media__sign=id, composition__name__status=2).values('composition__name__name', 'composition', 'person__name__name', 'person'))
            
            comp_list = []
            for i in comp:
                track = '%s - %s' % (i['person__name__name'], i['composition__name__name'])
                comp_list.append({
                    'cid': i['composition'],
                    'pid': i['person'],
                    'title': track,
                })

            comp_list = sorted(comp_list, key=operator.itemgetter('title'))

            names = set(list(NamePerson.objects.filter(status=4, person__artist=True).values_list('name', flat=True)))
            alphabet_filter = sorted(set([uppercase(i.encode('utf-8').replace('-','')).decode('utf-8')[0] for i in names]))

            


            return simplejson.dumps({'content': comp_list, 'alphabet_filter': alphabet_filter})
            
        return simplejson.dumps({})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))





@only_superuser
@never_cache
def track_upload(request):
    #try:
        import shutil
        from music.func import get_mp3_tags

        if request.user.is_superuser:
            if request.POST and request.is_ajax():
                files = request.FILES.getlist('upload')
                id = request.POST.get('tr_id')
                type = request.POST.get('tr_type')
                mp3 = {'good': [], 'bad': []}

                if id:
                    for i in files:

                        original_title = i.name.rstrip(u'.mp3')
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
                            media_obj = Mediafiles.objects.create(sign=sign, path=db_path, profile=request.profile, original_file_name=original_title, mtype=type)

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
                            
                            try:
                                comp_obj = Composition.objects.get(pk=id)
                            except Composition.DoesNotExist:
                                pass
                            else:
                                comp_obj.media.add(media_obj)
                            
                            mp3['good'].append(original_title)
                        else:
                            mp3['bad'].append(original_title)
                    
                    #request.session['music_upload_mp3'] = mp3
                    
                    return HttpResponse(simplejson.dumps({'good': mp3['good'], 'bad': mp3['bad'], 'id': id}), content_type='application/json')
                
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def get_artists_by_char(request, artist_char):
    #try:
        artists = list(Person.objects.filter(name__name__istartswith=artist_char, name__status=4, artist=True).values('name__name', 'id').order_by('name__name'))

        artist_select = artists[0]['id']

        # Фильтр по букве композиции
        names = set(list(Composition.objects.filter(compositionpersonrel__person__id=artist_select, name__status=2).values_list('name__name', flat=True)))
        alphabet_filter = sorted(set([uppercase(i.encode('utf-8')).decode('utf-8')[0] for i in names]))

        alphabet_filter.insert(0, "Нет")

        return simplejson.dumps({'artists': artists, 'alphabet': alphabet_filter})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def get_tracks_by_artist(request, artist):
    #try:
        names = set(list(Composition.objects.filter(compositionpersonrel__person__id=artist, name__status=2).values_list('name__name', flat=True)))
        alphabet_filter = sorted(set([uppercase(i.encode('utf-8')).decode('utf-8')[0] for i in names]))

        alphabet_filter.insert(0, "Нет")
        
        return simplejson.dumps({'alphabet': alphabet_filter})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

