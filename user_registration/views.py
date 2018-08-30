# -*- coding: utf-8 -*- 
import time
import httplib2
import urllib
import cgi
import oauth2
import os
import operator
import random
import base64
import collections

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.mail import send_mail, get_connection, EmailMultiAlternatives
from django.contrib import auth
from django.contrib.sessions.models import Session as DjangoSession
#from django.contrib.gis.utils import GeoIP
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import simplejson as json
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags, escape
from django.db.models import Q, F, Count

from bs4 import BeautifulSoup

from registration.models import RegistrationProfile
from base.models import *
from base.models_choices import SHOW_PROFILE_CHOICES
from base.models_dic import NameCity
from base.views import get_bg
from api.func import resize_image
from user_registration.func import *
from kinoinfo_folder.func import low


@never_cache
def user_main(request):
    return render_to_response('user/main.html', {}, context_instance=RequestContext(request))


def get_interface(ip, platform, browser, display):
    '''
    получение/создание интерфейса
    '''
    interface, created = Interface.objects.get_or_create(
        ip_address=ip,
        platform=platform,
        browser=browser,
        display=display,
        defaults={
            'ip_address': ip,
            'platform': platform,
            'browser': browser,
            'display': display,
        }
    )
    return interface


def get_user(interface=None):
    '''
    получение/создание пользователя
    '''
    # создаю пользователя

    username = sha1_string_generate()
    try:
        User.objects.get(username=username)
        rand = random.uniform(1000.0, 999999.0)
        username = sha1_string_generate(str(rand))
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username, '', 'pswd')
    user.is_staff = False
    user.is_active = True
    username = 'User_%s' % user.id
    user.username = username
    user.save()
    # создаю профайл пользователя
    RegistrationProfile.objects.create_profile(user)
    # создаю персону
    person = Person.objects.create(male=0)
    # создаю настройки персоны по умолчанию
    person_interface = PersonInterface.objects.create()
    folder = md5_string_generate(user.id)
    #try: os.makedirs('%s/%s' % (settings.AVATAR_FOLDER, folder))
    #except OSError: pass
    site = settings.SITE_ID
    profile = Profile.objects.create(user=user, person=person, personinterface=person_interface, login_counter=1, folder=folder, site_id=site)
    if interface:
        profile.interface.add(interface)
    return user


def ttest(request):
    folder = md5_string_generate(request.user.id)
    os.makedirs('%s/%s' % (settings.AVATAR_FOLDER, folder))
    return HttpResponse('True')


def auth_user(request):
    '''
    авторизация
    '''
    user = get_user()
    user = auth.authenticate(username=user.username, password='pswd')
    auth.login(request, user)


@never_cache
def login(request):
    '''
    Страница авторизации
    '''
    if request.user.is_authenticated():
        msg = request.session.get('o_auth_msg', '')
        request.session['o_auth_msg'] = ''
        template = 'user/login.html'
        if request.current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
            template = 'user/login_vlada.html'

        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            template = 'mobile/user/login.html'

        if request.subdomain == 'pm-prepare' and request.current_site.domain in ('imiagroup.com.au'):
            template = 'pmprepare/user/login.html'

        return render_to_response(template, {'message': msg}, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('main'))


@never_cache
def logout(request):
    from django.contrib import auth
    auth.logout(request)
    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
    return HttpResponseRedirect(ref)


@never_cache
def user_settings(request):
    '''
    Настройки пользователя
    '''
    user = request.user
    if user.is_authenticated():
        options = request.profile.personinterface
        return render_to_response('user/settings.html', {'options': options}, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('main'))


def create_account(profile, uid, avatar, **kw):
    code = kw.get('code')
    gender = kw.get('gender')
    dob = kw.get('dob')
    fullname = kw.get('name')
    nickname = kw.get('nick')
    nickname = None if nickname == 'Неизвестно' else nickname
    fullname = None if fullname == 'Неизвестно Неизвестно' else fullname
    email = kw.get('email')
    try:
        acc = Accounts.objects.get(login=uid)
        if code:
            acc.validation_code = code
        else:
            if gender:
                acc.male = gender
            if dob:
                acc.born = dob
            if fullname or nickname:
                if fullname:
                    acc.fullname
                if nickname:
                    acc.nickname
            acc.auth_status = True
            profile.auth_status = True
            profile.save()
        if email:
            acc.email = email
        acc.save()
    except Accounts.DoesNotExist:
        if code:
            acc = Accounts.objects.create(login=uid, validation_code=code, email=email)
        else:
            acc = Accounts.objects.create(login=uid, validation_code=code, email=email, auth_status=True, nickname=nickname, fullname=fullname, born=dob, male=gender, avatar=avatar)
            profile.auth_status = True
            profile.save()
            profile.accounts.add(acc)


def save_profile_data(profile, nickname, fullname, dob, gender):
    '''
    Сохранение данных пользователя полученных через OpenID/OAuth
    '''
    if gender or dob:
        person = profile.person
        if gender:
            person.male = gender
        if dob:
            person.born = dob
        person.save()
    nickname = None if nickname == 'Неизвестно' else nickname
    fullname = None if fullname == 'Неизвестно Неизвестно' else fullname
    if fullname or nickname:
        language = Language.objects.get(pk=1)
        if fullname:
            save_name_person(profile, fullname, 1, language)
        if nickname:
            save_name_person(profile, nickname, 2, language)
    profile.auth_status = True
    profile.save()


def delete_user(user):
    '''
    Удаление пользователя
    '''
    import shutil
    profile = user.get_profile()
    acc = Accounts.objects.filter(profile=profile)
    for i in acc:
        try:
            Accounts.objects.exclude(profile=profile).filter(pk=i.id)
        except Accounts.DoesNotExist:
            i.delete()
    #Person.objects.get(pk=profile.person.id).delete()
    PersonInterface.objects.get(pk=profile.personinterface.id).delete()
    #try: shutil.rmtree('%s/%s' % (settings.AVATAR_FOLDER, profile.folder))
    #except OSError: pass
    profile.delete()
    #[s.delete() for s in  DjangoSession.objects.all() if s.get_decoded().get('_auth_user_id') == user.id]
    user.delete()


def lda(request, profile):
    '''
    lda - logout, delete, auth
    '''
    if request.profile != profile:
        user = request.user
        auth.logout(request)
        delete_user(user)
        user = profile.user
        user = auth.authenticate(username=user.username, password='pswd')
        auth.login(request, user)


def create_profile_avatar(request, url):
    if url:
        resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
        if content:
            file_name = '%s_%s.jpg' % (request.user.id, md5_string_generate(request.user.id))
            f = open('%s/%s' % (settings.AVATARS, file_name), 'wb')
            f.write(content)
            f.close()
            return file_name
    return None


def merge_func(current_profile, merge_profile, merge_settings=1):
    kid = current_profile.kid
    merge_kid = merge_profile.kid
    
    if not kid and merge_kid:
        current_profile.kid = merge_kid
        current_profile.save()
    
    if not current_profile.bg and merge_profile.bg:
        current_profile.bg = merge_profile.bg
        current_profile.bg_url = merge_profile.bg_url
        current_profile.save()

    # добавление аккаунтов
    def acc_add():
        for i in merge_profile.accounts.all():
            current_profile.accounts.add(i)
    # добавление групп пользователя (прав)
    def group_add():
        grp = [i for i in current_profile.user.groups.all()]
        for i in merge_profile.user.groups.all():
            if i not in grp:
                current_profile.user.groups.add(i)
                
    # текущие настройки профиля
    current_profile_settings = PersonInterface.objects.get(profile=current_profile)
    # если выбраны настройки из другого профиля, то импортирую их
    if int(merge_settings) != 1:
        current_profile_settings.option1 = merge_profile.personinterface.option1
        current_profile_settings.option2 = merge_profile.personinterface.option2
        current_profile_settings.option3 = merge_profile.personinterface.option3
        current_profile_settings.option4 = merge_profile.personinterface.option4
        current_profile_settings.wf_topic = merge_profile.personinterface.wf_topic
        current_profile_settings.wf_last = merge_profile.personinterface.wf_last
        current_profile_settings.wf_style = merge_profile.personinterface.wf_style
        current_profile_settings.wf_msg_open = merge_profile.personinterface.wf_msg_open
    
    profile_person = current_profile.person
    if not profile_person.country and merge_profile.person.country:
        profile_person.country = merge_profile.person.country
    if not profile_person.city and merge_profile.person.city:
        profile_person.city = merge_profile.person.city
    if not profile_person.male and merge_profile.person.male:
        profile_person.male = merge_profile.person.male
    if not profile_person.born and merge_profile.person.born:
        profile_person.born = merge_profile.person.born
    if not profile_person.video and merge_profile.person.video:
        profile_person.video = merge_profile.person.video

    profile_person.save()
    
    # суммирую деньги с счетов на текущий счет
    current_profile_settings.money += merge_profile.personinterface.money
    current_profile_settings.save()
    
    # импортирую лайки в текущий профиль
    current_likes = [like.film for like in current_profile_settings.likes.all()]
    for like in merge_profile.personinterface.likes.all():
        if like.film not in current_likes:
            current_profile_settings.likes.add(like)
    
    # импортирую платные действия
    PaidActions.objects.filter(profile=merge_profile).update(profile=current_profile)
    PaidActions.objects.filter(director=merge_profile).update(director=current_profile)
    
    # если юзер создавал организации, то импортирую их
    Organization.objects.filter(creator=merge_profile).update(creator=current_profile)
    
    # если юзер редактор организации
    orgs_editors = Organization.objects.filter(editors=merge_profile)
    for org in orgs_editors:
        org.editors.remove(merge_profile)
        org.editors.add(current_profile)
    
    # если юзер сотрудник орг.
    orgs_staff = Organization.objects.filter(staff=merge_profile)
    for org in orgs_staff:
        org.staff.remove(merge_profile)
        org.staff.add(current_profile)
    
    # импортирую действия над организациями
    ActionsLog.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # если автор новости, то импортирую связь
    News.objects.filter(autor=merge_profile).update(autor=current_profile)
    
    # покупки билетов
    BuyTicketStatistic.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # подписки rss
    SubscriptionFeeds.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # подписки на релизы
    SubscriptionRelease.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    SubscriptionTopics.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # сообщения
    NewsReaders.objects.filter(user=merge_profile).update(user=current_profile)

    # меню в профиле
    OrgMenu.objects.filter(profile=merge_profile).update(profile=current_profile)

    # редактор связей фильмов
    SourceFilms.objects.filter(rel_profile=merge_profile).update(rel_profile=current_profile)
    ReleasesRelations.objects.filter(rel_profile=merge_profile).update(rel_profile=current_profile)
    
    # лог списывания со счета
    WithdrawMoney.objects.filter(who=merge_profile).update(who=current_profile)
    WithdrawMoney.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # депозит
    UserDeposit.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # забанненые
    BannedUsersAndIPs.objects.filter(profile=merge_profile).update(profile=current_profile)
    BannedUsersAndIPs.objects.filter(who=merge_profile).update(who=current_profile)
    
    # лайки на форуме
    WomenForumLikes.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    FilmsVotes.objects.filter(user=merge_profile).update(user=current_profile)
    
    LetsGetClients.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    LetsGetCalendarNotified.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # номер телефона
    if merge_profile.phone and not current_profile.phone:
        current_profile.phone = merge_profile.phone
        current_profile.save()
    
    # директора и исполнители проектов
    for proj in Projects.objects.filter(directors=merge_profile):
        proj.directors.remove(merge_profile)
        proj.directors.add(current_profile)
    
    for proj in Projects.objects.filter(members=merge_profile):
        proj.members.remove(merge_profile)
        proj.members.add(current_profile)


    # псевдоним
    cur_usr = current_profile.user
    if merge_profile.user.first_name and not cur_usr.first_name:
        cur_usr.first_name = merge_profile.user.first_name
        cur_usr.save()
    
    # медиафайлы
    Mediafiles.objects.filter(profile=merge_profile).update(profile=current_profile)
    
    # реклама юзера
    SiteBanners.objects.filter(profile=merge_profile).update(profile=current_profile)

    # оплаченная реклама юзера
    SiteBanners.objects.filter(user=merge_profile).update(user=current_profile)

    # клики по рекламе
    SiteBannersClicks.objects.filter(profile=merge_profile).update(profile=current_profile)

    # подписки
    SubscriberUser.objects.filter(profile=merge_profile).update(profile=current_profile)

    # торрент-файлы
    TorrentsUsers.objects.filter(profile=merge_profile).update(profile=current_profile)

    BookingSettings.objects.filter(profile=merge_profile).update(profile=current_profile)

    acc_add()
    group_add()
    add_interface(merge_profile.user, current_profile.user)
    
    # добавляю права юзеру
    if merge_profile.user.is_staff:
        current_profile.user.is_staff = True
    if merge_profile.user.is_superuser:
        current_profile.user.is_superuser = True
    if merge_profile.user.email and not current_profile.user.email:
        current_profile.user.email = merge_profile.user.email
        current_profile.person = merge_profile.person
        current_profile.save()
    current_profile.user.save()
    delete_user(merge_profile.user)



@never_cache
def accounts_merger(request):
    if request.user.is_authenticated() and request.user.get_profile().auth_status:
        if request.method == 'POST':
            if 'merge' in request.POST:
                import shutil
                
                # другой профиль для слияния
                merge_profile_id = request.session['o_auth_merge_profile'].id if request.session.get('o_auth_merge_profile', '') else None
                
                if merge_profile_id:
                    request.session['o_auth_merge_profile'] = ''
                else:
                    return HttpResponseRedirect(reverse('profile_accounts'))
                
                # выбор 1 настройки из 2 профилей
                merge_settings = request.POST['merge_settings']
                # объект другого профиля для слияния
                merge_profile = Profile.objects.select_related('personinterface', 'accounts', 'person').get(pk=merge_profile_id)
                # объект текущего профиля
                current_profile = request.user.get_profile()

                merge_func(current_profile, merge_profile, merge_settings)
                
        else:
            msg = request.session.get('o_auth_msg', '')
            request.session['o_auth_msg'] = ''
            merge_profile = request.session.get('o_auth_merge_profile', '')
            if merge_profile:
                accounts = Accounts.objects.filter(profile=request.user.get_profile()).order_by('pk')
                merge_accounts = Accounts.objects.filter(profile=merge_profile).order_by('pk')
                current_site = request.current_site
                template = 'user/accounts_merger.html'
                if current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                    template = 'user/accounts_merger_vlada.html'
                if current_site.domain in ('imiagroup.com.au') and request.subdomain == 'pm-prepare':
                    template = 'pmprepare/user/accounts_merger.html'
                return render_to_response(template, {'message': msg, 'accounts': accounts, 'merge_accounts': merge_accounts}, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('profile_accounts'))


def accounts(request, profile, uid):
    # если авторизация
    if not profile.auth_status:
        # ищу пользователя с акк
        try:
            profile = Profile.objects.get(accounts__login=uid)
            return (1, profile)
        # если не нахожу то создаю акк
        except Profile.DoesNotExist: return (2, profile)
    # если уже авторизован
    else:
        # есть ли есть такой же акк у этого пользователя, то предупреждение
        try:
            Profile.objects.get(user=request.user, accounts__login=uid)
            return (3, profile)
        # если нет, то создаю акк
        except Profile.DoesNotExist:
            try:
                profile = Profile.objects.exclude(user=request.user).get(accounts__login=uid)
                return (4, profile)
            except Profile.DoesNotExist: return (5, profile)


def send_mail_func(request, subject, msg, email):
    from smtplib import SMTPRecipientsRefused
    try:
        send_mail(subject, msg, '', [email])
        request.session['o_auth_msg'] = _(u'На ваш email %s отправлен ключ подтверждения') % email
    except SMTPRecipientsRefused: request.session['o_auth_msg'] = _(u'Введите email правильно')


def accounts_interim(request, profile, uid, **kw):
    acc = accounts(request, profile, uid)
    status = acc[0]
    profile = acc[1]
    code = kw.get('code')
    if status == 1 and code is None:
        lda(request, profile)
    elif (status == 1 or status == 2 or status == 4 or status == 5) and code:
        create_account(profile, uid, None, **kw)
        send_mail_func(request, kw.get('subject'), kw.get('msg'), kw.get('email'))
    elif (status == 2 or status == 5) and code is None:
        avatar = create_profile_avatar(request, kw.get('avatar_url'))
        create_account(profile, uid, avatar, **kw)
    elif status == 3:
        request.session['o_auth_msg'] = _(u'У вас уже есть такая учетная запись')
        return HttpResponseRedirect(reverse("login"))
    elif status == 4 and code is None:
        request.session['o_auth_msg'] = _(u'Эта учетная запись закреплена за другим вашим аккаунтом! Вы можете объединить аккаунты.')
        request.session['o_auth_merge_profile'] = profile
        return HttpResponseRedirect(reverse('accounts_merger'))


def add_interface(from_user, to_user):
    for i in from_user.get_profile().interface.all():
        to_user.get_profile().interface.add(i)


def create_auth_msg(request, email):
    md5_string = md5_string_generate(request.user.username)
    auth_link = 'http://%s/user/login/email/%s/' % (request.get_host(), md5_string) 
    msg = _(u"Для авторизации пройдите по ссылке %s") % auth_link
    profile = request.profile
    accounts_interim(request, profile, email, email=email, subject=_(u'Авторизация'), msg=msg, code=md5_string)


@never_cache
def email_auth_send(request):
    '''
    Отпрвление пользователю письма авторизации
    '''
    if request.user.is_authenticated() and request.POST and request.POST.get('email_auth'):
        email = request.POST['email_auth']
        if email:
            email = re.findall(r'^\S+@\S+$', escape(strip_tags(email.strip())))
            if email:
                create_auth_msg(request, email[0])
            else: request.session['o_auth_msg'] = _(u'Введите email')
        else: request.session['o_auth_msg'] = _(u'Введите email')
    else: request.session['o_auth_msg'] = _(u'Введите email')
    return HttpResponseRedirect(reverse('login'))


@never_cache
def email_auth(request, code):
    '''
    Авторизации через e-mail
    '''
    try:
        # поиск аккаунта с кодом активации
        acc = Accounts.objects.get(validation_code=code)
        acc.validation_code = None
        acc.auth_status = True
        acc.save()
        # поиск профиля с активированным аккаунтом
        try:
            profile = Profile.objects.get(accounts=acc)
        except Profile.DoesNotExist: 
            if request.user.is_authenticated():
                profile = request.user.get_profile()
            else:
                user = get_user()
                profile = user.get_profile()
                
            profile.accounts.add(acc)
            
        profile.auth_status = True
        profile.save()
        
        next = request.GET.get('next')
        if next and next != 'adv':
            orgs = Organization.objects.filter(email=acc.login)
            for i in orgs:
                i.editors.add(profile)
                
        # если пользователь известен (автозарегистрирован)
        if request.user.is_authenticated():
            current_user = request.user
            # если этот пользователь не является тем пользователем для которого активирован аккаунт
            if current_user != profile.user:
                # если у этого пользователя нет ниодного аккаунта, авторизуем как найденного пользователя
                if not current_user.get_profile().auth_status: 
                    subscr = current_user.get_profile().personinterface.temp_subscription
                    auth.logout(request)
                    add_interface(current_user, profile.user)
                    user = profile.user
                    user = auth.authenticate(username=user.username, password='pswd')
                    auth.login(request, user)
                    p_interface = user.get_profile().personinterface
                    p_interface.temp_subscription = subscr
                    p_interface.save()
                # если у пользователя есть еще аккаунты, то предложение о слиянии
                else:
                    request.session['o_auth_msg'] = _(u'Эта учетная запись закреплена за другим вашим аккаунтом! Вы можете объединить аккаунты.')
                    request.session['o_auth_merge_profile'] = profile
                    return HttpResponseRedirect(reverse('accounts_merger'))
        # если пользователь неизвестен (клик по ссылке активации через другой браузер/комп)
        # авторизуем как найденного пользователя
        else:
            user = profile.user
            user = auth.authenticate(username=user.username, password='pswd')
            auth.login(request, user)
            
        if next:
            if next == 'adv':
                return HttpResponseRedirect(reverse('profile_adv', kwargs={'id': request.profile.id}))
            else:
                return HttpResponseRedirect(next)
            
    except Accounts.DoesNotExist:
        next = request.GET.get('next')
        if next:
            return HttpResponseRedirect(next)
            
        request.session['o_auth_msg'] = _(u'Неверный ключ авторизации')
        return HttpResponseRedirect(reverse('login'))
    return HttpResponseRedirect(reverse('profile_accounts'))


@never_cache
def email_auth2(request, code):
    '''
    Авторизации через e-mail
    '''
    try:
        # поиск аккаунта с кодом активации
        acc = Accounts.objects.get(validation_code=code)
        acc.validation_code = None
        acc.auth_status = True
        acc.save()
        # поиск профиля с активированным аккаунтом
        profile = Profile.objects.get(accounts=acc)
        profile.auth_status = True
        profile.save()
        # если пользователь известен (автозарегистрирован)
        if request.user.is_authenticated():
            user = request.user
            # если этот пользователь не является тем пользователем для которого активирован аккаунт
            if user != profile.user:
                # если у этого пользователя нет ниодного аккаунта, авторизуем как найденного пользователя
                if not user.get_profile().auth_status:
                    auth.logout(request)
                    add_interface(user, profile.user)
                    delete_user(user)
                    user = profile.user
                    user = auth.authenticate(username=user.username, password='pswd')
                    auth.login(request, user)
                # если у пользователя есть еще аккаунты, то предложение о слиянии
                else:
                    request.session['o_auth_msg'] = _(u'Эта учетная запись закреплена за другим вашим аккаунтом! Вы можете объединить аккаунты.')
                    request.session['o_auth_merge_profile'] = profile
                    return HttpResponseRedirect(reverse('accounts_merger'))
        # если пользователь неизвестен (клик по ссылке активации через другой браузер/комп)
        # авторизуем как найденного пользователя
        else:
            user = profile.user
            user = auth.authenticate(username=user.username, password='pswd')
            auth.login(request, user)
    except Accounts.DoesNotExist:
        request.session['o_auth_msg'] = _(u'Неверный ключ авторизации')
        return HttpResponseRedirect(reverse('login'))
    return HttpResponseRedirect(reverse('profile_accounts'))


def lj_auth_send(request):
    '''
    Авторизация через LiveJournal.com
    '''
    if request.method == 'POST' and 'lj_auth' in request.POST:
        from django_openid_consumer.views import begin
        url = '%s.livejournal.com' % escape(strip_tags(request.POST['lj_auth']))
        return begin(request, redirect_to=None, on_failure=None, template_name='user/login.html', lj_url=url)
    else: raise Http404


def save_name_person(profile, name, status, language):
    '''
    Сохранение имен пользователя
    '''
    try: Person.objects.get(profile=profile, name__name=name, name__status=status)
    except Person.DoesNotExist:
        name_person, created = NamePerson.objects.get_or_create(status=status, language=language, name=name, defaults={
            'status': status, 'language': language, 'name': name
        })
        profile.person.name.add(name_person)
    


def openid_auth(request):
    '''
    Авторизация по OpenID
    '''
    user = request.user
    if user.is_authenticated() and request.openid:
        user_openid = request.openid
        email = None
        nickname = None
        fullname = None
        dob = None
        gender = None
        if request.openid.sreg:
            email = request.openid.sreg.get('email')
            nickname = request.openid.sreg.get('nickname')
            fullname = request.openid.sreg.get('fullname')
            dob = request.openid.sreg.get('dob')
            gender = request.openid.sreg.get('gender')
        if gender:
            gender = 2 if gender == 'F' else 1
        else:
            gender = None
        #return HttpResponse(str('%s<br />%s<br />%s<br />%s<br />%s<br />%s<br />' % (user_openid, email, nickname, fullname, dob, gender)))
        acc = accounts_interim(request, user.get_profile(), user_openid, email=email, nick=nickname, name=fullname, gender=gender, dob=dob)
        if acc: return acc
        return HttpResponseRedirect(reverse('profile_accounts'))
    return HttpResponseRedirect(reverse('main'))


@require_POST    
def oauth_func(request):
    '''
    Выбор сервера для OAuth авторизации
    '''
    if 'mailru_button' in request.POST:
        url = 'https://connect.mail.ru/oauth/authorize?client_id=%s&response_type=code&redirect_uri=%s' % (settings.MAILRU_ID, settings.MAILRU_REDIRECT_URI)
    elif 'yandex_button' in request.POST:
        url = 'https://oauth.yandex.ru/authorize?response_type=code&client_id=%s' % settings.YANDEX_ID
    elif 'google_button' in request.POST:
        url = 'https://accounts.google.com/o/oauth2/auth?redirect_uri=%s&response_type=code&client_id=%s&scope=https://www.googleapis.com/auth/userinfo.email+https://www.googleapis.com/auth/userinfo.profile' % (settings.GOOGLE_REDIRECT_URI, settings.GOOGLE_ID)
    elif 'facebook_button' in request.POST:
        url = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&response_type=code' % (settings.FACEBOOK_ID, settings.FACEBOOK_REDIRECT_URI)
    elif 'vkontakte_button' in request.POST:
        url = 'http://oauth.vk.com/authorize?client_id=%s&redirect_uri=%s&response_type=code' % (settings.VK_ID, settings.VK_REDIRECT_URI)
    elif 'twitter_button' in request.POST:
        request_token_url = 'https://api.twitter.com/oauth/request_token?oauth_callback=%s' % settings.TWITTER_REDIRECT_URI
        authenticate_url = 'https://api.twitter.com/oauth/authenticate'
        consumer = oauth2.Consumer(settings.TWITTER_ID, settings.TWITTER_SECRET_KEY)
        client = oauth2.Client(consumer)
        #client.disable_ssl_certificate_validation = True
        #return HttpResponse(str(dir(client)))
        resp, content = client.request(request_token_url, 'POST')
        if resp['status'] == '200':
            request.session['request_token'] = dict(cgi.parse_qsl(content))
            request.session['twitter_consumer'] = consumer
            url = "%s?oauth_token=%s" % (authenticate_url, request.session['request_token']['oauth_token'])
        else: 
            request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
            return HttpResponseRedirect(reverse('login'))
    else: raise Http404
    return HttpResponseRedirect(url)

@never_cache
def yandex_oauth(request):
    '''
    Авторизация через OAuth yandex.ru
    https://tech.yandex.ru/oauth/doc/dg/reference/auto-code-client-docpage/
    https://tech.yandex.ru/passport/doc/dg/concepts/about-docpage/
    '''
    if request.method == 'GET' and 'code' in request.GET:

        url = 'https://oauth.yandex.ru/token'

        headers = {
            'Content-type':'application/x-www-form-urlencoded',
            #'Authorization': "Basic {0}".format(base64.b64encode("{0}:{1}".format(settings.YANDEX_ID, settings.YANDEX_SECRET_KEY)))
        }

        body = urllib.urlencode({
            'grant_type': 'authorization_code',
            'code': request.GET['code'],
            'client_id': settings.YANDEX_ID,
            'client_secret': settings.YANDEX_SECRET_KEY,
        })

        resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='POST', body=body)
        
        if resp['status'] == '200':
            objs = json.loads(content)
            token = objs.get('access_token')
            
            url = 'https://login.yandex.ru/info?oauth_token=%s' % token

            resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
            
            if resp['status'] == '200':
                objs = json.loads(content)
                login = objs.get('login')
                email = objs.get('default_email')
                avatar = objs.get('default_avatar_id')
                avatar_url = 'https://avatars.yandex.net/get-yapic/%s/islands-68' % avatar

                if email:
                    login = email

                acc = accounts_interim(request, request.profile, login, email=email, nick=None, name=None, gender=None, dob=None, avatar_url=avatar_url)

                if acc: return acc
                return HttpResponseRedirect(reverse('profile_accounts'))

            else:
                request.session['o_auth_msg'] = _(u'Ошибка 3')
        else:
            objs = json.loads(content)
            error = objs.get('error','')
            error_description = objs.get('error_description','')
            request.session['o_auth_msg'] = _(u'Ошибка 2, %s (%s)') % (error, error_description)
    else:
        error = request.GET.get('error','')
        error_description = request.GET.get('error_description','')
        request.session['o_auth_msg'] = _(u'Ошибка 1, %s (%s)') % (error, error_description)

    return HttpResponseRedirect(reverse('login'))


def mailru_oauth(request):
    '''
    Авторизация через OAuth mail.ru
    '''
    if request.method == 'GET' and 'code' in request.GET:
        url = 'https://connect.mail.ru/oauth/token'
        body = urllib.urlencode({
            'client_id': settings.MAILRU_ID,
            'client_secret': settings.MAILRU_SECRET_KEY,
            'grant_type': 'authorization_code',
            'redirect_uri': settings.MAILRU_REDIRECT_URI,
            'code': request.GET['code']
        })
        resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='POST', body=body)
        if resp['status'] == '200':
            url = 'http://www.appsmail.ru/platform/api'
            objs = json.loads(content)
            params = 'app_id=%smethod=users.getInfosecure=1session_key=%s' % (settings.MAILRU_ID, objs['access_token'])
            body = urllib.urlencode({
                'method': 'users.getInfo',
                'app_id': settings.MAILRU_ID,
                'sig': hashlib.md5(params + settings.MAILRU_SECRET_KEY).hexdigest(),
                'session_key': objs['access_token'],
                'secure': 1
            })
            resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='POST', body=body)
            if resp['status'] == '200':
                user_data = json.loads(content)
                email = user_data[0].get('email', None)
                uid = 'mail.ru_%s' % user_data[0].get('uid', None)
                nickname = user_data[0].get('nick', None).encode('utf-8')
                first_name = user_data[0].get('first_name', None).encode('utf-8')
                last_name = user_data[0].get('last_name', None).encode('utf-8')
                fullname = '%s %s' % (first_name, last_name)
                birthday = user_data[0].get('birthday', None)
                avatar_url = user_data[0].get('pic_128', None)
                dob = birthday if birthday != '' else None
                if dob:
                    dob = dob.split('.')
                    dob = '%s-%s-%s' % (dob[2], dob[1], dob[0])
                gender = user_data[0].get('sex', None)
                if gender is not None: gender = 1 if int(gender) == 0 else 2
                acc = accounts_interim(request, request.profile, uid, email=email, nick=nickname, name=fullname, gender=gender, dob=dob, avatar_url=avatar_url)
                if acc: return acc
                return HttpResponseRedirect(reverse('profile_accounts'))
            else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
        else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
    else: request.session['o_auth_msg'] = _(u'Неверный запрос')
    return HttpResponseRedirect(reverse('login'))
        

def twitter_oauth(request):
    '''
    Авторизация через OAuth twitter.com
    '''
    if request.method == 'GET':
        if 'denied' not in request.GET:
            oauth_verifier = request.GET['oauth_verifier']
            access_token_url = 'https://api.twitter.com/oauth/access_token/?oauth_verifier=%s' % oauth_verifier
            token = oauth2.Token(request.session['request_token']['oauth_token'], request.session['request_token']['oauth_token_secret'])
            client = oauth2.Client(request.session['twitter_consumer'], token)
            resp, content = client.request(access_token_url, 'GET')
            if resp['status'] == '200':
                access_token = dict(cgi.parse_qsl(content))
                uid = 'twitter.com_%s' % access_token['user_id']
                nickname = access_token['screen_name']
                avatar_url = 'https://api.twitter.com/1/users/show.json?screen_name=%s' % nickname
                ava_resp, ava_content = httplib2.Http(disable_ssl_certificate_validation=True).request(avatar_url, method='GET')
                ava_data = json.loads(ava_content)
                avatar_url = ava_data.get('profile_image_url', None)
                acc = accounts_interim(request, request.profile, uid, nick=nickname, avatar_url=avatar_url)
                if acc: return acc
                return HttpResponseRedirect(reverse('profile_accounts'))
            else: 
                request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
        else: request.session['o_auth_msg'] = _(u'Авторизация была отменена')
    else: request.session['o_auth_msg'] = _(u'Неверный запрос')
    return HttpResponseRedirect(reverse('login'))


def google_oauth(request):
    '''
    Авторизация через OAuth google.com
    '''
    if request.method == 'GET' and 'code' in request.GET:
        url = 'https://accounts.google.com/o/oauth2/token'
        headers = {'content-type':'application/x-www-form-urlencoded'}
        body = urllib.urlencode({
            'code': request.GET['code'],
            'client_id': settings.GOOGLE_ID,
            'client_secret': settings.GOOGLE_SECRET_KEY,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        })
        resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='POST', body=body, headers=headers)
        if resp['status'] == '200':
            objs = json.loads(content)
            url = 'https://www.googleapis.com/oauth2/v1/userinfo?access_token=%s' % objs['access_token']
            resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
            if resp['status'] == '200':
                user_data = json.loads(content)
                email = user_data.get('email', None)
                uid = 'google.com_%s' % user_data.get('id', None)
                fullname = user_data.get('name', None).encode('utf-8')
                dob = user_data.get('birthday', None)
                gender = user_data.get('gender', None)
                avatar_url = user_data.get('picture', None)
                if dob:
                    dob = dob.split('-')
                    if dob[0] == '0000': dob = '1900-%s-%s' % (dob[1], dob[2])
                if gender == 'other': gender = None
                elif gender == 'male': gender = 1
                elif gender == 'female': gender = 2
                acc = accounts_interim(request, request.profile, uid, email=email, name=fullname, gender=gender, dob=dob, avatar_url=avatar_url)
                if acc: return acc
                return HttpResponseRedirect(reverse('profile_accounts'))
            else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
        else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
    else: request.session['o_auth_msg'] = _(u'Неверный запрос')
    return HttpResponseRedirect(reverse('login'))
    
    
def facebook_oauth(request):
    '''
    Авторизация через OAuth facebook.com
    '''
    if request.method == 'GET' and 'code' in request.GET:
        url = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (settings.FACEBOOK_ID, settings.FACEBOOK_REDIRECT_URI, settings.FACEBOOK_SECRET_KEY, request.GET['code'])
        resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
        if resp['status'] == '200':
            access = dict(cgi.parse_qsl(content))
            url = 'https://graph.facebook.com/me?access_token=%s' % access['access_token']
            resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
            if resp['status'] == '200':
                user_data = json.loads(content)
                fullname = user_data.get('name')
                if fullname:
                    fullname = fullname.encode('utf-8')
                gender = user_data.get('gender')
                if gender:
                    gender = gender.encode('utf-8')
                uid = 'facebook.com_%s' % user_data.get('id')
                avatar_url = 'http://graph.facebook.com/%s/picture' % user_data.get('id')
                if gender == 'male': gender = 1
                elif gender == 'female': gender = 2
                else: gender = None
                acc = accounts_interim(request, request.profile, uid, name=fullname, gender=gender, avatar_url=avatar_url)
                if acc: return acc
                return HttpResponseRedirect(reverse('profile_accounts'))
            else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
        else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
    else: request.session['o_auth_msg'] = _(u'Неверный запрос')
    return HttpResponseRedirect(reverse('login'))

    
def vkontakte_oauth(request):
    '''
    Авторизация через OAuth vk.com
    '''
    if request.method == 'GET' and 'code' in request.GET:
        url = 'https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&code=%s&redirect_uri=%s' % (settings.VK_ID, settings.VK_SECRET_KEY, request.GET['code'], settings.VK_REDIRECT_URI)
        try:
            resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method='GET')
            if resp['status'] == '200':
                objs = json.loads(content)
                url = 'https://api.vk.com/method/users.get?uids=%s&fields=uid,first_name,last_name,nickname,screen_name,sex,bdate,photo_medium&access_token=%s' % (objs['user_id'], objs['access_token'])
                try:
                    resp, content = httplib2.Http(disable_ssl_certificate_validation=True).request(url, method="GET")
                    if resp['status'] == '200':
                        user_data = json.loads(content)
                        first_name = user_data['response'][0].get('first_name', None).encode('utf-8')
                        last_name = user_data['response'][0].get('last_name', None).encode('utf-8')
                        fullname = '%s %s' % (first_name, last_name)
                        nickname = user_data['response'][0].get('nickname', None).encode('utf-8')
                        dob = user_data['response'][0].get('bdate', None)
                        gender = user_data['response'][0].get('sex', None)
                        uid = 'vk.com_%s' % user_data['response'][0].get('uid', None)
                        avatar_url = user_data['response'][0].get('photo_medium', None)
                        if nickname == '': nickname = None
                        if dob:
                            dob = dob.split('.')
                            try: dob = '%s-%s-%s' % (dob[2], '{0:0=2d}'.format(int(dob[1])), '{0:0=2d}'.format(int(dob[0])))
                            except IndexError: dob = '1900-%s-%s' % ('{0:0=2d}'.format(int(dob[1])), '{0:0=2d}'.format(int(dob[0])))
                        if gender == 2: gender = 1
                        elif gender == 1: gender = 2
                        else: gender = None
                        acc = accounts_interim(request, request.profile, uid, nick=nickname, name=fullname, gender=gender, dob=dob, avatar_url=avatar_url)
                        if acc: return acc
                        return HttpResponseRedirect(reverse('profile_accounts'))
                    else: request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
             
                except httplib2.SSLHandshakeError:
                    request.session['o_auth_msg'] = _(u'Ошибка SSL (2)')
            else: 
                request.session['o_auth_msg'] = _(u'Ошибка %s') % resp['status']
                if request.user.is_superuser:
                    request.session['o_auth_msg'] = resp

        except httplib2.SSLHandshakeError:
            request.session['o_auth_msg'] = _(u'Ошибка SSL (1)')
    else: request.session['o_auth_msg'] = _(u'Неверный запрос')
    return HttpResponseRedirect(reverse('login'))  
    


def get_usercard(user_obj, ucity=True, ugroups=False):
    '''
    Функция возвращает данные из визитки пользователя
    '''
    if not isinstance(user_obj, list):
        user_obj = [user_obj,]

    profiles = Profile.objects.select_related('user', 'person', 'person__country', 'personinterface').filter(user__in=user_obj)
        
    city_dict = {}
    if ucity:
        for i in list(NameCity.objects.filter(city__person__profile__user__in=user_obj, status=1).values('city', 'name')):
            city_dict[int(i['city'])] = i['name']
        
    names_dict = {}
    for i in list(NamePerson.objects.filter(person__profile__user__in=user_obj, status=1).order_by('id').values('person', 'name')):
        names_dict[int(i['person'])] = i['name']
    
    data = {}
    for i in profiles:
        sex, born, emails, emails_not_auth, name, acc, accs, full, nick, login = ([], [], [], [], [], [], [], [], [], [])

        card = i.person
        money = '%.2f' % i.personinterface.money
        email = i.user.email
        
        city = None
        if ucity and card.city:
            city_name = city_dict.get(card.city_id)
            city = {'id': card.city_id, 'name': city_name}

        country = {'id': card.country_id, 'name': card.country.name, 'name_en': card.country.name_en} if card.country else None
    
        person_name_obj = names_dict.get(card.id)
        
        for j in i.accounts.all():
            acc.append({'id': j.id, 'obj': j})
            
            if j.fullname:
                full.append(j.fullname)
            if j.nickname:
                nick.append(j.nickname)
            if j.login:
                login.append(j.login.split('@')[0])
            
            if not card.male:
                if j.male and j.male not in sex:
                    sex.append(j.male)
            if not card.born:
                if j.born and j.born not in born:
                    born.append(j.born)
            if j.email and j.email not in emails:
                if j.auth_status:
                    emails.append(j.email)
                else:
                    emails_not_auth.append(j.email)
            if not person_name_obj:
                if j.fullname and j.fullname not in name:
                    name.append(j.fullname)
        
        if not full and not nick:
            accs = login
        else:
            accs = full + nick
            
        accs = sorted(accs, reverse=True)
        short_name = accs[0] if accs else 'User_%s' % i.user_id
        nickname = i.user.first_name

        groups = []
        if ugroups:
            groups = [j.name for j in i.user.groups.all()]
        
        if person_name_obj:
            name = person_name_obj 
        else:
            if nickname:
                name = nickname
            else:
                name = short_name

        if card.male or card.male == 0:
            sex = card.male
        else:
            sex = sex[0] if len(sex) == 1 else 0
            
        if card.born:
            born = card.born
        else:
            born = born[0] if len(born) == 1 else None 
        
        if acc:
            acc = sorted(acc, key=operator.itemgetter('id'))
    
        data[i.user_id] = {
            'sex': sex, 
            'born': born, 
            'emails': emails, 
            'email': email, 
            'emails_not_auth': emails_not_auth, 
            'name': name, 
            'city': city, 
            'country': country, 
            'card': card, 
            'money': money, 
            'accounts': acc, 
            'profile': i, 
            'superuser': i.user.is_superuser,
            'groups': groups,
        }
    
    if len(data.keys()) == 1:
        return data.values()[0]
    else:
        return data
        


@never_cache
def profile(request, id=None):
    from film.views import get_youtube_video_player

    current_user = request.user
    if current_user.is_authenticated():
        current_site = request.current_site
        template = 'user/profile_new.html'

        if current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
            if current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                template = 'user/profile_new_vlada.html'
            sex = ((0, 'No'),(1, 'Male'),(2, 'Female'))
        else:
            sex = ((0, 'Нет'),(1, 'М'),(2, 'Ж'))

        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            template = 'mobile/user/profile_new.html'

        if request.subdomain == 'pm-prepare' and request.current_site.domain in ('imiagroup.com.au'):
            template = 'pmprepare/user/profile.html'

        if id:
            id = int(id)
            is_my_profile = True if current_user.id == id else False
        else:
            is_my_profile = True
            
        if id and not is_my_profile:
            try:
                user = User.objects.get(pk=id)
            except User.DoesNotExist:
                raise Http404
        else:
            user = current_user
            
        card = get_usercard(user, ugroups=True)

        if not current_user.is_superuser and not is_my_profile:
            if card['profile'].show_profile == '2':
                raise Http404

        if request.POST and (current_user.is_superuser or is_my_profile):
            poster = request.FILES.get('profile_poster_file')
            if poster:
                file_format = low(poster.name)
                img_format = re.findall(r'\.(jpg|png|jpeg|bmp)$', file_format)

                if img_format:
                    img_obj = poster.read()
                    img_name = 'u%s_%s.%s' % (user.id, md5_string_generate(user.id)[:8], img_format[0])
                    img_path_tmp = '%s/%s' % (settings.AVATAR_FOLDER, img_name)
                    img_db_path = img_path_tmp.replace(settings.MEDIA_ROOT, '')

                    try:
                        exist_poster = card['profile'].person.poster.get(status=1)
                        try:
                            os.remove('%s%s' % (settings.MEDIA_ROOT, exist_poster.file))
                        except OSError: pass
                        exist_poster.delete()
                    except Images.DoesNotExist: pass

                    with open(img_path_tmp, 'wb') as f:
                        f.write(img_obj)

                    resized = resize_image(1000, None, img_obj, 1500)
                    if resized:
                        resized.save(img_path_tmp)

                    image_obj = Images.objects.create(status=1, file=img_path_tmp.replace(settings.MEDIA_ROOT, ''))
                    card['profile'].person.poster.add(image_obj)
                    
            if request.user.is_superuser:
                new_bg = request.FILES.get('person_page_bg_file')
                bg_url = request.POST.get('person_page_bg_url','').strip()
                video = request.POST.get('trailer')

                if new_bg and bg_url:
                    file_format = low(new_bg.name)
                    img_format = re.findall(r'\.(jpg|png|jpeg|bmp)$', file_format)

                    if img_format:
                        img_obj = new_bg.read()
                        img_name = 'u%sbg_%s.%s' % (user.id, md5_string_generate(user.id)[:8], img_format[0])
                        img_path_tmp = '%s/%s' % (settings.PROFILE_BG, img_name)
                        img_db_path = img_path_tmp.replace(settings.MEDIA_ROOT, '')
                        
                        if card['profile'].bg:
                            try:
                                os.remove('%s%s' % (settings.MEDIA_ROOT, card['profile'].bg))
                            except OSError: pass

                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)

                        card['profile'].bg = img_db_path
                        card['profile'].bg_url = bg_url
                        card['profile'].save()

                if video is not None:
                    if video.strip():
                        code = get_youtube_video_player(video, width=560, height=315)
                        card['card'].video = code
                    else:
                        card['card'].video = None
                    card['card'].save()
                    
            return HttpResponseRedirect(reverse('profile', kwargs={'id': user.id}))


        p_accounts = card['accounts']
        p_count = len(p_accounts)

        try:
            profile_poster = card['profile'].person.poster.get(status=1).file
        except Images.DoesNotExist:
            profile_poster = None
        
        card['is_my_profile'] = is_my_profile
        data = {'p_count': p_count, 'card': card, 'poster': profile_poster, 'is_my_profile': is_my_profile, 'user_id': id, 'sex': sex, 'nickname': user.first_name}
        
        if not card['email'] and len(card['emails']):
            user.email = card['emails'][0]
            user.save()
            card['email'] = card['emails'][0]
        
        if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru', 'letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or 'vsetiinter.net' and request.subdomain == 'ya':
        
            countries_ids = set(list(NameCity.objects.filter(status=1).exclude(city__country=None).values_list('city__country', flat=True)))
            countries = Country.objects.filter(pk__in=countries_ids).order_by('name')
            
            user_country = card['country']['id'] if card['country'] else countries[0].id
            
            cities_names = list(NameCity.objects.filter(status=1, city__country__id=user_country).order_by('name').values('id', 'city__id', 'name'))
                
            year_now = datetime.datetime.now().year
            year_now_past = year_now - 3
            years = [i for i in range(1930, year_now_past)]
            years.reverse()

            sites = []
            groups = []
            in_sites = []
            if current_user.is_superuser:
                sites = DjangoSite.objects.all()
                groups = Group.objects.all()

                in_sites = list(i for i in card['profile'].site_admin.all().values_list('id', flat=True))
                in_sites = [int(i) for i in in_sites]
                
                data['withdraw'] =  WithdrawMoney.objects.filter(profile=card['profile']).order_by('-dtime')
            

            # ТРЕЙЛЕР
            trailer_code = card['card'].video if card['card'].video else ''
            trailer_url = ''
            if trailer_code:
                trailer = BeautifulSoup(trailer_code, from_encoding='utf-8')
                trailer = trailer.find('iframe')
                if trailer:
                    trailer_url = 'https:%s' % trailer['src']
                    trailer_code = trailer
                    trailer_code['width'] = 250
                    trailer_code['height'] = 150
                else:
                    trailer_code = ''
            trailer = str(trailer_code)

            user_bg = get_usr_bg(request, card['profile'])

            data['countries'] = countries
            data['cities_names'] = cities_names
            data['born_years'] = years
            data['born_days'] = [i for i in range(1, 32)]
            data['born_months'] = [datetime.date(year_now, i, 1) for i in range(1, 13)]
            data['show_profile'] = SHOW_PROFILE_CHOICES
            data['sites'] = sites
            data['groups'] = groups
            data['in_sites'] = in_sites
            data['video'] = trailer
            data['video_url'] = trailer_url
            data['user_bg'] = user_bg

            return render_to_response(template, data, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))

'''
@never_cache
def profile_background(request, id):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        card = get_usercard(user)

        exist = get_usr_bg(request, card['profile'])
        if not exist:
            if card['profile'].bg and not request.POST:
                exist, exist_created = SiteBanners.objects.get_or_create(
                    profile = card['profile'],
                    btype = '3',
                    defaults = {
                        'profile': card['profile'],
                        'btype': '3',
                        'file': card['profile'].bg,
                        'name': '',
                        'url': card['profile'].bg_url,
                        'user': request.profile,
                        'accepted': True,
                        'views': 1,
                    })
                if not exist_created:
                    exist.views += 1
                    exist.save()

        if request.POST:     
            if request.user.is_superuser:
                new_bg = request.FILES.get('person_page_bg_file')
                bg_url = request.POST.get('person_page_bg_url','').strip()

                if new_bg and bg_url:
                    file_format = low(new_bg.name)
                    img_format = re.findall(r'\.(jpg|png|jpeg|bmp)$', file_format)

                    if img_format:
                        
                        img_obj = new_bg.read()
                        img_name = 'u%sbg_%s.%s' % (user.id, md5_string_generate(user.id)[:8], img_format[0])
                        img_path_tmp = '%s/%s' % (settings.PROFILE_BG, img_name)
                        img_db_path = img_path_tmp.replace(settings.MEDIA_ROOT, '/upload')
                        
                        if exist:
                            try:
                                path = '%s%s' % (settings.MEDIA_ROOT.replace('/upload', ''), exist.file)
                                os.remove(path)
                            except OSError: pass
                            exist.file = img_db_path
                            exist.url = bg_url
                            exist.user = request.profile
                            exist.save()
                        else:
                            exist = SiteBanners.objects.create(
                                profile = card['profile'],
                                file = img_db_path,
                                name = '',
                                url = bg_url,
                                user = request.profile,
                                accepted = True,
                                btype = '3',
                            )

                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)
                    
            return HttpResponseRedirect(reverse('profile_background', kwargs={'id': user.id}))

        clicks = SiteBannersClicks.objects.filter(banner=exist).count() if exist else 0

        
        adv = get_bg(request)

        tmplt = 'user/profile_background.html'
        #if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        #    tmplt = 'mobile/user/profile_background.html'

        return render_to_response(tmplt, {'card': card, 'is_my_profile': is_my_profile, 'adv': adv, 'user_bg': exist, 'clicks': clicks}, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))


@never_cache
def profile_adv_mypage(request, id):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        card = get_usercard(user)

        user_bg = get_usr_bg(request, card['profile'])

        tmplt = 'user/profile_adv_on_mypage.html'
        #if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        #    tmplt = 'mobile/user/profile_background.html'

        return render_to_response(tmplt, {'card': card, 'is_my_profile': is_my_profile, 'simple': True, 'user_bg': user_bg}, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))



@never_cache
def profile_adv_site(request, id):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        card = get_usercard(user)


        city = request.current_user_city_id
        country = request.current_user_country_id
        style = ''
        banner_city, banner_country, banner_other = ([], [], [])
        banner, banner_id, banner_url = (None, None, None)

        price = 3

        # выбрать оплаченную рекламу
        banners = SiteBanners.objects.filter(Q(country__pk=country) | Q(country=None), user__personinterface__money__gte=price, balance__gte=price, btype='1', user=card['profile'], deleted=False).values('url', 'id', 'views', 'country', 'cities__pk', 'style', 'name', 'text', 'file').order_by('-cities__pk')

        for i in banners:
            if i['cities__pk'] == request.current_user_city_id:
                banner_city.append(i)
            elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                banner_country.append(i)
            elif not i['country']:
                banner_other.append(i)
        
        if banner_city:
            banner = random.choice(banner_city)
        elif banner_country:
            banner = random.choice(banner_country)
        elif banner_other:
            banner = random.choice(banner_other)

        adv_type = 'banner'
        if banner:
            # swf баннер
            if banner['style'] == None:
                adv_type = 'banner'
                swf = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (banner['file'], banner['file'])
                if banner['url']:
                    swf = u'<noindex><a class="flb_link" id="flb_id_%s" href="%s" target="_blank" rel="nofollow">%s<div class="flb_layout"></div></a></noindex>' % (banner['id'], banner['url'], swf)
                else:
                    swf = u'<div class="flb_link" id="flb_id_%s">%s</div>' % (banner['id'], swf)
            # рекламный блок из конструктора блоков
            else:
                adv_type = 'adv'
                style = banner['style']
                swf = u'<span class="adv_anchor">%s</span>' % banner['name']
                swf += u'<div class="adv_text">%s</div>' % banner['text']
                banner_id = banner['id']
                banner_url = banner['url']
        else:
            swf = u'Banner'


        mbanner_city, mbanner_country, mbanner_other = ([], [], [])
        mbanner, mbanner_id, mbanner_url = (None, None, None)

        mprice = 3

        # выбрать оплаченную рекламу
        mbanners = SiteBanners.objects.filter(Q(country__pk=country) | Q(country=None), user__personinterface__money__gte=mprice, balance__gte=mprice, btype='6', user=card['profile'], deleted=False).values('url', 'id', 'views', 'country', 'cities__pk', 'style', 'name', 'text', 'file').order_by('-cities__pk')

        for i in mbanners:
            if i['cities__pk'] == request.current_user_city_id:
                mbanner_city.append(i)
            elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                mbanner_country.append(i)
            elif not i['country']:
                mbanner_other.append(i)
        
        if mbanner_city:
            mbanner = random.choice(mbanner_city)
        elif mbanner_country:
            mbanner = random.choice(mbanner_country)
        elif mbanner_other:
            mbanner = random.choice(mbanner_other)

        mstyle = ''
        if mbanner:
            mstyle = mbanner['style']
            mswf = u'<span class="adv_anchor">%s</span>' % mbanner['name']
            mswf += u'<div class="adv_text">%s</div>' % mbanner['text']
            mbanner_id = mbanner['id']
            mbanner_url = mbanner['url']
        else:
            mswf = u'Banner'


        user_bg = get_usr_bg(request, card['profile'])


        tmplt = 'user/profile_adv_on_site.html'
        #if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        #    tmplt = 'mobile/user/profile_background.html'

        return render_to_response(tmplt, {'card': card, 'is_my_profile': is_my_profile, 'swf_object': swf, 'adv_style': style, 'adv_type': adv_type, 'banner_id': banner_id, 'banner_url': banner_url, 'user_bg': user_bg, 'mswf_object': mswf, 'mbanner_id': mbanner_id, 'mbanner_url': mbanner_url, 'madv_style': mstyle}, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))
'''


def left_banner_func(request, site, city, country):
    style = ''
    adv_type = ''
    banner_city, banner_country, banner_other = ([], [], [])
    banner, banner_id, banner_url = (None, None, None)

    now = datetime.datetime.now()

    banners = SiteBanners.objects.filter(btype='7', deleted=False, sites=site, bg_disable_dtime_to=None).values('id', 'name', 'text').order_by('-id')

    banner = None
    if banners:
        banner = banners[0]


    if banner:
        adv_type = 'code'
        swf = banner['text']
    else:

        btype = '1'
        price = get_adv_price(btype)
        banners = SiteBanners.objects.filter(Q(country__pk=country) | Q(country=None), user__personinterface__money__gte=price, balance__gte=price, btype__in=('1', '5'), deleted=False, sites=site).values('url', 'id', 'views', 'country', 'cities__pk', 'style', 'name', 'text', 'dtime').order_by('-cities__pk')

        for i in banners:
            future = i['dtime'].date() + datetime.timedelta(days=13)
            if now.date() <= future:
                if i['cities__pk'] == request.current_user_city_id:
                    banner_city.append(i)
                elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                    banner_country.append(i)
                elif not i['country']:
                    banner_other.append(i)
        
        if banner_city:
            banner = random.choice(banner_city)
        elif banner_country:
            banner = random.choice(banner_country)
        elif banner_other:
            banner = random.choice(banner_other)


        if banner:
            if not request.bot:
                set_adv_view(request, banner['id'])

            # swf баннер
            if banner['style'] == None:
                adv_type = 'banner'
                swf = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (banner['file'], banner['file'])
                if banner['url']:
                    swf = u'<noindex><a class="flb_link" id="flb_id_%s" href="%s" target="_blank" rel="nofollow">%s<div class="flb_layout"></div></a></noindex>' % (banner['id'], banner['url'], swf)
                else:
                    swf = u'<div class="flb_link" id="flb_id_%s">%s</div>' % (banner['id'], swf)
            # рекламный блок из конструктора блоков
            else:
                adv_type = 'adv'
                style = banner['style']
                swf = u'<span class="adv_anchor">%s</span>' % banner['name']
                swf += u'<div class="adv_text">%s</div>' % banner['text']

                banner_id = banner['id']
                banner_url = banner['url']

        else:
            adv_type = 'banner'
            swf = u'Banner'
    
    return {'swf_object': swf, 'request': request, 'adv_style': style, 'adv_type': adv_type, 'banner_id': banner_id, 'banner_url': banner_url}



def left_banner_user_func(request, site, city, country, user_id):

    btype = '4'
    price = get_adv_price(btype)

    banners = SiteBanners.objects.filter(Q(profile__user__pk=user_id, country__pk=country) | Q(profile__user__pk=user_id, country__pk=None), user__personinterface__money__gte=price, balance__gte=price, btype=btype, deleted=False).values('file', 'url', 'id', 'views', 'country', 'cities__pk', 'dtime').order_by('-cities__pk')

    now = datetime.datetime.now()

    banner = None
    get_country = False
    for i in banners:
        future = i['dtime'].date() + datetime.timedelta(days=13)
        if now.date() <= future:
            if i['cities__pk'] == request.current_user_city_id:
                banner = i
                break
            elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                banner = i
                get_country = True
            elif not get_country and not i['country'] and not i['cities__pk']:
                banner = i

    if banner:
        if not request.bot:
            set_adv_view(request, banner['id'])

        swf = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (banner['file'], banner['file'])
        if banner['url']:
            swf = u'<noindex><a class="flb_link" id="flb_id_%s" href="%s" target="_blank" rel="nofollow">%s<div class="flb_layout"></div></a></noindex>' % (banner['id'], banner['url'], swf)
        else:
            swf = u'<div class="flb_link" id="flb_id_%s">%s</div>' % (banner['id'], swf)
    else:
        swf = u'Banner'

    return {'swf_object': swf, 'request': request, 'adv_type': 'banner'}


@never_cache
def profile_adv(request, id):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        if not is_my_profile and not request.user.is_superuser:
            raise Http404

        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile
        user_bg = get_usr_bg(request, card['profile'])
        today = datetime.datetime.today().date()

        sites = {}
        for i in DjangoSite.objects.filter(pk__in=(1, 5)):
            sites[str(i.id)] = i

        pages = {
            '1': 'Страницы сайта',
            '2': 'Моя',
        }
        visibles = {
            '1': 'Я',
            '2': 'Все',
        }


        set_cookie = False
        if request.POST:
            site = request.POST.get('site')
            site = sites.get(str(site), request.current_site)
            page = request.POST.get('page', '1')
            visible = request.POST.get('visible')
            
            if not pages.get(page):
                page = '1'
            if not visibles.get(visible):
                visible = '1'
            cookie = '%s;%s;%s' % (site.id, int(page), int(visible))
            set_cookie = True
        else:
            if request.COOKIES.has_key('profile_adv_filter'):
                value = request.COOKIES['profile_adv_filter']
                site, page, visible = value.split(';')
                site = sites.get(site, request.current_site)
            else:
                site = request.current_site
                page = '1'
                visible = '1'

        filter = {'deleted': False}

        new_mob_btype = 6
        if page == '1':
            btypes = (1, 2, 5, 6, 7)
            new_bg_btype = 2
            new_adv_btype = 1
            filter['btype__in'] = btypes
            filter['sites'] = site
        else:
            btypes = (3, 4)
            new_bg_btype = 3
            new_adv_btype = 4
            filter['btype__in'] = btypes

        if request.user.is_superuser:
            if not is_my_profile:
                filter['user'] = card['profile']
        else:
            filter['user'] = card['profile']

        banners = list(SiteBanners.objects.filter(**filter).values('id', 'name', 'text', 'budget', 'balance', 'user__personinterface__money', 'user', 'spent', 'btype', 'file', 'dtime', 'views', 'last_show', 'bg_disable_dtime_to'))

        banners_ids = []

        for i in banners:
            banners_ids.append(i['id'])

        clicks = {}
        for i in SiteBannersClicks.objects.filter(banner__pk__in=banners_ids):
            if not clicks.get(i.banner_id):
                clicks[i.banner_id] = 0
            clicks[i.banner_id] += 1

        prices_data = {}
        for i in ActionsPriceList.objects.filter(pk__in=settings.PRICES.values(), allow=True):
            prices_data[i.id] = i.price

        data = {}
        for i in banners:
            im_author = True if request.profile.id == i['user'] else False
            
            click = clicks.get(i['id'], 0)
            view = i['views']

            from_date, to_date = (i['dtime'].date(), i['last_show'])
            if to_date and to_date < from_date:
                to_date = None

            spent_percent = 0
            if i['spent'] and i['budget']:
                spent_percent = int((i['spent'] * 100) / i['budget'])

            if not data.get(i['btype']):
                data[i['btype']] = {'past': [], 'current': []}

            time_status = 'past'

            price_rel = settings.PRICES.get(i['btype'], 0)
            price = prices_data.get(price_rel, 0)

            if int(i['btype']) == 3:
                time_status = 'current'
            if int(i['btype']) == 7:
                if not i['bg_disable_dtime_to']:
                    time_status = 'current'
            elif int(i['btype']) == 4 and (from_date + datetime.timedelta(days=13)) >= today:
                time_status = 'current'
            elif i['balance'] >= price and i['user__personinterface__money'] >= price:
                if (from_date + datetime.timedelta(days=13)) >= today:
                    time_status = 'current'

            data[i['btype']][time_status].append({
                'im_author': im_author,
                'clicks': click,
                'name': i['name'],
                'views': view,
                'spent': '%5.2f' % i['spent'],
                'spent_percent': spent_percent,
                'id': i['id'],
                'from_date': from_date,
                'to_date': to_date,
                'btype': i['btype'],
                'file': i['file'],
                'text': i['text'],
            })

        for k, v in data.iteritems():
            data[k]['past'] = sorted(v['past'], key=operator.itemgetter('id'), reverse=True)
            data[k]['current'] = sorted(v['current'], key=operator.itemgetter('id'), reverse=True)

        if page == '1':
            bg = get_bg(request, site)
            adv_id = bg['id']
            adv_url = bg['url']
            adv_img = bg['img']

            lb = left_banner_func(request, site, request.current_user_city_id, request.current_user_country_id)
        else:
            adv_id = user_bg.id
            adv_url = user_bg.url
            adv_img = user_bg.file

            lb = left_banner_user_func(request, site, request.current_user_city_id, request.current_user_country_id, request.user.id)

        tmplt = 'user/profile_adv.html'
        #if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        #    tmplt = 'mobile/user/profile_background.html'

        response = render_to_response(tmplt, {'card': card, 'user_bg': user_bg, 'sites': sites.values(), 'site': site, 'data': data, 'visibles': visibles, 'visible': visible, 'pages': pages, 'page': page, 'new_bg_btype': new_bg_btype, 'new_adv_btype': new_adv_btype, 'new_mob_btype': new_mob_btype, 'adv_id': adv_id, 'adv_url': adv_url, 'adv_img': adv_img, 'lb': lb}, context_instance=RequestContext(request))
        if set_cookie:
            response.set_cookie('profile_adv_filter', cookie)
        return response

    return HttpResponseRedirect(reverse('main'))


@never_cache
def profile_adv_details(request, id, adv):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        if not is_my_profile and not request.user.is_superuser:
            raise Http404

        data_type = 1 # 1 - клики, 2 - просмотры
        city = None
        if request.POST:
            data_type = int(request.POST.get('type', 1))
            city = int(request.POST.get('city', 0))

        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile

        user_bg = get_usr_bg(request, card['profile'])
        
        filter = {'pk': adv, 'deleted': False, 'user': card['profile']}

        try:
            banner = SiteBanners.objects.get(**filter)
        except SiteBanners.DoesNotExist:
            raise Http404

        from_date, to_date = (banner.dtime.date(), banner.last_show)
        spent = 0
        
        city_clicks = list(SiteBannersClicks.objects.filter(banner=banner).distinct('profile__person__city').values_list('profile__person__city', flat=True))
        city_views = list(SiteBannersViews.objects.filter(banner=banner).distinct('profile__person__city').values_list('profile__person__city', flat=True))
        cities_ids = list(set(city_clicks) | set(city_views))
        cities = list(NameCity.objects.filter(city__pk__in=cities_ids, status=1).order_by('name').values('city', 'name'))
        cities.insert(0, {'city': 0, 'name': 'ВСЕ'})

        profiles = []
        data = {}

        if data_type == 1:
            model = SiteBannersClicks
            price = get_adv_price(banner.btype)
        elif data_type == 2:
            model = SiteBannersViews
            price = ActionsPriceList.objects.get(pk=48, allow=True).price

        filter = {'banner': banner}
        if city:
            filter['profile__person__city__pk'] = city

        user_count = 0
        for i in model.objects.select_related('profile').filter(**filter):
            try:
                item_date = i.dtime.date()
            except AttributeError:
                item_date = i.dtime

            if not data.get(item_date):
                data[item_date] = {'data': [], 'spent': 0}

            if i.profile:
                uid = i.profile.user_id 
                profiles.append(i.profile)
            else:
                uid = None

            data[item_date]['data'].append({'profile': uid, 'dtime': i.dtime})
            data[item_date]['spent'] += price
            spent += price

            user_count += 1

        spent = '%5.2f' % spent

        data = collections.OrderedDict(sorted(data.items(), reverse=True))

        peoples = org_peoples(set(profiles), True)

        for key_date, value_list in data.iteritems():
            for i in value_list['data']:
                user_obj = peoples.get(i['profile'])
                i['profile_obj'] = user_obj
                if user_obj and key_date > user_obj['date_joined'].date():
                    i['returned'] = True

            value_list['spent'] = '%5.2f' % value_list['spent']

        tmplt = 'user/profile_adv_details.html'
        #if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        #    tmplt = 'mobile/user/profile_background.html'

        return render_to_response(tmplt, {'card': card, 'user_bg': user_bg, 'data': data, 'data_type': data_type, 'from_date': from_date, 'to_date': to_date, 'user_count': user_count, 'spent': spent, 'cities': cities, 'city': city, 'adv_id': banner.id}, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))



def adv_report_budget_func(profile, adv):
    #import pdfkit

    filter = {'pk': adv, 'deleted': False, 'user': profile}

    try:
        banner = SiteBanners.objects.get(**filter)
    except SiteBanners.DoesNotExist:
        raise Http404

    cities = {}
    for i in list(NameCity.objects.filter(status=1).values('city', 'name')):
        cities[i['city']] = i['name']


    from_date = banner.dtime.date().strftime('%d.%m.%Y')
    to_date = banner.last_show.strftime('%d.%m.%Y') if banner.last_show else ''

    click_price = get_adv_price(banner.btype)
    views_price = ActionsPriceList.objects.get(pk=48, allow=True).price

    click_cities = {}
    click_count = 0
    click_spent = 0
    for i in list(SiteBannersClicks.objects.filter(banner=banner).values_list('profile__person__city', flat=True)):
        if not click_cities.get(i):
            city_name = cities.get(i)
            click_cities[i] = {'count': 0, 'spent': 0, 'name': city_name}
        click_cities[i]['count'] += 1
        click_cities[i]['spent'] += click_price
        click_count += 1
        click_spent += click_price
    click_cities = sorted(click_cities.values(), key=operator.itemgetter('name'))

    views_cities = {}
    views_count = 0
    views_spent = 0
    for i in list(SiteBannersViews.objects.filter(banner=banner).values_list('profile__person__city', flat=True)):
        if not views_cities.get(i):
            city_name = cities.get(i)
            views_cities[i] = {'count': 0, 'spent': 0, 'name': city_name}
        views_cities[i]['count'] += 1
        views_cities[i]['spent'] += views_price
        views_count += 1
        views_spent += views_price
    views_cities = sorted(views_cities.values(), key=operator.itemgetter('name'))

    html = u'''
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <script type="text/javascript" src="/static/base/js/jquery-1.8.3.min.js"></script>
            <style type="text/css">
            @page {
              size: A4;
              margin: 0;
            }
            @media print {
              html, body {
                width: 210mm;
                height: 297mm;
              }
            }
            body {
                width: 210mm;
                min-height: 297mm;
                background: #FFF;
            }
            </style>
            <script type="text/javascript">
            $(document).ready(function(){
                window.print();
            });
            </script>
        </head>
        <body>
        <div style="font-size: 24px; padding-bottom: 10px;">Отчет по рекламной кампании "%s"</div>
        <div style="font-size: 18px; padding-bottom: 10px;">Период показов %s - %s</div>
        <table style="border-collapse: collapse; width: 100%%; font-size: 16px;">
            <tr style="background: #FFF;">
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Города</th>
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Число кликов</th>
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Сумма (руб.)</th>
            </tr>
            <tr style="background: #FFF;">
                <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%s</b></td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%s</b></td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%5.2f</b></td>
            </tr>
    ''' % (banner.name, from_date, to_date, len(click_cities), click_count, click_spent)

    for i in click_cities:
        html += u'''
            <tr style="background: #FFF;">
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%5.2f</td>
            </tr>''' % (i['name'], i['count'], i['spent'])
        

    html += u'''<tr style="background: #FFF;">
            <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Города</th>
            <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Число показов</th>
            <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Сумма (руб.)</th>
        </tr>
        <tr style="background: #FFF;">
            <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%s</b></td>
            <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%s</b></td>
            <td style="padding: 5px; border-bottom: 1px solid #EEE;"><b>%5.2f</b></td>
        </tr>
        ''' % (len(views_cities), views_count, views_spent)

    for i in views_cities:
        html += u'''
            <tr style="background: #FFF;">
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%5.2f</td>
            </tr>''' % (i['name'], i['count'], i['spent'])

    html += u'''<tr style="background: #309c30;">
            <th style="padding: 5px; color: #FFF; text-align: left;" colspan="2">Общая сумма:</th>
            <th style="padding: 5px; color: #FFF; text-align: left;">%5.2f</th>
        </tr>''' % (click_spent + views_spent)

    html += u'</table></body></html>'


    return html
    #file_name = 'adv_id_%s.pdf' % banner.id
    #file_path = '%s/%s' % (settings.ADV_REPORTS, file_name)

    #options = {'encoding': "UTF-8"}
    #pdfkit.from_string(html, file_path, options=options)
    
    #with open(file_path) as f:
    #    return f.read(), file_name, file_path




@never_cache
def profile_adv_report_budget(request, id, adv):
    
    current_user = request.user
    if current_user.is_authenticated():
        is_my_profile = True if current_user.id == int(id) else False
        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        if not is_my_profile and not request.is_superuser:
            raise Http404

        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile

        result = adv_report_budget_func(card['profile'], adv)
        return HttpResponse(str(result.encode('utf-8')))

        
        '''
        pdf = adv_report_budget_func(card['profile'], adv)

        if pdf:
            response = HttpResponse(pdf[0], mimetype='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=%s' % pdf[1]
            return response
        '''
    return HttpResponseRedirect(reverse('main'))


def adv_report_users_func(profile, adv):
    #import pdfkit

    filter = {'pk': adv, 'deleted': False, 'user': profile}

    try:
        banner = SiteBanners.objects.get(**filter)
    except SiteBanners.DoesNotExist:
        raise Http404

    cities = {}
    for i in list(NameCity.objects.filter(status=1).values('city', 'name')):
        cities[i['city']] = i['name']

    from_date = banner.dtime.date().strftime('%d.%m.%Y')
    to_date = banner.last_show.strftime('%d.%m.%Y') if banner.last_show else ''

    click_price = get_adv_price(banner.btype)
    views_price = ActionsPriceList.objects.get(pk=48, allow=True).price

    profiles_ids = list(SiteBannersClicks.objects.filter(banner=banner).values_list('profile', flat=True))
    profiles = Profile.objects.select_related('user').filter(pk__in=profiles_ids)

    peoples = org_peoples(profiles, True)

    for i in profiles:
        peoples[i.user_id]['main_email'] = i.user.email
        peoples[i.user_id]['emails'] = []

    # Если нет основного мэйла, достаем остальные
    for i in list(Accounts.objects.filter(profile__in=profiles).exclude(email=None).values('email', 'profile', 'profile__user')):
        if i['email']:
            peoples[long(i['profile__user'])]['emails'].append(i['email'].strip())

    click_cities = {}
    for i in list(SiteBannersClicks.objects.filter(banner=banner).values('profile', 'profile__user', 'profile__person__city')):
        if not click_cities.get(i['profile__person__city']):
            city_name = cities.get(i['profile__person__city'])
            click_cities[i['profile__person__city']] = {'name': city_name, 'users': []}
        profile = peoples.get(i['profile__user'])

        user_email = ''
        if profile['main_email']:
            user_email = profile['main_email']
        if not user_email and profile['emails']:
            user_email = profile['emails'][0]

        user_url = u'http://kinoinfo.ru/user/profile/%s/' % profile['id']

        click_cities[i['profile__person__city']]['users'].append({'name': profile['name'], 'url': user_url, 'email': user_email})
    
    click_cities = sorted(click_cities.values(), key=operator.itemgetter('name'))

    html = u'''
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <script type="text/javascript" src="/static/base/js/jquery-1.8.3.min.js"></script>
            <style type="text/css">
            @page {
              size: A4;
              margin: 0;
            }
            @media print {
              html, body {
                width: 210mm;
                height: 297mm;
              }
            }
            body {
                width: 210mm;
                min-height: 297mm;
                background: #FFF;
            }
            </style>
            <script type="text/javascript">
            $(document).ready(function(){
                window.print();
            });
            </script>
        </head>
        <body>
        <div style="font-size: 24px; padding-bottom: 10px;">Отчет по рекламной кампании "%s"</div>
        <div style="font-size: 18px; padding-bottom: 10px;">Период показов %s - %s</div>
        <table style="border-collapse: collapse; width: 100%%; font-size: 16px;">
            <tr style="background: #FFF;">
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Города</th>
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">Пользователь</th>
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">E-Mail</th>
                <th style="background: #8F8F8F; padding: 5px; color: #FFF; text-align: left;">URL</th>
            </tr>
    ''' % (banner.name, from_date, to_date)

    cname = ''
    for i in click_cities:
        if i['name'] != cname:
            html += u'''
                <tr style="background: #FFF;">
                    <td style="padding: 5px; border-bottom: 1px solid #EEE; vertical-align: top;" rowspan="%s">%s</td>
                ''' % (len(i['users']), i['name'])

        for j in i['users']:
            if i['name'] == cname:
                html += u'<tr>'

            html += u'''
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;">%s</td>
                <td style="padding: 5px; border-bottom: 1px solid #EEE;"><a href="%s" target="_blank">%s</td>
                </tr>''' % (j['name'], j['email'], j['url'], j['url'])

        html += u'</tr>'
        
        if i['name'] != cname:
            cname = i['name']

    html += u'</table></body></html>'

    '''
    file_name = 'adv_users_id_%s.pdf' % banner.id
    file_path = '%s/%s' % (settings.ADV_REPORTS, file_name)

    options = {'encoding': "UTF-8"}
    pdfkit.from_string(html, file_path, options=options)

    with open(file_path) as f:
        return f.read(), file_name, file_path
    '''
    return html



@never_cache
def profile_adv_report_users(request, id, adv):

    current_user = request.user
    if current_user.is_authenticated():
        is_my_profile = True if current_user.id == int(id) else False
        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        if not is_my_profile and not request.is_superuser:
            raise Http404


        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile

        result = adv_report_users_func(card['profile'], adv)
        return HttpResponse(str(result.encode('utf-8')))

        '''
        pdf = adv_report_users_func(card['profile'], adv)

        if pdf:
            response = HttpResponse(pdf[0], mimetype='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=%s' % pdf[1]
            return response
        '''
    return HttpResponseRedirect(reverse('main'))


@never_cache
def profile_booking_settings(request, id):
    current_user = request.user
    if current_user.is_authenticated():

        is_my_profile = True if current_user.id == int(id) else False

        if not is_my_profile:
            if request.user.is_superuser:
                try:
                    user = User.objects.get(pk=id)
                except User.DoesNotExist:
                    raise Http404
        else:
            user = current_user

        if not is_my_profile and not request.user.is_superuser:
            raise Http404

        card = get_usercard(user, ugroups=True)

        country = request.session.get('booker_country_id', 2)

        if request.POST:
            
            if 'country' in request.POST:
                country = int(request.POST.get('country', 2))

            else:

                cinemas = [long(i) for i in request.POST.get('cinemas','').split(';') if i]

                if cinemas:
                    permission_denied = BookerCinemas.objects.filter(permission='1', cinema__id__in=cinemas).exclude(settings__profile=request.profile).values_list('cinema', flat=True)


                    sett, created = BookingSettings.objects.get_or_create(
                        profile = card['profile'],
                        defaults = {
                            'profile': card['profile'],
                        })
                    
                    exists = BookerCinemas.objects.filter(settings=sett, cinema__city__country__pk=country).values_list('cinema', flat=True)

                    for_del = list(set(exists) - set(cinemas))
                    for_add = list(set(cinemas) - set(exists))
                    
                    #for_del = list(Cinema.objects.filter(pk__in=for_del))
                    BookerCinemas.objects.filter(settings=sett, cinema__pk__in=for_del).delete()

                    for i in Cinema.objects.filter(pk__in=for_add):
                        permission = '0' if i.id in permission_denied else '1'

                        BookerCinemas.objects.create(
                            settings = sett,
                            cinema = i,
                            permission = permission,
                        )


                    #sett.cinemas.remove(*for_del)
                    #sett.cinemas.add(*for_add)

                return HttpResponseRedirect(reverse('profile_booking_settings', kwargs={'id': id}))

        card['is_my_profile'] = is_my_profile
        user_bg = get_usr_bg(request, card['profile'])

        cities = {}
        for i in list(NameCity.objects.filter(status=1, city__country__id=country).values('name', 'city')):
            cities[i['city']] = {'id': i['city'], 'name': i['name']}

        booker_cinemas = {}
        booker_data = {}
        for i in Cinema.objects.filter(bookingsettings__profile=card['profile'], city__id__in=cities):
            booker_cinemas[i.id] = i
            if not booker_data.get(i.city_id):
                booker_data[i.city_id] = {'id': i.city_id, 'name': '', 'cinemas': []}

        user_city_exist = False
        data = {}
        for i in list(NameCinema.objects.filter(status=1, cinema__city__id__in=cities).values('name', 'cinema', 'cinema__city')):
            city = cities.get(i['cinema__city'])

            if not data.get(city['id']):
                if card['city']['id'] == i['cinema__city']:
                    user_city_exist = True
                    user_city = True
                else:
                    user_city = False

                data[city['id']] = {'id': i['cinema__city'], 'name': city['name'], 'user_city': user_city, 'cinemas': []}

            if booker_data.get(city['id']):
                booker_data[city['id']]['name'] = city['name']

            cinema = {'id': i['cinema'], 'name': i['name']}

            if booker_cinemas.get(i['cinema']):
                booker_data[city['id']]['cinemas'].append(cinema)
            else:
                data[city['id']]['cinemas'].append(cinema)

        for i in (data, booker_data):
            for k, v in i.iteritems():
                v['cinemas'] = sorted(v['cinemas'], key=operator.itemgetter('name'))

        data = sorted(data.values(), key=operator.itemgetter('name'))
        booker_data = sorted(booker_data.values(), key=operator.itemgetter('name'))

        if not user_city_exist:
            data[0]['user_city'] = True

        request.session['booker_country_id'] = country

        return render_to_response('user/profile_booking_settings.html', {'card': card, 'user_bg': user_bg, 'data': data, 'booker_data': booker_data, 'country': country}, context_instance=RequestContext(request))

    return HttpResponseRedirect(reverse('main'))


#@never_cache
def adv_order_sender():
    import settings_kinoafisha

    stype = '5'
    today = datetime.datetime.today().date()
    past_from = today - datetime.timedelta(days=14)

    objects = {}
    end_objects = []
    for i in SubscriberObjects.objects.filter(in_work=True, type=stype):
        if not objects.get(i.obj):
            objects[i.obj] = {'obj': i, 'name': '', 'end_objs_ids': [], 'end_objs': [], 'users': []}
        objects[i.obj]['end_objs_ids'].append(i.end_obj)
        end_objects.append(i.end_obj)

    filter = {'pk__in': end_objects, 'deleted': False, 'dtime__lte': past_from}
    banners = SiteBanners.objects.filter(**filter)

    # Юзеры подписанные
    profiles = {}
    for i in SubscriberUser.objects.select_related('profile', 'profile__user').filter(type=stype, obj__in=objects.keys()):
        if not profiles.get(i.profile_id):
            #user_money = money.get(int(i.id), 0)
            profiles[i.profile_id] = {'obj': i.profile, 'subs_user': i, 'main_email': None, 'emails': [], 'money': 0}
            if i.profile.user.email:
                profiles[i.profile_id]['main_email'] = i.profile.user.email.strip()

    # Если нет основного мэйла, достаем остальные
    for i in list(Accounts.objects.filter(profile__pk__in=profiles.keys()).exclude(email=None).values('email', 'profile')):
        if i['email']:
            profiles[long(i['profile'])]['emails'].append(i['email'].strip())

    data = {}
    for i in banners:
        if not data.get(i.user_id):
            data[i.user_id] = []
        data[i.user_id].append(i)

    # параметры мэйл сервера Kinoafisha
    connection = get_connection(
        host = settings_kinoafisha.EMAIL_HOST, 
        port = settings_kinoafisha.EMAIL_PORT, 
        username = settings_kinoafisha.EMAIL_HOST_USER , 
        password = settings_kinoafisha.EMAIL_HOST_PASSWORD, 
    )
    connection.open()

    for k, v in data.iteritems():
        profile = profiles.get(k)

        #try:
        if profile:
            user_email = None
            if profile['main_email']:
                user_email = profile['main_email']
            if not user_email and profile['emails']:
                user_email = profile['emails'][0]

            user_money_notification = ''
            adv_balance_notification = ''
            adv_time_notification = ''

            if user_email:

                advs_balance = []
                advs_time = []
                advs = []

                files = []

                for adv in v:
                    if (adv.dtime.date() + datetime.timedelta(days=13)) < today:
                        pdf = adv_report_budget_func(profile['obj'], adv.id)
                        pdf_users = adv_report_users_func(profile['obj'], adv.id)

                        if pdf or pdf_users:
                            files.append({'file': [pdf, pdf_users], 'name': adv.name, 'adv_id': adv.id})

                msg = ''
                if files:
                    msg += u'<div style="background: #FFF; padding: 10px; margin-bottom: 20px;">Завершились Ваши рекламные кампании:<br />'
                    for f in files:
                        msg += u'"%s"<br />'  % f['name']
                    msg += u'</div>'
                    msg += u'<div style="background: #FFF; padding: 10px; margin-bottom: 20px;">Отчеты в формате PDF прикреплены к данному письму</div>'

                if msg:
                    html = u'<div style="background: #EDEDED; color: #444; font-size: 14px; padding: 20px; font-family:Arial,\'Helvetica Neue\', Helvetica, sans-serif;">%s<div><a href="http://www.kinoafisha.ru/user/profile/" target="_blank" style="color: #BA5B32;">Мой профиль</a> | <a href="http://www.kinoafisha.ru/user/profile/%s/adv/" target="_blank" style="color: #BA5B32;">Управление рекламой</a></div></div>' % (msg, profile['obj'].user_id)

                    html_clear = msg
                    
                    subject = u'Отчет по Вашим рекламным кампаниям'

                    mail = EmailMultiAlternatives(subject, html_clear, settings.DEFAULT_FROM_EMAIL, [user_email.strip()])
                    mail.attach_alternative(html, "text/html")
                    for f in files:
                        for inner in f['file']:
                            if inner:
                                mail.attach_file(inner[2], mimetype='application/pdf')
                    mail.send()
                    
                    for f in files:
                        obj = objects.get(f['adv_id'])
                        SubscriberLog.objects.create(user=profile['subs_user'], obj=obj['obj'])
                        obj['obj'].in_work = False
                        obj['obj'].save()
                    
    connection.close()


def adv_notification_sender():
    import settings_kinoafisha

    stype = '4'
    today = datetime.datetime.today().date()
    past_from = today - datetime.timedelta(days=14)

    objects = {}
    end_objects = []
    for i in SubscriberObjects.objects.filter(in_work=True, type=stype):
        if not objects.get(i.obj):
            objects[i.obj] = {'obj': i, 'name': '', 'end_objs_ids': [], 'end_objs': [], 'users': []}
        objects[i.obj]['end_objs_ids'].append(i.end_obj)
        end_objects.append(i.end_obj)

    filter = {'pk__in': end_objects, 'deleted': False, 'dtime__gte': past_from}
    banners = SiteBanners.objects.filter(**filter)

    # Юзеры подписанные
    profiles = {}
    for i in SubscriberUser.objects.select_related('profile', 'profile__user').filter(type=stype, obj__in=objects.keys()):
        if not profiles.get(i.profile_id):
            #user_money = money.get(int(i.id), 0)
            profiles[i.profile_id] = {'obj': i.profile, 'subs_user': i, 'main_email': None, 'emails': [], 'money': 0}
            if i.profile.user.email:
                profiles[i.profile_id]['main_email'] = i.profile.user.email.strip()
    
    for i in list(PersonInterface.objects.filter(profile__pk__in=profiles.keys()).values('profile', 'money')):
        profiles[long(i['profile'])]['money'] = i['money']

    # Если нет основного мэйла, достаем остальные
    for i in list(Accounts.objects.filter(profile__pk__in=profiles.keys()).exclude(email=None).values('email', 'profile')):
        if i['email']:
            profiles[long(i['profile'])]['emails'].append(i['email'].strip())

    data = {}
    for i in banners:
        if not data.get(i.user_id):
            data[i.user_id] = []
        data[i.user_id].append(i)

    # параметры мэйл сервера Kinoafisha
    connection = get_connection(
        host = settings_kinoafisha.EMAIL_HOST, 
        port = settings_kinoafisha.EMAIL_PORT, 
        username = settings_kinoafisha.EMAIL_HOST_USER , 
        password = settings_kinoafisha.EMAIL_HOST_PASSWORD, 
    )
    connection.open()
    
    for k, v in data.iteritems():
        profile = profiles.get(k)
        
        #try:
        if profile:
            user_email = None
            if profile['main_email']:
                user_email = profile['main_email']
            if not user_email and profile['emails']:
                user_email = profile['emails'][0]

            user_money_notification = ''
            adv_balance_notification = ''
            adv_time_notification = ''

            if user_email:
                #if profile['money'] < 10:
                #    user_money_notification = u'<div style="background: #FFF; padding: 10px; margin-bottom: 20px;">У Вас на личном счете осталось мало средств (%s руб.) для оплаты рекламных кампаний</div>' % profile['money']

                advs_balance = []
                advs_time = []
                advs = []

                for adv in v:
                    if adv.balance < 10:
                        advs_balance.append(adv)
                        advs.append(adv)
                    if (adv.dtime.date() + datetime.timedelta(days=13)) == (today + datetime.timedelta(days=1)):
                        advs_time.append(adv)
                        advs.append(adv)

                if advs_balance:
                    adv_balance_notification = u'<div style="background: #FFF; padding: 10px; margin-bottom: 20px;">На балансе Ваших рекламных кампании осталось мало средств:<br />'
                for adv in advs_balance:
                    adv_balance_notification += u'"%s" (%s руб.)<br />' % (adv.name, adv.balance)
                if advs_balance:
                    adv_balance_notification += u'</div>'

                if advs_time:
                    adv_time_notification = u'<div style="background: #FFF; padding: 10px; margin-bottom: 20px;">Завтра истекает срок 14 дней для Ваших рекламных кампаний:<br />'
                for adv in advs_time:
                    adv_time_notification += u'"%s"<br />' % adv.name
                if advs_time:
                    adv_time_notification += u'</div>'

                if user_money_notification or adv_balance_notification or adv_time_notification:
                    html = u'<div style="background: #EDEDED; color: #444; font-size: 14px; padding: 20px; font-family:Arial,\'Helvetica Neue\', Helvetica, sans-serif;">%s%s%s<div><a href="http://www.kinoafisha.ru/user/profile/" target="_blank" style="color: #BA5B32;">Мой профиль</a> | <a href="http://www.kinoafisha.ru/user/profile/%s/adv/" target="_blank" style="color: #BA5B32;">Управление рекламой</a></div></div>' % (user_money_notification, adv_balance_notification, adv_time_notification, profile['obj'].user_id)

                    html_clear = u'%s%s%s' % (user_money_notification, adv_balance_notification, adv_time_notification)
                    
                    subject = u'Ваши рекламные кампании на Киноафише'

                    mail = EmailMultiAlternatives(subject, html_clear, settings.DEFAULT_FROM_EMAIL, [user_email.strip()])
                    mail.attach_alternative(html, "text/html")
                    mail.send()

                    for j in set(advs):
                        obj = objects.get(j.id)
                        SubscriberLog.objects.create(user=profile['subs_user'], obj=obj['obj'])

                        obj['obj'].in_work = False
                        obj['obj'].save()

        #else:
        #    error = 'Нет мэйла'
        #    SubscriberLog.objects.create(user=subs_user_obj, obj=subs_obj, notified=False, error=error)
        #except Exception as e:
        #    return HttpResponse(str(e))
        #    pass
        #error = u'Ошибка %s' % e.args
        #SubscriberLog.objects.create(user=subs_user_obj, obj=subs_obj, notified=False, error=error[:128])

    connection.close()


@never_cache
def profile_recommend(request, id):
    from movie_online.IR import check_int_rates_inlist

    current_user = request.user
    current_site = request.current_site

    if id:
        id = int(id)
        is_my_profile = True if current_user.id == id else False
    else:
        is_my_profile = True
        
    if id and not is_my_profile:
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = current_user
    
    card = get_usercard(user, ugroups=True)
    card['is_my_profile'] = is_my_profile

    rtypes = {
        0: '--------',
        3: 'Рекомендую',
        1: 'Хочу смотреть',
        5: 'Не рекомендую',
        4: 'Не буду смотреть',
    }
    years = []
    genres = {0: {'id': 0, 'name': '--------'}}
    countries = {0: {'id': 0, 'name': '--------'}}

    films_kid = set(list(Likes.objects.filter(personinterface__profile__user=user).values_list('film', flat=True)))

    for i in Film.objects.using('afisha').select_related('country', 'country2', 'genre1', 'genre2', 'genre3').filter(pk__in=films_kid):
        years.append(int(i.year))
        
        if i.country_id:
            if not countries.get(i.country_id):
                countries[i.country_id] = {'id': i.country_id, 'name': i.country.name}
        if i.country2_id:
            if not countries.get(i.country_id):
                countries[i.country2_id] = {'id': i.country2_id, 'name': i.country2.name}

        if i.genre1_id:
            if not genres.get(i.genre1_id):
                genres[i.genre1_id] = {'id': i.genre1_id, 'name': i.genre1.name}
        if i.genre2_id:
            if not genres.get(i.genre2_id):
                genres[i.genre2_id] = {'id': i.genre2_id, 'name': i.genre2.name}
        if i.genre3_id:
            if not genres.get(i.genre3_id):
                genres[i.genre3_id] = {'id': i.genre3_id, 'name': i.genre3.name}

    years = list(sorted(set(years)))
    years.insert(0, '--------')

    countries = sorted(countries.values(), key=operator.itemgetter('name'))
    genres = sorted(genres.values(), key=operator.itemgetter('name'))

    rtype = 0
    year = 0
    genre = 0
    country = 0
    if request.POST:
        year = request.POST.get('year', 0)
        genre = request.POST.get('genre', 0)
        country = request.POST.get('country', 0)
        rtype = request.POST.get('type', 0)

        try: year = int(year)
        except ValueError: year = 0
        try: genre = int(genre)
        except ValueError: genre = 0
        try: country = int(country)
        except ValueError: country = 0
        try: rtype = int(rtype)
        except ValueError: rtype = 0

    filter1 = {'personinterface__profile__user': user}
    filter2 = {}

    set_filter = False
    if year or genre or country or rtype:
        if rtype:
            filter1['evaluation__in'] = [1, 2] if rtype == 1 else [rtype, ]
            set_filter = True
        elif year:
            filter2['year'] = year
            set_filter = True
    else:
        rtype = 3
        filter1['evaluation__in'] = [rtype, ]
        set_filter = True

  
    kids = {}
    for i in list(Likes.objects.filter(**filter1).values('id', 'film')):
        kids[i['film']] = i['id']


    if set_filter:
        filter2['pk__in'] = kids.keys()
        f = Film.objects.using('afisha').filter(**filter2)
    else:
        if genre:
            queries = [Q(genre1__pk=genre, pk__in=kids.keys()), Q(genre2__pk=genre, pk__in=kids.keys()), Q(genre3__pk=genre, pk__in=kids.keys())]
        elif country:
            queries = [Q(country__pk=country, pk__in=kids.keys()), Q(country2__pk=country, pk__in=kids.keys())]

        query = queries.pop()
        for item in queries:
            query |= item
        f = Film.objects.using('afisha').filter(query)

    fnames = FilmsName.objects.using('afisha').filter(film_id__id__in=kids.keys(), status=1, type__in=(1, 2)).order_by('-type')
    fnames_dict = {}
    for i in fnames:
        if not fnames_dict.get(i.film_id_id):
            fnames_dict[i.film_id_id] = []
        fnames_dict[i.film_id_id].append({'type': i.type, 'name': i.name})

    ratings = check_int_rates_inlist(kids.keys())

    data = []
    count = 0
    for i in f:
        like_id = kids.get(i.id)
        rate = ratings.get(i.id)
        rating = {'rate': rate['int_rate'], 'show_ir': rate['show_ir'], 'show_imdb': rate['show_imdb'], 'rotten': rate['rotten']}

        fnames = fnames_dict.get(i.id, [{'name': '', 'type': 2}])
        fname = ''
        for n in fnames:
            fname = n['name']
            if n['type'] == 2:
                break

        data.append({
            'id': i.id,
            'name_ru': fname,
            'year': i.year,
            'rating': rating,
            'rate': rating['rate'],
            'like_id': like_id,
        })

        count += 1

    data = sorted(data, key=operator.itemgetter('like_id'), reverse=True)

    user_bg = get_usr_bg(request, card['profile'])

    tmplt = 'user/profile_recommend.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/user/profile_recommend.html'

    return render_to_response(tmplt, {'card': card, 'user_bg': user_bg, 'profile': profile, 'data': data, 'rtype': rtype, 'rtypes': rtypes, 'count': count, 'countries': countries, 'genres': genres, 'years': years, 'country': country, 'genre': genre, 'year': year}, context_instance=RequestContext(request))



@never_cache
def profile_subscribers(request, id, vid):

    current_user = request.user
    if id:
        id = int(id)
        is_my_profile = True if current_user.id == id else False
    else:
        is_my_profile = True
    
    if id and not is_my_profile:
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = current_user


    if not is_my_profile and not request.user.is_superuser:
        raise Http404

    card = get_usercard(user, ugroups=True)
    card['is_my_profile'] = is_my_profile

    # проверка принадлежит ли блог юзеру, чья страница открывается
    blog = get_object_or_404(OrgSubMenu, pk=vid, orgmenu__profile__user__id=user.id)
    
    subscribers = SubscriberUser.objects.filter(obj=vid, type='1')

    profiles = [i.profile for i in subscribers]
    peoples = org_peoples(profiles, True)

    data = []
    for i in subscribers:
        profile = peoples.get(i.profile.user_id)
        data.append({'user': profile['name'], 'user_id': profile['id'], 'dtime': i.dtime})
    
    data = sorted(data, key=operator.itemgetter('dtime'), reverse=True)

    user_bg = get_usr_bg(request, card['profile'])

    template = 'user/profile_subscribers.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        template = 'mobile/user/profile_subscribers.html'

    return render_to_response(template, {'blog': blog, 'vid': vid, 'user_bg': user_bg, 'card': card, 'data': data}, context_instance=RequestContext(request))


@never_cache
def profile_subscribers_log(request, id, vid):
    current_user = request.user
    if id:
        id = int(id)
        is_my_profile = True if current_user.id == id else False
    else:
        is_my_profile = True
    
    if id and not is_my_profile:
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = current_user

    if not is_my_profile and not request.user.is_superuser:
        raise Http404

    card = get_usercard(user, ugroups=True)
    card['is_my_profile'] = is_my_profile

    # проверка принадлежит ли блог юзеру, чья страница открывается
    blog = get_object_or_404(OrgSubMenu, pk=vid, orgmenu__profile__user__id=user.id)
    
    tmp = SubscriberLog.objects.select_related('user__profile').filter(obj__obj=vid).order_by('-dtime')

    profiles = set([i.user.profile for i in tmp if i.user])

    peoples = org_peoples(profiles, True)

    data = []
    for i in tmp:
        profile = peoples.get(i.user.profile.user_id) if i.user else None
        data.append({'obj': i, 'profile': profile})
    
    user_bg = get_usr_bg(request, card['profile'])

    template = 'user/profile_subscribers_log.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        template = 'mobile/user/profile_subscribers_log.html'
        
    return render_to_response(template, {'card': card, 'user_bg': user_bg, 'vid': vid, 'blog': blog, 'data': data}, context_instance=RequestContext(request))




@only_superuser
@never_cache
def withdraw_user_money(request, id):
    if request.POST:
        try:
            summa = float(request.POST.get('sum').replace(',','.'))
        except ValueError:
            summa = None
            
        if summa:
            profile = Profile.objects.get(user__id=id)
            interface = profile.personinterface
            if interface.money < summa:
                interface.money = 0
            else:
                interface.money -= summa
            interface.save()
            
            WithdrawMoney.objects.create(summa=summa, profile=profile, who=request.profile)
            
    kw = {'id': id}
    if request.profile.user_id == int(id):
        kw = {}
    return HttpResponseRedirect(reverse('profile', kwargs=kw))


@only_superuser
@never_cache
def user_permission_set(request, id):
    if request.POST:
        groups = request.POST.getlist('u_groups')
        sites = request.POST.getlist('sites_edit')
        profile = Profile.objects.select_related('user').get(user__pk=id)
        
        admin = True if '0' in groups else False
        profile.user.is_superuser = admin
        profile.user.save()
        
        profile.site_admin.clear()
        profile.user.groups.clear()
        
        if '2' in groups:
            for i in DjangoSite.objects.filter(pk__in=sites):
                profile.site_admin.add(i)

        for i in Group.objects.filter(pk__in=groups):
            profile.user.groups.add(i)

    return HttpResponseRedirect(reverse('profile', kwargs={'id': id}))


def send_job_report(paid_obj, proj_id):

    summa = paid_obj.action.price * paid_obj.number
    current_group = None
            
    in_groups = paid_obj.profile.user.groups.filter(actionspricelist__group='8').distinct('pk')
    
    current_group = in_groups[0]

    user_name = org_peoples([paid_obj.profile])[0]['name']

    date_y, date_m, date_d = paid_obj.dtime.split('-')
    report_date = u'%s.%s.%s' % (date_d, date_m, date_y)

    msg_html = u'<div style="background: #FFF; padding: 10px; font-size: 14px; color: #333;">\
        <h3>Очет по работе за %s</h3>\
        <b>%s</b> (%s)<br /><br />\
        Описание: %s<br />\
        Кол.часов: %s<br />\
        Сумма: %s руб.<br /><div>' % (
            report_date, 
            user_name, 
            current_group.name, 
            paid_obj.extra, 
            paid_obj.number,
            summa
        )
        
    msg_clear = BeautifulSoup(msg_html, from_encoding="utf-8").text

    subject = u'Отчет по работе за %s' % report_date

    project = Projects.objects.get(pk=proj_id) 
    send = False
    
    # параметры мэйл сервера
    connection = get_connection(
        host = settings.EMAIL_HOST, 
        port = settings.EMAIL_PORT, 
        username = settings.EMAIL_HOST_USER , 
        password = settings.EMAIL_HOST_PASSWORD, 
        use_tls = settings.EMAIL_USE_TLS,
    )
    connection.open()
    
    for i in project.directors.all():

        card = get_usercard(i.user_id, ucity=False)
        email = None
        if card['email']:
            email = card['email']
        elif not card['email'] and card['emails']:
            card['profile'].user.email = card['emails'][0]
            card['profile'].user.save()
            card['email'] = card['emails'][0]
            email = card['email']
        if not card['email'] and card['emails_not_auth']:
            email = card['emails_not_auth'][0]
        
        if email:
            mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, [email.strip()], connection=connection)
            mail.attach_alternative(msg_html, "text/html")
            mail.send()
    
            send = True
            
    if send:
        # копия для Иванова
        if email != 'kinoafisharu@gmail.com':
            subject = u'%s [КОПИЯ]' % subject
            mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, ['kinoafisharu@gmail.com'], connection=connection)
            mail.attach_alternative(msg_html, "text/html")
            mail.send()

        # копия для Юры
        subject = u'%s [КОПИЯ]' % subject
        mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, ['twohothearts@gmail.com'], connection=connection)
        mail.attach_alternative(msg_html, "text/html")
        mail.send()
        
    connection.close()
    return True




@never_cache
def profile_accounts(request, id=None):
    current_user = request.user
    if current_user.is_authenticated():
        if id:
            id = int(id)
            is_my_profile = True if current_user.id == id else False
        else:
            is_my_profile = True
        
        if id and not is_my_profile:
            user = get_object_or_404(User, pk=id)
        else:
            user = current_user

        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile

        profile = card['profile']
        
        if is_my_profile or current_user.is_superuser or request.is_admin:
            if request.method == 'POST' and 'account' in request.POST:
                acc_id = request.POST['account']
                if 'confirm_acc' in request.POST and not is_my_profile:
                    acc = Accounts.objects.filter(profile__user__id=id, pk=acc_id).update(validation_code=None, auth_status=True)
                    Profile.objects.filter(user__pk=id).update(auth_status=True)
                    return HttpResponseRedirect(reverse('profile_accounts', kwargs={'id': id}))
                else:
                    try: 
                        acc = Accounts.objects.get(profile=profile, pk=acc_id)
                        try: os.remove('%s/%s/%s' % (settings.AVATAR_FOLDER, profile.folder, acc.avatar))
                        except OSError: pass
                        profile.accounts.remove(acc)
                        acc.delete()
                    except Accounts.DoesNotExist: pass
                    return HttpResponseRedirect(reverse('profile_accounts'))
            else:
                current_site = request.current_site
                p_accounts = card['accounts']
                p_count = len(p_accounts)
                folder = user.get_profile().folder
                
                interface = profile.personinterface
                subscription = interface.temp_subscription
                subscription_topics = interface.temp_subscription_topics

                user_bg = get_usr_bg(request, card['profile'])

                data = {'card': card, 'user_bg': user_bg, 'p_accounts': p_accounts, 'p_count': p_count, 'subscription': subscription, 'subscription_topics': subscription_topics, 'folder': folder}
                
                if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru', 'letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or 'vsetiinter.net' and request.subdomain == 'ya':
                    template = 'user/profile_accounts.html'
                    if current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                        template = 'user/profile_accounts_vlada.html'

                    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
                        template = 'mobile/user/profile_accounts.html'

                    if request.subdomain == 'pm-prepare' and request.current_site.domain in ('imiagroup.com.au'):
                        template = 'pmprepare/user/profile_accounts.html'

                    return render_to_response(template, data, context_instance=RequestContext(request))
        else:
            raise Http404
    return HttpResponseRedirect(reverse('main'))


@never_cache
def add_job_action(request):
    if request.POST:
        details = request.POST.get('details')
        hours = request.POST.get('hours')
        proj_id = request.POST.get('proj_id')
        date = request.POST.get('date')
        stage = request.POST.get('stage')
        action = request.POST.get('action')
        
        stage = int(stage) if stage else None

        in_groups = request.profile.user.groups.filter(actionspricelist__group='8').distinct('pk')

        if in_groups:
            current_group = in_groups[0]
        
            if date and hours:
                try:
                    action = ActionsPriceList.objects.select_related('action').get(pk=action, project=proj_id, allow=True)
                except ActionsPriceList.DoesNotExist:
                    pname = Projects.objects.get(pk=proj_id).name
                    return HttpResponse(str('У проекта "%s" нет оплачиваемого действия!' % pname.encode('utf-8')))
                    
                paid = PaidActions.objects.create(
                    action = action, 
                    profile = request.profile,
                    object = None,
                    act = '1',
                    extra = details,
                    number = int(hours),
                    stage_id = stage,
                )

                paid.dtime = date
                paid.save()
                
                result = send_job_report(paid, proj_id)

    return HttpResponseRedirect(reverse('profile_job'))
        

@never_cache
def profile_job(request, id=None):
    current_user = request.user
    current_site = request.current_site

    projects = Projects.objects.only('id', 'name').all()

    if current_user.is_authenticated():
        if id:
            id = int(id)
            is_my_profile = True if current_user.id == id else False
        else:
            is_my_profile = True
        
        if id and not is_my_profile:
            try:
                user = User.objects.get(pk=id)
            except User.DoesNotExist:
                raise Http404
        else:
            user = current_user
        
        project_id = request.GET.get('project')
        if project_id:
            project_id = int(project_id)
            request.session['job_project_id'] = project_id
        
        if not project_id and projects:
            project_id = int(request.session.get('job_project_id', projects[0].id))
        
        card = get_usercard(user, ugroups=True)
        card['is_my_profile'] = is_my_profile

        profile = card['profile']
        
        if is_my_profile or current_user.is_superuser:
            orgs = Organization.objects.only('id', 'buildings', 'name').filter(staff=profile)

            current_group = None
            
            in_groups = user.groups.filter(actionspricelist__group='8').distinct('pk')
            
            actions_list = []
            actions = []
            tasks = []
            tasks_count = 0
            if in_groups:
                current_group = in_groups[0]

                actions = PaidActions.objects.select_related('action').filter(profile=profile, action__user_group=current_group, action__project=project_id, future=False).order_by('-dtime')
                for i in actions:
                    summa = i.action.price * i.number
                    actions_list.append({'obj': i, 'summa': summa})
                    
                actions = ActionsPriceList.objects.filter(user_group=current_group, project=project_id)

                tasks = PaidActions.objects.filter(profile=profile, action__user_group=current_group, action__project=project_id, future=True, is_accepted=True).order_by('dtime')
                tasks_count = tasks.count()

            stages = ProjectStages.objects.filter(projects__pk=project_id).order_by('id')
            
            user_bg = get_usr_bg(request, card['profile'])

            data = {'card': card, 'user_bg': user_bg, 'orgs': orgs, 'user_page': user, 'actions': actions_list, 'projects': projects, 'project_id': project_id, 'current_group': current_group, 'stages': stages, 'user_actions': actions, 'profile': profile, 'tasks': tasks, 'tasks_count': tasks_count}
            
            if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru', 'letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au') or 'vsetiinter.net' and request.subdomain == 'ya':
                template = 'user/profile_job.html'
                if current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
                    template = 'user/profile_job_vlada.html'

                if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
                    template = 'mobile/user/profile_job.html'

                return render_to_response(template, data, context_instance=RequestContext(request))
        else:
            raise Http404
    return HttpResponseRedirect(reverse('main'))


# доделать, вывод заданий по работе!!!
@never_cache
def profile_job_tasks(request, id=None):
    current_user = request.user
    current_site = request.current_site

    projects = Projects.objects.only('id', 'name').all()

    if current_user.is_authenticated():
        if id:
            id = int(id)
            is_my_profile = True if current_user.id == id else False
        else:
            is_my_profile = True
        
        if id and not is_my_profile:
            try:
                user = User.objects.get(pk=id)
            except User.DoesNotExist:
                raise Http404
        else:
            user = current_user
        
        project_id = request.GET.get('project')
        if project_id:
            project_id = int(project_id)
            request.session['job_project_id'] = project_id
        
        if not project_id:
            project_id = int(request.session.get('job_project_id', projects[0].id))
        
        profile = user.get_profile()
        
        if is_my_profile or current_user.is_superuser:
            return HttpResponse(str())
        else:
            raise Http404
    return HttpResponseRedirect(reverse('main'))


@never_cache
def profile_xjob(request, id=None):
    job_spec = {
        u'Программист': {'1': 28, '2': 29},
        u'Менеджер': {'1': 32, '2': 33},
    }
    
    if id and 'report' in request.GET:
        try:
            user = User.objects.get(pk=id)
        except User.DoesNotExist:
            raise Http404
    
        project_id = '2'

        profile = user.get_profile()
        
        current_group, act_id = (None, None)
        in_groups = user.groups.filter(name__in=('Программист', 'Менеджер'))
        actions_list = []
        if in_groups:
            current_group = in_groups[0]

            act = job_spec.get(current_group.name)
            if act:
                act_id = act.get(project_id)
        
                user_name = org_peoples([profile])[0]['name']

                html = u'<link rel="stylesheet" href="http://kinoinfo.ru/static/base/css/style.css" type="text/css" media="screen" />\
                    <br /><b>%s</b> (%s)<br /><br />\
                    <table class="panel_list auto_fat">\
                    <th>Описание</th><th>Дата</th><th>Сумма</th><th>Кол.часов</th>' % (user_name, current_group.name)

                actions = PaidActions.objects.select_related('action').filter(profile=profile, action__pk=act_id, action__project=project_id, future=False).order_by('-dtime')
                actions_list = []
                for i in actions:
                    summa = int(i.action.price * i.number)

                    html += u'<tr>'
                    html += u'<td><div>%s</div></td>' % i.extra
                    html += u'<td><div>%s</div></td>' % i.dtime.strftime('%d.%m.%Y')
                    html += u'<td><div>%s</div></td>' % summa
                    html += u'<td><div>%s</div></td>' % i.number
                    html += u'</tr>'
                
                html += u'</table>'

                return HttpResponse(str(html.encode('utf-8')))
    raise Http404




@only_superuser
@never_cache
def delete_person_name(request, uid, nid):
    person = Person.objects.get(profile__user__id=uid)
    name = NamePerson.objects.get(pk=nid)
    person.name.remove(name)
    return HttpResponseRedirect(reverse('user_details', kwargs={'id': uid}))


@never_cache
def user_details(request, id=None):
    return HttpResponseRedirect(reverse('profile'))



def user_deposit():
    now = datetime.datetime.now().date().day
    if now == 1:
        money = Profile.objects.select_related('personinterface').only('personinterface', 'id').filter(personinterface__money__gt=0)
        for i in money:
            interface = i.personinterface
            percents = (interface.money / 100) * 10
            interface.money += percents
            interface.save()
            UserDeposit.objects.create(summa=percents, profile=i)



@never_cache
def view_post(request, user_id=None, vid=None, id=None):
    from letsgetrhythm.views import view_func
    
    current_user = request.user
    if user_id:
        user_id = int(user_id)
        is_my_profile = True if current_user.id == user_id else False
    else:
        is_my_profile = True

    if user_id and not is_my_profile:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = current_user
            
    card = get_usercard(user, ugroups=True)
    card['is_my_profile'] = is_my_profile

    # проверка принадлежат ли посты юзеру, чья страница открывается
    menu = get_object_or_404(OrgSubMenu, pk=vid, orgmenu__profile__user__id=user.id)
    if id:
        try:
            menu.news.get(pk=id, autor__user=user)
        except News.DoesNotExist:
            raise Http404

    # проверка на приватное меню
    private = OrgSubMenu.objects.filter(pk=vid, orgmenu__profile__user__id=user.id).values('orgmenu__private')[0]
    if private['orgmenu__private'] and not is_my_profile:
        raise Http404


    xaccess = False
    xuser_id = request.GET.get('u')
    if xuser_id:
        if int(request.profile.user_id) == int(xuser_id):
            access = True
    else:
        xuser_id = request.profile.user_id
        access = True
    
    access = True if request.user.is_superuser or request.is_admin or xaccess else False
    
    data = view_func(request, vid, id, 'user', access)

    if data == 'redirect':
        return HttpResponseRedirect(reverse('profile_view', kwargs={'user_id': user.id, 'vid': vid}))

    if not id and data['count'] == 1:
        kw = {'vid': vid, 'id': data['news_data'][0]['obj'].id, 'user_id': user.id}
        return HttpResponseRedirect(reverse('profile_view_post', kwargs=kw))

    extend_template = 'base.html'

    template = 'user/view.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        template = 'mobile/user/view.html'

    main_email = request.user.email
    emails = []
    for i in request.profile.accounts.all():
        if i.email and i.email.strip():
            emails.append(i.email.strip())
    emails = set(emails)
    email_exist = True if main_email or emails else False

    try:
        subscribed = SubscriberUser.objects.get(profile=request.profile, type='1', obj=data['vid']).id
    except SubscriberUser.DoesNotExist:
        subscribed = False

    comments_subscribed = False
    if id:
        try:
            comments_subscribed = SubscriberUser.objects.get(profile=request.profile, type='2', obj=id).id
        except SubscriberUser.DoesNotExist: pass
        
    user_bg = get_usr_bg(request, card['profile'])

    data['extend_template'] = extend_template
    data['card'] = card
    data['email_exist'] = email_exist
    data['subscribed'] = subscribed
    data['comments_subscribed'] = comments_subscribed
    data['user_bg'] = user_bg
    
    return render_to_response(template, data, context_instance=RequestContext(request))



@never_cache
def user_gallery(request, user_id=None, vid=None):
    from vladaalfimov.views import gallery_func
    current_user = request.user
    if user_id:
        user_id = int(user_id)
        is_my_profile = True if current_user.id == user_id else False
    else:
        is_my_profile = True
    
    if user_id and not is_my_profile:
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise Http404
    else:
        user = current_user

    card = get_usercard(user, ugroups=True)
    card['is_my_profile'] = is_my_profile

    template = 'user/gallery.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        template = 'mobile/user/gallery.html'

    menu = get_object_or_404(OrgSubMenu, pk=vid, orgmenu__profile__user=user)
    
    access = True if request.user.is_superuser or request.is_admin or is_my_profile else False
    
    data = gallery_func(request, vid, menu, access, '', org_type=False, user_id=user.id)
    if data == 'redirect':
        return HttpResponseRedirect(reverse("profile_gallery", kwargs={'user_id': user.id, 'vid': vid}))
    
    user_bg = get_usr_bg(request, card['profile'])

    data['card'] = card
    data['user_bg'] = user_bg

    return render_to_response(template, data, context_instance=RequestContext(request))


@only_superuser_or_admin
@never_cache
def user_change_page_type(request, vid, user_id):
    if request.POST:
        if request.user.is_superuser or request.is_admin:
            menu = get_object_or_404(OrgSubMenu, pk=vid)
            menu.page_type = request.POST.get('page_type')
            menu.save()
            current_site = request.current_site

            if menu.page_type == '1':
                ref = 'profile_view'
                return HttpResponseRedirect(reverse(ref, kwargs={'user_id': user_id, 'vid': vid}))
            elif menu.page_type == '2':
                ref = 'profile_gallery'
                return HttpResponseRedirect(reverse(ref, kwargs={'user_id': user_id, 'vid': vid}))
            
    raise Http404



@only_superuser
@never_cache
def edit_person_name(request, user_id, name_id):
    if request.method == "POST":
        name = NamePerson.objects.get(pk=request.POST['name_id'])
        name.name = request.POST['name'] # Должна быть проверка на наличие такого имени в БД
        name.save()
        return HttpResponseRedirect(reverse('user_details', kwargs={'id': request.POST['user_id']}))
    else:
        name_obj = get_object_or_404(NamePerson, pk=name_id)
        return render_to_response('user/edit_user_name.html', {'name_obj': name_obj, 'user_id': user_id}, context_instance=RequestContext(request))



def subscriber_blog_sender():
    stype = '1'

    # Новые посты в блогах в очереде на отправку
    objects = {}
    end_objects = []
    for i in SubscriberObjects.objects.filter(in_work=True, type=stype):
        if not objects.get(i.obj):
            objects[i.obj] = {'obj': i, 'name': '', 'end_objs_ids': [], 'end_objs': [], 'users': []}
        objects[i.obj]['end_objs_ids'].append(i.end_obj)
        end_objects.append(i.end_obj)

    for i in list(OrgSubMenu.objects.filter(pk__in=objects.keys()).values('id', 'name')):
        objects[i['id']]['name'] = i['name']

    # Текст постов
    authors_profiles = []
    end_objs = {}
    for i in News.objects.select_related('autor').filter(pk__in=set(end_objects), visible=True):
        end_objs[i.id] = {'id': i.id, 'title': i.title, 'text': i.text, 'author_id': i.autor.user_id}
        authors_profiles.append(i.autor)

    # Авторы блогов
    authors = org_peoples(set(authors_profiles), True)

    # Структура {блог: [{'ид', заголовок', 'текст', 'автор'}, {'ид', 'заголовок', 'текст', 'автор'}]}
    for k, v in objects.iteritems():
        for i in v['end_objs_ids']:
            end_obj = end_objs.get(i)
            if end_obj:
                author = authors.get(end_obj['author_id'])
                end_obj['author_name'] = author['name']
                v['end_objs'].append(end_obj)

    # Юзеры подписанные на эти блоги
    users = SubscriberUser.objects.select_related('profile', 'profile__user').filter(type=stype, obj__in=objects.keys())

    # Мэйлы юзеров
    profiles = {}
    profiles_ids = []
    subscribers = {}
    for i in users:
        if i.profile:
            if not profiles.get(i.profile_id):
                profiles[i.profile_id] = {'obj': i, 'main_email': None, 'emails': [], 'subscriber': []}
                if i.profile.user.email:
                    profiles[i.profile_id]['main_email'] = i.profile.user.email.strip()
                else:
                    profiles_ids.append(i.profile_id)
            # список блогов на которые подписан конкретный юзер
            profiles[i.profile_id]['subscriber'].append(i.obj)

    # Если нет основного мэйла, достаем остальные
    accs_dict = {}
    for i in list(Accounts.objects.filter(profile__pk__in=profiles_ids).values('email', 'profile')):
        if i['email']:
            profiles[i['profile']]['emails'].append(i['email'].strip())

    # Добавлям данные каким юзерам отправлять сообщения
    for k, v in profiles.iteritems():
        for i in v['subscriber']:
            el = dict(v)
            el.pop('subscriber')
            objects[i]['users'].append(el)

    
    for k, i in objects.iteritems():
        blog_name = i['name'].strip()
        if blog_name:

            subject = u'Блог "%s" [Новые статьи]' % blog_name

            msg_clear = u'Блог "%s". \n\n' % blog_name

            html = u'<div style="background: #EDEDED; color: #444; font-size: 14px; padding: 20px; font-family:Arial,\'Helvetica Neue\', Helvetica, sans-serif;">'
            html += u'<b style="font-size: 18px;">Блог "%s"</b>' % blog_name
            
            if i['end_objs']:
                eobjs = []
                for j in i['end_objs']:
                    html += u'<div style="background: #FFF; padding: 20px; margin: 20px 0 40px 0; line-height: 22px; overflow: hidden;">'
                    html += u'<b>%s</b><br /><br />' % j['title']
                    html += u'%s<br />' % j['text']
                    url = u'http://kinoafisha.ru/user/profile/%s/view/%s/post/%s/' % (j['author_id'], k, j['id'])
                    html += u'<br /><a href="%s" target="_blank" style="color: #BA5B32;">Оригинал тут</a><br /></div>' % url

                    msg_clear += u'"%s" - прочитать можно тут %s\n' % (j['title'], url)
                    
                    eobjs.append(j['id'])

                for j in i['users']:
                    try:
                        user_email = None
                        if j['main_email']:
                            user_email = j['main_email']
                        if not user_email and j['emails']:
                            user_email = j['emails'][0]

                        if user_email:
                            
                            unsubscribe = u'http://kinoafisha.ru/user/unsubscribe/%s/' % j['obj'].unsubscribe
                            user_html = u'<div style="background: #F6F6F6; padding: 10px; font-size: 12px; text-align: center; margin-top: 20px; color: #999;">'
                            user_html += u'Вы получили это письмо, так как подписались на блог "%s"<br />' % blog_name
                            user_html += u'Чтобы отписаться от сообщений, перейдите по ссылке - <a href="%s" target="_blank" style="color: #D3967C;">%s</a>' % (unsubscribe, unsubscribe)
                            user_html += u'</div></div>'

                            complete_html = u'%s%s' % (html, user_html)

                            mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, [user_email.strip()])
                            mail.attach_alternative(complete_html, "text/html")
                            mail.send()
                            SubscriberLog.objects.create(user=j['obj'], obj=i['obj'])
                        else:
                            error = 'Нет мэйла'
                            SubscriberLog.objects.create(user=j['obj'], obj=i['obj'], notified=False, error=error)
                    except Exception as e:
                        error = u'Ошибка %s' % e.args
                        SubscriberLog.objects.create(user=j['obj'], obj=i['obj'], notified=False, error=error[:128])
                
                SubscriberObjects.objects.filter(obj=k, end_obj__in=eobjs, type=stype).update(in_work=False)
                #i['obj'].in_work = False
                #i['obj'].save()



def subscriber_comments_sender():
    stype = '2'

    # Новые ответы к комментам к посту в очереде на отправку
    objects = {}
    end_objects = []
    for i in SubscriberObjects.objects.filter(in_work=True, type=stype):
        if not objects.get(i.obj):
            objects[i.obj] = {'obj': i, 'name': '', 'vid': None, 'author': None, 'branches': {}, 'ignore': [], 'type': None, 'extra': ''}
        end_objects.append(i.end_obj)

    # Текст ответов
    authors_profiles = []
    end_objs = {}

    news_objs = list(News.objects.filter(pk__in=set(end_objects), reader_type='10').values('id', 'dtime', 'text', 'autor', 'autor__user', 'parent', 'parent__title', 'parent__autor__user', 'parent__orgsubmenu', 'branch', 'branch__autor', 'branch__text', 'branch__dtime', 'parent__reader_type', 'parent__extra'))
    
    for i in news_objs:
        if i['autor'] != i['branch__autor']:
            answer = {'id': i['id'], 'dtime': i['dtime'], 'text': i['text'], 'author_id': i['autor__user']}
            end_objs[i['id']] = answer
            authors_profiles.append(i['autor'])

            if not objects[i['parent']]['name']:
                objects[i['parent']]['name'] = i['parent__title']
                objects[i['parent']]['vid'] = i['parent__orgsubmenu']
                objects[i['parent']]['author'] = i['parent__autor__user']
                objects[i['parent']]['type'] = i['parent__reader_type']
                objects[i['parent']]['extra'] = i['parent__extra']

            if not objects[i['parent']]['branches'].get(i['branch__autor']):
                objects[i['parent']]['branches'][i['branch__autor']] = {}

            if not objects[i['parent']]['branches'][i['branch__autor']].get(i['branch']):
                objects[i['parent']]['branches'][i['branch__autor']][i['branch']] = {'text': i['branch__text'], 'answers': [], 'dtime': i['branch__dtime']}

            objects[i['parent']]['branches'][i['branch__autor']][i['branch']]['answers'].append(answer)
        else:
            objects[i['parent']]['ignore'].append(i['id'])


    # Авторы ответов
    authors_profiles = list(Profile.objects.filter(pk__in=authors_profiles))
    authors = org_peoples(set(authors_profiles), True)

    # Юзеры подписанные на эти комменты
    users = SubscriberUser.objects.select_related('profile', 'profile__user').filter(type=stype, obj__in=objects.keys())

    # Мэйлы юзеров
    profiles = {}
    profiles_ids = []
    subscribers = {}
    for i in users:
        if i.profile:
            if not profiles.get(i.profile_id):
                profiles[i.profile_id] = {'obj': i, 'main_email': None, 'emails': [], 'subscriber': []}
                if i.profile.user.email:
                    profiles[i.profile_id]['main_email'] = i.profile.user.email.strip()
                else:
                    profiles_ids.append(i.profile_id)
            # список статей на которые подписан конкретный юзер
            profiles[i.profile_id]['subscriber'].append(i.obj)

    # Если нет основного мэйла, достаем остальные
    accs_dict = {}
    for i in list(Accounts.objects.filter(profile__pk__in=profiles_ids).values('email', 'profile')):
        if i['email']:
            profiles[i['profile']]['emails'].append(i['email'].strip())


    # post_id: {'name', 'branches': 
    #               {parent_author: 
    #                   {'dtime', branch': branch_id: 
    #                       {'text', 'answers': 
    #                           [{'id', 'dtime', 'text', 'author_id'}]
    #                       }
    #                    }
    #                }
    #           }
    

    for k, i in objects.iteritems():
        post_title = i['name'].strip()
        eobjs = i['ignore']

        if post_title:
            
            subject = u'Ответы на Ваши комментарии'

            msg_clear = u'Ответы на Ваши комментарии к статье "%s". \n\n' % post_title

            html = u'<div style="background: #EDEDED; color: #444; font-size: 14px; padding: 20px; font-family:Arial,\'Helvetica Neue\', Helvetica, sans-serif;">'
            html += u'<b style="font-size: 18px;">Ответы на Ваши комментарии к статье "%s"</b>' % post_title

            if i['branches']:
                
                for u, answers in i['branches'].iteritems():

                    try:
                        profile = profiles.get(u)
                        if profile:
                            user_email = None
                            if profile['main_email']:
                                user_email = profile['main_email']
                            if not user_email and profile['emails']:
                                user_email = profile['emails'][0]

                            user_html = ''
                            if not i['type']:
                                url = u'http://kinoafisha.ru/user/profile/%s/view/%s/post/%s/' % (i['author'], i['vid'], k)
                            elif i['type'] == '14':
                                url = u'http://kinoinfo.ru/film/%s/reviews/#r%s' % (i['extra'], k)
                            
                            
                            for comm_val in sorted(answers.values(), key=operator.itemgetter('dtime')):

                                user_html += u'<div style="background: #FFF; padding: 20px; margin: 20px 0 20px 0; line-height: 22px; overflow: hidden;">'
                                user_html += u'<div style="color: #999;">'
                                user_html += u'<b>Ваш комментарий:</b><br />'
                                user_html += u'%s</div>' % comm_val['text'].replace('\n', '<br />')

                                for answ in comm_val['answers']:
                                    eobjs.append(answ['id'])

                                    author_name = authors.get(answ['author_id'])
                                    author_name = author_name['name'] if author_name else ''

                                    user_html += u'<br /><b>%s отвечает:</b><br />' % author_name
                                    user_html += u'%s<br />' % answ['text'].replace('\n', '<br />')
                                
                                user_html += u'</div>'

                            if user_email:
                                user_html += u'<a href="%s" target="_blank" style="color: #BA5B32;">Все комментарии тут</a><br />' % url

                                msg_clear += u'Все комментарии тут %s\n' % url

                                if not i['type']:
                                    unsubscribe = u'http://kinoafisha.ru/user/unsubscribe/%s/' % profile['obj'].unsubscribe
                                elif i['type'] == '14':
                                    unsubscribe = u'http://kinoinfo.ru/user/unsubscribe/%s/' % profile['obj'].unsubscribe
                                
                                user_html += u'<div style="background: #F6F6F6; padding: 10px; font-size: 12px; text-align: center; margin-top: 20px; color: #999;">'
                                user_html += u'Вы получили это письмо, так как подписались на ответы на ваши комментарии к статье "%s"<br />' % post_title
                                user_html += u'Чтобы отписаться от сообщений, перейдите по ссылке - <a href="%s" target="_blank" style="color: #D3967C;">%s</a>' % (unsubscribe, unsubscribe)
                                user_html += u'</div></div>'

                                complete_html = u'%s%s' % (html, user_html)

                                mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, [user_email.strip()])
                                mail.attach_alternative(complete_html, "text/html")
                                mail.send()
                                SubscriberLog.objects.create(user=profile['obj'], obj=i['obj'])

                            else:
                                error = 'Нет мэйла'
                                SubscriberLog.objects.create(user=profile['obj'], obj=i['obj'], notified=False, error=error)
                        else:
                            for comm_val in sorted(answers.values(), key=operator.itemgetter('dtime')):
                                for answ in comm_val['answers']:
                                    eobjs.append(answ['id'])

                    except Exception as e:
                        error = u'Ошибка %s' % str(e.args)
                        SubscriberLog.objects.create(user=profile['obj'], obj=i['obj'], notified=False, error=error[:128])
                        
        SubscriberObjects.objects.filter(obj=k, end_obj__in=eobjs, type=stype).update(in_work=False)



def subscriber_comments_author_blog_sender():
    msg_for_admin = ''

    stype = '3'

    # Новые ответы к комментам к посту в очереде на отправку
    objects = {}
    end_objects = []
    for i in SubscriberObjects.objects.filter(in_work=True, type=stype):
        if not objects.get(i.obj):
            objects[i.obj] = {
                'obj': i, 'name': '', 'vid': None, 'author': None, 'objs': [],
                'ignore': [], 'type': None, 'extra': ''
            }
        end_objects.append(i.end_obj)

    # Текст ответов
    authors_profiles = []
    news_objs = list(News.objects.filter(pk__in=set(end_objects), reader_type='10').values(
        'id', 'text', 'dtime', 'autor', 'autor__user', 'parent', 'parent__title',
        'parent__autor', 'parent__autor__user', 'parent__orgsubmenu',
        'branch__autor', 'parent__reader_type', 'parent__extra'
    ))

    for i in news_objs:
        if i['autor'] != i['branch__autor'] and i['autor'] != i['parent__autor']:
            answer = {'id': i['id'], 'dtime': i['dtime'], 'text': i['text'], 'author_id': i['autor__user']}

            authors_profiles.append(i['autor'])

            if not objects[i['parent']]['name']:
                objects[i['parent']]['name'] = i['parent__title']
                objects[i['parent']]['vid'] = i['parent__orgsubmenu']
                objects[i['parent']]['author'] = i['parent__autor__user']
                objects[i['parent']]['type'] = i['parent__reader_type']
                objects[i['parent']]['extra'] = i['parent__extra']

            objects[i['parent']]['objs'].append(answer)
        else:
            objects[i['parent']]['ignore'].append(i['id'])

    # Авторы ответов
    authors_profiles = list(Profile.objects.filter(pk__in=authors_profiles))
    authors = org_peoples(set(authors_profiles), True)

    # Юзеры подписанные на эти комменты
    users = SubscriberUser.objects.select_related('profile', 'profile__user').\
        filter(type=stype, obj__in=objects.keys())

    # Мэйлы юзеров
    profiles = {}
    profiles_ids = []
    for i in users:
        if i.profile:
            if not profiles.get(i.profile_id):
                profiles[i.profile_id] = {'obj': i, 'main_email': None, 'emails': [], 'subscriber': []}
                if i.profile.user.email:
                    profiles[i.profile_id]['main_email'] = i.profile.user.email.strip()
                else:
                    profiles_ids.append(i.profile_id)
            # список статей на которые подписан конкретный юзер
            obj = objects.get(i.obj)
            if obj:
                profiles[i.profile_id]['subscriber'].append(obj)

    # Если нет основного мэйла, достаем остальные
    for i in list(Accounts.objects.filter(profile__pk__in=profiles_ids).values('email', 'profile')):
        if i['email']:
            profiles[i['profile']]['emails'].append(i['email'].strip())

    #{profile_id: {'main_email', 'obj': , 'emails': [], 'subscriber': [{'objs': [], 'obj', 'name', 'vid', 'author', 'ignore': []}]}}

    subject = u'У Вас новые комментарии'

    for k, p in profiles.iteritems():

        user_email = None
        if p['main_email']:
            user_email = p['main_email']
        if not user_email and p['emails']:
            user_email = p['emails'][0]

        eobjs = []

        msg_clear = u'%s. \n\n' % subject

        html = u'<div style="background: #EDEDED; color: #444; font-size: 14px; padding: 20px; font-family:Arial,\'Helvetica Neue\', Helvetica, sans-serif;"><b style="font-size: 18px;">%s</b><div style="background: #FFF; padding: 20px; margin: 20px 0 20px 0; line-height: 22px; overflow: hidden;">' % subject

        content = ''
        ok = {}
        for i in p['subscriber']:
            eobjs = [o['id'] for o in i['objs']]
            eobjs = eobjs + i['ignore']

            count = len(i['objs'])
            post_title = i['name'].strip()

            if count and post_title:
                if not i['type']:
                    url = u'http://kinoafisha.ru/user/profile/%s/view/%s/post/%s/' % (i['author'], i['vid'], i['obj'].obj)
                elif i['type'] == '14':
                    url = u'http://kinoinfo.ru/film/%s/reviews/#r%s' % (i['extra'], i['obj'].obj)

                html_url = u'<b><a href="%s" target="_blank" style="color: #BA5B32;">%s</a></b><br />' % (url, post_title)

                content += html_url

                msg_for_admin += html_url

                for answ in i['objs']:
                    author_name = authors.get(answ['author_id'])
                    author_name = author_name['name'] if author_name else ''

                    content += u'<br /><b>%s отвечает:</b><br />' % author_name
                    content += u'%s<br />' % answ['text'].replace('\n', '<br />')

                msg_clear += u'Новых комментариев %s шт. \n' % count
                msg_clear += u'%s \n\n' % url

            ok[i['obj']] = eobjs
        try:
            if content:
                complete_html = u'%s%s</div></div>' % (html, content)

                if user_email:
                    mail = EmailMultiAlternatives(subject, msg_clear, settings.DEFAULT_FROM_EMAIL, [user_email.strip()])
                    mail.attach_alternative(complete_html, "text/html")
                    mail.send()
                    for o in ok:
                        SubscriberLog.objects.create(user=p['obj'], obj=o)
                else:
                    error = 'Нет мэйла'
                    for o in ok:
                        SubscriberLog.objects.create(user=p['obj'], obj=o, notified=False, error=error)

        except Exception as e:
            error = u'Ошибка %s' % str(e.args)
            SubscriberLog.objects.create(user=p['obj'], obj=ok.keys()[0], notified=False, error=error[:128])

        for k, v in ok.iteritems():
            SubscriberObjects.objects.filter(obj=k.obj, end_obj__in=v, type=stype).update(in_work=False)

        if msg_for_admin:
            # оповещение админа об новых комментариях
            subject = u'Новые комментарии'
            admins_email = ['kinoafisharu@gmail.com', 'twohothearts@gmail.com']
            mail = EmailMultiAlternatives(subject, '', settings.DEFAULT_FROM_EMAIL, admins_email)
            mail.attach_alternative(msg_for_admin, "text/html")
            mail.send()


@never_cache
def unsubscribe(request, code):
    try:
        obj = SubscriberUser.objects.get(unsubscribe=code)
        unsubscribe = True
    except SubscriberUser.DoesNotExist:
        unsubscribe = False

    unsubscribe_success = False

    if request.POST and unsubscribe:
        if 'un' in request.POST:
            obj.delete()
            unsubscribe_success = True
        else:
            return HttpResponseRedirect(reverse('main'))
    
    if unsubscribe:
        obj_type = ''
        obj_name = ''
        
        if obj.type == '1':
            obj_type = 'Блог'
            try:
                obj_name = OrgSubMenu.objects.get(pk=obj.obj).name
            except OrgSubMenu.DoesNotExist: pass

        return render_to_response('user/profile_unsubscribe.html', {'unsubscribe_success': unsubscribe_success, 'obj_type': obj_type, 'obj_name': obj_name}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('main'))





@only_superuser
@never_cache
def import_kinoafisha_users(request):
    from api.models import RegisteredUsers
    from django.contrib.auth.models import Group
    group = Group.objects.get(name='API')
    result = RegisteredUsers.objects.using('afisha').exclude(email='').order_by('pk')
    for i in result:
        firstname = i.firstname if i.firstname else ''
        lastname = i.lastname if i.lastname else ''
        fullname = '%s %s' % (firstname, lastname)
        fullname = None if fullname == ' ' else fullname.strip()
        nickname = i.nickname if i.nickname else None
        email = i.email
        access_level = i.access_level
        date_registration = i.date_registration
        gender = i.sex if i.sex.isdigit() else None
        dob = i.date_of_birth if i.date_of_birth != '0000-00-00' else None
        rule = i.rule
        try:
            acc = Accounts.objects.get(login=email)
        except Accounts.DoesNotExist:
            acc = Accounts.objects.create(login=email, validation_code=None, email=email, auth_status=True, nickname=nickname, fullname=fullname, born=dob, male=gender, avatar=None)
            user = get_user()
            if rule == 10:
                user.is_superuser = True
            if rule == 10 or rule == 22:
                user.groups.add(group)
            user.date_joined = '%s 00:00:00' % date_registration
            user.get_profile().auth_status = True
            user.get_profile().save()
            user.get_profile().accounts.add(acc)
            user.save()
    return HttpResponse('ok')















########### test
def user_list():
    '''
    Получение списка пользователей кроме superuser
    '''
    return User.objects.exclude(is_superuser=True).order_by('pk')
    
@never_cache
def get_user_list(request):
    '''
    Список пользователей
    '''
    if request.user.is_authenticated() and request.user.is_superuser:
        if request.method == 'POST' and 'user' in request.POST:
            user_id = request.POST['user']
            if request.user.id != int(user_id):
                user = User.objects.get(pk=user_id)
                delete_user(user)
                return HttpResponseRedirect(reverse('get_user_list'))
        users = user_list()
        return render_to_response('user/user_list.html', {'users': users}, context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('main'))




def test_delete(request):
    User.objects.filter(pk__in=[41]).delete()
    return HttpResponse('ok')



@never_cache
def test_ava(request):
    t1 = 'STATIC<br />'
    for dirName,subdirList,fileList in os.walk(settings.STATIC_ROOT):
        t1 += '<ul>' + dirName
        for fname in fileList:
            t1 += "<li>" + fname  + '</li>'
        t1 += '</ul>'
    t2 = 'MEDIA<br />'
    for dirName,subdirList,fileList in os.walk(settings.MEDIA_ROOT):
        t2 += '<ul>' + dirName
        for fname in fileList:
            t2 += "<li>" + fname  + '</li>'
        t2 += '</ul>'
    '''
    t1 = ''
    for dirName,subdirList,fileList in os.walk(settings.AVATAR_FOLDER):
        t1 += '<ul>' + dirName
        for fname in fileList:
            t1 += "<li>" + fname  + '</li>'
        t1 += '</ul>'
    '''
    return HttpResponse(t1 + t2)

def mailru_complete2(request):
    content = '[{"pic_50":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar50","friends_count":47,"pic_22":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar22","nick":"чувак с mail.ru","is_verified":1,"is_online":1,"pic_big":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatarbig","last_name":"с mail.ru","has_pic":1,"email":"modnyi.kuzya@mail.ru","pic_190":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar190","referer_id":"","vip":0,"pic_32":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar32","birthday":"","referer_type":"","link":"http://my.mail.ru/mail/modnyi.kuzya/","uid":"18236122197594170328","app_installed":1,"pic_128":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar128","sex":0,"pic":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar","pic_small":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatarsmall","pic_180":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar180","first_name":"чувак","pic_40":"http://avt.appsmail.ru/mail/modnyi.kuzya/_avatar40"}]'
    response_data = {'resp': 'resp', 'content': content}
    
    user_data = json.loads(content)
    email = user_data[0].get('email', None)
    uid = 'mail.ru_%s' % user_data[0].get('uid', None)
    nickname = user_data[0].get('nick', None).encode('utf-8')
    first_name = user_data[0].get('first_name', None).encode('utf-8')
    last_name = user_data[0].get('last_name', None).encode('utf-8')
    fullname = '%s %s' % (first_name, last_name)
    birthday = user_data[0].get('birthday', None)
    avatar_url = user_data[0].get('pic_128', None)
    dob = birthday if birthday != '' else None
    if dob:
        dob = dob.split('.')
        dob = '%s-%s-%s' % (dob[2], dob[1], dob[0])
    gender = user_data[0].get('sex', None)
    if gender is not None: gender = 1 if int(gender) == 0 else 2
    acc = accounts_interim(request, request.user.get_profile(), uid, email=email, nick=nickname, name=fullname, gender=gender, dob=dob, avatar_url=avatar_url)
    if acc: return acc
    return HttpResponseRedirect(reverse("profile"))


@only_superuser
@never_cache
def clear_empty_users(request):
    import shutil
    
    today = datetime.datetime.today()
    past_date = today - datetime.timedelta(days=90)

    profiles = Profile.objects.select_related('person', 'personinterface').filter(accounts=None, person__name=None, phone=None, user__email='', user__is_superuser=False, user__last_login__lt=past_date, personinterface__money=0)
    
    # проверку на staff организации !!!
    
    users = []
    persons = []
    interfaces = []
    for i in profiles:
        users.append(i.user_id)
        persons.append(i.person_id)
        interfaces.append(i.personinterface_id)
        
        try: shutil.rmtree('%s/%s' % (settings.AVATAR_FOLDER, i.folder))
        except OSError: pass
    
    PersonInterface.objects.filter(pk__in=interfaces).delete()
    Person.objects.filter(pk__in=persons).delete()
    profiles.delete()
    User.objects.filter(pk__in=users).delete()
    
    empty = User.objects.filter(email='', last_login__lt=past_date, is_superuser=False, profile=None).delete()
    
    return HttpResponse(str())


@only_superuser
@never_cache
def replace_users_avatars(request):
    import shutil
    from django.db.models import Q
    
    folders = list(i for i in Profile.objects.all().values_list('folder', flat=True))

    accs = list(Accounts.objects.exclude(Q(avatar=None) | Q(avatar='')).values_list('profile__folder', flat=True))

    for folder in folders:
        try:
            for f in os.listdir('%s/%s' % (settings.AVATAR_FOLDER, folder)):
                file_path = '%s/%s/%s' % (settings.AVATAR_FOLDER, folder, f)
                if os.path.isfile(file_path):
                    dst = '%s/%s' % (settings.AVATARS, f)
                    shutil.copy(file_path, dst)
        except OSError: pass
    
    try: shutil.rmtree(settings.AVATAR_FOLDER)
    except OSError: pass
        
    return HttpResponse(str())
    

@only_superuser
@never_cache
def clear_empty_sessions(request):
    today = datetime.datetime.today()
    DjangoSession.objects.filter(expire_date__lt=today).delete()
    
    #users = list(User.objects.all().values_list('pk', flat=True))

    #[s.delete() for s in  DjangoSession.objects.all() if long(s.get_decoded().get('_auth_user_id', 0)) not in users]
    
    return HttpResponse(str('fin*'))


