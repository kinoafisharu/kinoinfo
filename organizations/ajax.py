# -*- coding: utf-8 -*-
import datetime
import operator

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.utils.html import strip_tags
from django.db.models import Q
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.core.cache import cache

from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models import *
from base.models_dic import *
from api.models import *
from kinoinfo_folder.func import low, capit, del_separator
from user_registration.func import org_peoples
from user_registration.ajax import user_by_phone, create_by_email


def xss_strip(val):
    val = val.replace('"','').replace("'",'').replace('<','').replace('>','').replace('=','')
    return val
    
def xss_strip2(text):
    tags = ['img', 'script', 'iframe']
    params = ['cookie', 'src=']
    text = BeautifulSoup(text, "html5lib", from_encoding="utf-8")
    for i in text.find_all(tags):
        i.extract()
    for t in tags:
        if t in text:
            xss_strip2(text)
    text = str(text)
    for p in params:
        text = text.replace(p,'')
    text = text.replace('<html><head></head><body>','').replace('</body></html>','')
    return text


def tags_save(site, profile, org, type, arr):
    tags_objs = {}
    tags_list = []
    # выбрали все метки из модели
    tags = OrganizationTags.objects.filter(group_flag=type)
    for i in tags:
        tags_objs[i.name] = i

    # преобразовываем полученные метки и сравниваем
    for ar in arr:
        ar = ar.split(',') if type not in ('2','3') else [ar]

        for i in ar:
            i = i.strip()
            if i:
                t_list = (i, capit(i).decode('utf-8'), low(i).decode('utf-8'))
                tag_obj = None
                for t in t_list:
                    tag_obj = tags_objs.get(t)
                    # если метка не обновлялась пропускаем
                    if tag_obj:
                        break

                # если метка новая создаем новую запись в модели
                if not tag_obj:
                    tag_obj = OrganizationTags.objects.create(name=t_list[0], group_flag=type)

                tags_list.append(tag_obj)

    if type in ('3', '4'):
        return tags_list

    org_tags = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag=type)

    # убрали старую метку из организации
    for i in org_tags:
        i.delete()
    # добавили новую метку в организацию
    for i in tags_list:
        Organization_Tags.objects.create(organizationtags=i, organization=org)
    
    ActionsLog.objects.create(
        profile = profile,
        object = '1',
        action = '2',
        object_id = org.id,
        attributes = 'Метки',
        site = site,
    )
            
@dajaxice_register
def get_organization_address(request, id, type, name, building, tag, area, city):
    try:
        org = Organization.objects.get(pk=id)
        
        profile = request.profile
        is_editor = True if profile in org.editors.all() else False
        xtmp = False

        if request.user.is_superuser or is_editor or request.is_admin:
            
            subdomain = request.subdomain
            domain = request.current_site.domain
        
            filter = {'name__status': 1}
            if subdomain in ('yalta', 'yalta2'):
                filter['name__name'] = 'Ялта'
            elif subdomain == 'orsk':
                filter['name__name'] = 'Орск'
            if domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                filter['name__name'] = 'Melbourne'
            if domain in ('kinoinfo.ru', 'kinoafisha.ru') and city:
                filter['name__pk'] = city
            
            if subdomain and domain == 'vsetiinter.net':
                xtmp = True

            city = City.objects.get(**filter)


            if not building:
                building = None
            
            street_obj = None

            street_slug = low(del_separator(name.encode('utf-8')))
            
            street_filter = {'slug': street_slug, 'type': type}
            
            if area:
                area_slug = low(del_separator(area.encode('utf-8')))
                area_obj, area_created = Area.objects.get_or_create(
                    slug = area_slug,
                    defaults = {
                        'name': area,
                        'slug': area_slug,
                    })
                street_filter['area'] = area_obj
            else:
                area_obj = None
                
            street_obj = Street.objects.filter(**street_filter)
            
            if street_obj:
                street_obj = street_obj[0]
            else:
                street_filter['name'] = name
                street_obj = Street.objects.create(**street_filter)
            
            building_obj, bu_created = Building.objects.get_or_create(
                city = city,
                street = street_obj,
                number = building,
                defaults = {
                    'city': city,
                    'street': street_obj,
                    'number': building,
                })

            current_site = request.current_site

            org_buildings = [i for i in org.buildings.all()]
            if building_obj not in org_buildings:
                for i in org_buildings:
                    org.buildings.remove(i)
                org.buildings.add(building_obj)

                ActionsLog.objects.create(
                    profile = profile,
                    object = '1',
                    action = '2',
                    object_id = org.id,
                    attributes = 'Адрес',
                    site = current_site,
                )
            
            tags_save(current_site, profile, org, '2', [tag])
            
            new_addr = 'No'
            if street_obj:
                if domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                    new_addr = '%s %s %s' % (building, street_obj.name, street_obj.get_type_display())
                    if area_obj:
                        new_addr = '%s, %s;' % (new_addr, area_obj.name)
                    else:
                        new_addr += ';'
                else:
                    new_addr = '%s %s %s;' % (street_obj.get_type_display(), street_obj.name, building)

            cache.delete('organization__%s__data' % org.uni_slug)

            return simplejson.dumps({'status': True, 'content': new_addr, 'tag': tag})
        else:
            return simplejson.dumps({'status': False})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

'''
@dajaxice_register
def get_organization_offers(request, id, arr, st):
    try:
        org = Organization.objects.get(pk=id)
        
        profile = RequestContext(request).get('profile')
        is_editor = True if profile in org.editors.all() else False
        
        if request.user.is_superuser or is_editor or request.is_admin:
            tags = []
            tags_del = []
            tags_new = []
            
            st = str(st)
            
            if st == '3':
                url_type = u'offers'
            elif st == '4':
                url_type = u'advert'
            

            for i in arr:
                val, oid = i.split('~%~')
                val = val.strip()
                oid = int(oid)
                if val:
                    tag = tags_save(request.current_site, profile, org, st, [val])[0]
                    tags.append({'id': oid, 'tag': tag})
                    tags_new.append(tag)
                else:
                    tags_del.append(oid)
            
            offers_tags = Organization_Tags.objects.select_related('organizationtags').filter(organization=org, organizationtags__group_flag=st)

            tags_back = []

            for i in offers_tags:
                if i.organizationtags_id in tags_del:
                    i.delete()
                    
                for t in tags:
                    if t['id'] == i.organizationtags_id:
                        i.organizationtags = t['tag']
                        i.save()
                        url = '/%s/%s/%s/' % (org.uni_slug, url_type, i.id)
                        tags_back.append({'tag': t['tag'].name, 'id': i.id, 'url': url})
                        while i.organizationtags in tags_new: tags_new.remove(i.organizationtags)
            
            for i in tags_new:
                new = Organization_Tags.objects.create(organizationtags=i, organization=org)
                url = '/%s/%s/%s/' % (org.uni_slug, url_type, new.id)
                tags_back.append({'tag': i.name, 'id': new.id, 'url': url})
            
            return simplejson.dumps({'status': True, 'err': False, 'content': tags_back})
        else:
            return simplejson.dumps({'status': False})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
'''


@dajaxice_register
def get_organization_tags(request, id, arr, type):
    #try:
    ref = request.META.get('HTTP_REFERER')
    
    org = Organization.objects.get(pk=id)
    
    profile = request.profile
    is_editor = True if profile in org.editors.all() else False

    if request.user.is_superuser or is_editor or request.is_admin and arr:
        # получаем массив меток из формы интерфейса и преобразуем их к множеству
        arr = set(arr)
        tags_error = False

        tags_save(request.current_site, profile, org, type, arr)

        cache.delete('organization__%s__data' % org.uni_slug)
        return simplejson.dumps({'status': True, 'err': False, 'content': sorted(arr), 'type': type})
    else:
        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_organization_phones(request, id, arr):
    #try:
        org = Organization.objects.get(pk=id)
        
        profile = request.profile
        is_editor = True if profile in org.editors.all() else False

        if request.user.is_superuser or is_editor or request.is_admin:

            phones_del = [i for i in org.phones.all()]

            phones = set(arr)

            phones_objs = []
            for i in phones:
                try:
                    ph = OrganizationPhones.objects.get(phone=i)
                except (OrganizationPhones.DoesNotExist, OrganizationPhones.MultipleObjectsReturned):
                    ph = OrganizationPhones.objects.create(phone=i)
                phones_objs.append(ph)

            for i in phones_del:
                org.phones.remove(i)

            for i in phones_objs:
                org.phones.add(i)

            cache.delete('organization__%s__data' % org.uni_slug)

            ActionsLog.objects.create(
                profile = profile,
                object = '1',
                action = '2',
                object_id = org.id,
                attributes = 'Телефоны',
                site = request.current_site,
            )
            return simplejson.dumps({'status': True, 'content': sorted(list(phones))})
        else:
            return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_organization_site(request, id, val):
    org = Organization.objects.get(pk=id)
    
    profile = request.profile
    is_editor = True if profile in org.editors.all() else False

    if request.user.is_superuser or is_editor or request.is_admin:
        site = val

        if site == 'http://':
            site = ''

        if site:
            if 'http://' not in site:
                site = 'http://%s' % site

        action = '2' if site else '3'
        if not org.site:
            action = '1'

        org.site = site
        org.save()

        cache.delete('organization__%s__data' % org.uni_slug)

        ActionsLog.objects.create(
            profile = profile,
            object = '1',
            action = action,
            object_id = org.id,
            attributes = 'Сайт',
            site = request.current_site,
        )

        return simplejson.dumps({'status': True, 'content': site})
    else:
        return simplejson.dumps({'status': False})


@dajaxice_register
def get_organization_email(request, id, val):
    #try:
        current_site = request.current_site
        org = Organization.objects.get(pk=id)
        
        profile = request.profile
        is_editor = True if profile in org.editors.all() else False

        if request.user.is_superuser or is_editor or request.is_admin:
            if val:
                if '@' not in val:
                    return simplejson.dumps({'status': True, 'err': True})

            action = '2' if val else '3'
            if not org.email:
                action = '1'

            org.email = val
            org.save()

            ActionsLog.objects.create(
                profile = profile,
                object = '1',
                action = action,
                object_id = org.id,
                attributes = 'E-mail',
                site = request.current_site,
            )

            if not val:
                if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                    val = u'No'
                else:
                    val = u'Нет'
            
            return simplejson.dumps({'status': True, 'err': False, 'content': val})
        else:
            return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def get_organization_name(request, id, val, own):
    org = Organization.objects.get(pk=id)
    
    profile = request.profile
    is_editor = True if profile in org.editors.all() else False

    if request.user.is_superuser or is_editor or request.is_admin:
        if val:
            
            lo = low(val.encode('utf-8'))
            name_slug = re.findall(ur'[a-zа-я0-9]', lo.decode('utf-8'))
            name_slug = ''.join(name_slug) if name_slug else ''
            
            org.name = val
            org.slug = name_slug
            if not own:
                own = None

            org.ownership = own
            org.save()

            ActionsLog.objects.create(
                profile = profile,
                object = '1',
                action = '2',
                object_id = org.id,
                attributes = 'Название',
                site = request.current_site,
            )

            return simplejson.dumps({'status': True, 'err': False, 'content': val, 'own': own})
        else:
            return simplejson.dumps({'status': True, 'err': True})
    else:
        return simplejson.dumps({'status': False})


@dajaxice_register
def get_organization_slides(request, id, slide):
    org = Organization.objects.get(pk=id)
    
    profile = request.profile
    is_editor = True if profile in org.editors.all() else False

    if request.user.is_superuser or is_editor or request.is_admin:
        img = OrganizationImages.objects.get(pk=slide)

        img_del = img.img.replace(settings.ORGANIZATIONS_FOLDER, settings.ORGANIZATIONS_PATH)

        os.remove(img_del)
        org.images.remove(img)
        img.delete()

        cache.delete('organization__%s__data' % org.uni_slug)
        
        ActionsLog.objects.create(
            profile = profile,
            object = '1',
            action = '3',
            object_id = org.id,
            attributes = 'Слайды',
            site = request.current_site,
        )
        return simplejson.dumps({'status': True})
    else:
        return simplejson.dumps({'status': False})

@dajaxice_register
def get_news_title(request, id, val):
    from base.models import News
    if request.user.is_superuser or request.is_admin and val:
        news = News.objects.get(pk=id)
        news.title = val
        news.save()
        return simplejson.dumps({'status': True, 'content': val})
    else:
        return simplejson.dumps({'status': False})


@dajaxice_register
def update_org_meta_tags_flag(request, meta_input_val, meta_flag):
    """Функция обновляет флаг-групповой признак у метки"""
    OrganizationTags.objects.filter(name=meta_input_val).update(group_flag=meta_flag)

@dajaxice_register
def update_org_meta_tags_alter_name(request, meta_input_val, alter_name):
    """Функция добовляет альтернативное название метки"""
    OrganizationTags.objects.filter(name=meta_input_val).update(alter_name=alter_name)


@dajaxice_register
def get_organization_staff(request, val, id, pid):
    #try:
        if request.user.is_authenticated():
            profile = request.profile
            if profile.auth_status:
                if pid == 'recipient':
                    objs = Profile.objects.select_related('user', 'person').filter(Q(accounts__nickname__icontains=val) | Q(accounts__fullname__icontains=val) | Q(accounts__login__icontains=val)).distinct('user__id').order_by('user__id')
                    users = []
                    for i in objs:
                        acc = []
                        for j in i.accounts.all():

                            if j.fullname:
                                if val.encode('utf-8') in low(j.fullname):
                                    fullname = j.fullname
                                    if 'http://' in low(fullname) or 'https://' in low(fullname):
                                        fullname = fullname.replace('http://','').replace('https://','')
                                    acc.append(fullname.strip())
                            if j.nickname:
                                if val.encode('utf-8') in low(j.nickname):
                                    nickname = j.nickname
                                    if 'http://' in low(nickname) or 'https://' in low(nickname):
                                        nickname = nickname.replace('http://','').replace('https://','')
                                    acc.append(nickname.split('@')[0].strip())
                            if j.login:
                                if val.encode('utf-8') in low(j.login):
                                    login = j.login
                                    if '@' in login:
                                        acc.append(login.split('@')[0].strip())
                                        
                        city = ''
                        if acc:
                            acc = set(sorted(acc, reverse=True))
                            acc_txt = ' / '.join(acc)
                            
                            
                            if i.person.city:
                                for j in i.person.city.name.all():
                                    if j.status == 1:
                                        city = j.name

                            users.append({'acc': acc_txt, 'id': i.user_id, 'city': city, 'checked': ''})

                    users = sorted(users, key=operator.itemgetter('acc'))
                    
                    return simplejson.dumps({'status': True, 'content': users, 'pid': pid, 'extra': True})
                else:
                    org = Organization.objects.get(pk=id)
                    is_editor = True if profile in org.editors.all() else False
                    if val:
                        if request.user.is_superuser or is_editor or request.is_admin:
                            val = val.strip()
                            
                            objs = Profile.objects.select_related('user', 'person').filter(Q(accounts__nickname__icontains=val) | Q(accounts__fullname__icontains=val) | Q(accounts__login__icontains=val) | Q(phone=val)).distinct('user__id').order_by('user__id')

                            if pid == 'staff':
                                peoples = [i.id for i in org.staff.all()]
                            elif pid == 'editor':
                                peoples = [i.id for i in org.editors.all()]
                            
                            users = []
                            for i in objs:
                                acc = []
                                for j in i.accounts.all():
                                    
                                    if j.fullname:
                                        if val.encode('utf-8') in low(j.fullname):
                                            acc.append(j.fullname)
                                    if j.nickname:
                                        if val.encode('utf-8') in low(j.nickname):
                                            acc.append(j.nickname)
                                    if j.login:
                                        if val.encode('utf-8') in low(j.login):
                                            acc.append(j.login)
                                            
                                acc = set(sorted(acc, reverse=True))
                                acc_txt = ' / '.join(acc)
                                
                                city = ''
                                if i.person.city:
                                    for j in i.person.city.name.all():
                                        if j.status == 1:
                                            city = j.name
                                
                                if not acc:
                                    acc_txt = 'User_%s' % i.user_id
                                
                                checked = 'checked' if i.id in peoples else ''
                                
                                users.append({'acc': acc_txt, 'id': i.user_id, 'city': city, 'checked': checked})

                            return simplejson.dumps({'status': True, 'content': users, 'pid': pid})
                        else:
                            return simplejson.dumps({'status': False})
                    else:
                        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def get_organization_staff_appoint(request, id, pid, arr):
    try:
        org = Organization.objects.get(pk=id)
        profile = request.profile
        is_editor = True if profile in org.editors.all() else False
        current_site = request.current_site
        subdomain = request.subdomain
        xtmp = False
        if subdomain and current_site.domain == 'vsetiinter.net':
            xtmp = True
        
        if arr:
            if request.user.is_superuser or is_editor or request.is_admin:
                data = {}
                for i in arr:
                    user, val = i.split(';')
                    data[int(user)] = val
                    
                profiles = Profile.objects.filter(user__id__in=data.keys())

                for i in profiles:
                    value = data.get(i.user_id)
                    if value == 'true':
                        if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                            org.editors.add(i)
                            org.staff.add(i)
                        else:
                            if pid == u'editor':
                                org.editors.add(i)
                            elif pid == u'staff':
                                org.staff.add(i)
                    else:
                        if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                            org.editors.remove(i)
                            org.staff.remove(i)
                        else:
                            if pid == u'editor':
                                org.editors.remove(i)
                            elif pid == u'staff':
                                org.staff.remove(i)
                            
                return simplejson.dumps({'status': True})
                
        return simplejson.dumps({'status': False})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def get_organization_relations(request, id, arr):
    #try:
    org = Organization.objects.get(pk=id)
    
    profile = request.profile
    is_editor = True if profile in org.editors.all() else False
    data = []
    
    if arr:
        if request.user.is_superuser or is_editor or request.is_admin:

            for i in org.relations.all():
                org.relations.remove(i)
                i.delete()
           
            for i in arr[:10]:
                name, site = i.split('~%~')
                if site == u'http://' or site == u'https://':
                    site = ''
                
                if site:
                    if u'https://' in site or u'http://' in site:
                        if u'https://' in site:
                            site = u'https://%s' % site.replace('https://','')
                        else:
                            site = u'http://%s' % site.replace('http://','')
                    else:
                        site = u'http://%s' % site

                    if name:
                        rel = OrganizationRelations.objects.create(
                            name = name,
                            link = site
                        )
                        org.relations.add(rel)
                        data.append({'name': name, 'link': site})
            
            return simplejson.dumps({'status': True, 'content': data})
    
    return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
        


@dajaxice_register
def get_organization_invite(request, id, email):
    #try:
    from user_registration.func import md5_string_generate
    from user_registration.views import get_user
    from django.core.mail import send_mail, EmailMultiAlternatives
    
    email = email.strip()
    
    limit, limit_create = EmailNotice.objects.get_or_create(
        email = email, 
        type = 1,
        defaults = {
            'email': email, 
            'type': 1, 
            'count': 1,
    })
    
    send_now = True
    
    if not limit_create:
        time_now = datetime.datetime.now()
        val = time_now - limit.dtime
        count = limit.count
        # если юзер уже отправил 5 сообщений и пытается отправить 6
        if count >= 1:
            # проверям сколько времени прошло с последней отправки, если меньше 20 мин, то блокируем
            if val.seconds < 1200:
                send_now = False
            # елси больше 20 мин, то отправляем
            else:
                count = 0
                limit.dtime = time_now
        else:
            limit.dtime = time_now
            
        limit.count = count + 1
        limit.save()
        
    
    if send_now:
        org = Organization.objects.get(pk=id, email=email)

        current_link = request.META.get('HTTP_REFERER')
        
        if current_link:
            f = open('%s/org_invite_text.txt' % settings.API_EX_PATH,'r')
            text = f.read()
            f.close()
            
            subdomain = request.subdomain
            
            if subdomain in ('yalta', 'yalta2'):
                city_name = 'Ялты'
            elif subdomain == 'orsk':
                city_name = 'Орска'
                
            text = text.replace('*city*', city_name)

            code = md5_string_generate(email)
            
            acc, created = Accounts.objects.get_or_create(
                login = email,
                defaults = {
                'login': email,
                'validation_code': code,
                'email': email,
            })
            
            create_user = False
            profile = None
            
            if created:
                try:
                    profile = Profile.objects.get(accounts=acc)
                except Profile.DoesNotExist:
                    new_user = get_user()
                    profile = new_user.get_profile()
                    profile.accounts.add(acc)
            else:
                acc.validation_code = code
                acc.save()

            
            subject = 'Приглашение'
            auth_link = 'http://ya.vsetiinter.net/user/login/email/%s/?next=%s' % (code, current_link)
            
            current_site = request.current_site
            portal_name = '%s.%s' % (subdomain, current_site.domain)
            portal_name = portal_name.encode('utf-8')
            
            msg = "%s\n\n\
                Для редактирования пройдите по ссылке: \n%s\n\n\
                С уважением, редакция портала %s" % (text, auth_link, portal_name)
            
            msg_html = '<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                %s <br /><br />\
                Для редактирования пройдите по ссылке: <br />\
                <a href="%s" target="_blank">%s</a><br /><br />\
                С уважением, редакция портала %s\
                </div>' % (text, auth_link, auth_link, portal_name)
            
            email = EmailMultiAlternatives(subject, msg, '', [email])
            email.attach_alternative(msg_html, "text/html")
            email.send()
            
            ActionsLog.objects.create(
                profile = RequestContext(request).get('profile'),
                object = '1',
                action = '4',
                object_id = org.id,
                attributes = 'Приглашение',
                site = request.current_site,
            )
            #send_mail('Приглашение', msg, '', [email])
            
    return simplejson.dumps({'status': True, 'content': send_now})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    


@dajaxice_register
def org_add_menu(request, id, title, menu_id, private):
    #try:
        ref = request.META.get('HTTP_REFERER').split('?')[0]
        
        is_user_profile = True if '/user/profile/' in ref else False
        
        access = False
        
        title = xss_strip(title)
        
        language = None
        if request.current_site.domain == 'imiagroup.com.au':
            try: language = Language.objects.get(code=request.current_language)
            except Language.DoesNotExist: pass
        
        
        if is_user_profile:
            obj = Profile.objects.get(user__id=id)
            if request.user.is_superuser or request.is_admin:
                 access = True
            else:
                if request.profile == obj:
                    access = True
            filter_1 = {'profile': obj, 'pk': menu_id}
            filter_2 = {'profile': obj, 'name': title, 'private': private}
            url = '/user/profile/%s/view/' % id
        else:
            obj = Organization.objects.get(uni_slug=id)
            if request.user.is_superuser or request.is_admin:
                access = True
            filter_1 = {'organization': obj, 'pk': menu_id}
            filter_2 = {'organization': obj, 'name': title}
            url = '/view/'
            if request.current_site.domain == 'vsetiinter.net':
                url = '/%s%s' % (id, url)
        
        new = 0
        link = ''
        lact = None
        if access:
            if menu_id:
                if title:
                    orgm = OrgMenu.objects.get(**filter_1) #f1
                    
                    if language:
                        orgmenulang, orgmenulang_created = OrgMenuLang.objects.get_or_create(
                            orgmenu = orgm,
                            language = language,
                            defaults = {
                                'orgmenu': orgm,
                                'language': language,
                                'name': title,
                            })
                        if not orgmenulang_created:
                            orgmenulang.name = title
                            orgmenulang.save()
                    else:
                        orgm.name = title
                        orgm.private = private
                        orgm.save()

                    new = 2
                    lact, lobj, lattr = ('2', menu_id, title)
                else:
                    try:
                        menu = OrgMenu.objects.get(**filter_1) #f1
                        orgsub = OrgSubMenu.objects.filter(orgmenu=menu)
                        for i in orgsub:
                            i.news.all().delete()

                            for g in i.gallery.select_related('photo').all():
                                try: os.remove('%s%s' % (settings.MEDIA_ROOT, g.photo.file))
                                except OSError: pass
                            
                                g.photo.delete()
                                g.delete()
                        
                        lact, lobj, lattr = ('3', menu.id, menu.name)
                            
                        orgsub.delete()
                        menu.delete()
                    except OrgMenu.DoesNotExist: pass
            else:
                if title:
                    menu_obj = OrgMenu.objects.create(**filter_2) #f2
                    
                    if language:
                        orgmenulang = OrgMenuLang.objects.create(
                            orgmenu = menu_obj,
                            language = language,
                            name = title,
                        )
                    
                    sub = OrgSubMenu.objects.create(name='example link')
                    menu_obj.submenu.add(sub)
                    menu_id = menu_obj.id
                    new = 1
                    link = '%s%s/' % (url, sub.id)
                    
                    lact, lobj, lattr = ('1', menu_id, menu_obj.name)
                    
            if lact:
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '4',
                    action = lact,
                    object_id = lobj,
                    attributes = lattr,
                    site = request.current_site,
                )
                    
            return simplejson.dumps({'status': True, 'id': id, 'title': title, 'menu_id': menu_id, 'new_menu': new, 'link': link})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def org_edit_submenu(request, id, arr, menu_id):
    try:
        ref = request.META.get('HTTP_REFERER').split('?')[0]
        
        is_user_profile = True if '/user/profile/' in ref else False
        
        access = False
        
        language = None
        if request.current_site.domain == 'imiagroup.com.au':
            try: language = Language.objects.get(code=request.current_language)
            except Language.DoesNotExist: pass
        
        
        menu_id_tmp = menu_id
        lact = None
        if is_user_profile:
            obj = Profile.objects.get(user__id=id)
            if request.user.is_superuser or request.is_admin:
                 access = True
            else:
                if request.profile == obj:
                    access = True
            filter_1 = {'profile': obj, 'pk': menu_id}
            url = '/user/profile/%s/view/' % id
        else:
            obj = Organization.objects.get(uni_slug=id)
            if request.user.is_superuser or request.is_admin:
                access = True
                
                filter_1 = {'organization': obj}
                
                if menu_id == 'about':
                    menu, menu_created = OrgMenu.objects.get_or_create(
                        organization = obj,
                        name = 'About Us',
                        defaults = {
                            'organization': obj,
                            'name': 'About Us',
                        })
                    menu_id = menu.id
                    
                filter_1['pk'] = menu_id
                url = '/view/'
                if request.current_site.domain == 'vsetiinter.net':
                    url = '/%s%s' % (id, url)
        
        if access:
            new_arr = []
            menu = OrgMenu.objects.get(**filter_1) #f1
            
            for i in arr:
                link = ''
                sub_name = None
                
                xid = i['id'].rstrip('/').split('/')[-1]
                
                if xid and int(xid):
                    xid = int(xid)
                    
                    sub_id = xid
                    sub_name = xss_strip(i['val'])
                    
                    if i['val']:
                        orgsubmenu = OrgSubMenu.objects.get(pk=xid)
                        
                        if language:
                            orgsubmenulang, orgsubmenulang_created = OrgSubMenuLang.objects.get_or_create(
                                orgsubmenu = orgsubmenu,
                                language = language,
                                defaults = {
                                    'orgsubmenu': orgsubmenu,
                                    'language': language,
                                    'name': sub_name,
                                })
                            if not orgsubmenulang_created:
                                orgsubmenulang.name = sub_name
                                orgsubmenulang.save()
                        else:
                            orgsubmenu.name = sub_name
                            orgsubmenu.save()
                        
                        
                        lact, lobj, lattr = ('2', xid, sub_name) 
                    else:
                        subs = OrgSubMenu.objects.filter(orgmenu=menu).count()
                        
                        if menu_id_tmp != 'about':
                            if subs > 1:
                                sub_name = None
                            else:
                                sub_name = "The only link can't be deleted!"
                        else:
                            sub_name = None
  
                        if sub_name is None:
                            orgsub = OrgSubMenu.objects.get(pk=xid, orgmenu=menu)
                            orgsub.news.all().delete()
                            
                            for g in orgsub.gallery.select_related('photo').all():
                                try: os.remove('%s%s' % (settings.MEDIA_ROOT, g.photo.file))
                                except OSError: pass
                            
                                g.photo.delete()
                                g.delete()
                            
                            lact, lobj, lattr = ('3', xid, orgsub.name)
                                
                            orgsub.delete()
                else:
                    strip_val = xss_strip(i['val'])
                    
                    if strip_val and strip_val != 'About Us' and menu_id != 'about':
                        sub = OrgSubMenu.objects.create(name=strip_val, page_type=None)
                        menu.submenu.add(sub)
                        sub_id = sub.id
                        sub_name = strip_val
                        
                        if language:
                            orgsubmenu = OrgSubMenuLang.objects.create(
                                orgsubmenu = sub,
                                language = language,
                                name = sub_name,
                            )
                    
                        
                        lact, lobj, lattr = ('1', sub_id, sub.name)


                if sub_name:
                    link = '%s%s/' % (url, sub_id)
                    new_arr.append({'id': sub_id, 'val': sub_name, 'link': link})
            
            if lact:
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '5',
                    action = lact,
                    object_id = lobj,
                    attributes = lattr,
                    site = request.current_site,
                )
            return simplejson.dumps({'status': True, 'arr': new_arr, 'menu_id': menu_id_tmp, 'id': id})
    
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def remove_org_staff(request, org, person):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            xtmp = False if subdomain and current_site.domain == 'vsetiinter.net' else True
        
            if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                org_obj = Organization.objects.get(pk=org)
                profile = Profile.objects.get(user__id=person)
                
                #org_obj.editors.remove(profile)
                #org_obj.staff.remove(profile)

    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


def set_stff(site, current, new, org):
    org_obj = Organization.objects.get(pk=org, domain=site)
    
    old_profile = None
    if current:
        old_profile = Profile.objects.get(user__id=current)

    new_profile = Profile.objects.get(user__id=new)

    if old_profile:
        org_obj.editors.remove(old_profile)
        org_obj.staff.remove(old_profile)
        
    org_obj.editors.add(new_profile)
    org_obj.staff.add(new_profile)

    profile = org_peoples([new_profile])

    return profile[0]
    

@dajaxice_register
def org_stff_pe(request, id, val, type, curr_person):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site

            profile = None
            if type == 'email':
                profile, code = create_by_email(val, True)
            elif type == 'phone':
                profile, ttype = user_by_phone(val, current_site)
            
            if profile:
                profile = set_stff(current_site, curr_person, profile.user_id, id)
                
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '1',
                    action = '2',
                    object_id = id,
                    attributes = 'Контакт.лицо',
                    site = current_site,
                )  
                
                return simplejson.dumps({
                    'status': True, 
                    'msg': '<span style="color: green;">Has Been Changed Successfully</span>',
                    'contact': profile,
                })
                
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def set_org_newstff(request, id, name, phone, email):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            
            org = Organization.objects.get(pk=id, domain=current_site)

            if not email:
                email = org.email
            if not phone:
                phones = org.phones.all()
                if phones:
                    phone = phones[0].phone

            profile = None
            if email:
                profile, code = create_by_email(email, True)
                if phone:
                    profile.phone = phone
                    profile.save()
            
            if not email and phone:
                profile, ttype = user_by_phone(phone, current_site)

            if profile:
                name_obj, name_created = NamePerson.objects.get_or_create(
                    name = name,
                    status = 1,
                    language_id = 2,
                    defaults = {
                        'name': name,
                        'status': 1,
                        'language_id': 2,
                    })
                
                if not profile.person.name.all():
                    profile.person.name.add(name_obj)
                
                profile = set_stff(current_site, None, profile.user_id, id)
                
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '1',
                    action = '1',
                    object_id = id,
                    attributes = 'Контакт.лицо',
                    site = current_site,
                )  
                
                return simplejson.dumps({
                    'status': True, 
                    'msg': '',
                    'contact': profile,
                })
                
        return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))




@dajaxice_register
def get_org_stff(request, char):
    #try:
        
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            xtmp = False if subdomain and current_site.domain == 'vsetiinter.net' else True
            
            if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                
                alphabet_filter = []
                for i in set(list(Profile.objects.filter(site=current_site, person__name__status=1).values_list('person__name__name', flat=True))):
                    
                    alphabet_filter.append(low(del_separator(i.encode('utf-8'))).decode('utf-8')[0].upper())

                alphabet_filter = sorted(set(alphabet_filter))

                profiles = Profile.objects.filter(site=current_site, person__name__name__istartswith=char).distinct('id')
                peoples = org_peoples(profiles)
                peoples = sorted(peoples, key=operator.itemgetter('name'))

                return simplejson.dumps({
                    'status': True, 
                    'content': peoples,
                    'alphabet_filter': alphabet_filter,
                })
                
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def set_org_stff(request, id, val, curr_person):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            xtmp = False if subdomain and current_site.domain == 'vsetiinter.net' else True
            
            if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or xtmp:
                
                profile = set_stff(current_site, curr_person, val, id)

                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '1',
                    action = '2',
                    object_id = id,
                    attributes = 'Контакт.лицо',
                    site = current_site,
                )  

                return simplejson.dumps({
                    'status': True, 
                    'msg': '<span style="color: green;">Has Been Changed Successfully</span>',
                    'contact': profile,
                })
                
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def get_org_by_name(request, name, tag):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            
            if name:
                profile = request.profile
                city = 'Melbourne'
                
                city_obj = City.objects.get(name__name=city, name__status=1)

                slug = low(del_separator(name.encode('utf-8')))

                try:
                    org = Organization.objects.get(slug=slug, domain=current_site)
                    ttype = 1
                except Organization.DoesNotExist:
                    build, bcreated = Building.objects.get_or_create(
                        number = None, 
                        street = None, 
                        city = city_obj,
                        defaults = {
                            'number': None, 
                            'street': None, 
                            'city': city_obj,
                        })
                        
                    org = Organization.objects.create(
                        name = name, 
                        slug = slug,
                        creator = profile, 
                        domain = current_site,
                    )

                    uni = unidecode(name)
                    uni = re.findall(ur'[a-z0-9]+', low(uni))
                    uni = '-'.join(uni) if uni else ''
                    uni_slug = '%s-%s' % (uni, org.id)
                    org.uni_slug = uni_slug
                    org.save()

                    org.buildings.add(build)
                    ttype = 2

                    ActionsLog.objects.create(
                        profile = profile,
                        object = '1',
                        action = '1',
                        object_id = org.id,
                        attributes = 'Организация',
                        site = request.current_site,
                    )    


                cl, created = LetsGetClients.objects.get_or_create(
                    organization = org,
                    site = current_site,
                    subdomain = subdomain,
                    defaults = {
                        'organization': org,
                        'site': current_site,
                        'subdomain': subdomain,
                        'tag': tag,
                    })
                
                html = ''
                if created:
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '10',
                        action = '1',
                        object_id = cl.id,
                        attributes = '',
                        site = current_site,
                    )
                
                    html = '<td><div><input type="checkbox" name="checker" value="%s"></div></td>\
                        <td><div><a href="/org/%s/" target="_blank">%s</a></div></td>\
                        <td><div></div></td>\
                        <td><div id="note1__%s" class="letsget_edit_notes"></div></td>\
                        <td><div id="note2__%s" class="letsget_edit_notes"></div></td>' % (cl.id, org.uni_slug, org.name, cl.id, cl.id)
                
                url = u'<a href="/org/%s/" target="_blank">%s</a>' % (org.uni_slug, org.name)
                
                return simplejson.dumps({
                    'status': True, 
                    'type': ttype, 
                    'created': created,
                    'html': html,
                    'url': url,
                    })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def set_organization_org_ka(request, id, movie):
    #try:
        if request.user.is_superuser:
            org = Organization.objects.get(pk=id)
            movie = Movie.objects.using('afisha').get(pk=movie)
            org.kid = movie.id
            org.save()
            
            link = '<a href="http://www.kinoafisha.ru/index.php3?id2=%s&status=2" target="_blank">%s</a>' % (movie.id, movie.name)
            return simplejson.dumps({'status': True, 'content': link})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def nof_newcinema(request, name, tag, city):
    try:
        from organizations.views import organizations_add_func

        if request.user.is_superuser:
            org, id = organizations_add_func(request, name, tag, city, '1')

            cinema = Cinema.objects.select_related('city').get(code=org.kid)
            name = cinema.name.get(status=1).name
            city = cinema.city.name.get(status=1).name

            return simplejson.dumps({'status': True, 'cinema': {'kid': cinema.code, 'name': name, 'city': city}})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def nof_newhall(request, name, cinema):
    try:
        if request.user.is_superuser:
            cinema = Cinema.objects.get(code=cinema)

            cinema_obj = Movie.objects.using('afisha').get(pk=cinema.code)

            name = name.strip().encode('utf-8')

            last_id = AfishaHall.objects.using('afisha').all().order_by('-id')[0].id
            last_id += 1


            name_obj, name_obj_created = AfishaHall.objects.using('afisha').get_or_create(
                name = name,
                defaults = {
                    'id': last_id,
                    'name': name,
                })

            hall_obj, hall_obj_created = AfishaHalls.objects.using('afisha').get_or_create(
                id_name = name_obj,
                movie = cinema_obj,
                defaults = {
                    'id_name': name_obj,
                    'movie': cinema_obj,
                    'places': 0,
                    'format': 0,
                })

            
            hall, hall_created = Hall.objects.get_or_create(
                cinema = cinema,
                kid = hall_obj.id,
                defaults = {
                    'cinema': cinema,
                    'kid': hall_obj.id,
                })

            names = [
                {'name': name, 'status': 1},
                {'name': low(del_separator(name)), 'status': 2},
            ]
            for i in names:
                hall_name, hall_name_created = NameHall.objects.get_or_create(
                    name = i['name'], 
                    status = i['status'],
                    defaults = {
                        'name': i['name'], 
                        'status': i['status'],
                    })

                if hall_name not in hall.name.all():
                    hall.name.add(hall_name)


            return simplejson.dumps({'status': True, 'hall': {'id': hall.id, 'name': name}})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))