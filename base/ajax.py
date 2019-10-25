# -*- coding: utf-8 -*- 
import operator
import datetime
import time
import collections
import json

from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from dajaxice.decorators import dajaxice_register
from django.db.models import Q
from django.template.defaultfilters import date as tmp_date
from django.utils.html import escape
from django.middleware.csrf import get_token

from api.func import *
from user_registration.func import org_peoples, only_superuser, md5_string_generate, get_adv_price
from user_registration.views import get_usercard, merge_func
from base.models import *
from release_parser.clickatell import clickatell_get_sms_status
from organizations.func import is_editor_func
from dateutil.relativedelta import relativedelta




@never_cache
@dajaxice_register
def get_details(request, method):
    try: 
        details = BeautifulSoup(open('%s/%s.xml' % (settings.API_EX_PATH, method)), "html.parser")
        link = 'http://%s/api/%s' % (request.get_host(), details.api_example.string)
        return simplejson.dumps(
            {'status': 'True',
            'api_title': details.api_title.string,
            'api_decription': details.api_decription.string, 
            'api_example': link, 
            'api_param': details.api_param.string, 
            'api_response_details': details.api_response_details.string})
    except IOError:
        return simplejson.dumps({'status': 'False'})
        

@dajaxice_register
def panel(request, id, op1=None, op2=None):
    if request.user.is_superuser:
        from base.models import User
        try:
            user = User.objects.get(pk=id)
            from django.contrib.auth.models import Group
            group = Group.objects.get(name='API')
            if op1:
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()
            if op2:
                user.groups.add(group)
            else:
                user.groups.remove(group)
            return simplejson.dumps({'status': 'True', 'value': id})
        except User.DoesNotExist: pass
    return simplejson.dumps({'status': 'False', 'value': id})


@dajaxice_register
def gallery_photo_del(request, id):
    try:
        try:
            id = int(id)
            step = 1
        except ValueError:
            step = 2
        
        if request.user.is_superuser or request.is_admin:
            access = True
        else:
            is_editor = False
            
            try:
                org = Organization.objects.get(orgmenu__submenu__gallery__pk=id)
            except Organization.DoesNotExist:
                pass
            else:
                is_editor = is_editor_func(request, org)
                        
            access = True if is_editor else False
            
            
        if access:
            if step == 1:
                try:
                    obj = ProjectsGallery.objects.get(pk=id)
                except ProjectsGallery.DoesNotExist:
                    pass
                else:
                    img_p = '%s%s' % (settings.MEDIA_ROOT, obj.photo.file)
                    try:
                        os.remove(img_p)
                    except OSError: pass
                    
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '7',
                        action = '3',
                        object_id = obj.id,
                        attributes = 'Изображение',
                        site = request.current_site,
                    )
                    
                    obj.photo.delete()
                    obj.delete()
            else:
                domain = request.current_site.domain
                subdomain = request.subdomain
            
                if domain == 'letsgetrhythm.com.au':
                    fname = 'letsget'
                elif domain == 'vladaalfimovdesign.com.au':
                    fname = 'vlada_imgs'
                elif domain == 'imiagroup.com.au':
                    fname = 'imiagroup'
                elif domain == 'vsetiinter.net':
                    fname = subdomain

                id = id.split('/')[-1]
                img_p = '%s/%s/%s' % (settings.GALLERY_PATH, fname, id)
                id = id.split('.')[0][:10]
                try:
                    os.remove(img_p)
                except OSError: pass

            return simplejson.dumps({'status': True, 'id': id})
        return simplejson.dumps({})    
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def gallery_photo_edit(request, id, title, descr):
    try:
        
        if request.user.is_superuser or request.is_admin:
            access = True
        else:
            is_editor = False
            
            try:
                org = Organization.objects.get(orgmenu__submenu__gallery__pk=id)
            except Organization.DoesNotExist:
                pass
            else:
                is_editor = is_editor_func(request, org)
                        
            access = True if is_editor else False
    
    
        if access:
            language = None
            if request.current_site.domain == 'imiagroup.com.au':
                try: language = Language.objects.get(code=request.current_language)
                except Language.DoesNotExist: pass
        
            try:
                title = title.strip()
                descr = descr.strip()
                
                obj = ProjectsGallery.objects.get(pk=id)
                obj.title = title
                obj.description = descr
                obj.save()
                
                if language:
                    proj_gallery, proj_gallery_created = ProjectsGalleryLang.objects.get_or_create(
                        gallery = obj,
                        language = language,
                        defaults = {
                            'gallery': obj,
                            'language': language,
                            'title': title,
                            'description': descr,
                        })
                    if not proj_gallery_created:
                        proj_gallery.title = title
                        proj_gallery.description = descr
                        proj_gallery.save()
                
                
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '7',
                    action = '2',
                    object_id = obj.id,
                    attributes = 'Изображение',
                    site = request.current_site,
                )
                return simplejson.dumps({'status': True, 'id': id, 'title': title, 'descr': descr})
            except ProjectsGallery.DoesNotExist: pass
            
        return simplejson.dumps({'status': True})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def e_past_info(request, id):
    try:
        if request.user.is_superuser or request.is_admin:
            now = datetime.datetime.now()
            current_site = request.current_site
            profiles = []
            pr = {}

            notify = LetsGetCalendarNotified.objects.select_related('event').filter(event__id=id, event__site=current_site).order_by('-id')
            notify = notify[0]
            
            client_email = ''
            if notify.profile:
                client = org_peoples([notify.profile])[0]
                client_link = '<a href="/user/profile/%s/" target="_blank">%s</a>' % (client['id'], client['name'])
                
                card = get_usercard(notify.profile.user)
                if card['email']:
                    client_email = card['email']
                elif not card['email'] and card['emails']:
                    notify.profile.user.email = card['emails'][0]
                    notify.profile.user.save()
                    card['email'] = card['emails'][0]
                    client_email = card['email']
                
                if not card['email'] and card['emails_not_auth']:
                    client_email = card['emails_not_auth'][0]
                
            else:
                org = notify.organization
                client_email = org.email
                client_link = '<a href="/org/%s/" target="_blank">%s</a>' % (org.uni_slug, org.name)

            data_list = []
            
            ev = notify
            
            past = True if ev.event.dtime < now else False
            
            data = {'link': client_link, 'e_sms_notified': 'Not Specified', 'e_sms_status': '', 'e_email_notified': 'Not Specified', 'e_email_status': '', 'e_invite_status': '', 'e_invite_notified': 'Not Specified', 'e_invoice_status': '', 'e_invoice_notified': 'Not Specified', 'client_email': client_email, 'e_sms_dtime': '', 'e_email_dtime': '', 'e_invite_dtime': '', 'e_invoice_dtime': ''}

            if ev.invite_status is not None:
                data['e_invite_notified'] = '<span style="color: green;">Yes</span>' if ev.invite_notified else '<span style="color: red;">No</span>'
                data['e_invite_status'] = ev.invite_status
                data['e_invite_dtime'] = ev.invite_dtime.strftime('%d/%m/%Y at %I:%M %p') if ev.invite_dtime else ''

            if ev.invoice_status is not None:
                data['e_invoice_notified'] = '<span style="color: green;">Yes</span>' if ev.invoice_notified else '<span style="color: red;">No</span>'
                data['e_invoice_status'] = ev.invoice_status
                data['e_invoice_dtime'] = ev.invoice_dtime.strftime('%d/%m/%Y at %I:%M %p') if ev.invoice_dtime else ''

            if ev.event.sms:
                if past:
                    if not ev.sms_notified and ev.sms_id:
                        status = clickatell_get_sms_status(ev.sms_id)
                        ev.sms_notified = status[0]
                        ev.sms_status = status[1]
                        ev.save()
                
                    data['e_sms_notified'] = '<span style="color: green;">Yes</span>' if ev.sms_notified else '<span style="color: red;">No</span>'
                    data['e_sms_status'] = ev.sms_status if ev.sms_status else ''
                    data['e_sms_dtime'] = ev.sms_dtime.strftime('%d/%m/%Y at %I:%M %p') if ev.sms_dtime else ''
                else:
                    data['e_sms_notified'] = 'Expected...'
                    data['e_sms_status'] = ''
                    
            if ev.event.email:
                if past:
                    data['e_email_notified'] = '<span style="color: green;">Yes</span>' if  ev.email_notified else '<span style="color: red;">No</span>'
                    data['e_email_status'] = ev.email_status if ev.email_status else ''
                    data['e_email_dtime'] = ev.email_dtime.strftime('%d/%m/%Y at %I:%M %p') if ev.email_dtime else ''
                else:
                    data['e_email_notified'] = 'Expected...'
                    data['e_email_status'] = ''
           
            return simplejson.dumps({'status': True, 'content': data})

    except Exception as e:
        open('%s/errors.txt.txt' % settings.API_DUMP_PATH, 'a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def links_main_page(request, link1, link2, link3, link4):
    try:
        if request.user.is_superuser or request.is_admin:
            xml = ''
            for ind, i in enumerate((link1, link2, link3, link4)):
                xml += '<link id="%s" value="%s"></link>' % (ind + 1, i)
            
            with open('%s/vlada_main_links.xml' % settings.API_EX_PATH, 'w') as f:
                f.write(xml)
                
            return simplejson.dumps({'status': True})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def set_merge_list(request, id):
    try:
        if request.user.is_superuser:
            mlist = request.session.get('users_merge_list', [])
            if id not in mlist:
                mlist.append(id)
            request.session['users_merge_list'] = mlist
            
            count = len(mlist)
            
            return simplejson.dumps({'status': True, 'content': count})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def get_merge_list(request, id=None):
    try:
        if request.user.is_superuser:
            mlist = request.session.get('users_merge_list', [])
            users = []

            if mlist:
                mlist = list(set(mlist).difference(set([id])))
                request.session['users_merge_list'] = mlist
                
                for i in Profile.objects.select_related('user').filter(user__id__in=mlist).distinct('user__id').order_by('user__id'):
                    acc = []
                    if filter != 'other':
                        for j in i.accounts.all():
                            if j.fullname:
                                acc.append(j.fullname)
                            if j.nickname:
                                acc.append(j.nickname)
                            if j.email:
                                acc.append(j.email)
                            if j.login and '@' in j.login:
                                acc.append(j.login)
                    acc = list(set(sorted(acc, reverse=True)))
                    users.append({'acc': acc, 'user_id': i.user_id})

            return simplejson.dumps({'status': True, 'content': users, 'count': len(mlist)})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def merge_list_merger(request, id):
    try:
        if request.user.is_superuser:
            mlist = request.session.get('users_merge_list', [])
            if mlist and id in mlist:
                mlist = list(set(mlist).difference(set([id])))
                current_profile = Profile.objects.get(user__id=id)
                for i in mlist:
                    merge_profile = Profile.objects.get(user__id=i)
                    merge_func(current_profile, merge_profile)
                    
                request.session['users_merge_list'] = []
                
                return simplejson.dumps({'status': True})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    


def add_left_banner(request):
    try:
        if request.POST and request.is_ajax():
            is_my_profile = False
            is_profile_page = False
            ref = request.META.get('HTTP_REFERER', '/').split('?')[0]

            # если я нахожусь на странице профиля
            if '/user/profile/' in ref:
                is_profile_page = True
                ref = ref.split('/user/profile/')
                # если в урле указан ид юзера
                if ref[1]:
                    # получаю ид юзера
                    user_id = int(ref[1].split('/')[0])
                    # проверяю являюсь ли я этим юзером
                    is_my_profile = True if request.user.id == user_id else False
                # если не указан ид юзера, то это однозначно мой профиль
                else:
                    is_my_profile = True


            id = int(request.POST.get('lbe_new_id', '0').strip())
            name = request.POST.get('lbe_new_name','').strip()[:128]
            file = request.FILES.get('lbe_new_file')
            url = request.POST.get('lbe_new_url','').strip()[:256]
            date_from = request.POST.get('lbe_new_datefrom')
            date_to = request.POST.get('lbe_new_dateto')
            country = int(request.POST.get('coic'))
            city = int(request.POST.get('ciic'))
            sites = request.POST.getlist('lbe_new_sites')

            sites_objs = DjangoSite.objects.filter(pk__in=sites) if sites else [request.current_site,]
                
            
            next = False if not id and not file else True
                    
            data = {'status': False, 'error': ''}

            if name and next:

                if sites_objs or is_my_profile:

                    if request.user.is_superuser or is_my_profile:

                        country_obj = Country.objects.get(pk=country) if country else None
                        if country_obj:
                            if city:
                                city_name = NameCity.objects.get(pk=city)
                                city_obj = City.objects.get(name=city_name, country=country)
                            else:
                                city_obj = None
                        else:
                            city_obj = None

                        if is_my_profile:
                            conflict = SiteBanners.objects.filter(
                                Q(date_from__lte=date_from, date_to__gte=date_to) | 
                                Q(date_from__lte=date_from, date_from__gt=date_to, date_to__lte=date_to) | 
                                Q(date_from__lte=date_from, date_to__gte=date_from, date_to__lte=date_to) | 
                                Q(date_from__gte=date_from, date_from__lte=date_to, date_to__gte=date_to) | 
                                Q(date_from__gte=date_from, date_to__lte=date_to), 
                                country=country_obj, city=city_obj, profile=request.profile, btype='1'
                            ).exclude(pk=id)
                        else: 
                            conflict = SiteBanners.objects.filter(
                                Q(date_from__lte=date_from, date_to__gte=date_to) | 
                                Q(date_from__lte=date_from, date_from__gt=date_to, date_to__lte=date_to) | 
                                Q(date_from__lte=date_from, date_to__gte=date_from, date_to__lte=date_to) | 
                                Q(date_from__gte=date_from, date_from__lte=date_to, date_to__gte=date_to) | 
                                Q(date_from__gte=date_from, date_to__lte=date_to), 
                                country=country_obj, city=city_obj, profile=None, btype='1'
                            ).exclude(pk=id)
                        
                        if conflict:
                            error = u'Для этой страны и города уже установлен баннер в период '
                            for i in conflict:
                                error += '<br />%s - %s' % (i.date_from, i.date_to)
                            data = {'status': True, 'error': error}
                        else:
                        
                            if file:
                                file_name = md5_string_generate(name.encode('utf-8'))
                                if is_profile_page:
                                    file_name = u'%s_%s' % (request.user.id, file_name)
                                file_path = u'%s/%s.swf' % (settings.ADV, file_name)
                                file_path_db = file_path.replace(settings.MEDIA_ROOT,'/upload')
                                
                                destination = open(file_path, 'wb+')
                                for chunk in file.chunks():
                                    destination.write(chunk)
                                destination.close()

                            if id:
                                filter = {'pk': id, 'btype': '1'}
                                if is_profile_page:
                                    filter['profile'] = request.profile
                                obj = SiteBanners.objects.get(**filter)
                                obj.name = name
                                obj.url = url
                                obj.date_from = date_from
                                obj.date_to = date_to
                                obj.country = country_obj
                                obj.city = city_obj
                                
                                if file:
                                    path = '%s/%s' % (settings.MEDIA_ROOT, obj.file.replace('/upload/',''))
                                    try: os.remove(path)
                                    except OSError: pass
                                    obj.file = file_path_db
                                    
                                obj.save()

                                if not is_profile_page:
                                    for i in obj.sites.all():
                                        obj.sites.remove(i)
                            else:

                                obj = SiteBanners.objects.create(
                                    name = name,
                                    file = file_path_db,
                                    url = url,
                                    date_from = date_from,
                                    date_to = date_to,
                                    country = country_obj,
                                    city = city_obj,
                                    btype = '1',
                                )

                            if is_profile_page and is_my_profile:
                                obj.profile = request.profile
                                obj.save()
                                sites = ''
                            else:
                                for i in sites_objs:
                                    obj.sites.add(i)
                                sites = ','.join(sites)

                            swf_obj = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (obj.file, obj.file)

                            city_name, city_id = (city_name.name, city_obj.id) if city_obj else (u'ВСЕ', '0')
                            country_name, country_id = (country_obj.name, country_obj.id) if country_obj else (u'ВСЕ', '0')

                            now = datetime.datetime.now().date()
                            
                            df_y, df_m, df_d = date_from.split('-')
                            dt_y, dt_m, dt_d = date_to.split('-')
                            date_from = datetime.date(int(df_y), int(df_m), int(df_d))
                            date_to = datetime.date(int(dt_y), int(dt_m), int(dt_d))

                            date_style = ''
                            if date_from < now and date_to < now: # прошедшее (серый)
                                date_style = 'background: #E6E6E6;'
                            elif date_from <= now and date_to >= now: # текущее (зеленый)
                                date_style = 'background: #D1ECDA;'
                            elif date_from > now and date_to > now: # будущее (синий)
                                date_style = 'background: #C2E0FF;'

                            dates = u'%s.%s.%s - %s.%s.%s' % (df_d, df_m, df_y, dt_d, dt_m, dt_y,)
                            html = u'<tr id="lbe_id_%s">' % obj.id
                            html += u'<td><div title="%s"><a class="lbe_title nolink">%s</a></div></td>' % (name, name)
                            html += u'<td><div title="%s"><a class="lbe_url" target="_blank">%s</a></div></td>' % (url, url)
                            html += u'<td><div title="%s" class="lbe_date_bl" fr="%s" to="%s"><span style="%s">%s</span><div class="lbe_img">%s</div></div></td>' % (dates, str(date_from), str(date_to), date_style, dates, swf_obj)
                            html += u'<td><div>0</div></td>'
                            html += u'<td><div class="lbe_item_clicks">0</div></td>'
                            html += u'<td><div class="lbe_country" id="%s">%s</div></td><td><div class="lbe_city" id="%s">%s</div></td>' % (country_id, country_name, city_id, city_name)
                            html += u'<td><div class="lbe_item_edit" id="%s"></div></td><td><div class="lbe_item_del"></div></td>' % sites
                            html += u'</tr>'

                            data.update({
                                'status': True,
                                'content': html,
                                'id': id,
                            })
                    
            return HttpResponse(simplejson.dumps(data), content_type='application/json')

        return HttpResponse(simplejson.dumps({}), content_type='application/json')
         
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))




def add_background_adm(request):
    try:
        access = False
        if request.user.is_superuser:
            access = True
        else:
            access = request.user.groups.filter(name='Рекламодатель').exists()

        if access and request.POST and request.is_ajax():
            now = datetime.datetime.now()

            id = int(request.POST.get('lbe_new_adv_id', '0').strip())
            name = request.POST.get('lbe_adv_new_anchor','')
            name = BeautifulSoup(name.strip(), from_encoding='utf-8').text.strip()[:128]
            file = request.FILES.get('lbe_new_file')
            url = request.POST.get('lbe_adv_new_url','')
            url = BeautifulSoup(url.strip(), from_encoding='utf-8').text.strip()[:256]
            budget = int(request.POST.get('lbe_adv_new_budget', 0))
            country = int(request.POST.get('background_new_country'))
            city = [int(i) for i in request.POST.get('background_new_cities','').split(';') if i]
            btype = int(request.POST.get('lbe_new_t', '0').strip())
            start = request.POST.get('lbe_new_start','')
            if start:
                start = datetime.datetime.strptime(start, "%Y-%m-%d")
            close = request.POST.get('close')

            sites_objs = [request.current_site,]
            if request.COOKIES.has_key('profile_adv_filter'):
                value = request.COOKIES['profile_adv_filter']
                site, page, visible = value.split(';')
                if int(site) in (1, 5):
                    sites_objs = [DjangoSite.objects.get(pk=site),]
                

            price = get_adv_price(btype)

            next = False if not id and not file else True
                    
            data = {'status': False, 'error': ''}
            
            if next and name:
                if btype in (3, 4):
                    next = True
                elif price:
                    next = True
            else:
                next = False


            if next:
                country_obj = Country.objects.get(pk=country) if country else None
                city_names = {}
                cities_in_country = 0
                if country_obj:
                    if city:
                        for i in NameCity.objects.filter(pk__in=city).values('pk', 'name', 'city'):
                            city_names[i['city']] = {'name': i['name'], 'id': i['city'], 'obj': None}

                        cities_in_country = City.objects.filter(country=country).count()

                        for i in City.objects.filter(pk__in=city_names.keys(), country=country):
                            city_names[i.pk]['obj'] = i

                

                if btype in (1, 4, 5):
                    obj_name = u'блок'
                elif btype in (2, 3):
                    obj_name = u'фон'

                if btype in (3, 4):
                    filter = {'country': country_obj, 'btype': btype, 'deleted': False, 'profile': request.profile}
                else:
                    filter = {'country': country_obj, 'btype': btype, 'user__personinterface__money__gte': price, 'balance__gte': price, 'deleted': False, 'sites__in': sites_objs}


                if city_names.keys():
                    filter['cities__pk__in'] = city_names.keys()
                else:
                    filter['cities'] = None
                conflict = SiteBanners.objects.filter(**filter).exclude(pk=id)

                conflict_exit = False
                for i in conflict:
                    if btype == 3:
                        conflict_exit = True
                    else:
                        future = i.dtime.date() + datetime.timedelta(days=13)
                        if btype == 2 and start:
                            if start.date() <= future:
                                conflict_exit = True
                        else:
                            if now.date() <= future:
                                conflict_exit = True

                if conflict_exit:
                    if country_obj and city_names.keys():
                        error = u'Для этой страны и города уже установлен %s' % obj_name
                    elif country_obj:
                        error = u'Для этой страны и всех городов уже установлен %s' % obj_name
                    else:
                        error = u'Для всех стран уже установлен %s' % obj_name
                    
                    data = {'status': True, 'error': error}
                else:
                    file_path_db = ''

                    if file:
                        file_name_add = ''
                        if btype == 2:
                            file_name_add = u'bg_'
                        elif btype == 3:
                            file_name_add = u'ubg_'
                        elif btype == 4:
                            file_name_add = u'uadv_'

                        file_format = file.name.split(u'.')[-1]

                        file_name = md5_string_generate(name.encode('utf-8'))

                        file_path = u'%s/%s%s.%s' % (settings.ADV, file_name_add, file_name, file_format)
                        file_path_db = file_path.replace(settings.MEDIA_ROOT,'/upload')
                        
                        destination = open(file_path, 'wb+')
                        for chunk in file.chunks():
                            destination.write(chunk)
                        destination.close()

                    if id:
                        filter = {'pk': id, 'btype': btype, 'deleted': False}
                        obj = SiteBanners.objects.get(**filter)
                        obj.name = name
                        obj.url = url
                        obj.country = country_obj
                        
                        if obj.budget != budget:
                            if obj.budget > budget:
                                difference = obj.budget - budget
                                balance = obj.balance - difference
                                obj.budget = budget
                                obj.balance = balance
                            else:
                                difference = budget - obj.budget
                                balance = obj.balance + difference
                                obj.budget = budget
                                obj.balance = balance

                                if balance > 10 and obj.user.personinterface.money > 10 and btype not in (3, 4):
                                    SubscriberObjects.objects.filter(type='4', obj=obj.id, end_obj=obj.id).update(in_work=True)


                        if file:
                            path = '%s/%s' % (settings.MEDIA_ROOT, obj.file.replace('/upload/',''))
                            try: os.remove(path)
                            except OSError: pass
                            obj.file = file_path_db

                        obj.save()

                    else:

                        obj = SiteBanners.objects.create(
                            name = name,
                            url = url,
                            budget = budget,
                            balance = budget,
                            country = country_obj,
                            btype = btype,
                            user = request.profile,
                            file = file_path_db,
                        )
                        if btype == 2 and start:
                            obj.dtime = start
                            obj.save()

                        if btype in (3, 4):
                            obj.profile = request.profile
                            obj.save()
                        else:
                            # Создается объект в очередь на рассылку
                            SubscriberObjects.objects.create(
                                type = '4',
                                obj = obj.id,
                                end_obj = obj.id,
                            )

                            # Создается подписка автора РК на уведомления
                            from user_registration.func import sha1_string_generate
                            unsubscribe = sha1_string_generate().replace('_','')
                            SubscriberUser.objects.get_or_create(
                                type = '4',
                                obj = obj.id,
                                profile = request.profile,
                                defaults = {
                                    'type': '4',
                                    'obj': obj.id,
                                    'profile': request.profile,
                                    'unsubscribe': unsubscribe,
                                })

                            # Создается объект в очередь на рассылку отчетов
                            SubscriberObjects.objects.create(
                                type = '5',
                                obj = obj.id,
                                end_obj = obj.id,
                            )

                            # Создается подписка автора РК на отчеты
                            unsubscribe = sha1_string_generate().replace('_','')
                            SubscriberUser.objects.get_or_create(
                                type = '5',
                                obj = obj.id,
                                profile = request.profile,
                                defaults = {
                                    'type': '5',
                                    'obj': obj.id,
                                    'profile': request.profile,
                                    'unsubscribe': unsubscribe,
                                })

                        for i in sites_objs:
                            obj.sites.add(i)

                    obj.cities.clear()
                    if cities_in_country > len(city_names.keys()):
                        for i in city_names.values():
                            if i['obj']:
                                obj.cities.add(i['obj'])


                    swf_obj = ''
                    if obj.file:
                        swf_obj = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (obj.file, obj.file)
                    
                    city_name, city_id = (u'ВСЕ', '')
                    if city_names and cities_in_country > len(city_names.keys()):
                        city_names = city_names.values()
                        cnames = ''
                        for ind, i in enumerate(city_names):
                            if ind < 3:
                                if cnames:
                                    cnames += ', '
                                cnames += i['name']
                            if city_id:
                                city_id += ','
                            city_id += str(i['id'])
                        city_name = cnames + '...' if cnames and len(city_names) > 3 else cnames
                    
                    country_name, country_id = (country_obj.name, country_obj.id) if country_obj else (u'ВСЕ', '0')

                    clicks = {}
                    profiles = []
                    for i in SiteBannersClicks.objects.filter(banner__pk=obj.id):
                        if not clicks.get(i.dtime.date()):
                            clicks[i.dtime.date()] = []
                        profiles.append(i.profile)
                        clicks[i.dtime.date()].append({'profile': i.profile.user_id, 'dtime': i.dtime})
                    
                    peoples = org_peoples(set(profiles), dic=True)
                    
                    for k, v in clicks.iteritems():
                        for i in v:
                            user_obj = peoples.get(i['profile'])
                            i['user'] = user_obj['id']
                            i['name'] = user_obj['name']

                    html_clicks = ''
                    click = 0
                    for click_date, click_val in clicks.iteritems():
                        click += len(click_val)
                        html_clicks += u'<tr style="display: none; background: #FFE6CC; font-size: 12px;" id="my_adv_%s">' % obj.id
                        html_clicks += u'<td><div>%s</div></td><td colspan="6"><div>' % click_date
                        for j in click_val:
                            click_time = tmp_date(j['dtime'], 'H:i')
                            html_clicks += u'<div>%s, <a href="/user/profile/%s/" target="_blank">%s</a></div>' % (click_time, j['user'], j['name'])
                        html_clicks += u'</div></td>'
                        html_clicks += u'</tr>'

                    html = u'<tr id="lbe_id_%s">' % obj.id
                    html += u'<td><div title="%s"><a class="lbe_adv_anchor nolink">%s</a></div></td>' % (name, name)
                    html += u'<td class="lbe_url_bl"><div title="%s"><a class="lbe_adv_url" target="_blank">%s</a></div><div class="lbe_img">%s</div></td>' % (url, url, swf_obj)
                    html += u'<td><div>%s</div></td>' % obj.views
                    
                    if click:
                        html += u'<td><div class="lbe_adv_item_clicks"><a title="Подробнее..." id="my_adv_info_%s">%s</a></div></td>' % (obj.id, click)
                    else:
                        html += u'<td><div class="lbe_adv_item_clicks">%s</div></td>' % click
                    
                    text = escape(obj.text) if obj.text else ''
                    style = obj.style if obj.style else ''

                    html += u'<td><div class="lbe_adv_country" id="%s">%s</div></td><td><div class="lbe_adv_city" id="%s">%s</div></td>' % (country_id, country_name, city_id, city_name)
                    html += u'<td><div class="lbe_adv_item_edit" id=""><input type="hidden" class="lbe_adv_text" value="%s"/><input type="hidden" class="lbe_adv_budget" value="%s"/><input type="hidden" class="lbe_adv_style" value="%s"/><input type="hidden" class="lbe_adv_balance" value="%s"/></div></td>' % (text, obj.budget, style, obj.balance)
                    html += u'<td><div class="lbe_item_del"></div></td>'
                    
                    html += u'</tr>'

                    data.update({
                        'status': True,
                        'content': html,
                        'id': id,
                        'close': close,
                    })
            
            return HttpResponse(simplejson.dumps(data), content_type='application/json')

        return HttpResponse(simplejson.dumps({}), content_type='application/json')
         
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def get_background_adv(request):
    try:
        try:
            obj = SiteBanners.objects.get(btype='0', user=request.profile, deleted=False)
        except SiteBanners.DoesNotExist:
            obj = None

        price = get_adv_price(0)

        html = u'''
            <div class="left_banner_editor_bl-adv" style="display: block;">
            <b>Убрать фон</b>
            <div class="lbe_adv_info">
            Вы можете убрать фон сайта (рекламу) за оплату в %s руб/сутки<br />
            Средства списываются с Вашего виртуального счета в нашей системе.<br />
            Фон сменится, как только на Вашем счету будет достаточно средств для оплаты за 1 сутки.<br />
            Пополнить свой счёт можно двумя способами: <br />
            1 - активностью на наших сайтах <a href="http://www.kinoafisha.ru/" target="_blank">Киноафиша</a> и <a href="http://kinoinfo.ru/" target="_blank">Киноинфо</a> (отзывы, голосования, лайки, рецензии)<br />
            2 - перечислением любой суммы на любой из наших счетов ниже: <br /><br />
            <div class="paypal_logo" title="PayPal">kinoafisharu@gmail.com</div>
            <div class="sberbank_logo" title="СберКарта">4276 4600 1280 4881</div><br />
            <div class="vtb24_logo" title="ВТБ24">4272 2904 4769 4951</div>
            <div class="webmoney_logo" title="WebMoney">R164037944803</div><br />
            В назначении платежа укажите <b>"KINOAFISHA_ID: %s"</b><br />''' % (price, request.user.id)
        
        if not request.acc_list['acc']:
            html += u'<br />Рекомендуем Вам <a href="/user/login/">авторизоваться</a> перед оформлением заказа<br />'

        if obj:
            html += u'<input type="button" value="Мой заказ" class="lbe_adv_bg_new_btn" /></div>'
            balance_show = ''
            obj_id = obj.id
            balance = obj.balance
            budget = obj.budget
        else:
            html += u'<input type="button" value="Оформить заказ" class="lbe_adv_bg_new_btn" /></div>'
            balance_show = u'style="display: none;"'
            obj_id = 0
            balance = 0
            budget = 0

        html += u'''
            <div class="lbe_adv_new">
                <div style="width: 370px; display: inline-block; vertical-align:top;">
                    <ul>
                        <li>Бюджет:</li>
                        <li><input type="text" value="" class="lbe_adv_bg_new_budget" style="width:50px;" /> руб. <b><span class="lbe_adv_new_days"></span></b></li>
                    </ul>
                    <ul class="lbe_adv_balance_bl" %s>
                        <li>Остаток:</li>
                        <li><span class="lbe_adv_bg_new_balance" style="width:50px; padding: 0 5px 0 5px;"></span> руб. <b><span class="lbe_adv_new_balance_days"></span></b></li>
                    </ul>
                </div>

                <br /><br />
                <input type="hidden" value="%s" class="lbe_new_adv_price" />
                <input type="hidden" value="%s" class="lbe_new_adv_id" />
                <input type="hidden" value="%s" class="lbe_new_adv_bg_balance" />
                <input type="hidden" value="%s" class="lbe_new_adv_bg_budget" />
                <input type="button" value="Назад" class="lbe_new_bg_cancel" />
                <input type="button" value="Сохранить" class="lbe_new_adv_bg_add" />
                <span class="lbe_load"></span>
                <div class="clear"></div>
                
                <div class="lbe_new_error"></div>
            </div>
            '''  % (balance_show, price, obj_id, balance, budget)

        html += u'</div>'

        return simplejson.dumps({
            'status': True,
            'content': html,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def disable_adv_bg(request, budget, id):
    try:
        price = get_adv_price(0)
        now = datetime.datetime.now()
        id = int(id)
        budget = int(budget.strip())
        if budget and budget >= 0:
            interface = request.profile.personinterface
            balance = budget
            if id:
                obj = SiteBanners.objects.get(
                    pk = id,
                    btype = '0',
                    user = request.profile,
                    deleted = False,
                )
                if obj.budget != budget:
                    if obj.budget > budget:
                        difference = obj.budget - budget
                        balance = obj.balance - difference
                        obj.budget = budget
                        obj.balance = balance
                    else:
                        nxt = False
                        if obj.bg_disable_dtime_to.date() <= now.date() and obj.balance < price and interface.money >= price:
                            nxt = True

                        difference = budget - obj.budget
                        balance = obj.balance + difference
                        obj.budget = budget
                        obj.balance = balance

                        if nxt:
                            to = now + datetime.timedelta(days=1)
                            interface.money -= price
                            interface.save()
                            obj.bg_disable_dtime_to = to
                            obj.balance -= price
                            obj.spent += price

                    obj.save()
            else:
                spent = False
                if interface.money >= price and balance >= price:
                    interface.money -= price
                    interface.save()
                    to = now + datetime.timedelta(days=1)
                    balance = balance - price
                    spent = True

                obj = SiteBanners.objects.create(
                    name = 'Убрать фон',
                    budget = budget,
                    balance = balance,
                    btype = '0',
                    user = request.profile,
                    bg_disable_dtime_to = to,
                )

                if spent:
                    obj.spent += price
                    obj.save()

            return simplejson.dumps({
                'status': True,
                'id': obj.id,
                'budget': obj.budget,
                'balance': obj.balance,
            })

        return simplejson.dumps({})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def add_adv_block(request, id, anchor, url, txt, budget, country, city, style, t, close):
    try:
        access = False
        if request.user.is_superuser:
            access = True
        else:
            access = request.user.groups.filter(name='Рекламодатель').exists()

        if access:
            id = int(id)
            details = BeautifulSoup(anchor.strip(), from_encoding='utf-8').text.strip()[:128]
            url = BeautifulSoup(url.strip(), from_encoding='utf-8').text.strip()[:256]
            txt = BeautifulSoup(txt.strip(), from_encoding='utf-8').text.strip()[:150]
            budget = int(budget)
            country = int(country)
            city = [int(i) for i in city]
            
            styles = ['lbe_blue', 'lbe_green', 'lbe_orange', 'lbe_pink', 'lbe_black']
            if style not in styles:
                style = ''

            sites_objs = [request.current_site,]
            if request.COOKIES.has_key('profile_adv_filter'):
                value = request.COOKIES['profile_adv_filter']
                site, page, visible = value.split(';')
                if int(site) in (1, 5):
                    sites_objs = [DjangoSite.objects.get(pk=site),]

            price = get_adv_price(t)

            if anchor and url and txt and budget and price:
                country_obj = Country.objects.get(pk=country) if country else None
                city_names = {}
                cities_in_country = 0
                if country_obj:
                    if city:
                        for i in NameCity.objects.filter(pk__in=city).values('pk', 'name', 'city'):
                            city_names[i['city']] = {'name': i['name'], 'id': i['city'], 'obj': None}

                        cities_in_country = City.objects.filter(country=country).count()

                        for i in City.objects.filter(pk__in=city_names.keys(), country=country):
                            city_names[i.pk]['obj'] = i

                if id:
                    filter = {'pk': id, 'btype': t, 'deleted': False}
                    if not request.user.is_superuser:
                        filter['user'] = request.profile
                    obj = SiteBanners.objects.get(**filter)
                    obj.name = anchor
                    if obj.budget != budget:
                        if obj.budget > budget:
                            difference = obj.budget - budget
                            balance = obj.balance - difference
                            obj.budget = budget
                            obj.balance = balance
                        else:
                            difference = budget - obj.budget
                            balance = obj.balance + difference
                            obj.budget = budget
                            obj.balance = balance

                    obj.url = url
                    obj.text = txt
                    obj.country = country_obj
                    
                    obj.cities.clear()
                    if cities_in_country > len(city_names.keys()):
                        for i in city_names.values():
                            if i['obj']:
                                obj.cities.add(i['obj'])

                    obj.style = style
                    obj.save()
                else:
                    obj = SiteBanners.objects.create(
                        name = anchor,
                        url = url,
                        text = txt,
                        budget = budget,
                        balance = budget,
                        country = country_obj,
                        btype = t,
                        user = request.profile,
                        style = style,
                    )
                    if cities_in_country > len(city_names.keys()):
                        for i in city_names.values():
                            if i['obj']:
                                obj.cities.add(i['obj'])

                    for i in sites_objs:
                        obj.sites.add(i)

                city_name, city_id = (u'ВСЕ', '')
                if city_names and cities_in_country > len(city_names.keys()):
                    city_names = city_names.values()
                    cnames = ''
                    for ind, i in enumerate(city_names):
                        if ind < 3:
                            if cnames:
                                cnames += ', '
                            cnames += i['name']
                        if city_id:
                            city_id += ','
                        city_id += str(i['id'])
                    city_name = cnames + '...' if cnames and len(city_names) > 3 else cnames


                country_name, country_id = (country_obj.name, country_obj.id) if country_obj else (u'ВСЕ', '0')


                clicks = {}
                profiles = []
                for i in SiteBannersClicks.objects.filter(banner__pk=obj.id):
                    if not clicks.get(i.dtime.date()):
                        clicks[i.dtime.date()] = []
                    profiles.append(i.profile)
                    clicks[i.dtime.date()].append({'profile': i.profile.user_id, 'dtime': i.dtime})

                peoples = org_peoples(set(profiles), dic=True)

                for k, v in clicks.iteritems():
                    for i in v:
                        user_obj = peoples.get(i['profile'])
                        i['user'] = user_obj['id']
                        i['name'] = user_obj['name']

                

                html_clicks = ''
                click = 0
                for click_date, click_val in clicks.iteritems():
                    click += len(click_val)
                    html_clicks += u'<tr style="display: none; background: #FFE6CC; font-size: 12px;" id="my_adv_%s">' % obj.id
                    html_clicks += u'<td><div>%s</div></td><td colspan="6"><div>' % click_date
                    for j in click_val:
                        click_time = tmp_date(j['dtime'], 'H:i')
                        html_clicks += u'<div>%s, <a href="/user/profile/%s/" target="_blank">%s</a></div>' % (click_time, j['user'], j['name'])
                    html_clicks += u'</div></td>'
                    html_clicks += u'</tr>'


                html = u'<tr id="lbe_id_%s">' % obj.id
                html += u'<td><div title="%s" class="lbe_adv_anchor">%s</div></td>' % (escape(obj.name), escape(obj.name))
                html += u'<td class="lbe_url_bl"><div title="%s"><a class="lbe_adv_url" target="_blank">%s</a></div></td>' % (obj.url, obj.url)
                html += u'<td><div>%s</div></td>' % obj.views
                if click:
                    html += u'<td><div class="lbe_adv_item_clicks"><a title="Подробнее..." id="my_adv_info_%s">%s</a></div></td>' % (obj.id, click)
                else:
                    html += u'<td><div class="lbe_adv_item_clicks">%s</div></td>' % click
                html += u'<td><div class="lbe_adv_country" id="%s">%s</div></td><td><div class="lbe_adv_city" id="%s">%s</div></td>' % (country_id, country_name, city_id, city_name)
                html += u'<td><div class="lbe_adv_item_edit" id=""><input type="hidden" class="lbe_adv_text" value="%s"/><input type="hidden" class="lbe_adv_budget" value="%s"/><input type="hidden" class="lbe_adv_style" value="%s"/><input type="hidden" class="lbe_adv_balance" value="%s"/></div></td>' % (escape(obj.text), obj.budget, obj.style, obj.balance)
                html += u'<td><div class="lbe_item_del"></div></td>'
                html += u'</tr>'
               
                html += html_clicks


                return simplejson.dumps({
                    'status': True,
                    'content': html,
                    'id': id,
                    'close': close,
                })

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def add_adv_code_block(request, id, anchor, txt, t, show):
    try:
        access = False
        if request.user.is_superuser:
            access = True

        if access:
            id = int(id)
            title = BeautifulSoup(anchor.strip(), from_encoding='utf-8').text.strip()[:128]
            txt = txt.strip()

            sites_objs = [request.current_site,]
            if request.COOKIES.has_key('profile_adv_filter'):
                value = request.COOKIES['profile_adv_filter']
                site, page, visible = value.split(';')
                if int(site) in (1, 5):
                    sites_objs = [DjangoSite.objects.get(pk=site),]

            if anchor and txt:
                if show:
                    to_date = None
                else:
                    to_date = datetime.datetime.today() + relativedelta(years=300)
                
                if id:
                    filter = {'pk': id, 'btype': t, 'deleted': False}
                    obj = SiteBanners.objects.get(**filter)
                    obj.name = anchor
                    obj.text = txt
                    obj.bg_disable_dtime_to = to_date
                    obj.save()
                else:
                    obj = SiteBanners.objects.create(
                        name = anchor,
                        text = txt,
                        btype = t,
                        user = request.profile,
                        bg_disable_dtime_to = to_date,
                    )
                    for i in sites_objs:
                        obj.sites.add(i)

                return simplejson.dumps({
                    'status': True,
                    'content': '',
                    'id': id,
                    'close': 1,
                })

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_lbe_list(request):
    try:

        is_my_profile = False
        is_profile_page = False
        ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
        # если я нахожусь на странице профиля
        if '/user/profile/' in ref:
            is_profile_page = True
            ref = ref.split('/user/profile/')
            # если в урле указан ид юзера
            if ref[1]:
                # получаю ид юзера
                user_id = int(ref[1].split('/')[0])
                # проверяю являюсь ли я этим юзером
                is_my_profile = True if request.user.id == user_id else False
            # если не указан ид юзера, то это однозначно мой профиль
            else:
                is_my_profile = True


        if request.user.is_superuser or is_profile_page:
            now = datetime.datetime.now().date()
            
            if is_my_profile:
                banners = SiteBanners.objects.select_related('country', 'city').filter(profile=request.profile, btype='1').order_by('id')
            else:
                banners = SiteBanners.objects.select_related('country', 'city').filter(profile=None, text=None, btype='1').order_by('id')
            

            clicks = {}
            banners_ids = [i.id for i in banners]
            for i in SiteBannersClicks.objects.filter(banner__pk__in=banners_ids):
                if not clicks.get(i.banner_id):
                    clicks[i.banner_id] = 0
                clicks[i.banner_id] += 1


            html = u'<table class="lbe_list_tbl modern_tbl">'
            html += u'<th>Название</th><th>URL</th><th>Период показа</th><th>Показ</th><th>Клик</th><th>Страна</th><th>Город</th><th></th><th></th>'

            if banners:
                for i in banners:
                    
                    swf_obj = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (i.file, i.file)

                    date_from = i.date_from
                    date_to = i.date_to
                    dates = u'%s - %s' % (date_from.strftime('%d.%m.%Y'), date_to.strftime('%d.%m.%Y'))
                    date_style = ''
                    if date_from < now and date_to < now: # прошедшее (серый)
                        date_style = 'background: #E6E6E6;'
                    elif date_from <= now and date_to >= now: # текущее (зеленый)
                        date_style = 'background: #D1ECDA;'
                    elif date_from > now and date_to > now: # будущее (синий)
                        date_style = 'background: #C2E0FF;'
                    
                    sites = [str(j.id) for j in i.sites.all()]
                    sites = ','.join(sites)
                    
                    if is_my_profile:
                        sites = ''

                    country, country_id = (i.country.name, i.country.id) if i.country else (u'ВСЕ', '0')
                    
                    if i.city:
                        city_obj = i.city.name.get(status=1)
                        city, city_id = (city_obj.name, i.city_id)
                    else:
                        city, city_id = (u'ВСЕ', '0')
                    
                    click = clicks.get(i.id, 0)

                    html += u'<tr id="lbe_id_%s">' % i.id
                    html += u'<td><div title="%s"><a class="lbe_title nolink">%s</a></div></td>' % (i.name, i.name)
                    html += u'<td><div title="%s"><a class="lbe_url" target="_blank">%s</a></div></td>' % (i.url, i.url)
                    html += u'<td><div title="%s" class="lbe_date_bl" fr="%s" to="%s"><span style="%s">%s</span><div class="lbe_img">%s</div></div></td>' % (dates, date_from, date_to, date_style, dates, swf_obj)
                    html += u'<td><div>%s</div></td>' % i.views
                    html += u'<td><div class="lbe_item_clicks">%s</div></td>' % click
                    html += u'<td><div class="lbe_country" id="%s">%s</div></td><td><div class="lbe_city" id="%s">%s</div></td>' % (country_id, country, city_id, city)
                    html += u'<td><div class="lbe_item_edit" id="%s"></div></td>' % sites
                    html += u'<td><div class="lbe_item_del"></div></td>'
                    html += u'</tr>'
                html += u'</table>'
            else:
                html += u'</table><br /><span class="lbe_list_empty">Пусто</span>'
 
            return simplejson.dumps({'status': True, 'content': html})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def del_lbe_item(request, id, btype=1):
    try:
        if request.user.is_superuser:
            filter = {'pk': id, 'btype': btype, 'deleted': False}

            if not request.user.is_superuser:
                if btype in (3, 4): # фон или рекламный блок (страница юзера)
                    filter['profile'] = request.profile
                else:
                    filter['user'] = request.profile

            try:
                obj = SiteBanners.objects.get(**filter)
            except SiteBanners.DoesNotExist:
                obj = None

            if obj:
                '''
                if obj.file:
                    path = '%s/%s' % (settings.MEDIA_ROOT, obj.file.replace('/upload/',''))
                    try: os.remove(path)
                    except OSError: pass
                SiteBannersClicks.objects.filter(banner=obj).delete()
                obj.delete()
                '''
                obj.deleted = True
                obj.save()

                SubscriberObjects.objects.filter(type='4', obj=obj.id, end_obj=obj.id).update(in_work=False)

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

'''
@dajaxice_register
def get_lbe_adv(request):
    try:
        # 3 рубля за 1 клик
        price = 3

        styles = [
            {'adv_class': '', 'name': 'Классический'},
            {'adv_class': 'lbe_blue', 'name': 'Синий'},
            {'adv_class': 'lbe_green', 'name': 'Зеленый'},
            {'adv_class': 'lbe_orange', 'name': 'Оранжевый'},
            {'adv_class': 'lbe_pink', 'name': 'Розовый'},
            {'adv_class': 'lbe_black', 'name': 'Черный'},
        ]

        style_html = '<select class="lbe_adv_new_style">'
        for i in styles:
            selected = ''
            if i['name'] == 'Классический':
                selected = ' selected'
            style_html += '<option value="%s"%s>%s</option>' % (i['adv_class'], selected, i['name'])
        style_html += '</select>'

        exist = SiteBanners.objects.filter(user=request.profile, btype='1').count()

        html = u'Вы можете добавить на сайт свой рекламный блок<br />Цена за 1 клик = %s.00 руб. (переход посетителя по объявлению в сутки)<br />' % price
        html += u'Средства списываются с Вашего виртуального счета в нашей системе.<br />'
        html += u'Блок начнет отображаться, как только на Вашем счету будет достаточно средств для оплаты 1 клика.<br />'
        html += u'Пополнить свой счёт можно двумя способами: <br />'
        html += u'1 - активностью на наших сайтах <a href="http://www.kinoafisha.ru/" target="_blank">Киноафиша</a> и <a href="http://kinoinfo.ru/" target="_blank">Киноинфо</a> (отзывы, голосования, лайки, рецензии)<br />'
        html += u'2 - перечислением любой суммы на любой из наших счетов ниже: <br /><br />'
        html += u'<div class="paypal_logo" title="PayPal">kinoafisharu@gmail.com</div>'
        html += u'<div class="sberbank_logo" title="СберКарта">4276 4600 1280 4881</div><br />'
        html += u'<div class="vtb24_logo" title="ВТБ24">4272 2904 4769 4951</div>'
        html += u'<div class="webmoney_logo" title="WebMoney">R164037944803</div><br />'
        html += u'В назначении платежа укажите <b>"KINOAFISHA_ID: %s"</b><br />' % request.user.id

        if not request.acc_list['acc']:
            html += u'<br />Рекомендуем Вам <a href="/user/login/">авторизоваться</a> перед созданием рекламного блока<br />'

        html += u'<input type="button" value="Добавить блок" class="lbe_adv_new_btn" />'

        visible = 'style="display: none;"' if not exist else ''

        html += u'<input type="button" value="Мои блоки" class="lbe_adv_my_btn" %s />' % visible

        return simplejson.dumps({'content': html, 'price': price, 'styles': style_html})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
'''

@dajaxice_register
def get_adv_conditions(request, txt=None):
    try:
        conditions_file = '%s/adv_conditions.txt' % settings.API_EX_PATH

        edit_btn = ''
        if request.user.is_superuser:
            if txt is not None:
                with open(conditions_file, 'w') as f:
                    f.write(txt.encode('utf-8'))

            edit_btn = u'<div style="padding-top: 10px;"><input type="button" value="Редактировать" class="adv_conditions_edit" /></div>'



        text = u'''Вы можете добавить на сайт рекламный блок<br />Цена за 1 клик = 3.00 руб. (переход посетителя по объявлению в сутки)<br />
            Средства списываются с Вашего виртуального счета в нашей системе.<br />
            Блок начнет отображаться, как только на Вашем счету будет достаточно средств для оплаты 1 клика.<br />
            Пополнить свой счёт можно двумя способами: <br />
            1 - активностью на наших сайтах <a href="http://www.kinoafisha.ru/" target="_blank">Киноафиша</a> и <a href="http://kinoinfo.ru/" target="_blank">Киноинфо</a> (отзывы, голосования, лайки, рецензии)<br />
            2 - перечислением любой суммы на любой из наших счетов ниже:'''


        try:
            with open(conditions_file, 'r') as f:
                text = f.read().decode('utf-8')
        except IOError:
            with open(conditions_file, 'w') as f:
                f.write(text.encode('utf-8'))
        
        adv_info = u'''
            <div class="adv_conditions_txt">
                %s
            </div>
            <br />
            <div class="paypal_logo" title="PayPal">kinoafisharu@gmail.com</div>
            <div class="sberbank_logo" title="СберКарта">4276 4600 1280 4881</div><br />
            <div class="vtb24_logo" title="ВТБ24">4272 2904 4769 4951</div>
            <div class="webmoney_logo" title="WebMoney">R164037944803</div><br />
            В назначении платежа укажите <b>"KINOAFISHA_ID: %s"</b><br />''' % (text, request.user.id)
        
        if not request.acc_list['acc']:
            adv_info += u'<br />Рекомендуем Вам <a href="/user/login/">авторизоваться</a> перед созданием рекламного блока<br />'
        
        adv_info = u'<div style="width: 700px; font-size: 14px; line-height: 25px;">%s%s</div>' % (adv_info, edit_btn)
        
        return simplejson.dumps({'content': adv_info})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_my_blocks(request, btype=1, admin=False):
    try:
        price = get_adv_price(btype)

        if btype in (1, 6):
            filter = {'user': request.profile, 'btype': btype, 'deleted': False}
        elif btype == 2:
            filter = {'sites': request.current_site, 'btype': btype, 'deleted': False}
        elif btype == 4:
            filter = {'btype': btype, 'profile': request.profile, 'deleted': False}
        elif btype == 5:
            if request.user.is_superuser:
                filter = {'btype': btype, 'deleted': False}

        banners = SiteBanners.objects.select_related('country').filter(**filter).order_by('id')

        adv_info = ''
        if btype in (1, 4, 6):
            if btype in (1, 6):
                banners = banners.exclude(style=None)
                adv_info_add = u'сайт свой'
            else:
                adv_info_add = u'свою страницу'

            adv_info += u'Вы можете добавить на %s рекламный блок<br />Цена за 1 клик = %s.00 руб. (переход посетителя по объявлению в сутки)<br />' % (adv_info_add, price)
            adv_info += u'Средства списываются с Вашего виртуального счета в нашей системе.<br />'
            adv_info += u'Блок начнет отображаться, как только на Вашем счету будет достаточно средств для оплаты 1 клика.<br />'
            adv_info += u'Пополнить свой счёт можно двумя способами: <br />'
            adv_info += u'1 - активностью на наших сайтах <a href="http://www.kinoafisha.ru/" target="_blank">Киноафиша</a> и <a href="http://kinoinfo.ru/" target="_blank">Киноинфо</a> (отзывы, голосования, лайки, рецензии)<br />'
            adv_info += u'2 - перечислением любой суммы на любой из наших счетов ниже: <br /><br />'
            adv_info += u'<div class="paypal_logo" title="PayPal">kinoafisharu@gmail.com</div>'
            adv_info += u'<div class="sberbank_logo" title="СберКарта">4276 4600 1280 4881</div><br />'
            adv_info += u'<div class="vtb24_logo" title="ВТБ24">4272 2904 4769 4951</div>'
            adv_info += u'<div class="webmoney_logo" title="WebMoney">R164037944803</div><br />'
            adv_info += u'В назначении платежа укажите <b>"KINOAFISHA_ID: %s"</b><br />' % request.user.id



        if not request.acc_list['acc']:
            adv_info += u'<br />Рекомендуем Вам <a href="/user/login/">авторизоваться</a> перед созданием рекламного блока<br />'

        
        adv_info += u'''
            <input type="button" value="Добавить блок" class="lbe_adv_new_btn" />
            <input type="button" value="Мои блоки" class="lbe_adv_my_btn" />'''

        banners_ids = [i.id for i in banners]
        profiles = []

        clicks = {'model': SiteBannersClicks, 'data': {}}
        views = {'model': SiteBannersViews, 'data': {}}

        for item in (clicks, views):
            for i in item['model'].objects.select_related('profile', 'banner', 'banner__user').filter(banner__pk__in=banners_ids):
                if not item['data'].get(i.banner_id):
                    item['data'][i.banner_id] = {}

                try:
                    item_date = i.dtime.date()
                except AttributeError:
                    item_date = i.dtime

                if not item['data'][i.banner_id].get(item_date):
                    item['data'][i.banner_id][item_date] = []

                if i.profile:
                    uid = i.profile.user_id 
                    profiles.append(i.profile)
                else:
                    uid = None

                item['data'][i.banner_id][item_date].append({'profile': uid, 'dtime': i.dtime})
    
        clicks = clicks['data']
        views = views['data']

        '''
        clicks = {}
        banners_ids = [i.id for i in banners]
        profiles = []
        for i in SiteBannersClicks.objects.select_related('profile').filter(banner__pk__in=banners_ids):
            if not clicks.get(i.banner_id):
                clicks[i.banner_id] = {}

            if not clicks[i.banner_id].get(i.dtime.date()):
                clicks[i.banner_id][i.dtime.date()] = []

            if i.profile:
                uid = i.profile.user_id 
                profiles.append(i.profile)
            else:
                uid = None

            clicks[i.banner_id][i.dtime.date()].append({'profile': uid, 'dtime': i.dtime})
        
        views = {}
        for i in SiteBannersViews.objects.select_related('profile').filter(banner__pk__in=banners_ids):
            if not views.get(i.banner_id):
                views[i.banner_id] = {}

            if not views[i.banner_id].get(i.dtime):
                views[i.banner_id][i.dtime] = []

            if i.profile:
                uid = i.profile.user_id 
                profiles.append(i.profile)
            else:
                uid = None

            views[i.banner_id][i.dtime].append({'profile': uid})
        '''


        peoples = org_peoples(set(profiles), dic=True)
        
        for item in (clicks, views):
            for banner, value in item.iteritems():
                for k, v in value.iteritems():
                    for i in v:
                        user_obj = peoples.get(i['profile'])
                        if user_obj:
                            i['user'] = user_obj['id']
                            i['name'] = user_obj['name']
                        else:
                            i['user'] = ''
                            i['name'] = u'Не найден'

        countries = {}
        for i in list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name')):
            countries[i['id']] = {'id': i['id'], 'name': i['name'], 'cities': []}

        cities_all = {}
        for i in list(NameCity.objects.filter(status=1, city__country__id__in=countries.keys()).order_by('name').values('id', 'city__id', 'name', 'city__country')):
            countries[i['city__country']]['cities'].append(i)
            cities_all[i['city__id']] = i['name']

        if btype in (1, 4, 5, 6):
            html_title = u'Управление рекламными блоками'
        elif btype in (2, 3):
            html_title = u'Управление фоном'


        html = u'<div class="left_banner_editor_bl-adv">'
        html += u'<b>%s</b>' % html_title
        html += u'<div class="lbe_adv_info">%s</div>' % adv_info
        html += u'<div class="lbe_adv_my">'
        html += u'<table class="lbe_list_tbl modern_tbl">'
        th_name = u'Анкор' if btype in (1, 6) else u'Название'
        html += u'<tr><th>%s</th><th>URL</th><th>Показ</th><th>Клик</th><th>Страна</th><th>Город</th><th></th><th></th></tr>' % th_name

        def get_count(data, id):
            count = 0
            xdata = data.get(id, {})
            xdata = collections.OrderedDict(sorted(xdata.items()))
            for k, v in xdata.iteritems():
                count += len(v)
            return count, xdata

        if banners:
            for i in banners:
                country_name, country_id = (i.country.name, i.country.id) if i.country else (u'ВСЕ', '0')
                city_name, city_id = (u'ВСЕ', '')
                cities_in_country = 0
                if int(country_id):
                    cities_in_country = len(countries[country_id]['cities'])
                    cities = list(i.cities.all().values_list('pk', flat=True))
                    if cities and cities_in_country > len(cities):
                        cnames = ''
                        for ind, j in enumerate(cities):
                            city_obj = cities_all.get(j, '')
                            if ind < 3:
                                if cnames:
                                    cnames += ', '
                                cnames += city_obj
                            if city_id:
                                city_id += ','
                            city_id += str(j)
                        city_name = cnames + '...' if cnames and len(cities) > 3 else cnames


                click, clicks_data = get_count(clicks, i.id)
        
                html_clicks = ''
                for click_date, click_val in clicks_data.iteritems():
                    html_clicks += u'''
                        <tr style="display: none; background: #FFE6CC; font-size: 12px;" id="my_adv_%s">
                        <td><div>%s</div></td><td colspan="7"><div>''' % (i.id, click_date)
                    for j in click_val:
                        #click_time = tmp_date(j['dtime'], 'H:i')
                        if j['user']:
                            html_clicks += u'<div><a href="/user/profile/%s/" target="_blank">%s</a></div>' % (j['user'], j['name'])
                        else:
                            html_clicks += u'<div>%s</div>' % j['name']
                    html_clicks += u'</div></td></tr>'


                view, views_data = get_count(views, i.id)
        
                html_views = ''
                for view_date, view_val in views_data.iteritems():
                    html_views += u'''
                        <tr style="display: none; background: #FFE6CC; font-size: 12px;" id="my_adv_v%s">
                        <td><div>%s</div></td><td colspan="7"><div>''' % (i.id, view_date)
                    for j in click_val:
                        if j['user']:
                            html_views += u'<div><a href="/user/profile/%s/" target="_blank">%s</a></div>' % (j['user'], j['name'])
                        else:
                            html_views += u'<div>%s</div>' % j['name']
                    html_views += u'</div></td></tr>'
                

                swf_obj = ''
                if i.file:
                    swf_obj = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (i.file, i.file)

                html += u'<tr id="lbe_id_%s">' % i.id
                if btype in (1, 6):
                    html += u'''
                        <td><div title="%s" class="lbe_adv_anchor">%s</div></td>
                        <td class="lbe_url_bl"><div title="%s"><a class="lbe_adv_url" target="_blank">%s</a></div></td>
                        ''' % (escape(i.name), escape(i.name), i.url, i.url)
                else:
                    html += u'''
                        <td><div title="%s"><a class="lbe_adv_anchor nolink">%s</a></div></td>
                        <td class="lbe_url_bl"><div title="%s"><a class="lbe_adv_url" target="_blank">%s</a></div><div class="lbe_img">%s</div></td>
                        ''' % (escape(i.name), escape(i.name), i.url, i.url, swf_obj)

                if view:
                    html += u'<td><div class="lbe_adv_item_clicks"><a title="Подробнее..." id="my_adv_info_v%s">%s</a></div></td>' % (i.id, view)
                else:
                    html += u'<td><div class="lbe_adv_item_clicks">%s</div></td>' % view

                if click:
                    html += u'<th style="display: none; font-size: 12px;" id="my_adv_v%s" colspan="8">Клики</th>'
                    html += u'<td><div class="lbe_adv_item_clicks"><a title="Подробнее..." id="my_adv_info_%s">%s</a></div></td>' % (i.id, click)
                else:
                    html += u'<td><div class="lbe_adv_item_clicks">%s</div></td>' % click

                html += u'<td><div class="lbe_adv_country" id="%s">%s</div></td><td><div class="lbe_adv_city" id="%s">%s</div></td>' % (country_id, country_name, city_id, city_name)
                html += u'<td><div class="lbe_adv_item_edit" id="" title="Редактировать"><input type="hidden" class="lbe_adv_text" value="%s"/><input type="hidden" class="lbe_adv_budget" value="%s"/><input type="hidden" class="lbe_adv_style" value="%s"/><input type="hidden" class="lbe_adv_balance" value="%s"/></div></td>' % (escape(i.text), i.budget, i.style, i.balance)
                html += u'<td><div class="lbe_item_del" title="Удалить"></div></td>'
                html += u'</tr>'
                if html_views:
                    html += u'<tr style="display: none; font-size: 12px;" id="my_adv_v%s"><th colspan="8">Показы</th></tr>' % i.id
                    html += html_views
                if html_clicks:
                    html += u'<tr style="display: none; font-size: 12px;" id="my_adv_%s"><th colspan="8">Клики</th></tr>' % i.id
                    html += html_clicks

            html += u'</table>'
        else:
            html += u'</table><br /><span class="lbe_list_empty">Пусто</span>'

        html += u'<br /><input type="button" value="Назад" class="lbe_adv_back" style="float: right;"/> <input type="button" value="Добавить блок" class="lbe_adv_new_btn lbe_adv_new_btn-mini"/><div class="clear"></div>'

        html += u'</div>' # lbe_adv_my


        style_html = ''
        adv_description = ''
        adv_preview = ''
        class_btn_save = ''
        upload_form_start = ''
        upload_form_end = ''
        upload_btn = ''

        if btype in (1, 6):
            styles = [
                {'adv_class': '', 'name': u'Классический'},
                {'adv_class': u'lbe_blue', 'name': u'Синий'},
                {'adv_class': u'lbe_green', 'name': u'Зеленый'},
                {'adv_class': u'lbe_orange', 'name': u'Оранжевый'},
                {'adv_class': u'lbe_pink', 'name': u'Розовый'},
                {'adv_class': u'lbe_black', 'name': u'Черный'},
            ]

            style_html = u'<select class="lbe_adv_new_style">'
            for i in styles:
                selected = ''
                if i['name'] == u'Классический':
                    selected = u' selected'
                style_html += u'<option value="%s"%s>%s</option>' % (i['adv_class'], selected, i['name'])
            style_html += u'</select>'

            style_html = u'''
                <ul>
                    <li>Стиль:</li>
                    <li class="lbe_adv_new_style_bl">%s</li>
                </ul>''' % style_html


            adv_description = u'''
                <ul>
                    <li>Описание: <span id="lbe_adv_chars"></span></li>
                    <li><textarea class="lbe_adv_new_text" style="width:230px; height: 70px;" maxlength="150" onkeyup="txt_len_counter(this, '#lbe_adv_chars');"></textarea></li>
                </ul>
                '''

            adv_preview = u'''
                <div class="lbe_adv_preview">
                    <div class="left_banner_title">Реклама</div>
                    <div class="lbe_adv_pre_tmp">
                        <span>Preview</span>
                        <a href="#" taget="_blank" rel="nofollow" class="lbe_adv_pre_anchor"></a>
                        <div class="lbe_adv_pre_text"></div>
                    </div>
                </div>
                '''

            class_btn_save = u'lbe_new_adv_add'
        else:
            adv_description = u'''
                <ul>
                    <li>Файл:</li>
                    <li><input type="file" class="background_new_file" name="lbe_new_file" /></li>
                </ul>
                '''
            csrf = get_token(request)
            class_btn_save = u'background_new_add'
            upload_form_start = u'''
                <form class="lbe_new_form" action="/background/uploader/" method="post" enctype="multipart/form-data" id="form">
                    <div style="display:none">
                        <input type="hidden" name="csrfmiddlewaretoken" value="%s" />
                    </div>
                ''' % csrf
            upload_form_end = u'</form>'

            upload_btn = u'''
                <input type="hidden" value="" name="background_new_country" />
                <input type="hidden" value="" name="background_new_cities" />
                <input type="submit" name="lbe_upld" value="" style="display: none;"/>
                '''


        html += u'''
        <div class="lbe_adv_new">
            %s
            <div style="width: 370px; display: inline-block; vertical-align:top;">
                <ul>
                    <li>%s:</li>
                    <li><input type="text" value="" name="lbe_adv_new_anchor" class="lbe_adv_new_anchor" maxlength="40" style="width:230px;" /></li>
                </ul>
                <ul>
                    <li>URL:</li>
                    <li><input type="text" value="http://" name="lbe_adv_new_url" class="lbe_adv_new_url" style="width:230px;" placeholder="http://" /></li>
                </ul>
                %s
                <ul>
                    <li>Бюджет:</li>
                    <li><input type="text" value="" name="lbe_adv_new_budget" class="lbe_adv_new_budget" style="width:50px;" /> руб. <b><span class="lbe_adv_new_clicks"></span></b></li>
                </ul>
                <ul class="lbe_adv_balance_bl">
                    <li>Остаток:</li>
                    <li><span class="lbe_adv_new_balance" style="width:50px; padding: 0 5px 0 5px;"></span> руб. <b><span class="lbe_adv_new_balance_clicks"></span></b></li>
                </ul>
                <ul>
                    <li>Страна:</li>
                    <li class="lbe_adv_new_target_country"></li>
                </ul>
                <ul>
                    <li>Города:</li>
                    <li class="lbe_adv_new_target_city">
                        <select class="multiselect" multiple="multiple" >
                        </select>
                    </li>
                </ul>
                %s
            </div>

            %s

            <br /><br />
            <input type="hidden" value="%s" class="lbe_new_adv_price" />
            <input type="hidden" value="0" class="lbe_new_adv_id" name="lbe_new_adv_id" />
            <input type="hidden" value="%s" class="lbe_new_t" name="lbe_new_t" />
            <input type="button" value="Назад" class="lbe_new_cancel" />
            <input type="button" value="Назад" class="lbe_edit_cancel" />
            <input type="button" value="Сохранить" class="%s" />
            <span class="lbe_load"></span>
            %s
            <div class="clear"></div>
            
            <div class="lbe_new_error"></div>
            %s
        </div>
        ''' % (upload_form_start, th_name, adv_description, style_html, adv_preview, price, btype, class_btn_save, upload_btn, upload_form_end)

        html += u'</div>' # left_banner_editor_bl-adv
        
        return simplejson.dumps({'status': True, 'content': html, 't': int(btype)})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def adv_click(request, id):
    try:
        now = datetime.datetime.now()
        next = True
        try:
            last = SiteBannersClicks.objects.filter(profile=request.profile, banner__pk=id).order_by('-dtime')[0]
            last = last.dtime
            if last.date() == now.date() and last.hour == now.hour and last.minute == now.minute:
                if (last.second + 5) >= now.second:
                    next = False
        except IndexError: pass

        if next:
            SiteBannersClicks.objects.create(profile=request.profile, banner_id=id)
        
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def adv_adv_click(request, id):
    try:
        
        now = datetime.datetime.now()
        next = True

        try:
            banner = SiteBanners.objects.get(pk=id, deleted=False)
        except SiteBanners.DoesNotExist:
            next = False

        if next:
            price = get_adv_price(banner.btype)
            try:
                banner = SiteBanners.objects.get(pk=id, deleted=False, user__personinterface__money__gte=price, balance__gte=price)
            except SiteBanners.DoesNotExist:
                next = False


        if next:
            try:
                user = Profile.objects.select_related('personinterface').get(pk=banner.user_id)
                interface = user.personinterface
                if interface.money >= price and banner.balance >= price:
                    banner_click, created = SiteBannersClicks.objects.get_or_create(
                        profile = request.profile, 
                        banner = banner,
                        defaults = {
                            'profile': request.profile, 
                            'banner': banner,
                        })
                    if created:
                        if price:
                            interface.money -= price
                            interface.save()
                            banner.balance -= price
                            banner.spent += price
                            banner.save()

            except SiteBannersClicks.MultipleObjectsReturned:
                sbv = None
                for i in SiteBannersClicks.objects.filter(banner=banner, profile=request.profile):
                    if sbv:
                        i.delete()
                    else:
                        sbv = i
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_adv_item_edit(request, new, btype, id):
    try:

        btype = int(btype)
        price = get_adv_price(btype)

        banner = None

        bg_start = ''
        bg_hide = ''
        if id:
            bg_hide = 'style="display: none;"'
            bg_start = 'disabled'
            filter = {'pk': id, 'deleted': False, 'btype': btype}
            if not request.user.is_superuser:
                filter['user'] = request.profile
            banner = SiteBanners.objects.select_related('country').get(**filter)


        countries = {}
        for i in list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name')):
            countries[i['id']] = {'id': i['id'], 'name': i['name'], 'cities': []}

        cities_all = {}
        for i in list(NameCity.objects.filter(status=1, city__country__id__in=countries.keys()).order_by('name').values('id', 'city__id', 'name', 'city__country')):
            countries[i['city__country']]['cities'].append(i)
            cities_all[i['city__id']] = i['name']


        html = u'<div class="left_banner_editor_bl-adv">'

        tabs = ''
        if request.user.is_superuser and btype in (1, 5, 7):

            constructor_activate, code_activate = ('', u'adv_tab_active') if btype == 7 else (u'adv_tab_active', '')
            constructor_class, code_class = (u'adv_tab_constructor', u'adv_tab_code') if not banner else ('', '')

            tabs = u'''
                <div class="adv_tabs">
                    <div class="adv_tab_l %s %s">Конструктор</div>
                    <div class="adv_tab_r %s %s">Встроить код</div>
                </div>''' % (constructor_class, constructor_activate, code_activate, code_class)
        
        country_id = '0'
        city_id = ''

        if banner:
            if banner.country:
                country_id = banner.country.id 
            if int(country_id):
                cities_in_country = len(countries[long(country_id)]['cities'])
                cities = list(banner.cities.all().values_list('pk', flat=True))

                if cities and cities_in_country > len(cities):
                    for ind, j in enumerate(cities):
                        if city_id:
                            city_id += ','
                        city_id += str(j)

        style_html, adv_description, adv_preview, class_btn_save, upload_form_start, upload_form_end, upload_btn = (u'', u'', u'', u'', u'', u'', u'')

        banner_style, banner_text, banner_url, banner_name, banner_budget, banner_balance, budget_clicks, balance_clicks, banner_id = (u'', u'', u'', u'', u'', u'', u'0', u'0', u'0')

        if banner:
            banner_style = banner.style
            banner_text = banner.text
            banner_url = banner.url
            banner_name = banner.name
            banner_budget = banner.budget
            banner_balance = banner.balance

            budget_clicks = int(banner.budget / price) if price else 0
            balance_clicks = int(banner.balance / price) if price else 0
            banner_id = banner.id

        if btype in (1, 6):

            styles = [
                {'adv_class': '', 'name': u'Классический'},
                {'adv_class': u'lbe_blue', 'name': u'Синий'},
                {'adv_class': u'lbe_green', 'name': u'Зеленый'},
                {'adv_class': u'lbe_orange', 'name': u'Оранжевый'},
                {'adv_class': u'lbe_pink', 'name': u'Розовый'},
                {'adv_class': u'lbe_black', 'name': u'Черный'},
            ]

            style_html = u'<select class="lbe_adv_new_style" name="style">'
            for i in styles:
                selected = ''
                if i['adv_class'] == banner_style:
                    selected = u' selected'
                style_html += u'<option value="%s"%s>%s</option>' % (i['adv_class'], selected, i['name'])
            style_html += u'</select>'

            style_html = u'''
                <ul>
                    <li>Стиль:</li>
                    <li class="lbe_adv_new_style_bl">%s</li>
                </ul>''' % style_html


            adv_description = u'''
                <ul>
                    <li>Описание: <span id="lbe_adv_chars"></span></li>
                    <li><textarea class="lbe_adv_new_text" style="width:230px; height: 70px;" maxlength="150" onkeyup="txt_len_counter(this, '#lbe_adv_chars');">%s</textarea></li>
                </ul>
                ''' % banner_text


            adv_preview = u'''
                <div class="lbe_adv_preview">
                    <div class="left_banner_title">Реклама</div>
                    <div class="lbe_adv_pre_tmp %s">
                        <span></span>
                        <a href="%s" taget="_blank" rel="nofollow" class="lbe_adv_pre_anchor">%s</a>
                        <div class="lbe_adv_pre_text">%s</div>
                    </div>
                </div>
                ''' % (banner_style, banner_url, banner_name, banner_text)

            class_btn_save = u'lbe_new_adv_add'
        else:
            adv_description = u'''
                <ul>
                    <li>Файл:</li>
                    <li><input type="file" class="background_new_file" name="lbe_new_file" /></li>
                </ul>
                '''

            if btype == 2:
                today = datetime.datetime.today().date()
                if banner:
                    today = banner.dtime.date()

                adv_description += u'''
                <link rel="stylesheet" href="/static/base/css/datepicker.css" type="text/css" media="screen" />
                <ul %s>
                    <li>Старт:</li>
                    <li><input type="text" class="background_new_start" name="lbe_new_start" value="%s" style="width: 80px;" %s /></li>
                </ul>
                ''' % (bg_hide, today, bg_start)

            csrf = get_token(request)
            class_btn_save = u'background_new_add'
            upload_form_start = u'''
                <form class="lbe_new_form" action="/background/uploader/" method="post" enctype="multipart/form-data" id="form">
                    <div style="display:none">
                        <input type="hidden" name="csrfmiddlewaretoken" value="%s" />
                    </div>
                ''' % csrf
            upload_form_end = u'</form>'

            upload_btn = u'''
                <input type="hidden" value="" name="background_new_country" />
                <input type="hidden" value="" name="background_new_cities" />
                <input type="submit" name="lbe_upld" value="" style="display: none;"/>
                '''

        balance_html = ''
        if banner and price:
            balance_html = u'''
                <ul class="lbe_adv_balance_bl">
                    <li>Остаток:</li>
                    <li><span class="lbe_adv_new_balance" style="width:50px; padding: 0 5px 0 5px;">%s</span> руб. <b><span class="lbe_adv_new_balance_clicks"> = кликов: %s</span></b></li>
                </ul>
                ''' % (banner_balance, balance_clicks)

        budget_html = ''
        if price and (banner or new):
            budget_html = u'''
                <ul>
                    <li>Бюджет:</li>
                    <li><input type="text" value="%s" name="lbe_adv_new_budget" class="lbe_adv_new_budget" style="width:50px;" /> руб. <b><span class="lbe_adv_new_clicks">= кликов: %s</span></b></li>
                </ul>''' % (banner_budget, budget_clicks)


        lbe_adv_new_show = ''

        if request.user.is_superuser and btype in (1, 5, 7):
            show_status = 'checked'
            if banner and banner.bg_disable_dtime_to:
                show_status = ''

            lbe_adv_code = ''
            if btype == 7:
                lbe_adv_new_show = u'style="display: none;"'
                lbe_adv_code = u'style="display: block;"'

            tabs += u'''
            <div class="lbe_adv_code" %s>
                <ul>
                    <li>Название:</li>
                    <li><input type="text" value="%s" name="lbe_adv_new_code_anchor" class="lbe_adv_new_code_anchor" style="width:230px;" /></li>
                </ul>
                <ul>
                    <li>Код:</li>
                    <li><textarea class="lbe_adv_new_code_text" style="width:530px; height: 180px;">%s</textarea></li>
                </ul>
                <ul>
                    <li>Включить:</li>
                    <li><input type="checkbox" class="lbe_adv_new_code_show" %s /></li>
                </ul>
            
                <br /><br />
                <input type="hidden" value="%s" class="lbe_new_adv_code_id" name="lbe_new_adv_code_id" />
                <input type="hidden" value="7" class="lbe_new_code_t" name="lbe_new_code_t" />
                <input type="button" value="Сохранить" class="lbe_new_adv_code_add"/>
                <span class="lbe_load"></span>
                <div class="clear"></div>
                <div class="lbe_new_error"></div>
            </div>''' % (lbe_adv_code, banner_name, banner_text, show_status, banner_id)

            if btype == 7:
                banner_style = ''
                banner_text = ''
                banner_url = ''
                banner_name = ''
                banner_budget = 0
                banner_balance = 0
                budget_clicks = 0
                balance_clicks = 0
                banner_id = 0


        html += u'''
        %s
        <div class="lbe_adv_new" %s>
            %s
            <div style="width: 370px; display: inline-block; vertical-align:top;">
                <ul>
                    <li>Название:</li>
                    <li><input type="text" value="%s" name="lbe_adv_new_anchor" class="lbe_adv_new_anchor" maxlength="40" style="width:230px;" /></li>
                </ul>
                <ul>
                    <li>URL:</li>
                    <li><input type="text" value="%s" name="lbe_adv_new_url" class="lbe_adv_new_url" style="width:230px;" placeholder="http://" /></li>
                </ul>
                %s
                %s
                %s
                <ul>
                    <li>Страна:</li>
                    <li class="lbe_adv_new_target_country"></li>
                </ul>
                <ul>
                    <li>Города:</li>
                    <li class="lbe_adv_new_target_city">
                        <select class="multiselect" multiple="multiple" >
                        </select>
                    </li>
                </ul>
                %s
            </div>
            %s
            <br /><br />
            <input type="hidden" value="%s" class="lbe_new_adv_price" />
            <input type="hidden" value="%s" class="lbe_new_adv_id" name="lbe_new_adv_id" />
            <input type="hidden" value="%s" class="lbe_new_t" name="lbe_new_t" />
            <input type="hidden" value="1" name="close" />
            <input type="button" value="Сохранить" class="%s" />
            <span class="lbe_load"></span>
            %s
            <div class="clear"></div>
            <div class="lbe_new_error"></div>
            %s
        </div>
        ''' % (tabs, lbe_adv_new_show, upload_form_start, banner_name, banner_url, adv_description, budget_html, balance_html, style_html, adv_preview, price, banner_id, btype, class_btn_save, upload_btn, upload_form_end)

        html += u'</div>' # left_banner_editor_bl-adv
    
        return simplejson.dumps({'status': True, 'content': html, 't': int(btype), 'country': country_id, 'city': city_id, 'id': banner_id})

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def get_cities_adv(request, country=None, city=[]):
    try:
        if country:
            city_id = city
            country_id = long(country)
        else:
            city_id = [request.current_user_city_id]
            country_id = request.current_user_country_id
        
        countries = list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name'))
        cities = list(NameCity.objects.filter(status=1, city__country__id=country_id).order_by('name').values('id', 'city__id', 'name'))

        html_countries = u'<select class="countries_list_adv">'
        html_countries += u'<option value="0">ВСЕ</option>'
        for i in countries:
            selected = u' selected' if i['id'] == country_id else ''
            html_countries += u'<option value="%s"%s>%s</option>' % (i['id'], selected, i['name'])
        html_countries += '</select>'
    
        html_cities = []
        for i in cities:
            selected = True if str(i['city__id']) in city_id else False
            html_cities.append({'key': i['id'], 'name': i['name'], 'selected': selected})
        
        return simplejson.dumps({
            'countries': html_countries,
            'cities': html_cities,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_adv_item_clicks(request, id):
    try:
        filter = {'pk': id, 'deleted': False}
        if not request.user.is_superuser:
            filter['user'] = request.profile
        
        banner = SiteBanners.objects.get(**filter)
        profiles = []
        clicks = {}
        for i in SiteBannersClicks.objects.select_related('profile', 'banner', 'banner__user').filter(banner=banner):
            try:
                item_date = i.dtime.date()
            except AttributeError:
                item_date = i.dtime

            if not clicks.get(item_date):
                clicks[item_date] = []

            if i.profile:
                uid = i.profile.user_id 
                profiles.append(i.profile)
            else:
                uid = None

            clicks[item_date].append({'profile': uid, 'dtime': i.dtime})
        

        peoples = org_peoples(set(profiles), dic=True)


        html = u'''
        <table class="lbe_list_tbl modern_tbl" style="font-size: 12px; width: 500px;">
        <tr id="my_adv_%s">
            <th>Дата</th>
            <th><input type="checkbox" class="check_all_next" /> <div class="my_adv_messenger">Отправить сообщение</div> <span class="my_adv_messenger_w"></span></th>
        </tr>''' % banner.id
        

        clicks = collections.OrderedDict(sorted(clicks.items(), reverse=True))

        for key_date, value_list in clicks.iteritems():
            html += u'<tr id="my_adv_%s"><td style="vertical-align: top;"><div>%s</div></td><td><div>' % (banner.id, key_date)

            for i in value_list:
                user_obj = peoples.get(i['profile'])
                if user_obj:
                    html += u'<div><input type="checkbox" class="check_all_item" value="%s" /> <a href="/user/profile/%s/" target="_blank">%s (%s)</a></div>' % (user_obj['id'], user_obj['id'], user_obj['name'], user_obj['city'])
                else:
                    html += u'<div>Не найден</div>'

            html += u'</div></td></tr>'
        
        return simplejson.dumps({
            'content': html
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_schedule_part(request, part, date):
    try:
        from slideblok.views import releasedata
        from news.views import cut_description

        
        today = datetime.datetime.now()
        set_date = date
        if set_date:
            try:
                set_day, set_month, set_year = set_date.split('.')
                set_date = datetime.date(int(set_year), int(set_month), int(set_day))
            except ValueError:
                set_date = None
       
            if set_date < today.date():
                set_date = None

            if set_date:
                city_id = request.current_user_city_id
                nextday = None
                if part == 'part_day':
                    set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 12, 0, 0)
                    nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 18, 0, 0)
                elif part == 'part_evening':
                    set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 18, 0, 0)
                    nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 22, 0, 0)
                elif part == 'part_night':
                    set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 22, 0, 0)
                    nextday = set_date + datetime.timedelta(days=1)
                    nextday = datetime.datetime(nextday.year, nextday.month, nextday.day, 6, 0, 0)

                if nextday and city_id:
                    filter = {
                        'dtime__gte': set_date, 
                        'dtime__lt': nextday,
                        'cinema__city__city__id': city_id, 
                        'cinema__cinema__name__status': 1, 
                        'cinema__cinema__city__name__status': 1
                    }

                    
                    film_list = set(list(SourceSchedules.objects.filter(**filter).exclude(film__source_id=0).distinct('film__kid').values_list('film__kid', flat=True)))

                    xfilm = {}
                    for i in film_list:
                        xfilm[i] = {}

                    data = releasedata(xfilm, {}, persons=False, likes=False, trailers=False, reviews=False, poster_size='small')

                    films_dict = {}
                    for i in data:
                        txt_cut = cut_description(i['descript'], True, 150)
                        i['descript_cut'] = txt_cut
                        films_dict[i['id']] = i

                    filter['film__kid__in'] = films_dict.keys()
                    sch = SourceSchedules.objects.filter(**filter).exclude(film__source_id=0).values('film__kid', 'cinema__cinema', 'cinema__cinema__name__name', 'dtime', 'sale', 'film__name', 'cinema__cinema__city__name__name', 'source_obj__url').distinct('cinema__cinema__city').order_by('dtime')
                    
                    schedules = []
                    for i in sch:
                        showtime = i['dtime'].time()
                        showdate = i['dtime'].date()
                        film = films_dict.get(i['film__kid'])
                        cinema = i['cinema__cinema__name__name']

                        if len(cinema) > 30:
                            cinema_size = 10
                        elif len(cinema) > 24:
                            cinema_size = 12
                        elif len(cinema) > 18:
                            cinema_size = 13
                        else:
                            cinema_size = 13

                        schedules.append({
                            'dtime': i['dtime'],
                            'film': film,
                            'cinema': cinema,
                            'cinema_size': cinema_size,
                        })
                    
                    html = ''
                    count = 1
                    for i in schedules:
                        
                        bgcolor, count = (u'#EBEBEB;', 0) if count == 2 else ('#F2F2F2;', 1)
                        count += 1

                        film_url = u'http://%s/film/%s/' % (request.get_host(), i['film']['id'])
                        film_poster = ''
                        if i['film']['posters']:
                            film_poster = u'<img src="%s" style="width: 50px;"/>' % i['film']['posters'] 

                        film_countries = ''
                        for j in i['film']['countries']:
                            if film_countries:
                                film_countries += '/'
                            film_countries += u'%s' % j

                        film_genres = ''
                        for j in i['film']['genres']:
                            if film_genres:
                                film_genres += '/'
                            film_genres += u'%s' % j

                        film_runtime = u'%s мин.' % i['film']['runtime'] if i['film']['runtime'] else ''

                        film_details = ''
                        if film_countries:
                            film_details = u'<em>%s</em>' % film_countries

                        if film_genres:
                            if film_details:
                                film_details += u','
                            film_details += u'<em>%s</em>' % film_genres

                        if film_runtime:
                            if film_details:
                                film_details += u','
                            film_details += u'<em>%s</em>' % film_runtime

                        film_rating = ''
                        if i['film']['rating']['show_imdb']:
                            film_rating = u'IMDb - %s' % i['film']['rating']['show_imdb']
                        if i['film']['rating']['rotten']:
                            if film_rating:
                                film_rating += u' / '
                            film_rating += u'RottenTomatoes - %s' % i['film']['rating']['rotten']
                        if i['film']['rating']['show_ir']:
                            if film_rating:
                                film_rating += u' / '
                            film_rating += u'Киномэтры - %s' % i['film']['rating']['show_ir']

                        if not film_rating:
                            film_rating = u'нет'

                        film_rate = str(i['film']['rate']) if i['film']['rate'] else u'?'
                            
                        html += u'<div id="film_info2018" style="background: %s"><div class="film_info-schedules"><ul><li class="film_info-sch"><div>%s</div><span style="font-size: %spx;">%s</span></li><li class="film_info-img"><a href="%s" target="_blank"><div class="film_info-data-img" id="poster" style="width: 50px;">%s</div></a></li><li class="film_info-data"><div><h2 id="film_name"><a href="%s" target="_blank">%s</a></h2><div id="film_details">%s</div><div id="film_info-description">%s</div></div></li><li class="film_info-rate"><div class="rate_color_%s"><div class="pen_rate"><b title="Репутация фильма: %s">%s</b></div></div><span>%s</span></li></ul></div><div class="clear"></div></div>' % (bgcolor, tmp_date(i['dtime'], 'H:i'), i['cinema_size'], i['cinema'], film_url, film_poster, film_url, i['film']['name_ru'], film_details, i['film']['descript_cut'], i['film']['rate'], film_rating, film_rate, i['film']['limit'])

                    if not html:
                        html = u'Нет'

                    return simplejson.dumps({'content': html, 'part': part})



        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_booking_article(request, id):
    try:
        try:
            article = News.objects.get(pk=id, autor=request.profile, visible=True, orgsubmenu__booker_profile=request.profile)
        except News.DoesNotExist:
            pass
        else:
            html = u'''
                <div class="txt_wrapper" style="width: 600px; font-size: 14px;">
                    <h3>%s</h3>
                    <br />
                    <div class="btxt">
                    %s
                    </div>
                    <div style="margin-top: 20px; background: #f2f2f2; padding: 5px;">
                        <div class="edit_btn" onclick="booking_article_edit(%s)" title="Редактировать"></div>
                        <div class="delete_btn" onclick="booking_article_remove(%s)" title="Удалить" style="float: right;"></div>
                        <input type="hidden" value="%s" class="booking-article-id" />
                    </div>
                </div>''' % (article.title, article.text, article.id, article.id, article.id)

            return simplejson.dumps({
                'status': True,
                'content': html,
                'title': article.title,
                'text': article.text,
            })

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def booking_article_remove(request, id):
    try:
        articles = News.objects.filter(pk=id, autor=request.profile, orgsubmenu__booker_profile=request.profile)
        if articles:
            articles.delete()
            return simplejson.dumps({
                'status': True,
                'content': id,
            })
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def booking_get_hall_data(request, id, parent, date_from=datetime.date.today()):
    try:
        date_from = datetime.datetime.strptime(str(date_from), '%Y-%m-%d')
        date_to = date_from + datetime.timedelta(days=1)

        cinemas = {}
        for i in Cinema.objects.filter(bookingsettings__profile=request.profile).distinct('pk').values('id', 'code', 'bookercinemas__permission'):
            cinemas[i['id']] = {'id': i['id'], 'kid': i['code'], 'name': '', 'access': i['bookercinemas__permission']}

        hall = Hall.objects.filter(pk=id, cinema__pk__in=cinemas.keys()).exists()

        if hall:
            schedules = BookingSchedules.objects.select_related('hall').filter(hall__id=id, dtime__gte=date_from)
            schedules_ids = [i.id for i in schedules]

            source_films_data = list(SourceFilms.objects.filter(bookingschedules__pk__in=schedules_ids).values('kid', 'bookingschedules'))
            source_kids = set([i['kid'] for i in source_films_data])

            names = {}
            for i in FilmsName.objects.using('afisha').filter(film_id__pk__in=source_kids, status=1, type__in=(1, 2)):
                if not names.get(i.film_id_id):
                    names[i.film_id_id] = {}
                names[i.film_id_id][i.type] = i.name

            source_films = {}
            for i in source_films_data:
                if not source_films.get(i['bookingschedules']):
                    source_films[i['bookingschedules']] = []
                name = names.get(i['kid'])
                name = name[2] if name.get(2) else name[1]
                source_films[i['bookingschedules']].append({'kid': i['kid'], 'name': name})

            data = {}
            for i in schedules:
                if not data.get(i.hall_id):
                    cinema = cinemas.get(i.hall.cinema_id)
                    data[i.hall_id] = {'hall_id': i.hall_id, 'dates': {}, 'date_range': {}, 'cinema': cinema}
                films = source_films.get(i.id, [])
                #data[i.hall_id]['schedules'].append({'time': i.dtime.strftime('%H:%M'), 'films': films})

                if not data[i.hall_id]['dates'].get(i.dtime.date()):
                    data[i.hall_id]['dates'][i.dtime.date()] = {'date': i.dtime.date(), 'ids': [], 'times': []}

                data[i.hall_id]['dates'][i.dtime.date()]['times'].append({'time': i.dtime, 'films': films, 'tmp': i.temp, 'id': i.id})
                data[i.hall_id]['dates'][i.dtime.date()]['ids'].append('%s%s' % (i.dtime.time(), films))
                data[i.hall_id]['dates'][i.dtime.date()]['ids'].sort()


            html = ''
            for i in data.values():
                i['dates'] = sorted(i['dates'].values(), key=operator.itemgetter('date'))

                old_date_times = []
                sch_date_from = None
                sch_date_to = None
                for j in i['dates']:
                    set_dates = True
                    if old_date_times:
                        if old_date_times == j['ids']:
                            sch_date_to = j['date']
                            set_dates = False
                    
                    if set_dates:
                        sch_date_from = j['date']
                        sch_date_to = j['date']

                    old_date_times = j['ids']

                    if not i['date_range'].get(sch_date_from):
                        i['date_range'][sch_date_from] = {'from': sch_date_from, 'to': None, 'times': j['times']}
                    i['date_range'][sch_date_from]['to'] = sch_date_to

            d_range = []
            html = ''
            for i in data.values():
                
                for j in sorted(i['date_range'].values(), key=operator.itemgetter('from')):
                    visible = '' if html else u'style="display: block;"'

                    html += u'<div class="bsi" id="from_%s" %s>' % (j['from'], visible)
                    
                    for t in sorted(j['times'], key=operator.itemgetter('time')):
        
                        films_html = ''
                        for f in t['films']:
                            films_html += u'%s ' % f['name']

                        time_html = u'%s, %s' % (t['time'].strftime('%H:%M'), films_html)
                        if not t['tmp']:
                            time_html = u'<b>%s</b>' % time_html

                        edit_class = u' booking-sch-item-edit' if t['tmp'] and i['cinema']['access'] else ''
                        
                        html += u'<div class="booking-sch-item%s" id="%s">%s</div>' % (edit_class, t['id'], time_html)

                    html += u'</div>'

                    d_range.append({
                        'from': str(j['from']),
                        'from_str': tmp_date(j['from'], 'j b'),
                        'to_str': tmp_date(j['to'], 'j b'),
                    })

                if i['cinema']['access'] == '1':
                    html += u'<div class="booking-sch-item booking-add-schedules-btn">Добавить сеанс</div>'

            return simplejson.dumps({
                'status': True,
                'hall_id': id,
                'parent_id': parent,
                'content': html,
                'date_range': d_range,
            })
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


def booking_get_schedule_by_id(request, id):
    schedule = BookingSchedules.objects.select_related('hall').get(pk=id)

    access = BookerCinemas.objects.filter(cinema__pk=schedule.hall.cinema_id, permission='1', settings__profile=request.profile).exists()

    films = [i.kid for i in schedule.films.all()]

    schedules = BookingSchedules.objects.filter(hall=schedule.hall, films__kid__in=films).order_by('dtime')

    data = {'hall_id': schedule.hall_id, 'dates': {}, 'date_range': {}}

    for i in schedules:
        if not data['dates'].get(i.dtime.date()):
            data['dates'][i.dtime.date()] = {'date': i.dtime.date(), 'ids': [], 'films': films, 'objs': []}

        data['dates'][i.dtime.date()]['objs'].append(i.id)
        data['dates'][i.dtime.date()]['ids'].append('%s%s' % (i.dtime.time(), films))
        data['dates'][i.dtime.date()]['ids'].sort()

    old_date_times = []
    sch_date_from = None
    sch_date_to = None

    # формируем диапозон дат с одинкаовыми сеансами
    for j in sorted(data['dates'].values(), key=operator.itemgetter('date')):
        set_dates = True
        if old_date_times:
            if old_date_times == j['ids']:
                sch_date_to = j['date']
                set_dates = False
        
        if set_dates:
            sch_date_from = j['date']
            sch_date_to = j['date']

        old_date_times = j['ids']

        if not data['date_range'].get(sch_date_from):
            data['date_range'][sch_date_from] = {'from': sch_date_from, 'to': None, 'films': j['films'], 'objs': []}
        data['date_range'][sch_date_from]['to'] = sch_date_to
        data['date_range'][sch_date_from]['objs'].extend(j['objs'])

    data['date_range'] = sorted(data['date_range'].values(), key=operator.itemgetter('from'))


    d_range = {}
    for i in data['date_range']:
        if schedule.dtime.date() >= i['from'] and schedule.dtime.date() <= i['to']:
            d_range = i
    
    d_range['hall_id'] = schedule.hall_id
    d_range['id'] = id
    d_range['objs'] = list(set(d_range['objs']))
    d_range['from'], d_range['to'] = (str(d_range['from']), str(d_range['to']))

    return d_range



@dajaxice_register
def booking_add_sch(request, halls, data, edit, real):
    try:
        next = False

        if edit:
            d_range = booking_get_schedule_by_id(request, edit)

            halls = [long(i) for i in halls]
            if len(halls) == 1:
                if d_range['hall_id'] != halls[0]:
                    # заменить в сеансах старый hall на новый
                    hall_obj = Hall.objects.get(pk=halls[0])
                    BookingSchedules.objects.filter(pk__in=d_range['objs']).update(hall=hall_obj)
            else:
                if d_range['hall_id'] not in halls:
                    # заменить в сеансах старый hall на новый (первый в списке halls), + добавить новые залы
                    hall_obj = Hall.objects.get(pk=halls[0])
                    del halls[0]
                    BookingSchedules.objects.filter(pk__in=d_range['objs']).update(hall=hall_obj)
                else:
                    # добавить сеансы в новые залы
                    halls.remove(d_range['hall_id'])
                next = True

            

            films = data[0]['films']
            if len(films) == 1:
                if d_range['films'] != films[0]:
                    # заменить в сеансах фильмы на новые
                    film_obj = SourceFilms.objects.get(kid=films[0], source_obj__url='http://www.kinoafisha.ru/')
                    for i in BookingSchedules.objects.filter(pk__in=d_range['objs']):
                        i.films.clear()
                        i.films.add(film_obj)
            else:
                if set(d_range['films']) != set(films):
                    for_del = list(set(d_range['films']) - set(films))
                    for_add = list(set(films) - set(d_range['films']))
                    for_del = SourceFilms.objects.filter(kid__in=for_del, source_obj__url='http://www.kinoafisha.ru/')
                    for_add = SourceFilms.objects.filter(kid__in=for_add, source_obj__url='http://www.kinoafisha.ru/')
                    for i in BookingSchedules.objects.filter(pk__in=d_range['objs']):
                        i.films.remove(*for_del)
                        i.films.add(*for_add)

            
            old_date_from = datetime.datetime.strptime(d_range['from'], "%Y-%m-%d").date()
            old_date_to = datetime.datetime.strptime(d_range['to'], "%Y-%m-%d").date()
            new_date_from = datetime.datetime.strptime(data[0]['from'], "%Y-%m-%d").date()
            new_date_to = datetime.datetime.strptime(data[0]['to'], "%Y-%m-%d").date()
            
            date_for_del = []
            date_for_add = []

            if old_date_from != new_date_from or old_date_to != new_date_to:
                
                if old_date_from < new_date_from:
                    while old_date_from < new_date_from:
                        tmp = {'from': old_date_from, 'to': old_date_from}
                        old_date_from = old_date_from + datetime.timedelta(days=1)
                        tmp['to'] = old_date_from
                        date_for_del.append(tmp)
                else:
                    while old_date_from > new_date_from:
                        date_for_add.append(new_date_from)
                        new_date_from = new_date_from + datetime.timedelta(days=1)

                if old_date_to < new_date_to:
                    while old_date_to < new_date_to:
                        old_date_to = old_date_to + datetime.timedelta(days=1)
                        date_for_add.append(old_date_to)
                else:
                    while old_date_to > new_date_to:
                        tmp = {'from': old_date_to, 'to': old_date_to + datetime.timedelta(days=1)}
                        date_for_del.append(tmp)
                        old_date_to = old_date_to - datetime.timedelta(days=1)
                        
                for i in date_for_del:
                    BookingSchedules.objects.filter(pk__in=d_range['objs'], dtime__gte=i['from'], dtime__lt=i['to']).delete()

            if date_for_add:
                next = True

        else:
            next = True



        temp = False if real else True

        if edit:
            BookingSchedules.objects.filter(pk__in=d_range['objs']).update(temp=temp)

        if next:

            halls = Hall.objects.filter(pk__in=halls)

            films_ids = []
            for i in data:
                films_ids.extend(i['films'])

            films = {}
            for i in SourceFilms.objects.filter(kid__in=set(films_ids)):
                films[i.kid] = i

            schedules = []

            for i in data:
                date_from = datetime.datetime.strptime(i['from'], "%Y-%m-%d").date()
                date_to = datetime.datetime.strptime(i['to'], "%Y-%m-%d").date()

                while date_to >= date_from:
                    dtime = datetime.datetime(date_from.year, date_from.month, date_from.day, 10)
                    i['dtime'] = dtime

                    for hall in halls:
                        filmsids = "".join(i['films'])

                        sch_id = '%s%s%s' % (dtime, hall.id, filmsids)
                        sch_id = sch_id.replace(' ', '').decode('utf-8')

                        if sch_id not in schedules:
                            
                            obj, created = BookingSchedules.objects.get_or_create(
                                unique = sch_id,
                                defaults = {
                                    'unique': sch_id,
                                    'hall': hall,
                                    'dtime': dtime,
                                    'temp': temp,
                                })
                            
                            if created:
                                for film in i['films']:
                                    film_obj = films.get(int(film))
                                    obj.films.add(film_obj)

                            schedules.append(sch_id)
                            
                    date_from = date_from + datetime.timedelta(days=1)

        return simplejson.dumps({
            'status': True,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def booking_edit_sch(request, id):
    try:
        d_range = booking_get_schedule_by_id(request, id)

        return simplejson.dumps({
            'status': True,
            'content': d_range,
            'id': id,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def get_booking_del_sch(request, id):
    try:
        if request.user.is_superuser:
            access = True
        else:
            access = request.user.groups.filter(name='Букер').exists()

        if access:
            d_range = booking_get_schedule_by_id(request, id)
            BookingSchedules.objects.filter(pk__in=d_range['objs']).delete()

        return simplejson.dumps({
            'status': True,
        })

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))