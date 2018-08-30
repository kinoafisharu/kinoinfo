#-*- coding: utf-8 -*-
import urllib
import re
import os
import datetime
import time
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils import simplejson
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models_dic import *
from base.models_choices import *
from base.models import *
from organizations.forms import *
from kinoinfo_folder.func import del_separator, low, capit
from user_registration.func import only_superuser, only_superuser_or_admin, md5_string_generate
from articles.views import pagination as pagi
from movie_online.debug import debug_logs

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned




@only_superuser_or_admin
@never_cache
def organizations(request):
    """
    Список всех организаций
    """
    tags = set(list(Organization.objects.all().values_list('tags', flat=True)))
    tags = OrganizationTags.objects.filter(pk__in=tags).order_by('name')

    if request.POST:
        tag = int(request.POST['tags'])
    else:
        tag = request.session.get('filter_organizations_show__tag', tags[0].id)


    orgs = Organization.objects.filter(tags__id=tag)
    count = Organization.objects.all().count()
    cat_count = orgs.count()

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, orgs, 12)

    request.session['filter_organizations_show__tag'] = tag
    return render_to_response('organizations/organizations_show.html', {'p': p, 'page': page, 'count': count, 'cat_count': cat_count, 'tags': tags, 'tag': tag}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def organization_details(request, id):

    org = Organization.objects.select_related('tags').get(pk=id)

    return render_to_response('organizations/organization_details.html', {'org': org}, context_instance=RequestContext(request))


'''
@only_superuser_or_admin
@never_cache
def admin_organization_add(request):

    if request.POST:
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_organization"))
    else:
        form = OrganizationForm()

    return render_to_response('organizations/organization_add.html', {'form': form}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def admin_organization_note(request):
    org = Organization.objects.exclude(note=None)
    for i in org:
        data = BeautifulSoup(i.note, from_encoding="utf-8")
        i.note = data.text
        i.save()
    return HttpResponse(str(org.count()))


@only_superuser_or_admin
@never_cache
def admin_organization_phones(request):
    org = OrganizationPhones.objects.all()
    del_phones = []
    for i in org:
        phone = i.phone.replace('(','').replace(')','').replace('+380','')
        if len(phone) > 10:
            phone = phone.lstrip('0')

        try:
            phone = int(phone)
            if len(str(phone)) > 10 or len(str(phone)) < 8:
                del_phones.append(i)
            else:
                i.phone = phone
                i.save()
        except ValueError:
            del_phones.append(i)

    orgs = Organization.objects.filter(phones__in=del_phones)

    for i in orgs:
        for p in del_phones:
            i.phones.remove(p)

    for i in del_phones:
        i.delete()

    return HttpResponse(str(len(del_phones)))


@only_superuser_or_admin
@never_cache
def admin_organization_sites(request):
    org = Organization.objects.exclude(site=None)

    for i in org:
        site = i.site
        if u'@' in site:
            i.site = None
            i.email = site
            i.save()
        elif u'в разработке' in site:
            i.site = None
            i.save()
        elif u'http://' not in site:
            i.site = 'http://%s' % site
            i.save()

    return HttpResponse(str(org.count()))


@only_superuser_or_admin
@never_cache
def admin_organization_edit(request, id):
    """
    Редактирование организации TEMP
    """
    org = get_object_or_404(Organization, pk=id)

    phones = []
    for i in org.phones.all():
        phones.append({'id': i.id, 'phone': i.phone})

    phones = sorted(phones, key=operator.itemgetter('id'))

    tags = OrganizationTags.objects.all()
    tags_objs = {}
    for i in tags:
        tags_objs[i.name] = i

    tags_error = False
    o_tags_list = []

    if request.POST:
        form = OrganizationForm(request.POST)

        if form.is_valid():

            # ОРГАНИЗАЦИЯ
            name = form.cleaned_data['name']
            ownership = form.cleaned_data['ownership']

            # метки
            tags_list = []
            for i in range(6):
                i = i + 1
                ta = request.POST.get('tag%s' % i)
                if ta:
                    t_list = (ta, capit(ta), low(ta))
                    tag_obj = None
                    for t in t_list:
                        tag_obj = tags_objs.get(t)
                        if tag_obj:
                            break

                    if not tag_obj:
                        tag_obj = OrganizationTags.objects.create(name=t_list[1])

                    tags_list.append(tag_obj)

            if not tags_list:
                tags_error = True
                for i in range(6):
                    i = i + 1
                    o_tags_list.append({'id': 99999999 + i, 'name': ''})
            else:

                org_tags = [i for i in org.tags.all()]
                for i in org_tags:
                    org.tags.remove(i)

                for i in tags_list:
                    org.tags.add(i)


                org.name = name

                if not ownership:
                    ownership = None

                org.ownership = ownership


                # АДРЕС
                city = form.cleaned_data['city']
                building = form.cleaned_data['buildings']
                street = form.cleaned_data['street']
                street_type = form.cleaned_data['street_type']

                if not building:
                    building = None

                if street:
                    street_slug = low(del_separator(street.encode('utf-8')))
                    street_obj, st_created = Street.objects.get_or_create(
                        slug = street_slug,
                        type = street_type,
                        defaults = {
                            'name': street,
                            'slug': street_slug,
                            'type': street_type,
                        })

                building_obj, bu_created = Building.objects.get_or_create(
                    city = city,
                    street = street_obj,
                    number = building,
                    defaults = {
                        'city': city,
                        'street': street_obj,
                        'number': building,
                    })

                org_buildings = [i for i in org.buildings.all()]
                if building_obj not in org_buildings:
                    for i in org_buildings:
                        org.buildings.remove(i)
                    org.buildings.add(building_obj)


                # КОНТАКТЫ
                email = form.cleaned_data['email']
                site = form.cleaned_data['site']

                phones = []
                phones_del = []
                for i in org.phones.all():
                    phones.append(request.POST.get('phone_%s' % i.id))
                    phones_del.append(i)

                phones_objs = []
                for i in phones:
                    if i:
                        ph, created = OrganizationPhones.objects.get_or_create(
                            phone = i,
                            defaults = {
                                'phone': i,
                            })
                        phones_objs.append(ph)

                for i in phones_del:
                    org.phones.remove(i)

                for i in phones_objs:
                    org.phones.add(i)


                note = form.cleaned_data['note']

                room_num = form.cleaned_data['room_num']
                room_type = form.cleaned_data['room_type']

                if not room_num:
                    room_num = None
                    room_type = None

                org.email = email
                org.site = site
                org.room_type = room_type
                org.note = note

                org.edited = datetime.datetime.now()
                org.profile = request.user.get_profile()

                org.save()

                return HttpResponseRedirect(reverse("organization_details", kwargs={'id': id}))
    else:

        address = org.buildings.all()[0]

        city = None
        for i in address.city.name.all():
            if i.status == 1:
                city = i

        o_tags = org.tags.all()

        empty_tags = 6 - o_tags.count()

        for i in o_tags:
            o_tags_list.append({'id': i.id, 'name': i.name})

        o_tags_list = sorted(o_tags_list, key=operator.itemgetter('name'))

        for i in range(empty_tags):
            i = i + 1
            o_tags_list.append({'id': 99999999 + i, 'name': ''})

        form = OrganizationForm(
            initial = {
                'name': org.name,
                'site': org.site,
                'email': org.email,
                'note': org.note,
                'room_num': org.room_num,
                'room_type': org.room_type,
                'city': city,
                'buildings': address.number,
                'street': address.street.name,
                'street_type': address.street.type,

            }
        )

    return render_to_response('organizations/organization_edit.html', {'form': form, 'phones': phones, 'tags': tags_objs, 'o_tags_list': o_tags_list, 'tags_error': tags_error}, context_instance=RequestContext(request))
'''


@only_superuser_or_admin
@never_cache
def organization_uni_temp(request):
    orgs = Organization.objects.all().order_by('name')
    for i in orgs:
        result = unidecode(i.name)
        result = re.findall(ur'[a-z0-9]+', low(result))
        result = '-'.join(result) if result else ''
        i.uni_slug = '%s-%s' % (result, i.id)
        i.save()
    return HttpResponse(str())


@only_superuser_or_admin
@never_cache
def admin_organization_notes(request, id=None):
    """
    Постмодерация описания организаций
    """
    if request.POST:
        note = request.POST.get('note', False)
        if note != False:
            org = Organization.objects.get(pk=id)
            org.note = note
            org.note_accept = True
            org.save()
        return HttpResponseRedirect(reverse("admin_organization_notes"))

    if id:
        warnings = [u"script", u"javascript", u"src", u"img", u"%68%74%74%70%3A%2F%2F", u"&#x68;&#x74;&#x74;&#x70;", u"&#104&#116&#116&#112", u"aHR0cDovLw==", u"href", u"http", u"https", u"ftp"]
        org = Organization.objects.get(pk=id)
        warning = False
        if org.note:
            for i in warnings:
                if i in org.note:
                    warning = True
                    break

        return render_to_response('organizations/notes_accept.html', {'org': org, 'warning': warning}, context_instance=RequestContext(request))
    else:
        orgs = Organization.objects.filter(note_accept=False)

        page = request.GET.get('page')
        try:
            page = int(page)
        except (ValueError, TypeError):
            page = 1
        p, page = pagi(page, orgs, 5)
        return render_to_response('organizations/notes_accept.html', {'p': p, 'page': page}, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def admin_organization_actions(request):
    log = ActionsLog.objects.select_related('profile').filter(object=1).order_by('-dtime')

    orgs_ids = set([i.object_id for i in log])
    orgs = Organization.objects.filter(pk__in=orgs_ids)

    orgs_dict = {}
    for i in orgs:
        orgs_dict[i.id] = i

    logs = []
    for i in log:
        org = orgs_dict.get(i.object_id)
        if org:
            logs.append({'log': i, 'org': org.name})
        else:
            logs.append({'log': i, 'org': ''})

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, logs, 15)
    return render_to_response('organizations/actions.html', {'p': p, 'page': page}, context_instance=RequestContext(request))



@only_superuser_or_admin
@never_cache
def organizations_doubles(request):
    orgs = Organization.objects.all().order_by('name')

    unique = {}
    double = []
    txt = ''
    for i in orgs:
        result = unidecode(i.name)
        result = re.findall(ur'[a-z0-9]+', low(result))
        result = '-'.join(result) if result else ''

        obj = unique.get(result)
        if obj:
            if obj not in double:
                txt += '%s <a href="http://kinoinfo.ru/organizations/show/%s" target="_blank">(ID %s)</a><br />' % (obj.name.encode('utf-8'), obj.id, obj.id)
                double.append(obj)
            double.append(i)
            txt += '%s <a href="http://kinoinfo.ru/organizations/show/%s" target="_blank">(ID %s)</a><br />' % (i.name.encode('utf-8'), i.id, i.id)
        else:
            unique[result] = i

    count = len(double)
    txt = '<b>Всего %s</b><br /><br />%s' % (count, txt)
    return HttpResponse(str(txt))


@only_superuser_or_admin
@never_cache
def organizations_name_handler(request):
    """Оработчик полученных при парсинге названий предприятий.
       Разбивает название отдельно на: название,
       метку названия, тип предприятия, владелец и записывает в модель."""


    # выгружаем все данные из модели
    org_obj = Organization.objects.all()
    # отчищаем логи, что бы при каждом запуске функции логи перезаписывались
    debug_logs("clear_logs")
    # счетчик итераций цикла for
    cnt = 0
    # из модели models_choices берем типы предприятий(ООО,ЧП и тп.)
    ownership = OWNERSHIP_CHOICES
    # создаем словарь для хранения/использования значений типов предприятий
    ownership_dict = {}

    # Разбор поля названий передприятий после парсинга, выбираем нужные значения
    # с помощью регулярных выражений по разделителям: запятая и тип предприятия
    for i in org_obj:
        cnt += 1
        name= str(i.name.encode('utf-8'))
        debug_logs('\n'+'\n'+"%s. %s" % (cnt, i.name.encode('utf-8')) + '\n')
        # <<< Запись в модель - название
        Organization.objects.filter(id=i.id).update(alter_name=name)

        # Проверка на наличие типа предприятия + добавление в словарь
        for j in ownership:
            ownership_dict[j[1]] = j[0]
            match_type = re.findall(r'(?ms)%s' % j[1], name)
            if match_type:
                match_type = match_type[0]
                break
            else:
                match_type = None
        # Проверка на наличие запятой
        match_comma = re.findall(r'(?ms)[,]', name)

        # Если запятая присутствует
        if match_comma:


            #берем название (запятая и пробел после названия)
            match_name = re.findall(r'(.+)[,][ ]', name)
            if match_name:
                # <<< Запись в модель - название
                Organization.objects.filter(id=i.id).update(name=match_name[0])
                debug_logs("название: %s" % (match_name[0]))

            # Если тип указан
            if match_type is not None:
                #берем метку (после запятой, но перед типом предприяия)
                match_tag = re.findall(r'(?ms).[,][ ](.+)%s' % match_type, name)
                if match_tag:
                    debug_logs("метка: %s " % (match_tag[0]))
                    # >>> Запись в модель - метки
                    check_tag(match_tag[0], i.id)

                #берем тип (уже взяли ранее просто передаем сюда)
                debug_logs("тип: %s " % (match_type))
                # >>> Запиь в модель - типа
                Organization.objects.filter(id=i.id).update(ownership=ownership_dict[match_type])
                #берем владельца (после типа предприятия и до конца строки)
                match_owner = re.findall(r'(?ms).%s(.+)$' % match_type, name)
                if match_owner:
                    debug_logs("владелец: %s" % (match_owner[0]))
                    # >>> Запись в модель - владельца
                    Organization.objects.filter(id=i.id).update(owner=match_owner[0])

            # Если тип не указан
            else:
                #берем метку (после запятой, и до конца строки)
                match_tag = re.findall(r'(?ms).[,][ ](.+)$', name)
                if match_tag:
                    debug_logs("метка: %s" % (match_tag[0]))
                    # >>> Запись в модель - метки
                    check_tag(match_tag[0], i.id)

        # Если запятая отсутствует
        else:

            # Если тип указан
            if match_type is not None:

                #берем название (все содержимое от начала строки до начала типа)
                match_name = re.findall(r'(?ms)(.+)%s' % match_type, name)
                if match_name:
                    debug_logs("название: %s" % (match_name[0]))
                    # <<< Запись в модель - название
                    Organization.objects.filter(id=i.id).update(name=match_name[0])

                else:
                    #или берем название (все содержимое от начала типа до конца строки)
                    match_name = re.findall(r'(?ms)%s(.+)' % match_type, name)
                    if match_name:
                        debug_logs("название: %s" % (match_name[0]))

                        # <<< Запись в модель - название
                        Organization.objects.filter(id=i.id).update(name=match_name[0])


                #берем тип (уже взяли ранее просто передаем сюда)
                debug_logs("тип: %s" % (match_type))

                # >>> Запиь в модель - типа
                Organization.objects.filter(id=i.id).update(ownership=ownership_dict[match_type])

                #берем владельца - после типа предприятия и до конца строки
                match_owner = re.findall(r'(?ms).%s(.+)$' % match_type, name)
                if match_owner:
                    debug_logs("владелец: %s" % (match_owner[0]))

                    # >>> Запись в модель - владельца
                    Organization.objects.filter(id=i.id).update(owner=match_owner[0])

            # Если тип не указан
            else:
                #берем название (все содержимое, т.к. по условию раздилители отсутствуют)
                match_name = re.findall(r'(?ms).+', name)
                if match_name:
                    debug_logs("название: %s" % (match_name[0]))

                    # <<< Запись в модель - название
                    Organization.objects.filter(id=i.id).update(name=match_name[0])



    # Процедура выполнена, перенаправляем пользователя на страницу логов
    return redirect('movie_logs')

def check_tag(tag, id):

    tags = capit(tag).decode('utf-8')
    tags = low(tag).decode('utf-8')

    obj=""

    try:
        obj = OrganizationTags.objects.get(name=tags)
        #obj = Organization.objects.get(tags__name=tags)
        debug_logs("already exists: %s " % (obj))

    except MultipleObjectsReturned:
        debug_logs("MultipleObjectsReturned: %s " % (obj))

    except ObjectDoesNotExist:
        debug_logs("ObjectDoesNotExist %s" % tags.encode('utf-8'))
        created = OrganizationTags.objects.create(name=tags, group_flag="org_name_tag")
        tag = OrganizationTags.objects.get(name=tags)
        org = Organization.objects.get(pk=id)
        org.tags.add(tag)
        debug_logs("tag %s, created %s " % (tag, created))




@only_superuser_or_admin
@never_cache
def org_invite_text(request):
    f = open('%s/org_invite_text.txt' % settings.API_EX_PATH,'r')
    content = f.read()
    f.close()
    
    if request.POST:
        form = OrganizationInviteTextForm(request.POST)
        if form.is_valid():
            content = request.POST['text'].encode('utf-8')
            f = open('%s/org_invite_text.txt' % settings.API_EX_PATH,'w')
            f.write(content)
            f.close()
    
    form = OrganizationInviteTextForm(
        initial={'text': content},
    )
    example = content.replace('*city*', 'Ялты')
    return render_to_response('organizations/invite_text.html', {'form': form, 'content': content, 'example': example}, context_instance=RequestContext(request))

