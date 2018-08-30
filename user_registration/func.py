# -*- coding: utf-8 -*- 
import time
import datetime
import hashlib
from random import randrange
from django.http import Http404
from base.models import *

def login_counter(request):
    if request.user.is_authenticated() and request.user.last_login.date() < datetime.date.today():
        request.user.last_login = datetime.datetime.now()
        request.user.save()

def md5_string_generate(something):
    '''
    Генератор md5 строк
    '''
    md5_string = "%s_some_text_%s" % (datetime.datetime.now(), something)
    return hashlib.md5(md5_string).hexdigest()
    
    
def sha1_string_generate(something=''):
    first_part = str(datetime.datetime.now())
    second_part = something
    if not second_part:
        second_part = '%s%s' % (str(randrange(100000, 999999)), str(randrange(100, 999)))
    first_part= hashlib.sha1(first_part).hexdigest()
    second_part = hashlib.sha1(second_part).hexdigest()
    rand = randrange(1000, 9999)
    rand = hashlib.sha1(str(rand)).hexdigest()
    unique = '%s_%s_%s' % (first_part[0:12], second_part[0:12], rand[0:4])
    return unique
    
def only_superuser(fn):
    '''
    Декоратор. Проверка на админа. 
    Если админ - выполняется метод, если нет - ошибка 404
    '''
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser:
            return fn(request, *args, **kwargs)
        else: raise Http404
    return wrapper


def only_superuser_or_admin(fn):
    '''
    Декоратор. Проверка на редактора сайта. 
    '''
    def wrapper(request, *args, **kwargs):
        if request.user.is_superuser or request.is_admin:
            return fn(request, *args, **kwargs)
        else: raise Http404
    return wrapper



def is_film_editor(request):
    editor = False
    if request.user.is_superuser or request.is_admin:
        editor = True
    else:
        try:
            groups = request.user.groups
            if groups:
                groups.get(name='Редактор фильмов')
                editor = True
        except: pass
    return editor

def is_linkanoid_user(request):
    result = False
    try:
        groups = request.user.groups
        if groups:
            groups.get(name='Linkanoid')
            result = True
    except: pass
    return result
    
def org_peoples(peoples, dic=False):
    listt = []
    dictt = {}
    
    ids = [i.id for i in peoples]
    
    persons = list(Person.objects.filter(profile__pk__in=ids).values('id', 'profile__kid', 'city', 'country', 'profile', 'profile__user', 'profile__user__first_name', 'profile__user__date_joined', 'profile__folder', 'profile__phone', 'profile__show_profile', 'profile__user__is_superuser', 'profile__user__last_name'))
    persons_dict = {}
    for i in persons:
        persons_dict[i['profile']] = i
    
    cities_dict = {}
    for i in list(NameCity.objects.filter(city__person__profile__pk__in=ids, status=1).values('city', 'name')):
        cities_dict[i['city']] = i['name']
    
    accs = list(Accounts.objects.filter(profile__pk__in=ids).values('avatar', 'fullname', 'nickname', 'login', 'profile'))
    accs_dict = {}
    for i in accs:
        if accs_dict.get(i['profile']):
            accs_dict[i['profile']].append(i)
        else:
            accs_dict[i['profile']] = [i]
    
    names = list(NamePerson.objects.filter(person__profile__pk__in=ids, status=1).order_by('id').values('person__profile', 'name'))
    names_dict = {}
    for i in names:
        names_dict[i['person__profile']] = i['name']
    
    
    for i in peoples:
        acc = []
        full = []
        nick = []
        login = []
        avatar = None
        person = persons_dict.get(i.id)
        if person:
            for j in accs_dict.get(i.id, []):
                if j['avatar'] and not avatar:
                    avatar = j['avatar']
                
                if j['fullname']:
                    full.append(j['fullname'])
                if j['nickname']:
                    nick.append(j['nickname'])
                if j['login']:
                    login.append(j['login'].split('@')[0])
                    
            if not full and not nick:
                acc = login
            else:
                acc = full + nick
                
            acc = sorted(acc, reverse=True)
            short_name = acc[0] if acc else 'User_%s' % person['profile__user']
            
            acc = set(acc)

            acc_txt = ' / '.join(acc)
            
            city = ''
            city_id = int(person['city']) if person['city'] else ''
            country_id = int(person['country']) if person['country'] else ''
            if city_id:
                city = cities_dict.get(city_id)
               
            fio = names_dict.get(i.id)
            
            name = fio if fio else short_name
            
            data = {
                'acc': acc_txt, 
                'name': name,
                'short_name': short_name,
                'nickname': person['profile__user__first_name'],
                'id': int(person['profile__user']), 
                'city': city,
                'city_id': city_id,
                'country_id': country_id,
                'folder': person['profile__folder'],
                'avatar': avatar,
                'show': person['profile__show_profile'],
                'fio': fio,
                'phone': person['profile__phone'],
                'is_superuser': person['profile__user__is_superuser'],
                'kid': person['profile__kid'],
                'date_joined': person['profile__user__date_joined'],
                'system': person['profile__user__last_name'],
            }
            
            dictt[i.user_id] = data
            
    if dic:        
        return dictt
    else:
        return dictt.values()


def get_adv_price(btype):
    price_rel = settings.PRICES.get(int(btype), 0)
    try:
        price = ActionsPriceList.objects.get(pk=price_rel, allow=True).price
    except ActionsPriceList.DoesNotExist:
        price = 0
    return price


def set_adv_view(request, banner_id):
    try:
        bg_views, bg_created = SiteBannersViews.objects.get_or_create(
            banner__pk = banner_id,
            profile = request.profile,
            defaults = {
                'banner_id': banner_id,
                'profile': request.profile,
            })
        if bg_created:
            try:
                banner = int(banner_id)
                banner = SiteBanners.objects.get(pk=banner)
            except ValueError: pass
            banner.views += 1
            banner.last_show = datetime.datetime.now().date()
            
            try:
                view_price = ActionsPriceList.objects.get(pk=48, allow=True).price
                user = Profile.objects.select_related('personinterface').get(pk=banner.user_id)
                interface = user.personinterface
                if interface.money >= view_price and banner.balance >= view_price:
                    interface.money -= view_price
                    interface.save()
                    banner.balance -= view_price
                    banner.spent += view_price
            except ActionsPriceList.DoesNotExist:
                pass

            banner.save()

    except SiteBannersViews.MultipleObjectsReturned:
        sbv = None
        for i in SiteBannersViews.objects.filter(banner__pk=banner_id, profile=request.profile):
            if sbv:
                i.delete()
            else:
                sbv = i


def get_usr_bg(request, profile, count=True):
    try:
        user_bg = SiteBanners.objects.filter(profile=profile, btype='3', deleted=False).order_by('-id')[0]
        if count and not request.bot:
            set_adv_view(request, user_bg.id)
    except IndexError:
        user_bg = None
    return user_bg
