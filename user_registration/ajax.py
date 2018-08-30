# -*- coding: utf-8 -*- 
import operator
from collections import defaultdict

from django.utils import simplejson
from django.conf import settings
from django.db.models import Q
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _

from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup

from api.func import get_client_ip
from user_registration.views import *
from base.models import *
from base.models_dic import City, Country
from kinoinfo_folder.func import low
from release_parser.func import actions_logger
from user_registration.func import org_peoples

@dajaxice_register
def user_reg(request, app_name, platform, display, geo_co, geo_ci):
    ip = get_client_ip(request)
    interface = get_interface(ip, platform, app_name, display)
    if interface:
        request.profile.interface.add(interface)
    if geo_co:
        try:
            country = Country.objects.get(name=geo_co)
        except Country.DoesNotExist: pass
        else:
            try:
                city = City.objects.get(name__name=geo_ci, name__status=1, country=country)
                person = request.profile.person
                person.country = country
                person.city = city
                person.save()
            except City.DoesNotExist: pass
    return simplejson.dumps({})

def test_test(request):
    ip = get_client_ip(request)
    profile = auth_user(request, ip, 'Linux', 'Opera', '1680x960')
    return HttpResponse()


@dajaxice_register
def sett(request, value, id):
    user = request.user
    interface = user.get_profile().personinterface
    warning = ''
    if not interface.first_change and not user.get_profile().auth_status:
        warning = 'Перед уходом не забудьте сохранить ваши настройки' 
        interface.first_change = True
    if id == 'op1': interface.option1 = value
    elif id == 'op2': interface.option2 = value
    elif id == 'op3': interface.option3 = value
    elif id == 'op4': interface.option4 = value
    interface.changed = True
    interface.save()
    return warning



def get_subscription_status(id, profile):
    try:
        subr = SubscriptionRelease.objects.get(profile=profile, kid=id)
        return subr
    except SubscriptionRelease.DoesNotExist:
        try:
            subr = SubscriptionRelease.objects.get(profile=profile, release__film_kid=id)
            return subr
        except SubscriptionRelease.DoesNotExist: pass
    except SubscriptionRelease.MultipleObjectsReturned:
        subr = None
        for i in SubscriptionRelease.objects.filter(profile=profile, kid=id):
            if subr:
                i.delete()
            else:
                subr = i


def get_cities_in_country(id_country):
    cities_dict = []
    for i in NameCity.objects.filter(city__country__id=id_country, status=1).order_by('name'):
        cities_dict.append({'name': i.name, 'key': i.id})
    return cities_dict



@dajaxice_register
def get_cities(request, id, title=False):
    
    cities_dict = []
    id = int(id)
    if id:
        cities_dict = get_cities_in_country(id)
        if request.user.is_superuser and title == "*special*":
            cities_dict.insert(0, {'name': u'ВСЕ', 'key': 0})
            title = False
    else:
        if request.user.is_superuser and id == 0:
            cities_dict = [{'name': u'ВСЕ', 'key': 0}]
            title = False
    
    if title:
        title = True

    if cities_dict:
        return simplejson.dumps({
            'status': True,
            'content': cities_dict,
            'all': title,
        })
    
    return simplejson.dumps({'status': False})   



@dajaxice_register
def subscription(request, id, cancel, email=None, city=None):
    try:
        if request.user.is_authenticated():

            card = get_usercard(request.user)
            profile = card['profile']
            
            # если посетитель подписывается и оставляет свои данные
            if city or email:
                if city:
                    try:
                        c = City.objects.get(name__id=city, name__status=1)
                        card['card'].city = c
                        if c.country:
                            card['card'].country = c.country
                        else:
                            return simplejson.dumps({'status': False})
                        card['card'].save()
                        card['city'] = {'id': c.id, 'name': ''}
                    except City.DoesNotExist:
                        return simplejson.dumps({'status': False})
                
                if email:  
                    if card['emails'] and email in card['emails']:
                        # сделать мэйл основным
                        request.user.email = email
                        request.user.save()
                        card['email'] = email
                        
            p_interface = profile.personinterface

            if card['email']:
                flag = True
            else:
                flag = False
                p_interface.temp_subscription = id
                p_interface.save()

            emails = card['emails'] if card['emails'] else False

            subr = get_subscription_status(id, profile)
            sub_status = False
            
            # отписка
            if cancel == 'cancel_subs':
                subr.delete()
                
                # если отписывается, то ставим лайк 'не буду смотреть'
                try:
                    like = Likes.objects.get(personinterface=profile.personinterface, film=id, evaluation=1)
                    like.evaluation = 4
                    like.save()
                    act = '2'
                except Likes.DoesNotExist:
                    like = Likes.objects.create(evaluation=4, film=id)
                    profile.personinterface.likes.add(like)
                    act = '1'
                
                actions_logger(18, id, profile, act)

                return simplejson.dumps({
                    'status': True,
                    'email': True,
                    'sub_status': sub_status,
                })

            # подписка
            else:
                # если у пользователя указан город
                if card['city']:
                    # и если указан мэйл
                    if card['email']:
                        
                        # то подписываю пользователя на уведомления
                        if not subr:
                            
                            SubscriptionRelease.objects.get_or_create(profile=profile, kid=id, defaults={'profile': profile, 'kid': id})
                            p_interface.temp_subscription = None
                            p_interface.save()

                            # ставим лайк 'хочу смотреть в кинотеатре'
                            act = None
                            try:
                                like = Likes.objects.get(personinterface=profile.personinterface, film=id)
                                if like.evaluation != 1:
                                    act = '2'
                                like.evaluation = 1
                                like.save()
                            except Likes.DoesNotExist:
                                like = Likes.objects.create(evaluation=1, film=id)
                                profile.personinterface.likes.add(like)
                                act = '1'
                            actions_logger(2, id, profile, act)

                            sub_status = True
                        else:
                            sub_status = True
                        return simplejson.dumps({
                            'status': True,
                            'email': True,
                            'sub_status': sub_status,
                        })
                    # если нет мэйла
                    else:
                        return simplejson.dumps({
                            'status': True,
                            'email': False,
                            'flag': flag,
                            'emails': emails,
                        })
                # если у пользователя не указан город
                else:
                    country = 2
                    city = 1
                    countries = []
                    cities = False
                    
                    countries_o = Country.objects.exclude(city=None)
                    for i in countries_o:
                        countries.append({'name': i.name, 'key': i.id})
                    
                    if card['country']:
                        country = card['country']['id']
                    
                    if card['city']:
                        city = card['city']['id']
                    
                    cities = get_cities_in_country(country)
       
                    return simplejson.dumps({
                        'status': True,
                        'email': False, 
                        'country': country,
                        'countries': countries,
                        'city': city,
                        'cities': cities,
                        'emails': emails,
                        'flag': flag,
                    })
        
        return simplejson.dumps({
            'status': False,
            'reload': True,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def subscription_topics(request, id, email=None):
    #try:
    '''
    if request.user.is_authenticated():
        card = get_usercard(request.user)
        profile = card['profile']
        
        # если посетитель подписывается и оставляет свои данные
        if email:  
            if card['emails'] and email in card['emails']:
                # сделать мэйл основным
                request.user.email = email
                request.user.save()
                card['email'] = email

        p_interface = profile.personinterface

        if card['email']:
            flag = True
        else:
            flag = False
            p_interface.temp_subscription_topics = id
            p_interface.save()

        emails = card['emails'] if card['emails'] else False

        try:
            subr = SubscriptionTopics.objects.get(profile=profile, kid=id)
        except SubscriptionTopics.DoesNotExist:
            subr = None
            
        sub_status = False
        
        # подписываем
        if not subr:
            # и если указан мэйл
            if card['email']:
                # то подписываю пользователя на уведомления
                SubscriptionTopics.objects.create(profile=profile, kid=id)

                p_interface.temp_subscription_topics = None
                p_interface.save()

                # ставим лайк 'хочу смотреть дома (в сети)'
                act = None
                try:
                    like = Likes.objects.get(personinterface=profile.personinterface, film=id)
                    if like.evaluation != 2:
                        act = '2'
                        like.evaluation = 2
                        like.save()
                except Likes.DoesNotExist:
                    like = Likes.objects.create(evaluation=2, film=id)
                    profile.personinterface.likes.add(like)
                    act = '1'

                actions_logger(16, id, profile, act)

                return simplejson.dumps({
                    'status': True,
                    'email': True,
                })
            # если нет мэйла
            else:
                return simplejson.dumps({
                    'status': True,
                    'email': False,
                    'emails': emails,
                })
                
        return simplejson.dumps({
            'status': False,
            'reload': False,
        })
    else:
        return simplejson.dumps({
            'status': False,
            'reload': True,
        })
    '''
    return simplejson.dumps({
        'status': False,
        'reload': False,
    })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def get_messenger(request):
    try:
        if request.user.is_authenticated():
            profile = request.profile
            if profile:

                dialogs_ids = DialogMessages.objects.filter(readers__user=profile, readers__status__in=('0', '2', '3', '4')).order_by('-pk').distinct('pk').values_list('pk', flat=True)

                readers = NewsReaders.objects.filter(dialogmessages__pk__in=dialogs_ids).values('id', 'user', 'user__user', 'status', 'dialogmessages__pk', 'message__autor', 'message__autor__user')

                users = []
                for i in readers:
                    users.append(i['user'])
                    users.append(i['message__autor'])

                profiles = Profile.objects.filter(pk__in=users)
                peoples = org_peoples(profiles, True)

                dialogs_data = {}
                for i in readers:
                    if not dialogs_data.get(i['dialogmessages__pk']):
                        dialogs_data[i['dialogmessages__pk']] = {'id': i['dialogmessages__pk'], 'news': 0, 'users_ids': [], 'users': ''}


                    readers_ids = []
                    new_messages = 0
                    
                    if profile.id == i['user']:
                        if i['status'] == '0':
                            dialogs_data[i['dialogmessages__pk']]['news'] += 1

                    for u in ((i['user__user'], i['user']), (i['message__autor__user'], i['message__autor'])):
                        if u[0] not in dialogs_data[i['dialogmessages__pk']]['users_ids']:
                            pname = ''
                            if profile.id != u[1]:
                                p = peoples.get(u[0], {})
                                pname = p.get('name')
                                if p['system']:
                                    pname = 'SYSTEM<div class="dialog_system"></div>'

                            if dialogs_data[i['dialogmessages__pk']]['users']:
                                dialogs_data[i['dialogmessages__pk']]['users'] += ', '
                            dialogs_data[i['dialogmessages__pk']]['users'] += '%s' % pname
                            dialogs_data[i['dialogmessages__pk']]['users_ids'].append(u[0])

                
                dialogs_data = sorted(dialogs_data.values(), key=operator.itemgetter('news'), reverse=True)
                

                return simplejson.dumps({
                    'status': True,
                    'content': dialogs_data,
                })

        return simplejson.dumps({
            'status': False,
        })
            
    except Exception as e:
        open('%s/ajax_errors.txt' % settings.API_DUMP_PATH, 'a').write('* get_messenger\n%s\n%s\n\n' % (dir(e), e.args))
        #open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def get_messenger_send(request, uids, msg, dialog, one=True):
    try:
        if request.user.is_authenticated():
            profile = request.profile

            msg = BeautifulSoup(msg, from_encoding="utf-8").text

            if msg:
            
                in_dialog = True
                types = 0
                
                if dialog:
                    dialog_obj = DialogMessages.objects.get(pk=dialog)
                    # проверка юзера на участие в диалоге
                    author_count = DialogMessages.objects.filter(readers__message__autor=profile)[:2].count()
                    if author_count == 0:
                        reader_count = DialogMessages.objects.filter(readers__user=profile)[:2].count()
                        in_dialog = False if reader_count == 0 else True

                    if not uids:
                        uids = list(dialog_obj.readers.all().distinct('user').values_list('user__user', flat=True))
                        types = 1
                else:
                    dialog_obj = None
                    if not uids:
                        uids = []
                        types = 1

                reader_type = '2' if len(uids) > 1 else '1'
                
                
                if uids:
                    msg_obj = News.objects.create(
                        title = 'Сообщение',
                        text = msg,
                        autor = profile,
                        site = request.current_site,
                        subdomain = '0',
                        reader_type = reader_type,
                    )
                    
                    #if long(profile.user_id) not in uids:
                    #    uids.append(long(profile.user_id))
                        
                    profiles = Profile.objects.filter(user__id__in=uids)
                    
                    if in_dialog:

                        author = None

                        for i in profiles:
                            
                            reader = NewsReaders.objects.create(user=i, status='0', message=msg_obj)

                            if dialog_obj:
                                dialog_obj.readers.add(reader)
                                if not author:
                                    author = NewsReaders.objects.create(user=profile, status='4', message=msg_obj)
                                    dialog_obj.readers.add(author)
                            else:
                                if one:
                                    dialog_obj = DialogMessages()
                                    dialog_obj.save()
                                    dialog_obj.readers.add(reader)
                                    if not author:
                                        author = NewsReaders.objects.create(user=profile, status='4', message=msg_obj)
                                        dialog_obj.readers.add(author)
                                else:
                                    dialog_obj_tmp = DialogMessages()
                                    dialog_obj_tmp.save()
                                    dialog_obj_tmp.readers.add(reader)
                                    author_tmp = NewsReaders.objects.create(user=profile, status='4', message=msg_obj)
                                    dialog_obj_tmp.readers.add(author_tmp)


                        
                messages = []
                if types == 1:
                    messages = get_messages_func(request, dialog_obj.id)
                
                dialog_obj_id = dialog_obj.id if dialog_obj else None

                return simplejson.dumps({
                    'status': True,
                    'dialog': dialog_obj_id,
                    'type': types,
                    'content': messages
                })
            else:
                return simplejson.dumps({
                    'status': False,
                })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_messenger_del(request, id):
    if request.user.is_authenticated():
        profile = request.profile
        if id and profile.auth_status:
            dialog = DialogMessages.objects.get(pk=id)
            for i in dialog.readers.filter(user=profile):
                i.status = '1'
                i.save()
            for j in dialog.readers.filter(message__autor=profile):
                j.message.autor_status = False
                j.message.save()
    return simplejson.dumps({})


def get_messages_func(request, id):
    profile = request.profile
    
    readers = News.objects.select_related('autor').filter(newsreaders__user=profile, newsreaders__status__in=('0', '2', '3', '4'), newsreaders__dialogmessages__pk=id).distinct('pk') # ОГРАНИЧИТЬ 100
    
    messages = []

    messages_temp = []

    profiles = [i.autor for i in readers]
    peoples = org_peoples(profiles, True)

    for i in readers:
        user = peoples.get(i.autor.user_id, {})
        uname, system = ('SYSTEM<div class="dialog_system"></div>', True) if user['system'] else (user['name'], False)
        
        recipient = 'from_recipient' if profile != i.autor else 'from_author'
        messages_temp.append(i.id)
        messages.append({
            'text': i.text.replace('\n', '<br />'), 
            'dtime': str(i.dtime), 
            'author': uname, 
            'last': False, 
            'recipient': recipient,
            'system': system,
        })
        
    NewsReaders.objects.filter(message__in=messages_temp, user=profile).exclude(status__in=('1', '4')).update(status='2')
    
    messages[-1]['last'] = True
    
    return messages


@dajaxice_register
def get_messenger_dialog(request, id):
    try:
        if request.user.is_authenticated() and request.profile:
            if id:
                messages = get_messages_func(request, id)
                
                return simplejson.dumps({
                    'status': True,
                    'content': messages,
                    'dialog': id,
                })
            else:
                return simplejson.dumps({
                    'status': False,
                })

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



def add_email_to_exist_profile(email, profile):
    from user_registration.func import md5_string_generate

    md5_string = md5_string_generate(email)
        
    acc, created = Accounts.objects.get_or_create(
        email = email,
        defaults = {
            'login': email,
            'email': email,
            'validation_code': md5_string,
        })

    accs = profile.accounts

    # если акк есть в профиле
    if acc in accs.all():
        next = True
    # нет в профиле
    else:
        # новый акк был только что создан
        if created:
            # подключаю к профилю
            accs.add(acc)
            next = True
        # акк существует но не для этого профиля
        else:
            next = False

    return next


def create_by_email(email, activate=False):
    from user_registration.func import md5_string_generate

    if email:
        code = md5_string_generate(email)
        
        filter = {'login': email, 'validation_code': code, 'email': email}
        if activate:
            filter['validation_code'] = None
            filter['auth_status'] = True
        
        acc, created = Accounts.objects.get_or_create(
            email = email,
            defaults = filter
            )
    
        profile = None
        
        try:
            profile = Profile.objects.select_related('user').get(accounts=acc)
            acc.validation_code = code 
            if activate:
                acc.validation_code = None
                acc.auth_status = True
            acc.save()
        except Profile.DoesNotExist:
            new_user = get_user()
            profile = Profile.objects.select_related('user').get(user=new_user)
            profile.accounts.add(acc)
            
    else:
        new_user = get_user()
        profile = Profile.objects.select_related('user').get(user=new_user)
        code = None
    
    return profile, code


def user_by_phone(phone, site=None):
    filter = {'phone': phone}
    if site:
        filter['site'] = site
    try:
        profile_obj = Profile.objects.select_related('user').get(**filter)
        ttype = 1
    except Profile.DoesNotExist:
        profile_obj, code = create_by_email(None)
        profile_obj.phone = phone
        profile_obj.save()
        ttype = 2
    return profile_obj, ttype


@dajaxice_register
def get_user_by_phone(request, phone, tag):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            
            profile_obj, ttype = user_by_phone(phone)
            profile = org_peoples([profile_obj])[0]
            
            cl, created = LetsGetClients.objects.get_or_create(
                profile = profile_obj,
                site = current_site,
                subdomain = subdomain,
                defaults = {
                    'profile': profile_obj,
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
                    <td><div><a href="/user/profile/%s/" target="_blank">%s</a></div></td>\
                    <td><div></div></td>\
                    <td><div id="note1__%s" class="letsget_edit_notes"></div></td>\
                    <td><div id="note2__%s" class="letsget_edit_notes"></div></td>' % (cl.id, profile['id'], profile['name'], cl.id, cl.id)

            url = u'<a href="/user/profile/%s/" target="_blank">%s</a>' % (profile['id'], profile['name'])
            
            return simplejson.dumps({
                'type': ttype,
                'created': created,
                'html': html,
                'status': True,
                'url': url,
            })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    

@dajaxice_register
def get_user_by_email(request, email, create):
    try:
        from django.core.mail import send_mail, EmailMultiAlternatives
         
        if request.user.is_superuser or request.is_admin:
            new_user = None
            ttype = 2
            if create:
                if email.strip():
                    new_user, code = create_by_email(email.strip())
            else:
                users = Profile.objects.select_related('user').filter(Q(accounts__login__icontains=email) | Q(accounts__email__icontains=email) | Q(user__email__icontains=email.strip())).distinct('user__id').order_by('user__id')

                users_list = [i for i in users]
                peoples = org_peoples(users_list)

                if peoples:
                    ttype = 1
                else:
                    ttype = 2
                    if email.strip():
                        new_user, code = create_by_email(email.strip())
                
            if new_user:
                peoples = org_peoples([new_user])


                subject = u'"Lets Get Rhythm" Invite'
                auth_link = u'http://%s/user/login/email/%s/' % (request.get_host(), code) 
                
                
                with open('%s/letsget_invite_text.txt' % settings.API_EX_PATH,'r') as f:
                    text = f.read()
                
                
                msg = u"%s\n\n\
                    TO CONFIRM ACCOUNT CLICK HERE: \n%s\n" % (text, auth_link)
                
                msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                    %s <br /><br />\
                    <h3>To confirm account click here: </h3>\
                    <a href="%s" target="_blank">%s</a><br />\
                    </div>' % (text, auth_link, auth_link)
                
                
                mail = EmailMultiAlternatives(subject, msg, '', [email.strip()])
                mail.attach_alternative(msg_html, "text/html")
                mail.send()
            
                    
            return simplejson.dumps({
                'content': peoples,
                'type': ttype,
                'status': True,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def new_usr(request, email='', groups=[], sites=[]):
    try:
        if request.user.is_superuser:
            html = u'<div style="width: 300px; font-size: 12px;">'

            if email and email.strip():
                new_user, code = create_by_email(email.strip(), True)
                user_groups = new_user.user.groups.all()
                user_sites = new_user.site_admin.all()
                for i in groups:
                    group = Group.objects.get(pk=i)
                    if group not in user_groups:
                        new_user.user.groups.add(group)
                    if group.name == 'Редактор сайтов':
                        for j in DjangoSite.objects.filter(pk__in=sites):
                            if j not in user_sites:
                                profile.site_admin.add(j)
                profile = org_peoples([new_user])[0]
                html += u'''
                    <div style="padding: 10px; background: #d9d9d9;">
                    <a href="/user/profile/%s/">%s</a>
                    </div>
                ''' % (profile['id'], profile['name'])

            else:
                html += u'''
                    <b>Введите E-Mail нового пользователя</b><br />
                    <input type="text" value="" class="new_usr_email" style="width: 220px; margin: 5px 0 20px 0;" /><br />
                '''

                html += u'''<b>Укажите необходимые права</b><br />
                    <select multiple="multiple" style="height: 110px; margin-top: 5px;" class="u_groups" name="u_groups">
                    <option value="0">СуперАдмины</option>'''

                for i in Group.objects.all():
                    site_editor = ''
                    if i.id == 2:
                        site_editor = u'class="site_editor"'
                    html += u'<option value="%s" %s>%s</option>' % (i.id, site_editor, i.name)
                html += u'</select>'
                
                html += u'''
                <select multiple="multiple" style="height: 110px;" class="sites_edit" name="sites_edit" disabled>
                '''
                for i in DjangoSite.objects.all():
                    html += u'<option value="%s">%s</option>' % (i.id, i.name)

                html += u'</select><br /><input type="button" value="Создать" class="new_usr_create" style="margin-top: 20px;"/>'

            html += u'</div>'

            return simplejson.dumps({
                'content': html,
            })

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_kinoafisha_user(request, nick, id=0):
    try:
        from organizations.ajax import xss_strip2
        
        questions = {
            1: u'Девичья фамилия Вашей матери',
            2: u'Отчество Вашего отца',
            3: u'Месяц Вашего рождения',
        }
        
        nick = xss_strip2(nick)
    
        month = ''
        for i in MONTHES_CHOICES:
            month += u'<option value="%s">%s</option>' % (low(i[1].encode('utf-8')).decode('utf-8'), i[1])
        month = u'<select class="kq_num3"><option value="">Не указан</option>%s</select>' % month
        
        data = ''
        btns = ''
        nickname = ''
        id = int(id)
        
        if id or nick:
            if not id:
                result = RegisteredUsers.objects.using('afisha').filter(nickname=nick)
                if result:
                    if result.count() > 1:
                        result = result.reverse()[0]
                    else:
                        result = result[0]
                    count = 1
                else:
                    count = 0
  
            else:
                try:
                    result = RegisteredUsers.objects.using('afisha').get(pk=id)
                    count = 1
                except RegisteredUsers.DoesNotExist:
                    count = 0
        
            nickname = nick
            if count == 1:
                nickname = result.nickname
                for i in result.pass_text.split('!'):
                    if i:
                        num, answer = i.split('#')
                        q = questions.get(int(num))
                        data += u'<div style="clear: both; margin-bottom: 7px;">'
                        data += u'<div class="ka_login_field"><b>%s:</b></div>' % q
                        if num == '3':
                            data += month
                        else:
                            data += u'<div><input type="text" value="" class="kq_num%s" size="30" /></div>' % num
                        data += u'</div>'
                data = u'<div class="ka_err"></div>%s' % data
                btns += u'<input type="button" value="Вперед!" class="kinoafisha_auth_fin kinoafisha_btn" />'
                btns += u'<input type="hidden" value="%s" class="kinoafisha_uid" />' % result.id
            else:
                data += u'<div style="clear: both; margin-bottom: 7px; color: #6677DD; text-align: center;">'
                data += u'<b>Вы уверены, что верно написали свой ник?</b><br />'
                data += u'</div>'
                btns += u'<input type="button" value="Уверен" class="ka_auth_yes kinoafisha_btn" /> '
                btns += u'<input type="button" value="Нет" class="ka_auth_no kinoafisha_btn" />'
        else:
            btns += u'<input type="button" value="Вперед!" class="kinoafisha_auth kinoafisha_btn" />'
        
        return simplejson.dumps({
            'status': True,
            'btns': btns,
            'content': data,
            'nickname': nickname,
        })
    except Exception as e:
        open('%s/ajax_errors.txt' % settings.API_DUMP_PATH, 'a').write('* get_kinoafisha_user\n%s\n%s\n\n' % (dir(e), e.args))


@dajaxice_register
def get_kinoafisha_user_list(request, nick):
    try:
        from organizations.ajax import xss_strip2

        nick = xss_strip2(nick)

        result = RegisteredUsers.objects.using('afisha').filter(Q(nickname__istartswith=nick) | Q(nickname__iendswith=nick) | Q(nickname__icontains=nick)).order_by('nickname').distinct('pk')
        
        users = ''
        for i in result:
            users += u'<option value="%s">%s</option>' % (i.id, i.nickname)
    
        data = u'<div style="clear: both; margin-bottom: 7px; color: #6677DD; text-align: center;">'
        data += u'<b>Попробуйте найти свой ник в списке:</b><br /><br /> <select class="ka_user_list"><option value="0">Ника в списке нет</option>%s</select>' % users
        data += u'</div>'
        
        btns = u'<input type="button" value="Дальше" class="ka_auth_next kinoafisha_btn" />'
        
        return simplejson.dumps({
            'status': True,
            'btns': btns,
            'content': data,
            'nickname': nick,
        })
    except Exception as e:
        open('%s/ajax_errors.txt' % settings.API_DUMP_PATH, 'a').write('* get_kinoafisha_user_list\n%s\n%s\n\n' % (dir(e), e.args))




@dajaxice_register
def kinoafisha_auth(request, id, q1, q2, q3):
    try:
        try:
            genders = {
                u'': None,
                u'0': None,
                u'ж': 2,
                u'м': 1,
                u'1': 1,
                u'2': 2,
            }
        
            result = RegisteredUsers.objects.using('afisha').get(pk=id)
            
            lock = False
            for i in result.pass_text.split('!'):
                if i:
                    num, answer = i.split('#')

                    if num == '1':
                        if low(answer.encode('utf-8')) != low(q1.encode('utf-8')):
                            lock = True
                    if num == '2':
                        if low(answer.encode('utf-8')) != low(q2.encode('utf-8')):
                            lock = True
                    if num == '3':
                        if low(answer.encode('utf-8')).decode('utf-8') != q3:
                            lock = True
            
            
            if not lock:
                # авторизация
                email = result.email if result.email else None
                
                fullname = ''
                if result.firstname:
                    fullname = u'%s %s' % (result.firstname, result.lastname)

                gender = genders.get(result.sex)
                
                dob = result.date_of_birth if result.date_of_birth else None
                
                params = {
                    'code': None, 
                    'email': email, 
                    'nick': result.nickname, 
                    'name': fullname, 
                    'gender': gender, 
                    'dob': dob,
                }
                
                #uid = email if email else 'Kinoafisha.ru_%s' % result.id
                uid = 'Kinoafisha.ru_%s' % result.id
                email = None
                
                acc = accounts_interim(request, request.profile, uid, email=email, nick=result.nickname, name=fullname, gender=gender, dob=dob)
                
                current_user = request.profile.kid
                if current_user and current_user != result.id:
                
                    # сообщения отвязываем от текущего юзера и привязываем к авторизованному
                    WFOpinion.objects.using('afisha').filter(user__id=current_user).update(user=result)
                    
                    # отвязываем игнорируемые сообщения и привязываем
                    WomenForumIgnored.objects.filter(user=current_user).update(user=result.id)
                    
                    # переносим доступный уровень для игнорирования сообщений
                    now = datetime.datetime.now()
                    try:
                        c = WomenForumIgnoreLevel.objects.get(user=current_user)
                        current_level = c.type
                        current_level_time = c.dtime
                    except WomenForumIgnoreLevel.DoesNotExist:
                        current_level = 1
                        current_level_time = now
                        
                    try:
                        n = WomenForumIgnoreLevel.objects.get(user=result.id)
                        new_level = n.type
                        new_level_time = n.dtime
                    except WomenForumIgnoreLevel.DoesNotExist:
                        new_level = 1
                        new_level_time = now
                    
                    if current_level > new_level:
                        level = current_level
                        level_time = current_level_time
                    elif current_level < new_level:
                        level = new_level
                        level_time = new_level_time
                    else:
                        level = new_level
                        level_time = new_level_time
                    
                    
                    level_obj, lcreated = WomenForumIgnoreLevel.objects.get_or_create(
                        user = result.id,
                        defaults = {
                            'user': result.id,
                            'dtime': level_time,
                            'type': level,
                        })
                    if not lcreated:
                        level_obj.type = level
                        level_obj.dtime = level_time
                        level_obj.save()
                    
                #if not request.profile.kid:
                request.profile.kid = result.id
                cur_user = request.profile.user
                if not cur_user.first_name:
                    cur_user.first_name = result.nickname
                    cur_user.save()
                request.profile.save()
                
                # освобождаем никнэйм
                if result.salt == '000000000000' and result.password == '000000000000':
                    try:
                        reg = RegisteredUsers.objects.using('afisha').get(pk=current_user)
                        reg.nickname = 'user_%s' % reg.id
                        reg.last_visit = datetime.datetime.now()
                        reg.save()
                    except RegisteredUsers.DoesNotExist: pass

                
                if request.current_site.domain == 'vsetiinter.net':
                    if request.subdomain == 'forums':
                        redirect_alt = 'http://forums.vsetiinter.net/women/'
                        redirect_to = request.META.get('HTTP_REFERER', redirect_alt)
                    elif request.subdomain == 'ya':
                        redirect_href = acc._headers.get('location')[1] if acc else '/user/profile/accounts/'
                        redirect_to = 'http://ya.%s%s' % (request.current_site.domain, redirect_href)
                else:
                    redirect_href = acc._headers.get('location')[1] if acc else '/user/profile/accounts/'
                    redirect_to = 'http://%s%s' % (request.current_site.domain, redirect_href)
                
                return simplejson.dumps({
                    'status': True,
                    'redirect_to': redirect_to,
                    'error': '',
                })
            else:
                return simplejson.dumps({
                    'status': True,
                    'redirect_to': '',
                    'error': 'Неверно указаны ответы на контрольные вопросы',
                })
            
        except RegisteredUsers.DoesNotExist:
            pass
            

        return simplejson.dumps({
            'status': False,
        })
        
    except Exception as e:
        open('%s/ajax_errors.txt' % settings.API_DUMP_PATH, 'a').write('* kinoafisha_auth\n%s\n%s\n\n' % (dir(e), e.args))



@dajaxice_register
def gen_auth_link(request, id):
    #try:
        from user_registration.func import md5_string_generate
        if request.user.is_superuser:
            acc = Accounts.objects.get(pk=id)
            
            code = md5_string_generate(acc.email)
            
            acc.validation_code = code
            acc.save()
            
            profile = Profile.objects.select_related('user').get(accounts=acc)
            try:
                profile.user.groups.get(name='Рекламодатель')
                url_param = u'?next=adv'
            except Group.DoesNotExist:
                url_param = ''


            auth_link = u'http://%s/user/login/email/%s/%s' % (request.get_host(), code, url_param)
            
            return simplejson.dumps({
                'url': auth_link,
            })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def get_countries_cities(request, check_all=False, country=None, city=None):
    #try:
        if request.user.is_superuser and check_all and country and city:
            city_id = long(city)
            country_id = long(country)
        else:
            city_id = request.current_user_city_id
            country_id = request.current_user_country_id
        
        countries = list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name'))
        cities = list(NameCity.objects.filter(status=1, city__country__id=country_id).order_by('name').values('id', 'city__id', 'name'))

        html_countries = u'<select class="country_in_card" name="coic">'
        if request.user.is_superuser and check_all:
            html_countries += u'<option value="0">ВСЕ</option>'
            
        for i in countries:
            selected = u' selected' if i['id'] == country_id else ''
            html_countries += u'<option value="%s"%s>%s</option>' % (i['id'], selected, i['name'])
        html_countries += '</select>'
    
    
        if request.user.is_superuser and check_all:
            html_cities = u'<select class="city_in_card" name="ciic" title="*special*">'
            html_cities += u'<option value="0">ВСЕ</option>'
        else:
            html_cities = u'<select class="city_in_card" name="ciic">'
            
        for i in cities:
            selected = u' selected' if i['city__id'] == city_id else ''
            html_cities += u'<option value="%s"%s>%s</option>' % (i['id'], selected, i['name'])
        html_cities += '</select>'
    
        return simplejson.dumps({
            'countries': html_countries,
            'cities': html_cities,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def get_countries_cities_alt(request, check_all=False, country=None, city=None):
    #try:
        if request.user.is_superuser and check_all and country and city:
            city_id = long(city)
            country_id = long(country)
        else:
            city_id = request.current_user_city_id
            country_id = request.current_user_country_id
        
        countries = list(Country.objects.filter(city__name__status=1).distinct('pk').order_by('name').values('id', 'name'))
        cities = list(NameCity.objects.filter(status=1, city__country__id=country_id).order_by('name').values('id', 'city__id', 'name'))

        html_countries = u'<select class="country_in_card_alt" name="coic">'
        if request.user.is_superuser and check_all:
            html_countries += u'<option value="0">ВСЕ</option>'
            
        for i in countries:
            selected = u' selected' if i['id'] == country_id else ''
            html_countries += u'<option value="%s"%s>%s</option>' % (i['id'], selected, i['name'])
        html_countries += '</select>'
    
    
        if request.user.is_superuser and check_all:
            html_cities = u'<select class="city_in_card_alt" name="ciic" title="*special*">'
            html_cities += u'<option value="0">ВСЕ</option>'
        else:
            html_cities = u'<select class="city_in_card" name="ciic">'
            
        for i in cities:
            selected = u' selected' if i['city__id'] == city_id else ''
            html_cities += u'<option value="%s"%s>%s</option>' % (i['id'], selected, i['name'])
        html_cities += '</select>'
    
        return simplejson.dumps({
            'countries': html_countries,
            'cities': html_cities,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


def subscriber_create_email(request, email, id, type):
    data = {'error': False, 'email_error': False, 'content': '', 'next': True}

    next = add_email_to_exist_profile(email, profile)

    if not next:
        try:
            prof = Profile.objects.get(accounts=acc)
            try:
                SubscriberUser.objects.get(profile=prof, type=type, obj=id)
                msg = 'Пользователь уже подписан'
            except SubscriberUser.DoesNotExist:
                msg = 'Этот E-Mail уже зарегистрирован в системе. Для подписки необходимо <a href="/user/login/">авторизоваться</a> используя этот же e-mail'
        except Profile.DoesNotExist:
            msg = 'Этот E-Mail уже зарегистрирован в системе. Для подписки необходимо <a href="/user/login/">авторизоваться</a> используя этот же e-mail'
        
        data = {
            'error': True,
            'email_error': True,
            'content': msg,
            'next': False,
        }

    return data

def subscriber_func(profile, id, type):
    from user_registration.func import sha1_string_generate

    types = [i[0] for i in SUBSCRIBE_TYPE]

    type = str(type)

    if type in types:
        obj = None
        # подписка на блог
        if type == '1':
            try:
                obj = OrgSubMenu.objects.get(pk=id)
            except OrgSubMenu.DoesNotExist: pass
        # подписка на комменты в блоге
        elif type == '2':
            try:
                obj = News.objects.get(pk=id)
            except News.DoesNotExist: pass
        
        if obj:
            unsubscribe = sha1_string_generate().replace('_','')

            subscriber_obj, subscriber_create = SubscriberUser.objects.get_or_create(
                profile = profile,
                type = type,
                obj = obj.id,
                defaults = {
                    'profile': profile,
                    'type': type,
                    'obj': obj.id,
                    'unsubscribe': unsubscribe,
                })

            return {'error': False, 'content': 'Вы успешно подписаны'}

    return {'error': True, 'content': 'Ошибка'}


@dajaxice_register
def subscriber(request, email, type, id):
    try:
        create_email = False

        main_email = request.user.email
        emails = []
        for i in request.profile.accounts.all():
            if i.email and i.email.strip():
                emails.append(i.email.strip())
        emails = set(emails)

        if not main_email and not emails:
            email = email.strip()
            if email and '@' in email:
                create_email = True
            else:
                return simplejson.dumps({
                    'error': True,
                    'content': 'Введите Ваш E-Mail!',
                })

        next = True
        if create_email:
            sub_create_email = subscriber_create_email(request, email, id, type)
            
            if sub_create_email['next']:
                next = True
            else:
                return simplejson.dumps(sub_create_email)


        if next:
            result = subscriber_func(request.profile, id, type)
            return simplejson.dumps(result)
            
        return simplejson.dumps({
            'error': True,
            'content': 'Ошибка',
        })

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))




def bpost_comments_gen(id, current_site, access, project_page=False):
    TR_delete = _(u'удалить')
    TR_answer = _(u'ответить')

    name = 'BPost_%s' % id
                
    tmp_dict = {}
    peoples = {}

    def printTree(L, new, data, margin=0):
        for i in L:
            if isinstance(i, list):
                data = printTree(i, new, data, margin)
            else:
                arrow = ''
                if not i.branch_id:
                    margin = 0
                else:
                    arrow = '<div class="answer-arrow"></div>'
                    idnt = tmp_dict.get(i.branch_id)
                    if not idnt:
                        margin = 15
                    else:
                        margin = idnt + 15
                        
                tmp_dict[i.id] = margin
                
                msg_date = i.dtime

                profile = peoples.get(i.autor.user_id)
                nickaname = profile['name'] if profile else ''

                delete_comment = ''
                if access:
                    delete_comment = u' | <a onclick="comments_remove(%s);">%s</a>' % (i.id, TR_delete)

                text = i.text.replace('\n', '<br />')
                data += u'<div class="cmmnt" style="margin-left: %spx;">%s<div id="cmmnt_h"><a href="/user/profile/%s/" rel="nofollow">%s</a><span>%s</span></div><div id="cmmnt_b">%s</div><div id="cmmnt_f"><a onclick="comments_add(this, %s);">%s</a>%s</div></div>' % (margin, arrow, profile['id'], nickaname, msg_date, text, i.id, TR_answer, delete_comment)
                
        return data

    def tree_level(parent):
        for item in sorted(parent_map[parent]):
            yield q[item]
            sub_items = list(tree_level(item))
            if sub_items:
                yield sub_items

    fgeneral, fcreated = ForumGeneral.objects.get_or_create(name=name, defaults={'name': name, 'site': current_site})

    if fcreated:
        obj = News.objects.get(pk=id)
        fgeneral.topics.add(obj)

    q = News.objects.select_related('autor').filter(parent=id, forumgeneral__id=fgeneral.id, reader_type='10')

    profiles = set([i.autor for i in q])
    
    q = dict(zip([i.id for i in q], q))
    
    peoples = org_peoples(profiles, True)
    
    parent_map = defaultdict(list)

    for item in q.itervalues():
        parent_map[item.branch_id].append(item.id)
    
    data = ''
    tmp = list(tree_level(None))

    data = printTree(tmp, id, data)
    
    return data



@dajaxice_register
def bpost_comments(request, id):
    try:
        ref = request.META.get('HTTP_REFERER','').split('?')[0]
        ref = ref.split('/post/')[1].replace('/','')
        current_site = request.current_site
        domains = ['kinoafisha.ru', 'kinoinfo.ru']

        if int(id) == int(ref):
            if current_site.domain in domains:
                data = bpost_comments_gen(id, current_site, request.user.is_superuser)
                return simplejson.dumps({'status': True, 'content': data})
        
        return simplejson.dumps({'status': False})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def bpost_send_comment(request, id, text, answer, email, notify, parent=None):
    try:
        from news.views import create_news

        ref = request.META.get('HTTP_REFERER','').split('?')[0]
        if '/post/' in ref:
            ref = ref.split('/post/')[1].replace('/','')
        elif '/discussion/' in ref:
            ref = 'discussion'
        elif '/reviews/' in ref:
            ref = 'reviews'

        current_site = request.current_site
        domains = ['kinoafisha.ru', 'kinoinfo.ru', 'imiagroup.com.au']
        text = text.strip()[:1000]
        answer = int(answer)
        
        if ref in ('reviews', 'discussion') or int(id) == int(ref):
            if text and current_site.domain in domains:
                type = '2'
                name = 'BPost_%s' % id
                
                fgeneral, fcreated = ForumGeneral.objects.get_or_create(name=name, defaults={'name': name, 'site': current_site})
                
                email_exist = True
                sub_create_email = {}

                if notify:
                    create_email = False

                    '''
                    main_email = request.user.email
                    emails = []
                    for i in request.profile.accounts.all():
                        if i.email and i.email.strip():
                            emails.append(i.email.strip())
                    emails = set(emails)
                    '''

                    main_email = request.user.email
                    if main_email:
                        email_exist = True
                    else:
                        emails = set([i.email.strip() for i in request.profile.accounts.all() if i.email and i.email.strip()])


                    if not main_email and not emails:
                        email = email.strip()
                        if email and '@' in email:
                            create_email = True
                        else:
                            return simplejson.dumps({
                                'status': True,
                                'error': True,
                                'content': 'Введите Ваш E-Mail!',
                                'parent': parent,
                            })
                    
                    if create_email:
                        sub_create_email = subscriber_create_email(request, email, id, type)
                        if sub_create_email['next']:
                            email_exist = True
                        else:
                            email_exist = False
                
                if not email_exist:
                    sub_create_email['status'] = True
                    sub_create_email['parent'] = parent
                    return simplejson.dumps(sub_create_email)
                else:

                    next = True
                    answer_obj = None
                    if answer:
                        try:
                            answer_obj = News.objects.get(pk=answer, parent__id=id)
                        except News.DoesNotExist:
                            next = False

                    if next:
                        comment = create_news(request, [], '', text, '10')
                        
                        if answer_obj:
                            comment.branch_id = answer_obj.id

                            if ref != 'discussion':
                                SubscriberObjects.objects.create(
                                    type = type,
                                    obj = id,
                                    end_obj = comment.id,
                                )

                        comment.parent_id = id
                        comment.save()

                        fgeneral.topics.add(comment)

                        if ref != 'discussion':
                            SubscriberObjects.objects.create(
                                type = '3',
                                obj = id,
                                end_obj = comment.id,
                            )

                        # подписка на ответы на коммент
                        if notify:
                            if ref != 'discussion':
                                result = subscriber_func(request.profile, id, type)

                        data = bpost_comments_gen(id, current_site, request.user.is_superuser)
                        return simplejson.dumps({'status': True, 'content': data, 'parent': parent})

        return simplejson.dumps({'status': False})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def bpost_remove_comment(request, id, comment, parent):
    try:
        
        if request.user.is_superuser:
            ref = request.META.get('HTTP_REFERER','').split('?')[0]
            if '/post/' in ref:
                ref = ref.split('/post/')[1].replace('/','')
            elif '/discussion/' in ref or '/reviews/' in ref:
                ref = 'discussion'

            current_site = request.current_site
            domains = ['kinoafisha.ru', 'kinoinfo.ru']

            if ref == 'discussion' or int(id) == int(ref):
                name = 'BPost_%s' % id
                
                fgeneral = ForumGeneral.objects.get(name=name)

                obj = News.objects.get(pk=comment, parent__id=id)
                fgeneral.topics.remove(obj)
                obj.delete()

                access = True if request.user.is_superuser else False
                data = bpost_comments_gen(id, current_site, access)

                return simplejson.dumps({'status': True, 'content': data, 'parent': parent})

        return simplejson.dumps({'status': False})

    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))