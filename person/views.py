#-*- coding: utf-8 -*- 
import datetime
import time
import operator
import urllib2

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.core.cache import cache
from django import db

from api.models import *
from base.models import *
from kinoinfo_folder.func import low, del_separator, uppercase
from release_parser.func import get_imdb_id, actions_logger
from release_parser.decors import timer
from user_registration.func import only_superuser, org_peoples, is_film_editor
from user_registration.views import get_usercard
from movie_online.IR import check_int_rates_inlist


def person_name_create(name, lang, status):
    name_obj, name_created = NamePerson.objects.get_or_create(
        name = name,
        language_id = lang,
        status = status,
        defaults = {
            'name': name,
            'language_id': lang,
            'status': status,
        })
    return name_obj, name_created


def afisha_person_name_create(person, name, flag):
    name_obj, name_created = AfishaPersonsName.objects.using('afisha').get_or_create(
        person_id = person,
        name = name,
        name_cross = '',
        flag = flag,
        defaults = {
            'person_id': person,
            'name': name,
            'name_cross': '',
            'flag': flag,
        })
    return name_obj, name_created


def get_person_func(request, id):
    timer = time.time()

    try:
        person = Person.objects.select_related('country').get(kid=id)
    except Person.DoesNotExist:
        raise Http404
    
    names = {}
    par_name = ''
    for i in person.name.filter(language__name__in=('Русский', 'Английский'), status__in=(1,3)):
        if i.status == 1:
            names[i.language_id] = i.name
        else:
            par_name = i.name
    
    action = list(RelationFP.objects.filter(person__kid=id).values('action__name', 'films__kid'))
    
    actions_list = []
    actions = {}
    born_txt = 'Дата рождения: '
    
    sex = (
        (0, 'Нет'),
        (1, 'М'),
        (2, 'Ж'),
    )
    
    for i in action:
        act = i['action__name']
        if act == u'актер/актриса' or act == u'голоса':
            if person.male:
                act, born_txt = (u'актер', 'Родился: ') if person.male == 1 else (u'актриса', 'Родилась: ')
            else:   
                act = u'актер/актриса'
            
            if i['action__name'] == u'голоса':
                act += u' озвучания'
            
        actions_list.append(act)
        
        if actions.get(i['films__kid']):
            if not act in actions[i['films__kid']]:
                actions[i['films__kid']].append(act)
        else:
            actions[i['films__kid']] = [act]
    
    actions_list = sorted(set(actions_list))
    

    if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
        cache.delete('person__%s__xdata' % id)

    cached_page = ''
    is_cached = cache.get('person__%s__xdata' % id, 'nocaсhed')

    if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
        cached_page = False

        fnames = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__in=set(actions.keys()), status=1).order_by('film_id__year')
        
        rates = check_int_rates_inlist(set(actions.keys()))
        
        film_data = {}
        for i in fnames:
            if film_data.get(i.film_id_id):
                if i.type == 2:
                    film_data[i.film_id_id]['name_ru'] = i.name
                elif i.type == 1:
                    film_data[i.film_id_id]['name_en'] = i.name
            else:
                rate = rates.get(i.film_id_id)
                film_data[i.film_id_id] = {'name_ru': '', 'name_en': '', 'kid': i.film_id_id, 'year': i.film_id.year, 'rate': rate}
                if i.type == 1:
                    film_data[i.film_id_id]['name_en'] = i.name
                else:
                    film_data[i.film_id_id]['name_ru'] = i.name
        
        data = {}
        for kid, acts in actions.iteritems():
            film = film_data.get(kid)
            if film:
                for act in acts:
                    if data.get(act):
                        data[act].append(film)
                    else:
                        data[act] = [film,]
                    data[act] = sorted(data[act], key=operator.itemgetter('year'), reverse=True)
        
        xdata = []
        for k, v in data.iteritems():
            xdata.append({'title': k, 'data': v})
            
        xdata = sorted(xdata, key=operator.itemgetter('title'))
    
        cache.set('person__%s__xdata' % id, xdata, 60*60*2)
    else:
        xdata = is_cached
        cached_page = True


    extresid = list(Objxres.objects.using('afisha').filter(objtypeid=302, objpkvalue=id).values_list('extresid', flat=True))
    
    photos = Extres.objects.using('afisha').filter(extresid__in=extresid, filename__icontains='small', info__icontains='*t')
    photo = ''
    for i in photos:
        filename = i.filename.replace('_small','')
        photo = 'http://persons.nodomain.kinoafisha.ru/%s' % filename
    
    country = []
    if request.user.is_superuser:
        country = list(Country.objects.all().order_by('name').values('id', 'name'))
    
    born_edit = ''
    if person.born:
        edit_y, edit_m, edit_d = str(person.born).split('-')
        born_edit = '%s%s%s' % (edit_d, edit_m, edit_y)
    
    imdb_id = get_imdb_id(person.iid) if person.iid else None

    timer = '%5.2f' % (time.time()-timer)

    tmplt = 'person/person.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/person/person.html'

    return render_to_response(tmplt, {'person': person, 'imdb_id': imdb_id, 'names': names, 'par_name': par_name, 'photo': photo, 'actions_list': actions_list, 'film_data': xdata, 'actions': actions, 'born_txt': born_txt, 'country': country, 'sex': sex, 'born_edit': born_edit, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


@never_cache
def get_person(request, id):
    return get_person_func(request, id)
        

@never_cache
def get_person_list(request, char=None):
    
    names = set(list(NamePerson.objects.filter(status=1, person__kid__gt=0).values_list('name', flat=True)))
    alphabet = sorted(set([uppercase(i[0]) for i in names]))

    if not char or len(char) != 1:
        char = u'А'

    persons = list(Person.objects.filter(name__name__istartswith=char, name__status=1, kid__gt=0).values('kid', 'name__name', 'name__language').order_by('name__name'))
    
    persons_dict = {}
    for i in persons:
        persons_dict[i['kid']] = {'name': i['name__name'].strip(), 'id': i['kid']}
    
    persons = sorted(persons_dict.values(), key=operator.itemgetter('name'))
    
    return render_to_response('person/list.html', {'persons': persons, 'char': char, 'alphabet': alphabet}, context_instance=RequestContext(request))

@only_superuser
@never_cache
def delete_person(request):
    if request.POST:
        id = request.POST.get('del')
        if id:
            # Киноафиша
            person_afisha = AfishaPersons.objects.using('afisha').get(pk=id)
            PersonsRelationFilms.objects.using('afisha').filter(person_id__pk=id).delete()
            AfishaPersonsName.objects.using('afisha').filter(person_id__pk=id).delete()

            # Киноинфо
            person = Person.objects.filter(kid=id)
            RelationFP.objects.filter(person=person).delete()
            try:
                profile = Profile.objects.get(person=person)
                profile.personinterface.all().delete()
                profile.accounts.all().delete()
                profile.delete()
            except: pass

            person_afisha.delete()
            person.delete()

        return HttpResponseRedirect(reverse('get_person_list'))

    raise Http404




def person_create_func(name_ru, parental, name_en):
    person_obj = AfishaPersons.objects.using('afisha').create(
        birth_year = 0,
        birth_mounth = 0,
        birth_day = 0,
        male = 0,
        national = 0,
        country_id = 0,
        imdb = 0
    )

    person = Person.objects.create(kid = person_obj.id)

    names_list = [
        {'name': name_ru.strip(), 'status': 1, 'lang': 1}, 
        {'name': low(del_separator(name_ru.strip().encode('utf-8'))), 'status': 2, 'lang': 1}, 
        {'name': name_en.strip(), 'status': 1, 'lang': 2}, 
        {'name': low(del_separator(name_en.strip().encode('utf-8'))), 'status': 2, 'lang': 2}, 
        {'name': parental.strip(), 'status': 3, 'lang': 1},
    ]
    for i in names_list:
        if i['name']:
            if i['status'] == 1:
                try:
                    afisha_person_name_create(person_obj, i['name'], i['lang'])
                except db.backend.Database._mysql.OperationalError:
                    i['name'] = i['name'].encode('ascii', 'xmlcharrefreplace')
                    afisha_person_name_create(person_obj, i['name'], i['lang'])

            name, created = person_name_create(i['name'], i['lang'], i['status'])
            person.name.add(name)

    return person_obj


@never_cache
def create_person(request):
    film_editor = is_film_editor(request)
    if film_editor:
        if request.POST:
            name_ru = request.POST.get('person_new_name_ru','').strip()
            name_en = request.POST.get('person_new_name_en','').strip()
            parental = request.POST.get('person_new_parental_name','').strip()

            if name_ru or name_en:
                person_obj = person_create_func(name_ru, parental, name_en)

                profile = request.profile
                actions_logger(21, person_obj.id, profile, '1') # фильм Название
            
            return HttpResponseRedirect(reverse('get_person', kwargs={'id': person_obj.id}))
            
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404