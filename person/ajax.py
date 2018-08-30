# -*- coding: utf-8 -*- 
import datetime
import operator

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.template.defaultfilters import date as tmp_date
from django.utils.html import strip_tags, escape
from django.db.models import Q

from dajaxice.decorators import dajaxice_register

from api.models import *
from base.models import *
from kinoinfo_folder.func import low, capit, uppercase, del_separator
from user_registration.func import org_peoples, is_film_editor
from release_parser.func import actions_logger


@dajaxice_register
def country(request, id, country):
    #try:
    if request.user.is_superuser or request.is_admin:
        country_obj = Country.objects.get(pk=country)
        person = Person.objects.get(pk=id)
        person.country = country_obj
        person.save()
        
        if person.kid and request.user.is_superuser:
            country_afisha = AfishaCountry.objects.using('afisha').get(pk=country_obj.kid)
            person_afisha = AfishaPersons.objects.using('afisha').get(pk=person.kid)
            
            act = None
            if person_afisha.country_id:
                if country_afisha.id != person_afisha.country_id:
                    act = '2'
            else:
                act = '1'
            
            actions_logger(23, id, request.profile, act) # персона Страна
            
            person_afisha.country = country_afisha
            person_afisha.save()
        
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def country_city(request, id, country, city):
    #try:
    
    person_id = request.user.get_profile().person_id
    
    if id == '0':
        id = person_id
    
    access = False
    owner = False
    if person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True    
    
    if access:
        country_obj = Country.objects.get(pk=country)
        city_name = NameCity.objects.get(pk=city)
        city_obj = City.objects.get(name=city_name, country=country)

        person = Person.objects.get(pk=id)
        person.country = country_obj
        person.city = city_obj
        person.save()

        return simplejson.dumps({'status': owner, 'content': city_name.name})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def names(request, id, name, par, en):
    try:
        from person.views import person_name_create

        access = False
        owner = False
        if request.profile.person_id == int(id):
            access = True
            owner = True
        elif request.user.is_superuser or request.is_admin:
            access = True
            
        if access:
            name = escape(strip_tags(name)).encode('utf-8').strip()
            par = escape(strip_tags(par)).encode('utf-8').strip()
            en = escape(strip_tags(en)).encode('utf-8').strip()

            slug_ru = low(del_separator(name))
            slug_en = low(del_separator(en))
            
            names = [
                {'name': name, 'lang': 1, 'status': 1},
                {'name': slug_ru, 'lang': 1, 'status': 2},
                {'name': en, 'lang': 2, 'status': 1},
                {'name': slug_en, 'lang': 2, 'status': 2},
                {'name': par, 'lang': 1, 'status': 3},
            ]

            person = Person.objects.get(pk=id)
            en_name = None
            new_name = None
            par_name = None
            act1 = None
            act2 = None
            
            if person.kid:
                for i in names:
                    if i['name']:
                        try:
                            person_name = person.name.get(status=i['status'], language__id=i['lang'])
                        except NamePerson.DoesNotExist:
                            person_name = None
                        except NamePerson.MultipleObjectsReturned:
                            person_name = None
                            for p in person.name.filter(status=i['status'], language__id=i['lang']):
                                if person_name:
                                    p.delete()
                                else:
                                    person_name = p

                        name_obj, created = person_name_create(i['name'], i['lang'], i['status'])
                        
                        if person_name:
                            if person_name != name_obj:
                                person.name.remove(person_name)
                                person.name.add(name_obj)
                                if not act1:
                                    act1 = '2'
                        else:
                            person.name.add(name_obj)
                            act1 = '1'

                        if i['status'] == 1 and i['lang'] in (1,2):
                            AfishaPersonsName.objects.using('afisha').filter(person_id__id=person.kid, flag=i['lang']).update(name=i['name'])
                        
                actions_logger(21, id, request.profile, act1) # персона Имя

            else:
                person.name.clear()
                act1 = '3'
                if name:
                    for i in names[0:1]:
                        if i['name']:
                            name_obj, created = person_name_create(i['name'], i['lang'], i['status'])
                            person.name.add(name_obj)
                            
                    act1 = '2'
                actions_logger(21, id, request.profile, act1) # персона Имя

            
            return simplejson.dumps({'status': owner, 'content': name})
        
    except Exception as e:
        return simplejson.dumps({'status': 'error', 'content': '%s * (%s)' % (dir(e), e.args)})



@dajaxice_register
def person_name_detect(request, ru, en):
    try:
        film_editor = is_film_editor(request)
        
        if film_editor:
            name = escape(strip_tags(ru)).encode('utf-8').strip()
            en = escape(strip_tags(en)).encode('utf-8').strip()

            slug_ru = low(del_separator(name))
            slug_en = low(del_separator(en))
            

            queries = []
            if name:
                queries.append(Q(name__icontains=slug_ru, status=1))
            if en:
                queries.append(Q(name__icontains=en, status=1))

            query = queries.pop()
            for item in queries:
                query |= item

            data = list(NamePerson.objects.filter(query, language__id__in=(1,2), person__kid__gt=0).values('language', 'person__kid', 'name'))

            names = {}
            for i in data:
                if not names.get(i['person__kid']):
                    names[i['person__kid']] = {'ru': '', 'en': '', 'id': i['person__kid']}
                if i['language'] == 1:
                    names[i['person__kid']]['ru'] = i['name']
                elif i['language'] == 2:
                    names[i['person__kid']]['en'] = i['name']
            
            names = sorted(names.values(), key=operator.itemgetter('ru'))

            txt = ''
            for i in names:
                txt += u'<div style="border-bottom:1px solid #CCC; padding:5px; background:#EBEBEB; min-width: 300px;"><a href="http://kinoinfo.ru/person/%s/" target="_blank">%s / %s</a></div>' % (i['id'], i['ru'], i['en'])
            if txt:
                txt = u'В базе есть похожие персоны:<br />%s' % txt

            return simplejson.dumps({
                'status': True,
                'content': txt,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def imdb_person_search(request, pid, name, exist):
    try:
        from person.views import person_name_create
        from release_parser.imdb import imdb_person_searching

        if request.user.is_superuser:
            name = escape(strip_tags(name)).encode('utf-8').strip()
            slug = low(del_separator(name))

            person = Person.objects.get(pk=pid)

            # если не было имени (en), то создаю
            if not exist:
                if name:
                    exist = True

                    person_names = person.name.all()

                    names = [
                        {'name': name, 'status': 1},
                        {'name': slug, 'status': 2},
                    ]

                    for i in names:
                        name_obj, created = person_name_create(i['name'], i['status'], 2)
                        if name_obj not in person_names:
                            person.name.add(name_obj)

            if exist:
                result = imdb_person_searching(name)
                txt = ''

                for i in result:

                    txt += '<div style="border-bottom:1px solid #CCC; padding:5px; background:#EBEBEB; min-width: 300px;"><a href="http://www.imdb.com%s" target="_blank">%s</a> <i>%s</i><br /> <input type="button" value="Выбрать" id="%s" class="imdb_person_list_select" /></div>' % (i['link'].encode('utf-8'), i['title'], i['details'], i['id'])
                
            
                txt += '<br /><div>Или укажите ссылку на страницу персоны IMDb:<br /><input type="text" value="" size="40" class="imdb_person_url" /> <input type="button" value="Искать" class="imdb_person_list_select" /><input type="hidden" value="%s" id="pid" /></div>' % person.id
        
                return simplejson.dumps({
                    'status': True,
                    'content': txt,
                    'query': name,
                })

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def imdb_person_data(request, pid, id):
    try:
        from release_parser.imdb import imdb_person_data
        from news.views import cut_description

        if request.user.is_superuser:
            # киноинфо
            person = Person.objects.get(pk=pid)
            person.iid = id
            person.save()
            # киноафиша
            afisha_person = AfishaPersons.objects.using('afisha').get(pk=person.kid)
            afisha_person.imdb = id
            afisha_person.save()

            result = imdb_person_data(id)

            country_exist = person.country_id if person.country else 0

            try:
                country = Country.objects.get(name_en=result['country'])
                result['country'] = country.id
            except Country.DoesNotExist:
                result['country'] = country_exist

            sex = [
                {'id': 0, 'name': 'Нет'},
                {'id': 1, 'name': 'М'},
                {'id': 2, 'name': 'Ж'},
            ]

            result['url'] = 'http://www.imdb.com/name/nm%s/bio' % id
            result['birth'] = str(result['birth'])
            result['countries'] = list(Country.objects.all().values('id', 'name').order_by('name'))
            result['person_sex'] = person.male
            result['sex'] = sex
            result['short_bio'] = cut_description(result['bio'], True, 400)
            result['status'] = True
            result['pid'] = pid
            result['imdb_id'] = id
            
            return simplejson.dumps(result)

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def imdb_person_save(request, pid, place, birth, bio, sex):
    try:
        if request.user.is_superuser:
            
            person = Person.objects.get(pk=pid)
            person_afisha = AfishaPersons.objects.using('afisha').get(pk=person.kid) #

            if place:
                country = Country.objects.get(pk=place)
                person.country = country
                person.city = None
                person_afisha.country_id = country.kid #

            if birth:
                person.born = birth
                year, month, day = birth.split('-') #
                person_afisha.birth_year = int(year) #
                person_afisha.birth_mounth = int(month) #
                person_afisha.birth_day = int(day) #

            if sex:
                person.male = sex
                person_afisha.male = sex #

            person.save()
            person_afisha.save() #

            return simplejson.dumps({'status': True})

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def gender(request, id, gender):
    #try:
    access = False
    owner = False
    if request.profile.person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True
        
    if access:
        person = Person.objects.get(pk=id)
        
        act = None
        if person.male:
            if int(gender) != person.male:
                act = '2' if int(gender) else '3'
        else:
            if int(gender):
                act = '1'
        
        person.male = gender
        person.save()
        
        if person.kid and request.user.is_superuser:
            person_afisha = AfishaPersons.objects.using('afisha').filter(pk=person.kid).update(male=gender)
  
            actions_logger(24, id, request.profile, act) # персона Пол
  
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def born(request, id, born):
    #try:
    if request.user.is_superuser or request.is_admin:
        if born:
            year, month, day = born.split('-')
            born = datetime.datetime(int(year), int(month), int(day))
        else:
            born = None
            day = 0
            month = 0
            year = 0

        person = Person.objects.get(pk=id)
        
        act = None
        if person.born:
            if born != person.born:
                act = '2' if born else '3'
        else:
            if born:
                act = '1'
                
        person.born = born
        person.save()

        if person.kid:
            person_afisha = AfishaPersons.objects.using('afisha').filter(pk=person.kid).update(
                birth_year = year,
                birth_mounth = month,
                birth_day = day
            )
        
            actions_logger(22, id, request.profile, act) # персона Дата рождения
        
        born = tmp_date(born, "d E Y г.") if born else ''

        return simplejson.dumps({'status': True, 'content': born})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def borned(request, id, year, month, day):
    #try:
    access = False
    owner = False
    if request.profile.person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True
        
    if access:
        try:
            born = datetime.datetime(int(year), int(month), int(day))
        except ValueError:
            born = ''
            
        if born:
            person = Person.objects.get(pk=id)
            person.born = born
            person.save()

            born = tmp_date(born, "d E Y г.") if born else ''

        return simplejson.dumps({'status': True, 'content': born})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def email(request, id, email):
    #try:
    access = False
    owner = False
    if request.user.get_profile().person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True    
    
    if access:
        email = escape(strip_tags(email))
        person = Person.objects.get(pk=id)
        exists = Accounts.objects.filter(email=email, auth_status=True, profile__person=person).count()
        if exists:
            user = User.objects.get(profile__person=person)
            user.email = email
            user.save()
            
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_person_email(request, id, val):
    #try:
        #from user_registration.func import md5_string_generate
        
        if request.user.is_superuser or request.is_admin:
            access = True    
        
        if access:
            msg = ''
            email = val.strip()
            profile = Profile.objects.get(person__id=id)

            try:
                acc = Accounts.objects.get(login=email)
                try:
                    p = Profile.objects.get(accounts=acc)
                    if profile != p:
                        msg = 'E-mail assigned to another person'
                    else:
                        msg = 'E-mail already exist'
                except Profile.DoesNotExist:
                    profile.accounts.add(acc)
            except Accounts.DoesNotExist:
                #code = md5_string_generate('%s--%s' % (email, id))
                acc = Accounts.objects.create(login=email, validation_code=None, auth_status=True, email=email)
                profile.accounts.add(acc)
            
            return simplejson.dumps({'msg': msg})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def show_profile(request, id, show):
    #try:
    access = False
    owner = False
    if request.user.get_profile().person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True    

    if access:
        person = Person.objects.get(pk=id)
        user = Profile.objects.get(person=person)
        user.show_profile = show
        user.save()
        
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def set_phone(request, id, show, num):
    #try:
    access = False
    owner = False
    if request.user.get_profile().person_id == int(id):
        access = True
        owner = True
    elif request.user.is_superuser or request.is_admin:
        access = True    

    if access:
        person = Person.objects.get(pk=id)
        user = Profile.objects.get(person=person)
        show = True if show == '1' else False 
        user.phone_visible = show
        user.phone = num
        user.save()
        
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def nickname(request, id, nick):
    #try:
        from organizations.ajax import xss_strip2
        
        id = int(id)

        access = False
        owner = False
        profile = request.profile
        if profile.person_id == id:
            access = True
            owner = True
        elif request.user.is_superuser or request.is_admin:
            access = True    

        # если юзер неавторизован
        if not profile.auth_status:
            return simplejson.dumps({'status': False})

        if access:
            nick = xss_strip2(nick.strip())
            if nick:
                # проверка на существующий ник
                exist = False
                try:
                    user = User.objects.get(first_name=nick, profile__auth_status=True)
                    if user.id != id:
                        exist = True
                except User.DoesNotExist: pass

                if exist:
                    return simplejson.dumps({'status': True, 'nick_err': False, 'nick_exist': True})
                else:
                    pass
                    #user = User.objects.get(first_name=nick, profile__auth_status=True)
                    #RegisteredUsers.objects.get(

                    
                
                if not exist:
                    User.objects.filter(profile__person__id=id).update(first_name=nick)
                    return simplejson.dumps({'status': True, 'nick_err': False, 'nick_exist': False, 'content': nick})

                return simplejson.dumps({'status': True, 'nick_err': False, 'nick_exist': False, 'content': nick})
            else:
                return simplejson.dumps({'status': True, 'nick_err': True, 'nick_exist': False})

    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def set_artist_type(request, id, atype):
    #try:
        if request.user.is_superuser or request.is_admin:
            person = Person.objects.get(pk=id)
            group = False if atype == '1' else True
            person.is_group = group
            person.save()
        return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
