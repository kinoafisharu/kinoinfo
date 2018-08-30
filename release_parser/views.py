#-*- coding: utf-8 -*-
import urllib
import re
import os
import datetime
import time
import calendar
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.template.defaultfilters import dictsort
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.utils import translation
from django import db

from unidecode import unidecode
from bs4 import BeautifulSoup

from api.views import get_dump_files, give_me_dump_please, xml_wrapper, create_dump_file, get_film_data
from api.models import *
from base.models_choices import *
from base.models import *
from kinoinfo_folder.func import get_month, del_separator, del_screen_type, low
from user_registration.func import only_superuser
from user_registration.ajax import create_by_email
from release_parser.forms import *
from release_parser.func import cron_success, get_imdb_id
from articles.views import pagination as pagi
from decors import timer

from movie_online.IR import check_int_rates, check_int_rates_inlist
from collections import OrderedDict

def parser_download(request, method):
    '''
    Скачивание дампов релизов
    '''
    method = method.replace('_dotseparator_', '.')
    return give_me_dump_please(request, method, '', True)

@only_superuser
@never_cache
def create(request, method):
    '''
    Создание дампов
    '''
    # запуск выполнения
    result = method()
    # если при выполнении ошибка, сообщение об ошибке
    if result:
        return HttpResponse(str(result))
    # иначе редирект на главную страницу парсера релизов
    else:
        return HttpResponseRedirect(reverse('kinoafisha_admin_main'))

# определение "языка" названия фильма
def language_identify(name):
    dic = {'ru': [], 'en': [], 'un': []}
    for i in name:
        if re.findall(r'[a-zA-Z]', i) and re.findall(r'[а-яА-Я]', i):
            dic['un'].append(i.strip())
        elif re.findall(r'[а-яА-Я]', i) and not re.findall(r'[a-zA-Z]', i):
            dic['ru'].append(i.strip())
        elif re.findall(r'[a-zA-Z]', i) and not re.findall(r'[а-яА-Я]', i):
            dic['en'].append(i.strip())

    f_name_ru = ' / '.join(dic['ru'])
    f_name_en = ' / '.join(dic['en'])
    f_name_un = ' / '.join(dic['un'])
    if f_name_un:
        f_name_ru, f_name_en = f_name_un, f_name_un
    return f_name_ru, f_name_en


def xml_noffilm(name_ru, slug_ru, name, slug, code, info, url, source=''):
    if not name_ru:
        name_ru = '*'
        slug_ru = '*'
    if not name:
        name = '*'
        slug = '*'
    if not code:
        code = ''
    if not url:
        url = ''
    data = '<film name_ru="%s" slug_ru="%s" name="%s" slug="%s" code="%s" source="%s">' % (name_ru.replace('"',"'").replace('&', '&amp;'), slug_ru, name.replace('"',"'").replace('&', '&amp;'), slug, code, source)
    data += '<info value="%s"></info>' % info
    data += '<url value="%s"></url>' % url
    data += '</film>'
    return data


def get_ignored_films():
    '''
    Возвращает список игнорируемых названий фильмов (slug)
    '''
    with open('%s/dump_ignore_films.xml' % settings.API_DUMP_PATH, 'r') as f:
        ignore = BeautifulSoup(f.read(), from_encoding="utf-8")
    ignored = [i['name'] for i in ignore.findAll('film')]
    return ignored

def get_ignored_cinemas():
    '''
    Возвращает список игнорируемых названий кинотеатров (slug)
    '''
    with open('%s/dump_ignore_cinemas.xml' % settings.API_DUMP_PATH, 'r') as f:
        ignore = BeautifulSoup(f.read(), from_encoding="utf-8")
    ignored = [i['name'] for i in ignore.findAll('cinema')]
    return ignored

def kinometro_ru():
    '''
    Парсер www.kinometro.ru, создание дампа релизов
    '''
    url = 'http://www.kinometro.ru/release/show/'
    # получаю страницу для парсинга
    page = urllib.urlopen(url)
    # если сервер доступен и найдена страница
    if page.getcode() == 200:
        text = ''
        release_date = ''
        release_date_old = ''
        page_data = BeautifulSoup(page.read(), from_encoding="utf-8")
        # получение основного блока с данными
        table = page_data.find('table', {'class' : 'sr_tbl'})
        # поиск данных в основном блоке
        for tr in table.findAll('tr'):
            if '<div>' in str(tr.td):
                if release_date_old:
                    text += '</release_date>'
                # получение даты релиза
                release_date = tr.td.div.string.encode('utf-8')
                # приведение даты к виду дд.мм.гг
                month = get_month(release_date)
                day = release_date[:2]
                year = release_date[-2:]
                text += '<release_date value="%s.%s.%s">' % (day, month, year)
            else:
                td = tr.findAll('td')
                # получение тега с названием фильма
                film_name = td[0].string.encode('utf-8').strip()
                # получение id фильма
                film_id = td[0].a.get('href').replace('/release/card/id/','').encode('utf-8')
                # вынос примечаний в скобках из названия фильма
                f_name_details = re.findall(r'\(.*?\)', film_name)
                details = ''
                if f_name_details:
                    for i in f_name_details:
                        details += str(i)
                film_name = re.sub(r'\(.*?\)', '', film_name)
                # разбор названий фильмов в теге
                f_name = film_name.split('/')
                if len(f_name) == 2:
                    f_name_ru, f_name_en = (f_name[0], f_name[1])
                elif len(f_name) > 2:
                    f_name_ru, f_name_en = language_identify(f_name)
                else:
                    f_name_ru, f_name_en = (f_name[0], '')
                f_name_ru = f_name_ru.replace(' ', '').replace('"', "'").strip()
                f_name_en = f_name_en.replace(' ', '').replace('"', "'").strip()
                # получение даты релиза в США
                usa_release = td[1].string.encode('utf-8').replace(' ','')
                # получение дистрибьютора
                distr = td[2].text.encode('utf-8').split('/')
                distr_name1, distr_name2 = (distr[0].strip(), distr[1].strip()) if len(distr) > 1 else (distr[0].strip(), '')
                tag_a = td[2].findAll('a')
                if len(tag_a) > 1:
                    distr_id1, distr_id2 = (tag_a[0].get('href'), tag_a[1].get('href'))
                elif len(tag_a) < 1:
                    distr_id1, distr_id2 = ('','')
                elif len(tag_a) == 1:
                    t = td[2].prettify().split(' /')
                    d_id = tag_a[0].get('href')
                    distr_id1 = ''
                    distr_id2 = ''
                    if len(t) > 1:
                        if d_id in t[0]:
                            distr_id1 = d_id
                        elif d_id in t[1]:
                            distr_id2 = d_id
                    else:
                        distr_id1 = d_id
                distr_id1 = distr_id1.replace('/distributor/show/id/','').encode('utf-8')
                distr_id2 = distr_id2.replace('/distributor/show/id/','').encode('utf-8')
                # получение кол-во копий
                copies = td[3].string.encode('utf-8') if td[3].string else ''
                # получение хронометража
                runtime = td[4].string.encode('utf-8') if td[4].string else ''
                # получение возрастных ограничений
                rated = td[5].string.encode('utf-8').replace('-', '')
                # полученные данные обарачиваю в xml теги
                text += '<film name_ru="%s" name="%s" code="%s">' % (f_name_ru, f_name_en, film_id)
                text += '<details value="%s"></details>' % details
                text += '<usa_release value="%s"></usa_release>' % usa_release
                text += '<distributor value="%s" code="%s"></distributor>' % (distr_name1, distr_id1)
                if distr_name2:
                    text += '<distributor value="%s" code="%s"></distributor>' % (distr_name2, distr_id2)
                text += '<copies value="%s"></copies>' % copies
                text += '<runtime value="%s"></runtime>' % runtime
                text += '<rated value="%s"></rated>' % rated
                text += '</film>'
            release_date_old = release_date
        text += '</release_date>'
        text = xml_wrapper(text)
        # создание дампа
        create_dump_file('kinometro_ru', settings.API_DUMP_PATH, text.replace('&','&amp;'))
    # если возникла ошибка
    else:
        return page.getcode()


def film_ru():
    '''
    Парсер film.ru, создание дампа релизов
    '''
    url = 'http://www.film.ru/afisha/soon.asp'
    # получаю страницу для парсинга
    page = urllib.urlopen(url)
    # если сервер доступен и найдена страница
    if page.getcode() == 200:
        text = ''
        release_date = ''
        release_date_old = ''
        page_data = BeautifulSoup(page.read())
        # получение основного блока с данными
        div_main = page_data.find('div', {'class' : 'left-column'})
        # поиск данных в основном блоке
        for div in div_main.findAll('div', {'class' : 'b-sl'}):
            # получение года релиза
            year = re.findall('\d+', str(div.b))
            for d in div.findAll('div', {'class': 'b-d'}):
                # приведение даты к виду дд.мм.гг
                r_date = d.string.encode('utf-8')
                month = get_month(r_date)
                day = '{0:0=2d}'.format(int(r_date[:2].strip()))
                release_date = "%s.%s.%s" % (day, month, year[0][-2:])
                if release_date_old:
                    text += '</release_date>'
                text += '<release_date value="%s">' % release_date
                # получение блока с данными о фильмах и дистрибьютерах
                bl_ml = d.find_next('div', {'class': 'b-ml'})
                for i in bl_ml.findAll('div', {'class': 'b-n'}):
                    # получение названия фильма
                    f_name_ru = i.h3.a.string.encode('utf-8').replace('"',"'")
                    # получение id фильма
                    film_id = i.h3.a.get('href').replace('/afisha/movie.asp?code=','').encode('utf-8')
                    # получение альт. названия фильма
                    f_name_en = i.find('span', {'class': 'nowrap'})
                    f_name_en = f_name_en.a.string.encode('utf-8').replace('"',"'") if f_name_en else '*'
                    # получение дистрибьютора
                    distr = i.find_next('span', {'class': 'b-destributor'}).a.string.encode('utf-8')
                    # полученные данные обарачиваю в xml теги
                    text += '<film name_ru="%s" name="%s" code="%s">' % (f_name_ru, f_name_en, film_id)
                    text += '<distributor value="%s"></distributor>' % distr
                    text += '</film>'
                release_date_old = release_date
        text += '</release_date>'
        text = xml_wrapper(text)
        # создание дампа
        create_dump_file('film_ru', settings.API_DUMP_PATH, text.replace('&','&amp;'))
    # если возникла ошибка
    else:
        return page.getcode()


@timer
def kinoafisha_country_import():
    '''
    Импорт стран из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    countries = AfishaCountry.objects.using('afisha').all().distinct('name')
    for i in countries:
        country, created = Country.objects.get_or_create(name=i.name, defaults={'name': i.name, 'name_en': i.name_en, 'kid': i.id})
        if not created:
            if country.kid != i.id:
                if country.kid != i.id:
                    country.kid= i.id
                country.save()

    cron_success('import', source.dump, 'country', 'Страны')


@only_superuser
@never_cache
def country_list(request):
    countries = Country.objects.all().order_by('name')
    return HttpResponse(list(countries))


@only_superuser
@never_cache
def city_list_in_db(request):
    cities = City.objects.all()
    city_dict = ''
    for i in cities:
        for n in i.name.all():
            if n.status == 1:
                city_dict += '%s - %s<br />' % (i.id, n.name.encode('utf-8'))
    return HttpResponse(city_dict)


def create_name_distr(name, status, distr):
    '''
    Создание названий дистр. и связи с дистр.
    '''
    obj, created = NameDistributors.objects.get_or_create(
        name=name, status=status, defaults={'name': name, 'status': status}
    )
    if obj not in distr.name.all():
        distr.name.add(obj)


def kinoafisha_usa_gathering_import():
    '''
    Импорт сборов США из kinoafisha.ru
    
    current_year = datetime.date.today().year
    past_three_year = current_year - 2
    box_date = datetime.date(past_three_year, 1, 1)
    
    # достаем иды уже записанных данных
    boxoffice_ids = list(BoxOffice.objects.filter(country__name='США', date_from__gte=box_date).values_list('bx_id', flat=True))
    
    # достаем новые данные для сша
    gathering = Gathering.objects.using('afisha').filter(friday_date__gte=box_date, country__id=1).exclude(id__in=boxoffice_ids)

    films = set([int(i.film_id) for i in gathering])
    
    #film = Film.objects.using('afisha').only('id', 'company').filter(pk__in=films).exclude(company=0)
    film = FilmsName.objects.using('afisha').select_related('film_id', 'film_id__company').exclude(film_id__company=0).filter(film_id__id__in=films, status=1, type=2)
    
    distr_obj = Distributors.objects.filter(usa=True)
    distr_dict = {}
    for i in distr_obj:
        distr_dict[i.kid] = i
    
    company = {}
    for i in film:
        obj = distr_dict.get(i.film_id.company_id)
        company[i.film_id_id] = {'distr': obj, 'filmname': i.name}
    
    
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    
    for i in gathering:
    
        comp = company.get(int(i.film_id))
        
        name = ''
        distributor = None
        if comp:
            name = comp['filmname']
            distributor = comp['distr']
        
        box_obj = BoxOffice.objects.create(
            bx_id = i.id,
            source_id = i.film_id,
            source_obj = source,
            name = name,
            kid = i.film_id,
            screens = i.day_in_rent,
            date_from = i.friday_date,
            date_to = i.sunday_date,
            week_sum = i.period_gathering,
            all_sum = i.total_gathering,
            week_audience = i.date_from,
            all_audience  = i.date_to,
            days = None,
            country_id = 1,
        )
        
        if distributor:
            box_obj.distributor.add(distributor)
    '''
    return HttpResponse(str())


@timer
def kinoafisha_reviews_import():
    from user_registration.views import get_user
    
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    
    emails = {
        u'Михаил Иванов': 'kinoafisharu@gmail.com',
        u'Сергей Наан': 's.naan@mail.ru',
        u'Александр Казанцев': 'elercant@mail.ru',
        u'Ирина Соловьёва': 'saechka.irina@gmail.com',
        u'Кирилл Розов': 'kirich1409@gmail.com',
        u'Александр Иванов': 'al.duma@rambler.ru',
        u'Вера Алёнушкина': 'mastif.alyonushkina@yandex.ru',
    }

    exists = list(News.objects.exclude(kid=None).filter(visible=True, reader_type='14').values_list('kid', flat=True))

    reviews = AfishaNews.objects.using('afisha').select_related('user').only('name', 'content', 'date_time', 'user', 'obj').filter(type=2, object_type=1)


    film_vote = FilmVotes.objects.using('afisha').all()
    votes_dict = {}
    for i in film_vote:
        votes_dict[int(i.id)] = {'obj': i, 'user': None}

    users_emails = {}
    users = {}
    current_site = DjangoSite.objects.get(domain='kinoinfo.ru')
    
    for i in reviews:
        author = users_emails.get(i.user_id)
        
        if not author:
            date_registration = i.user.date_registration
            
            fullname = '%s %s' % (i.user.firstname, i.user.lastname) if i.user.firstname else ''
            fullname = fullname.strip()
            
            nickname = i.user.nickname if i.user.nickname else None
            gender = i.user.sex if i.user.sex.isdigit() else None
            dob = i.user.date_of_birth if i.user.date_of_birth != '0000-00-00' else None
        
            email = i.user.email
            if not email:
                email = emails.get(fullname)
            
            if email:
                users_emails[i.user_id] = {'email': email, 'full': fullname, 'gender': gender, 'dob': dob, 'nick': nickname, 'reg': date_registration}
                author = users_emails[i.user_id]

        
        if author:
            user_obj = users.get(author['email'])
            
            if not user_obj:
                try:
                    user_obj = Profile.objects.filter(Q(user__email=author['email']) | Q(accounts__login=author['email'])).order_by('-id')[0]
                except IndexError:
                    acc = Accounts.objects.create(login=author['email'], validation_code=None, email=author['email'], auth_status=True, nickname=author['nick'], fullname=author['full'], born=author['dob'], male=author['gender'], avatar=None)
                    user = get_user()
                    user.date_joined = '%s 00:00:00' % author['reg']
                    user_obj = user.get_profile()
                    user_obj.auth_status = True
                    user_obj.save()
                    user_obj.accounts.add(acc)
                    user.save()
                    
                users[author['email']] = user_obj

            if votes_dict.get(int(i.id)):
                votes_dict[int(i.id)]['user'] = user_obj
                votes_dict[int(i.id)]['film'] = i.obj_id
            
            if long(i.id) not in exists:
                new = News.objects.create(
                    title = i.name, 
                    autor = user_obj,
                    site = current_site,
                    subdomain = 0,
                    text = i.content,
                    visible = True,
                    reader_type = '14',
                    autor_nick = 0,
                    extra = i.obj_id,
                    kid = i.id,
                )
                new.dtime = i.date_time
                new.save()
    
    for_del = []

    for j in votes_dict.values():
        if j['user']:
            try:
                FilmsVotes.objects.get_or_create(
                    kid = j['film'],
                    user = j['user'],
                    defaults = {
                        'kid': j['film'],
                        'user': j['user'],
                        'rate_1': j['obj'].rate_1,
                        'rate_2': j['obj'].rate_2,
                        'rate_3': j['obj'].rate_3,
                    })
            except FilmsVotes.MultipleObjectsReturned:
                fv_obj = None
                for j in FilmsVotes.objects.filter(kid=j['film'], user=j['user']).order_by('id'):
                    if fv_obj:
                        for_del.append(j.id)
                    else:
                        fv_obj = j


    FilmsVotes.objects.filter(pk__in=for_del).delete()

    cron_success('import', source.dump, 'reviews_and_rates', 'Рецензии и оценки')


@timer
def kinoafisha_news_import():
    
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    exists = list(News.objects.exclude(kid=None).filter(visible=True, reader_type__in=('17','20')).values_list('kid', flat=True))

    reviews = AfishaNews.objects.using('afisha').only('name', 'content', 'date_time').filter(type__in=(0, 1)).exclude(pk__in=exists).order_by('date_time')

    current_site = DjangoSite.objects.get(domain='kinoinfo.ru')
    
    date_tmp = datetime.datetime.now()
    for i in reviews:
    
        if i.date_time:
            date_tmp = i.date_time
        
        if i.type == 0:
            reader_type = '17'
        else:
            reader_type = '20'
        
        new = News.objects.create(
            title = i.name, 
            autor = None,
            site = current_site,
            subdomain = 0,
            text = i.content,
            visible = True,
            reader_type = reader_type,
            autor_nick = 0,
            kid = i.id,
        )
        new.dtime = date_tmp
        new.save()

    cron_success('import', source.dump, 'news', 'Новости')



@timer
def kinoafisha_opinions_import():
    '''
    Импорт отзывов из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    
    current_site = DjangoSite.objects.get(domain='kinoinfo.ru')
    
    exists_ids = list(NewsFilms.objects.filter(source_obj=source).values_list('source_id', flat=True))

    profiles_exist = []
    
    opinions = GGOpinion.objects.using('afisha').select_related('user_id').only('date', 'text', 'nick', 'user_id').filter(type_obj=103, deleted=False).exclude(pk__in=exists_ids)
    
    users_kids = {}
    
    for i in opinions:
        
        if i.user_id:
            user_email = i.user_id.email.strip()
            nickname = i.user_id.nickname.strip()
            profile = users_kids.get(i.user_id)
        else:
            user_email = i.email.strip()
            nickname = i.nick.strip()
            profile = None

        if not user_email:
            user_email = ''
        if not nickname:
            nickname = 'Аноним'

        if not profile:
            profile, code = create_by_email(user_email.encode('utf-8'))
            if i.user_id:
                users_kids[i.user_id] = profile
        
        if profile.id not in profiles_exist:
            user_obj = profile.user
            if not user_obj.first_name:
                user_obj.first_name = nickname
                user_obj.save()
            profiles_exist.append(profile.id)
        
        text = i.text.split('<spr>')[1]
        
        topic = News.objects.create(
            title = '',
            text = text,
            visible = True,
            autor = profile,
            autor_nick = 1,
            extra = i.obj_id, 
            reader_type = '8', 
            site = current_site, 
            subdomain = 0,
            parent = None,
            branch = None,
            kid = i.id,
        )

        topic.dtime = i.date
        topic.save()

        NewsFilms.objects.create(
            kid = i.obj_id,
            message = topic,
            source_id = i.id,
            source_obj = source,
        )
        
    cron_success('import', source.dump, 'opinions', 'Отзывы')


@timer
def kinoafisha_genres_import():
    '''
    Импорт жанров из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    genres = AfishaGenre.objects.using('afisha').all()
    for i in genres:
        genre, created = Genre.objects.get_or_create(
            name = i.name,
            defaults = {
                'name': i.name,
                'name_en': i.name_en,
                'kid': i.id,
            })
    cron_success('import', source.dump, 'genre', 'Жанры')

@timer
def kinoafisha_statusact_and_actions():
    '''
    Импорт статусов и типов персон из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    statusact = PersonsStatusAct.objects.using('afisha').all().order_by('id')
    for i in statusact:
        st, created_st = StatusAct.objects.get_or_create(name=i.status_act, defaults={'name': i.status_act})

    actions = PersonsTypeAct.objects.using('afisha').all().order_by('id')
    for i in actions:
        act, created_act = Action.objects.get_or_create(name=i.type_act, defaults={'name': i.type_act})

    cron_success('import', source.dump, 'status_act_and_type', 'Статусы и типы персон')

@timer
def kinoafisha_city_import():
    '''
    Импорт городов из kinoafisha.ru
    '''
    from release_parser.kinobit_cmc import get_source_data

    cities = AfishaCity.objects.using('afisha').select_related('country').all().distinct('name')

    city_afisha = [i.id for i in cities]
    city = list(City.objects.all().values_list('kid', flat=True))
    unique = list(set(city) - set(city_afisha))
    City.objects.filter(kid__in=unique).delete()

    countries = {}
    for i in cities:
        country = None
        if i.country:
            if countries.get(i.country.name):
                country = countries.get(i.country.name)
            else:
                try:
                    country = Country.objects.get(name=i.country.name)
                    countries[i.country.name] = country
                except Country.DoesNotExist:
                    country = None
                    countries[i.country.name] = country

        city, created_c = City.objects.get_or_create(kid=i.id, defaults={'kid': i.id})
        if country:
            if not city.country or city.country != country:
                city.country = country
                city.save()

        try:
            low_name = low(del_separator(i.name))
        except UnicodeDecodeError:
            low_name = low(del_separator(i.name.encode('utf-8')))

        names = [
            {'name': i.name, 'status': 1},
            {'name': low_name, 'status': 2}
        ]
        for n in names:
            city_name, created_n = NameCity.objects.get_or_create(name=n['name'], status=n['status'], defaults={'name': n['name'], 'status': n['status']})
            # если импортируется новый город, то добавляю ему названия
            if created_c:
                city.name.add(city_name)
            # если такой город уже есть
            else:
                # и такого названия у него нет
                if city_name not in city.name.all():
                    # и если это название основное и отличается от текущего
                    for j in city.name.all():
                        if n['status'] == 1 and j.status == 1 and j.name != n['name']:
                            city.name.remove(j)
                            city.name.add(city_name)

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    SourceCities.objects.filter(source_id__in=unique, source_obj=source).delete()

    cities_list = get_source_data(source, 'city', 'list')

    kinoinfo_cities = {}
    for i in City.objects.all():
        kinoinfo_cities[i.kid] = i

    for i in cities:
        if str(i.id) not in cities_list:
            city_obj = kinoinfo_cities.get(i.id)
            if city_obj:
                SourceCities.objects.create(
                    source_id = i.id,
                    source_obj = source,
                    city = city_obj,
                    name = i.name,
                )
    cron_success('import', source.dump, 'city', 'Города')



@timer
def kinoafisha_metro_import():
    '''
    Импорт метро из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    ids = list(Metro.objects.filter(kid__gt=0).values_list('kid', flat=True))
    for i in AfishaMetro.objects.using('afisha').exclude(id__in=ids).all():
        Metro.objects.create(kid=i.id, name=i.name)
    cron_success('import', source.dump, 'metro', 'Метро')


@timer
def kinoafisha_cinemacircuit_import():
    '''
    Импорт сети кинотеатров из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    ids = list(CinemaCircuit.objects.filter(kid__gt=0).values_list('kid', flat=True))
    for i in Seti.objects.using('afisha').exclude(id__in=ids).all():
        CinemaCircuit.objects.create(kid=i.id, name=i.name)
    cron_success('import', source.dump, 'cinemacircuit', 'Сети кинотеатров')


@timer
def kinoafisha_distributor_import():
    '''
    Импорт дистрибьюторов из kinoafisha.ru
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    # выборка дистрибьюторов
    distributors = Prokat.objects.using('afisha').select_related('country').all()
    distributors_usa = Company.objects.using('afisha').all()

    distr_afisha = [i.id for i in distributors]
    distr_k = list(Distributors.objects.filter(usa=False).values_list('kid', flat=True))
    unique = list(set(distr_k) - set(distr_afisha))
    Distributors.objects.filter(kid__in=unique, usa=False).delete()

    countries_list = list(Prokat.objects.using('afisha').all().exclude(country=0).distinct('country').values_list('country_id', flat=True))

    kinoinfo_distr = Distributors.objects.all()
    kinoinfo_distr_dict = {}
    kinoinfo_distr_dict_usa = {}
    for i in kinoinfo_distr:
        if i.usa:
            kinoinfo_distr_dict_usa[i.kid] = i
        else:
            kinoinfo_distr_dict[i.kid] = i

    # выборка стран дистрибьюторов, для связи объекта дистрибьютор с объектом страна
    usa = Country.objects.get(name='США')

    countries = Country.objects.filter(kid__in=countries_list)
    country_obj = {}
    for i in countries:
        country_obj[i.kid] = i

    data = [{'d': distributors, 'usa': False}, {'d': distributors_usa, 'usa': True}]

    for distributor in data:
        for i in distributor['d']:

            # очистка названия дистр. от спец.символов
            try:
                slug = low(del_separator(i.name))
            except UnicodeDecodeError:
                slug = low(del_separator(i.name.encode('utf-8')))

            names = [
                {'name': i.name, 'status': 1},
                {'name': slug, 'status': 2},
            ]
            if distributor['usa']:
                country = usa
                distr = kinoinfo_distr_dict_usa.get(i.id)
            else:
                country_id = i.country_id if i.country_id else 2
                country = country_obj.get(country_id)
                distr = kinoinfo_distr_dict.get(i.id)

            if not distr:
                # создаю дистр. если он не существует
                distr = Distributors.objects.create(kid=i.id, country=country, usa=distributor['usa'])
                created_d = True
            else:
                created_d = False
                if distr.country != country:
                    distr.country = country
                    distr.save()

            for n in names:
                name_obj, created = NameDistributors.objects.get_or_create(
                    name = n['name'],
                    status = n['status'],
                    defaults = {
                        'name': n['name'],
                        'status': n['status']
                    })
                if created_d:
                    distr.name.add(name_obj)
                else:
                    # и такого названия у него нет
                    if name_obj not in distr.name.all():
                        # и если это название основное и отличается от текущего
                        for j in distr.name.all():
                            if n['status'] == 1 and j.status == 1 and j.name.encode('utf-8') != n['name']:
                                distr.name.remove(j)
                                distr.name.add(name_obj)

    cron_success('import', source.dump, 'distributor', 'Дистрибьюторы')


@timer
def kinoafisha_cinema_import():
    from release_parser.kinobit_cmc import get_source_data

    cinema = Movie.objects.using('afisha').select_related('city').all()

    cinema_afisha = [i.id for i in cinema]
    cinema_k = list(Cinema.objects.all().values_list('code', flat=True))
    unique = list(set(cinema_k) - set(cinema_afisha))
    Cinema.objects.filter(code__in=unique).delete()

    for i in cinema:
        try:
            city = City.objects.get(kid=i.city_id)
            obj, created_c = Cinema.objects.get_or_create(code=i.id, defaults={'code': i.id, 'city': city})

            try:
                slug = low(del_separator(i.name))
            except UnicodeDecodeError:
                slug = low(del_separator(i.name.encode('utf-8')))

            names = [
                {'name': i.name.encode('utf-8'), 'status': 1},
                {'name': slug, 'status': 2}
            ]

            if not created_c:
                if obj.city != city:
                    obj.city = city
                    obj.save()

            for n in names:
                name_obj, created = NameCinema.objects.get_or_create(name=n['name'], status=n['status'], defaults={'name': n['name'], 'status': n['status']})
                if created_c:
                    obj.name.add(name_obj)
                else:
                    # и такого названия у него нет
                    if name_obj not in obj.name.all():
                        # и если это название основное и отличается от текущего
                        for j in obj.name.all():
                            if n['status'] == 1 and j.status == 1 and j.name.encode('utf-8') != n['name']:
                                obj.name.remove(j)
                                obj.name.add(name_obj)
        except City.DoesNotExist: pass

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    SourceCinemas.objects.filter(source_id__in=unique, source_obj=source).delete()

    cities_dict = get_source_data(source, 'city', 'dict')

    cinemas_list = get_source_data(source, 'cinema', 'list')

    kinoinfo_cinemas = {}
    for i in Cinema.objects.select_related('city').all():
        kinoinfo_cinemas[i.code] = i

    for i in cinema:
        if str(i.id) not in cinemas_list:
            cinema_obj = kinoinfo_cinemas.get(i.id)
            if cinema_obj:
                city_obj = cities_dict.get(str(i.city_id))
                if city_obj:
                    SourceCinemas.objects.create(
                        source_id = i.id,
                        source_obj = source,
                        city = city_obj,
                        cinema = cinema_obj,
                        name = i.name,
                    )
    cron_success('import', source.dump, 'cinema', 'Кинотеатры')



@timer
def kinoafisha_cinema2_import():
    from base.func import org_build_create, get_org_street
    
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    REG_PHONE = re.compile(r'\+?\s?[\(\d+\)]?\s?[\d+\-?]')

    exists = list(Organization.objects.filter(kid__gte=1).values_list('kid', flat=True))

    cinema = Movie.objects.using('afisha').exclude(id__in=exists)

    cities = {}
    for i in City.objects.filter(kid__gte=1):
        cities[i.kid] = i

    metro_objs = {}
    for i in Metro.objects.filter(kid__gte=1):
        metro_objs[i.kid] = i

    org_streets_dict = {}
    for i in Street.objects.all():
        org_streets_dict[i.slug.encode('utf-8')] = i

    phones_objs = {}
    for i in OrganizationPhones.objects.filter(organization__source_obj=source):
        phones_objs[i.phone] = i

    circuits = {}
    for i in CinemaCircuit.objects.filter(kid__gte=1):
        circuits[i.kid] = i


    for i in cinema:
        city = cities.get(i.city_id)
        metro = metro_objs.get(i.metro_id)
        circuit = circuits.get(i.set_field_id)
        
        phones = i.phones.split(',')
        sites = i.site.split('#')
        contact_persons = [i.kontakt1.strip(), i.kontakt2.strip()]
        
        emails = i.mail.strip()
        index = i.ind.strip() if i.ind else None
        title = i.name.strip()
        source_id = i.id
        address_txt = i.address.strip()
        fax = i.fax.strip()
        director = i.director.strip()
        cinema_path = i.path.strip()
        techinfo = i.techinfo.strip()
        comment = i.comment.strip()
        workingtime = i.workingtime.strip()
        tech_comment = i.tech_comment.strip()
        longitude = i.longitude
        latitude = i.latitude
        
        
        # АДРЕС
        if city:
            if address_txt:
              
                street_name, street_type, house = get_org_street(address_txt)

                if street_type:
                    if street_name:
                        street_slug = low(del_separator(street_name))
                        street_obj = org_streets_dict.get(street_slug)
                        if not street_obj:
                            street_obj = Street.objects.create(name=street_name, slug=street_slug, type=street_type)
                            org_streets_dict[street_slug] = street_obj
                    else:
                        street_obj = None
                        house = None
                        
                    building_obj = org_build_create(house, city, street_obj, cinema_path)
            else:
                building_obj = org_build_create(None, city, None)
                street_type = True
        else:
            building_obj = None
        

        # ТЕЛЕФОНЫ
        phones_list = []
        for ph in phones:
            phone = REG_PHONE.findall(ph)
            if phone:
                phone = ''.join(phone)
                phone = phone.decode('utf-8').replace(' -','').strip()
                phone_info = ph.replace(phone,'').replace('- ','').strip()
                phone_obj = phones_objs.get(phone)
                if not phone_obj:
                    phone_obj = OrganizationPhones.objects.create(phone=phone, note=phone_info)
                    phones_objs[phone] = phone_obj
                phones_list.append(phone_obj)
        
        
        
        
        # САЙТ
        site = None
        for i in sites:
            if i.strip() and u'http' in i:
                site = i.strip()
        
        # ОПИСАНИЕ
        note = ''
        if comment:
            note += comment
        if workingtime:
            if note:
               note += u'<br /><br />'
            note += workingtime
        if fax:
            if note:
               note += u'<br /><br />'
            note += u'Факс %s' % fax
        if techinfo:
            if note:
               note += u'<br /><br />'
            note += techinfo
        
        
        # ЭКСТРА
        extra = ''
        if director:
            extra += u'Директор: %s' % director
        for ind, i in enumerate(contact_persons):
            if i:
                ind += 1
                if extra:
                    extra += u'<br />'
                extra += u'Контакт %s: %s' % (ind, i)
        
        uni = unidecode(title)
        uni = re.findall(ur'[a-z0-9]+', low(uni))
        uni = '-'.join(uni) if uni else ''
        
        org_obj = Organization.objects.create(
            name = title,
            site = site,
            email = emails,
            note = note,
            source_obj = source,
            source_id = source_id,
            kid = source_id,
            extra = extra,
            domain_id = 1,
            circuit = circuit,
        )
        
        org_obj.uni_slug = '%s-%s' % (uni, org_obj.id)
        org_obj.save()
        
        for j in phones_list:
            org_obj.phones.add(j)

        if building_obj:
            org_obj.buildings.add(building_obj)
        
        '''
        url = 'http://www.kinoafisha.ru/logo_cinemas/%s-000_small.jpg' % org_obj.id
        resp, content = httplib2.Http().request(url, method='GET')
        if content:
            folder = request.user.get_profile().folder
            file_name = '%s_%s.jpg' % (request.user.id, md5_string_generate(request.user.id))
            f = open('%s/%s' % (settings.AVATARS, file_name), 'wb')
            f.write(content)
            f.close()
        '''

    cron_success('import', source.dump, 'cinemanew', 'Кинотеатры new')



@timer
def kinoafisha_cinema_rates_import():
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    orgs = {}
    for i in Organization.objects.only('kid').filter(kid__gt=1):
        orgs[i.kid] = i

    rates = {}
    for i in AfishaCinemaRate.objects.select_related('organization').filter(organization__kid__gte=1):
        rates[i.organization.kid] = i

    for i in MovieExtData.objects.using('afisha').all():
        rate = rates.get(i.id)
        if rate:
            if i.vnum != rate.vnum:
                rate.rate1 = i.rate1
                rate.rate2 = i.rate2
                rate.rate3 = i.rate3
                rate.rate = i.rate
                rate.vnum = i.vnum
                rate.save()
        else:
            org = orgs.get(i.id)
            if org:
                AfishaCinemaRate.objects.create(
                    organization = org,
                    rate1 = i.rate1,
                    rate2 = i.rate2,
                    rate3 = i.rate3,
                    rate = i.rate,
                    vnum = i.vnum,
                )

    cron_success('import', source.dump, 'cinemarates', 'Оцнки для кинотеатров')


@timer
def kinoafisha_films_import():
    from release_parser.kinobit_cmc import get_source_data

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    films = get_source_data(source, 'film', 'list')
    films = list(map((lambda x: long(x)), films))
    
    # Очищаем удаленные с киноафиши
    all_films_afisha = list(Film.objects.using('afisha').all().values_list('id', flat=True))
        
    ki_films = list(Films.objects.exclude(kid=None).values_list('kid', flat=True))
    for_del = list(set(ki_films) - set(all_films_afisha))
    Films.objects.filter(kid__in=for_del).delete()
    ki_films = []

    for_del = list(set(films) - set(all_films_afisha))
    SourceFilms.objects.filter(kid__in=for_del).delete()
    all_films_afisha, for_del = ([], [])
    
    
    film = FilmsName.objects.using('afisha').select_related('film_id').exclude(film_id__id__in=films).filter(status=1, type=2)
    
    for i in film:
        if str(i.film_id_id) not in films:
            imdb = get_imdb_id(i.film_id.idalldvd) if i.film_id.idalldvd else None
            year = i.film_id.year if i.film_id.year else None
            SourceFilms.objects.create(
                source_id = i.film_id_id,
                source_obj = source,
                name = i.name,
                kid = i.film_id_id,
                year = year,
                imdb = imdb,
            )
            films.append(i.film_id_id)
    cron_success('import', source.dump, 'film', 'Фильмы')

@timer
def kinoafisha_films_import_v2():
    films = set(list(Films.objects.exclude(kid=None).values_list('kid', flat=True)))
    film = Film.objects.using('afisha').only('id', 'year', 'idalldvd').exclude(id__in=films)
    for i in film:
        if i.year:
            Films.objects.create(
                year = i.year,
                imdb_id = i.idalldvd,
                kid = i.id
            )
@timer
def kinoafisha_persons_rel():
    films = Films.objects.only('creators', 'id').exclude(kid=None)
    
    films_dict = {}
    for i in films:
        films_dict[i.kid] = i
    
    rel = PersonsRelationFilms.objects.using('afisha').filter(film_id__id__in=films_dict.keys())
    persons_kids = set([i.person_id_id for i in rel])
    
    persons = Person.objects.filter(kid__in=persons_kids)
    persons_dict = {}
    for i in persons:
        persons_dict[i.kid] = i
        
    for i in rel:
        person_obj = persons_dict.get(int(i.person_id_id))
        film_obj = films_dict.get(i.film_id_id)
        if film_obj and person_obj:
            rel_obj, rel_created = RelationFP.objects.get_or_create(
                person = person_obj,
                status_act_id = i.status_act_id_id,
                action_id = i.type_act_id_id,
                films = film_obj,
                defaults = {
                    'person': person_obj,
                    'status_act_id': i.status_act_id_id,
                    'action_id': i.type_act_id_id,
                    'films': film_obj,
            })
            

@timer
def kinoafisha_hall_import():
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    #source_halls = {}
    #for i in SourceHalls.objects.filter(source_obj=source):
    #    source_halls[int(i.source_id)] = i

    source_cinemas = {}
    for i in SourceCinemas.objects.filter(source_obj=source):
        source_cinemas[int(i.source_id)] = i

    halls = AfishaHalls.objects.using('afisha').select_related('id_name').all()
    for i in halls:
        try:
            cinema = Cinema.objects.get(code=i.movie_id)
            obj, created = Hall.objects.get_or_create(kid=i.id, defaults={'kid': i.id, 'cinema': cinema})

            try:
                slug = low(del_separator(i.id_name.name))
            except UnicodeDecodeError:
                slug = low(del_separator(i.id_name.name.encode('utf-8')))

            names = [
                {'name': i.id_name.name, 'status': 1},
                {'name': slug, 'status': 2}
            ]
            for n in names:
                name_obj, created = NameHall.objects.get_or_create(name=n['name'], status=n['status'], defaults={'name': n['name'], 'status': n['status']})
                if name_obj not in obj.name.all():
                    obj.name.add(name_obj)
            '''
            source_hall = source_halls.get(i.id)
            if not source_hall:
                source_cinema = source_cinemas.get(i.movie_id)
                if source_cinema:
                    SourceHalls.objects.create(
                        source_id = i.id,
                        source_obj = source,
                        kid = i.id,
                        name = i.id_name.name,
                        name_alter = slug,
                        cinema = source_cinema,
                    )
            '''
        except Cinema.DoesNotExist: pass
    cron_success('import', source.dump, 'hall', 'Залы')
    
    

@timer
def kinoafisha_schedules_import():
    from release_parser.kinobit_cmc import get_source_data

    today = datetime.date.today()

    sessions = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__movie_id__city', 'schedule_id__film_id').filter(schedule_id__date_from__gte=today).filter(schedule_id__movie_id__city__country__name='Украина')

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    #source_halls = {}
    #for i in SourceHalls.objects.filter(source_obj=source):
    #    source_halls[int(i.source_id)] = i

    films = get_source_data(source, 'film', 'dict')
    cinemas = get_source_data(source, 'cinema', 'dict')
    schedules = get_source_data(source, 'schedule', 'list')

    for i in sessions:
        cinema_obj = cinemas.get(str(i.schedule_id.movie_id_id))
        if cinema_obj:
            film_obj = films.get(str(i.schedule_id.film_id_id))
            if film_obj:
                t = i.session_list_id.time
                delta = i.schedule_id.date_to - i.schedule_id.date_from
                for day in range(delta.days + 1):
                    d = i.schedule_id.date_from + datetime.timedelta(days=day)
                    dtime = datetime.datetime(d.year, d.month, d.day, t.hour, t.minute)

                    sch_id = '%s%s%s%s' % (dtime, cinema_obj.id, cinema_obj.city_id, film_obj.id)
                    sch_id = sch_id.replace(' ', '').decode('utf-8')

                    #hall_obj = source_halls.get(i.schedule_id.hall_id_id)

                    if sch_id not in schedules:

                        SourceSchedules.objects.create(
                            source_id = sch_id,
                            source_obj = source,
                            film = film_obj,
                            cinema = cinema_obj,
                            dtime = dtime,
                            #hall_obj = hall_obj,
                        )
                        schedules.append(sch_id)

                    #elif hall_obj:
                    #    SourceSchedules.objects.filter(source_id=sch_id).update(hall_obj=hall_obj)

    cron_success('import', source.dump, 'schedule', 'Сеансы')


@timer
def kinoinfo_ua_releases_import():
    '''
    Агрегация UA релизов на киноинфо
    '''
    source = ImportSources.objects.get(url='http://kino-teatr.ua/')

    exists = UkrainianReleases.objects.all().values_list('kid', flat=True)

    releases = SourceReleases.objects.filter(source_obj=source).exclude(Q(film__kid__in=exists) | Q(film__kid=None)).values('release', 'film__kid')

    created = []
    for i in releases:
        if i['film__kid'] not in created:
            UkrainianReleases.objects.create(
                kid = i['film__kid'],
                release = i['release'],
            )
            created.append(i['film__kid'])



@timer
def kinoafisha_schedules_booking_import():
    from release_parser.kinobit_cmc import get_source_data

    cinemas = list(Cinema.objects.filter(bookingsettings__pk__gt=0).distinct('pk').values_list('code', flat=True))
    
    today = datetime.date.today()

    sessions = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__movie_id__city', 'schedule_id__film_id').filter(schedule_id__date_from__gte=today, schedule_id__movie_id__id__in=cinemas)

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    halls_ids = set([i.schedule_id.hall_id_id for i in sessions])

    halls = {}
    #for i in Hall.objects.filter(kid__in=halls_ids):
    for i in Hall.objects.filter(cinema__code__in=cinemas):
        halls[i.kid] = i

    films = get_source_data(source, 'film', 'dict')
    
    schedules = list(BookingSchedules.objects.filter(hall__cinema__code__in=cinemas, dtime__gte=today).values_list('unique', flat=True))

    for i in sessions:
        
        hall_obj = halls.get(i.schedule_id.hall_id_id)

        if hall_obj:
            
            film_obj = films.get(str(i.schedule_id.film_id_id))
            if film_obj:

                t = i.session_list_id.time
                delta = i.schedule_id.date_to - i.schedule_id.date_from
                for day in range(delta.days + 1):
                    d = i.schedule_id.date_from + datetime.timedelta(days=day)
                    dtime = datetime.datetime(d.year, d.month, d.day, t.hour, t.minute)

                    sch_id = '%s%s%s' % (dtime, hall_obj.id, film_obj.id)
                    sch_id = sch_id.replace(' ', '').decode('utf-8')

                    if sch_id not in schedules:

                        obj = BookingSchedules.objects.create(
                            unique = sch_id,
                            hall = hall_obj,
                            dtime = dtime,
                        )
                        obj.films.add(film_obj)

                        schedules.append(sch_id)

    cron_success('import', source.dump, 'schedule_booking', 'Сеансы букинг')
    


@timer
def kinoafisha_persons_import():
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    afisha_countries = list(AfishaPersons.objects.using('afisha').exclude(country=None).values_list('country_id', flat=True).distinct('country'))

    countries = Country.objects.filter(kid__in=afisha_countries)
    countries_dict = {}
    for i in countries:
        countries_dict[i.kid] = i

    afisha_persons = AfishaPersonsName.objects.using('afisha').select_related('person_id').filter(flag__in=(1, 2))

    persons = Person.objects.exclude(kid=None)
    persons_dict = {}
    for i in persons:
        persons_dict[i.kid] = i

    languages = Language.objects.filter(name__in=('Русский', 'Английский'))
    lang_dict = {}
    for i in languages:
        lang_dict[i.name] = i

    for i in afisha_persons:
        name = i.name.encode('utf-8').strip()
        slug = low(del_separator(name))
        if i.flag == 1:
            lang = lang_dict.get(u'Русский')
        elif i.flag == 2:
            lang = lang_dict.get(u'Английский')

        names = [
            {'name': name, 'status': 1},
            {'name': slug, 'status': 2}
        ]

        if i.person_id.country_id:
            country = countries_dict.get(i.person_id.country_id)
        else:
            country = None

        person = persons_dict.get(i.person_id_id)
        
        birthday = None
        if i.person_id.birth_year:
            birthday = datetime.date(int(i.person_id.birth_year), int(i.person_id.birth_mounth), int(i.person_id.birth_day))
                
        if person:
            edit = False
            if person.born != birthday:
                person.born = birthday
                edit = True
            if person.country != country:
                person.country = country
                edit = True
            if person.male != i.person_id.male:
                person.male = i.person_id.male
                edit = True
            if person.iid != i.person_id.imdb:
                person.iid = i.person_id.imdb
                edit = True
            
            if edit:
                person.save()
        else:
            birthday = None
            if i.person_id.birth_year:
                birthday = datetime.date(int(i.person_id.birth_year), int(i.person_id.birth_mounth), int(i.person_id.birth_day))

            person = Person.objects.create(
                country = country,
                kid = i.person_id_id,
                iid = i.person_id.imdb,
                male = i.person_id.male,
                born = birthday,
            )
            persons_dict[i.person_id_id] = person

        for name in names:
            name_obj, name_created = NamePerson.objects.get_or_create(
                name = name['name'],
                status = name['status'],
                language = lang,
                defaults = {
                    'name': name['name'],
                    'status': name['status'],
                    'language': lang,
                })

            if name_obj not in person.name.all():
                person.name.add(name_obj)
    cron_success('import', source.dump, 'person', 'Персоны')


def distributor_identification(name, slug):
    '''
    Поиск дистрибьюторов по slug, alt, name
    '''
    try:
        distr = Distributors.objects.get(name__name=slug, name__status=2)
        return distr, 2
    except Distributors.DoesNotExist:
        try:
            distr = Distributors.objects.get(name__name=name, name__status=1)
            return distr, 1
        except Distributors.DoesNotExist:
            try:
                distr = Distributors.objects.get(name__name=name, name__status=0)
                return distr, 0
            except Distributors.DoesNotExist:
                return False, False


@timer
def kinoafisha_budget_import():
    '''
    Парсер бюджетов фильмов из киноафиши
    '''
    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')

    REG_BUDGET = re.compile(r'бюджет\:?\s\d+\s?.+[\$|долларов|fr|ffr|евро|крон|стерл|стерлингов|йен|гривен]')

    exist_budgets = list(FilmsBudget.objects.all().values_list('kid', flat=True))

    films = Film.objects.using('afisha').only('comment').exclude(Q(id__in=exist_budgets) | Q(comment=None) | Q(comment='')).filter(comment__icontains='бюджет')

    for i in films:
        comment = low(i.comment.encode('utf-8'))
        result = REG_BUDGET.findall(comment)
        if result:
            res = ''.join(result).replace('бюджет:', '').replace('бюджет', '')
            res = '%s$' % res.split('$,')[0] if len(res.split('$,')) > 1 else res
            res = '%s$' % res.split('$.')[0] if len(res.split('$.')) > 1 else res
            res = '%s$' % res.split('долларов,')[0] if len(res.split('долларов,')) > 1 else res
            res = '%s$' % res.split('долларов.')[0] if len(res.split('долларов.')) > 1 else res
            res = res.replace('долларов', '$')
            res = '%sfr' % res.split('ffr,')[0] if len(res.split('ffr,')) > 1 else res
            res = '%sfr' % res.split('ffr.')[0] if len(res.split('ffr.')) > 1 else res
            res = '%sfr' % res.split('fr,')[0] if len(res.split('fr,')) > 1 else res
            res = '%sfr' % res.split('fr.')[0] if len(res.split('fr.')) > 1 else res
            res = '%sевро' % res.split('евро,')[0] if len(res.split('евро,')) > 1 else res
            res = '%sевро' % res.split('евро.')[0] if len(res.split('евро.')) > 1 else res
            res = '%s крон' % res.split(' крон,')[0] if len(res.split(' крон,')) > 1 else res
            res = '%s крон' % res.split(' крон.')[0] if len(res.split(' крон.')) > 1 else res
            res = '%s стерлингов' % res.split(' стерл.')[0] if len(res.split(' стерл.')) > 1 else res
            res = '%s стерлингов' % res.split('стерлингов.')[0] if len(res.split('стерлингов.')) > 1 else res
            res = '%s стерлингов' % res.split('стерлингов,')[0] if len(res.split('стерлингов,')) > 1 else res
            res = '%sйен' % res.split('йен,')[0] if len(res.split('йен,')) > 1 else res
            res = '%sйен' % res.split('йен.')[0] if len(res.split('йен.')) > 1 else res
            res = '%sгривен' % res.split('гривен,')[0] if len(res.split('гривен,')) > 1 else res
            res = '%sгривен' % res.split('гривен.')[0] if len(res.split('гривен.')) > 1 else res

            res = res.strip()
            
            if isinstance(res, str):
                FilmsBudget.objects.create(
                    kid = i.id,
                    budget = res
                )

    cron_success('import', source.dump, 'budgets', 'Беджеты фильмов')

#############################################


@only_superuser
@never_cache
def distributor_add(request):
    '''
    Форма добавления новых дистрибьюторов
    '''
    if request.POST:
        form = DistributorsForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.iid = form.cleaned_data['iid'] if form.cleaned_data['iid'] else None
            f.kid = form.cleaned_data['kid'] if form.cleaned_data['kid'] else None
            form.save()
            return HttpResponseRedirect(reverse("distributor_list"))
    else:
        form = DistributorsForm()
    return render_to_response('release_parser/distributor_form.html', {'form': form}, context_instance=RequestContext(request))

@only_superuser
@never_cache
def distributor_edit(request, id):
    '''
    Форма редактирования дистрибьюторов
    '''
    org = get_object_or_404(Distributors, pk=id)
    if request.POST:
        form = DistributorsForm(request.POST)
        if form.is_valid():
            org.iid = form.cleaned_data['iid'] if form.cleaned_data['iid'] else None
            org.kid = form.cleaned_data['kid'] if form.cleaned_data['kid'] else None
            org.country = form.cleaned_data['country']
            org.save()
            return HttpResponseRedirect(reverse("distributor_edit", kwargs={'id': id}))
    else:
        form = DistributorsForm(
            initial={
                'iid': org.iid,
                'kid': org.kid,
                'country': org.country,
            }
        )
    return render_to_response('release_parser/distributor_form.html', {'form': form, 'org': org}, context_instance=RequestContext(request))

@only_superuser
@never_cache
def distributor_delete(request, id):
    '''
    Удаление дистрибьюторов
    '''
    org = get_object_or_404(Distributors, pk=id)
    if request.method == "POST":
        org.delete()
        return HttpResponseRedirect(reverse("distributor_list"))
    else:
        return HttpResponseRedirect(reverse("distributor_edit", kwargs={'id': id}))

@only_superuser
@never_cache
def distributor_delete_name(request, distr_id, name_id):
    '''
    Удаление связи между дистрибьютором и названием
    '''
    distr = get_object_or_404(Distributors, pk=distr_id)
    name = get_object_or_404(NameDistributors, pk=name_id)
    distr.name.remove(name)
    return HttpResponseRedirect(reverse("distributor_edit", kwargs={'id': distr_id}))

@only_superuser
@never_cache
def org_name_list(request):
    '''
    Список названий дистрибьюторов
    '''
    names = NameDistributors.objects.all().order_by('pk')
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, names, 15)

    return render_to_response('release_parser/distributor_list.html', {'status': 'names', 'content': names, 'p': p, 'page': page}, context_instance=RequestContext(request))

@only_superuser
@never_cache
def add_org_name(request):
    '''
    Добавление нового названия дистрибьютора
    '''
    if request.POST:
        form = NameDistributorsForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("org_name_list"))
    else:
        form = NameDistributorsForm()
    return render_to_response('release_parser/org_name_form.html', {'form': form}, context_instance=RequestContext(request))

@only_superuser
@never_cache
def edit_org_name(request, id):
    '''
    Редактирование названия дистрибьютора
    '''
    name = get_object_or_404(NameDistributors, pk=id)
    if request.POST:
        form = NameDistributorsForm(request.POST)
        if form.is_valid():
            name.status = form.cleaned_data['status']
            name.language = form.cleaned_data['language']
            name.name = form.cleaned_data['name']
            name.save()
            return HttpResponseRedirect(reverse("edit_org_name", kwargs={'id': id}))
    else:
        form = NameDistributorsForm(
            initial = {
                'status': name.status,
                'name': name.name,
                'language': name.language,
            }
        )
    return render_to_response('release_parser/org_name_form.html', {'form': form, 'org_name': name}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def delete_org_name(request, id):
    '''
    Удаление названия дистрибьютора
    '''
    name = get_object_or_404(NameDistributors, pk=id)
    if request.method == "POST":
        name.delete()
        return HttpResponseRedirect(reverse("org_name_list"))
    else:
        return HttpResponseRedirect(reverse("edit_org_name", kwargs={'id': id}))


def cinema_identification(cinema_slug, filter1, filter2={}, city=None):
    '''
    Идентификация кинотеатров.
    Принимает очищенное название, один обязательный фильтр, второй необязательный
    Формат фильтра: {'поле_выборки': значение}
    Пример фильтра: {'name__name': name_slug, 'city__id': city_id}
    Если используются два фильтра, то логика выборки - Выбрать по первому фильтру, если ненайденно, то выбрать по второму фильтру
    Возвращает KID кинотеатра или None
    '''
    cinema = Cinema.objects.filter(Q(**filter1) | Q(**filter2)).distinct('pk')
    cinema_count = cinema.count()
    if cinema_count == 1:
        return cinema[0].code
    else:
        try:
            filter = {'name': cinema_slug}
            if city:
                filter['city__kid'] = city
            cinema = NotFoundCinemasRelations.objects.get(**filter)
            return cinema.kid
        except NotFoundCinemasRelations.DoesNotExist:
            return None


def film_identification(name_ru, name_en, filter_distr1, filter_distr2, year=None, ident_type=None, type_params1=None, distr=True, source=None):
    '''
    Идентификация фильмов
    '''
    def list_ident(film_obj):
        list = []
        for i in film_obj:
            if i.prokat1_id and i.prokat1_id != 0 or i.prokat2_id and i.prokat2_id != 0:
                list.append(i)
        if len(list) == 1:
            return list[0].id, ''
        elif len(list) > 1:
            return False, 'Найдено больше 1 фильма'
        elif len(list) == 0:
            if ident_type == 'movie_online':
                return film_obj[0].id, 'Фильм найден, но нет дистриб.на киноафише'
            else:
                if distr:
                    return False, 'Фильм найден, но нет дистриб.на киноафише / %s' % film_obj[0].id
                else:
                    return film_obj[0].id, ''


    filter_year = {'year': year} if year else {}

    filter_name_ru = {'filmsname__slug': name_ru, 'filmsname__status': 1}
    filter_name_en = {'filmsname__slug': name_en, 'filmsname__status': 1} if name_en else {}
    # выбираем фильмы, соответствующие русскому основному очищенному названию или оригинальному основному очищенному
    # и был у найденных был хотя бы один из двух указанных прокатчиков. И количество найденных в Counter

    filter_d1_1 = {}
    filter_d1_2 = {}
    filter_d2_1 = {}
    filter_d2_2 = {}


    if filter_distr1:
        filter_d1_1 = {'prokat1__id': filter_distr1}
        filter_d1_2 = {'prokat2__id': filter_distr1}
    if filter_distr2:
        filter_d2_1 = {'prokat1__id': filter_distr2}
        filter_d2_2 = {'prokat2__id': filter_distr2}

    filter_country_list = {}

    if ident_type == 'movie_online':
         filter_year = year
         filter_country_list = {'country__name': type_params1}

    # сперва проверяю по связям 'ненайденный фильм - фильм киноафиши'
    if not name_ru and name_en:
        name_ru = name_en
        
    try:
        notfound_filter = {'name': name_ru}
        if source:
            notfound_filter['source_obj'] = source

        noffilm = NotFoundFilmsRelations.objects.get(**notfound_filter)
        return noffilm.kid, ''
    # если не нашел, то
    except NotFoundFilmsRelations.DoesNotExist:
        film_obj = Film.objects.using('afisha').select_related('filmsname', 'prokat1', 'prokat2').filter(
            Q(**filter_name_ru) | Q(**filter_name_en)).filter(Q(Q(**filter_d1_1) | Q(**filter_d1_2)) | Q(Q(**filter_d2_1) | Q(**filter_d2_2))
        ).filter(**filter_year).distinct('pk').filter(**filter_country_list)

        counter = film_obj.count()
        # если был найден единственный фильм согласно фильтру
        if counter == 1:
            # тогда добавляю в список найденных и тогда конец и формируем данные для
            # xml: ид фильма, xml-данные, название дистрибьютора и все данные о фильме
            return list_ident(film_obj)
        # если не было найдено ни одного фильма
        elif counter == 0:
            obj = False
            # ищу по альт.названиям киноафиши, если не нахожу, то пробую найти его в
            # альтернативных названиях второй дополнительной таблицы
            # связи названий с названием на Киноафише
            filter_name_ru['filmsname__status'] = 5

            film_obj = Film.objects.using('afisha').select_related('filmsname', 'prokat1', 'prokat2').filter(
                **filter_name_ru).filter(Q(Q(**filter_d1_1) | Q(**filter_d1_2)) | Q(Q(**filter_d2_1) | Q(**filter_d2_2))).filter(**filter_year).distinct('pk').filter(**filter_country_list)

            counter = film_obj.count()
            if counter == 1:
                return list_ident(film_obj)
            elif counter > 1:
                return list_ident(film_obj)
            elif counter == 0:
                try:
                    obj = KIFilmRelations.objects.get(name__name=name_ru)
                except KIFilmRelations.DoesNotExist:
                    # если русскому не нашлось, то
                    if name_en:
                        try:
                            obj = KIFilmRelations.objects.get(name__name=name_en)
                        # если не был найден, то в список ненайденных и конец
                        except KIFilmRelations.DoesNotExist:
                            return False, 'Фильм не найден'
                        # если найдено больше одного, то мы эту ситуацию игнорируем (лучше вывести в лог ошибок)
                        except KIFilmRelations.MultipleObjectsReturned:
                            return False, 'Найдено больше 1 фильма'
                    else:
                        return False, 'Фильм не найден'
                except KIFilmRelations.MultipleObjectsReturned:
                    return False, 'Найдено больше 1 фильма'
                # если найден единственный фильм по названию, то проверяем дистрибьюторов и если да, то пишем xml-данные и конец
                if obj:
                    film_obj = Film.objects.using('afisha').select_related('filmsname', 'prokat1', 'prokat2').filter(
                        pk=obj.kid).filter(Q(Q(**filter_d1_1) | Q(**filter_d1_2)) | Q(Q(**filter_d2_1) | Q(**filter_d2_2))).filter(**filter_year).distinct('pk').filter(**filter_country_list)

                    counter = film_obj.count()
                    if counter:
                        return obj.kid, ''
                    else:
                        return False, 'Фильм не найден'
        elif counter > 1:
            return list_ident(film_obj)


@only_superuser
@never_cache
def film_list_form(request):
    '''
    Обработка ненайденных фильмов с фильтами
    '''
    # список источников
    sources = ImportSources.objects.all()
    # список дистрибьюторов
    distr = Distributors.objects.all()
    # xml файлы для чтения/хранения данных
    xml = open('%s/dump_film_releases.xml' % settings.API_DUMP_PATH, 'r')
    film_releases = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()
    xml_nof = open('%s/dump_kinometro_nof_film.xml' % settings.NOF_DUMP_PATH, 'r')
    film_nof = BeautifulSoup(xml_nof.read(), from_encoding="utf-8")
    xml_nof.close()
    # необходимые переменные
    fil = {}
    f_obj = None
    f_name = None
    f_value = '0'
    source = None
    release = None
    date_release = []
    f = []
    # фильтрация в режиме ручного выбора фильтра
    xml_data_list = [film_releases, film_nof]
    if request.POST:
        # фильт Найденные/Ненайденные
        if 'found' in request.POST and request.POST['found']:
            f_name = 'found'
            f_value = request.POST[f_name]
            xml_data_list = [film_releases] if int(request.POST['found']) == 1 else [film_nof]
        # фильт Дистрибьюторы
        elif 'distr' in request.POST and request.POST['distr'] and request.POST['distr'] != '0':
            f_name = 'distr'
            f_value = request.POST[f_name]
            f_obj = f_name
            distrib = distr.get(pk=request.POST['distr'])
            distrib_list = [i.name for i in distrib.name.all()]
        # фильт Источники
        elif 'source' in request.POST and request.POST['source']:
            f_name = 'source'
            f_value = request.POST[f_name].encode('utf-8')
            source = f_value
        # фильт Дата Релиза
        elif 'release' in request.POST and request.POST['release']:
            f_name = 'release'
            f_value = request.POST[f_name].encode('utf-8')
            release = f_value
    # фильтрация на основе сохраненного ранее выбора фильтра (куки)
    if not f_name:
        if 'filter_name' in request.COOKIES and 'filter_value' in request.COOKIES:
            filter_name = request.COOKIES["filter_name"]
            filter_value = request.COOKIES["filter_value"]
            # фильт Найденные/Ненайденные
            if 'found' in filter_name:
                f_name = filter_name
                f_value = filter_value
                xml_data_list = [film_releases] if int(filter_value) == 1 else [film_nof]
            # фильт Дистрибьюторы
            elif 'distr' in filter_name:
                f_name = filter_name
                f_value = filter_value
                f_obj = f_name
                distrib = distr.get(pk=filter_value)
                distrib_list = [i.name for i in distrib.name.all()]
            # фильт Источники
            if 'source' in filter_name:
                f_name = filter_name
                f_value = filter_value
                source = f_value
            # фильт Дата Релиза
            if 'release' in filter_name:
                f_name = filter_name
                f_value = filter_value
                release = f_value

    if f_value == '0':
        xml_data_list = [film_releases, film_nof]
    try:
        f_v = int(f_value)
    except ValueError:
        if f_name == 'release':
            f_v = datetime.date(int(f_value[:4]), int(f_value[5:7]), int(f_value[8:10]))
        else:
            f_v = f_value.decode('utf-8')

    fil = {'name': f_name, 'value': f_v}

    # функция сбора данных о релизе
    def create_film_dict(i):
        di = {}
        # названия
        name_ru = i['name_ru'].encode('utf-8').replace('&', '&amp;')
        slug_ru = i['slug_ru'].encode('utf-8')
        name = i['name'].encode('utf-8').replace('&', '&amp;')
        slug = i['slug'].encode('utf-8')
        kid = i.get('kid')
        # получение KID
        if kid and kid != 'None':
            try:
                kid = Film.objects.using('afisha').get(pk=kid)
            except Film.DoesNotExist:
                kid = None
        #dtimedate_format = datetime_format(int('20' + i.release['value'][-2:]), int(i.release['value'][-5:-3]), int(i.release['value'][-8:-6]))
        dtimedate_format = datetime.date(int(i.release['value'][:4]), int(i.release['value'][-5:-3]), int(i.release['value'][8:]))
        # данные релиза
        name_ru_s = low(del_separator(del_screen_type(name_ru))) if name_ru != '*' else name_ru
        name_s = low(del_separator(del_screen_type(name))) if name != '*' else name

        di = {
            'name': name_ru_s + ' @ ' + name_s,
            'name2': name_ru + ' / ' + name,
            'release': dtimedate_format,
            'distr': i.distributor['value'],
            'k_obj': kid,
            'copies': i.copies['value'],
            'run': i.runtime['value'],
            }
        url = {'url': 'http://www.kinometro.ru/release/card/id/%s' % i['code']}
        di.update(url)
        f.append(di)
    # формирование данных на основе выбранного фильтра
    for j in xml_data_list:
        for i in j.findAll('film'):
            #dtimedate_format = datetime_format(int(i.release['value'][-2:]), int(i.release['value'][-5:-3]), int(i.release['value'][-8:-6]))
            dtimedate_format = datetime.date(int(i.release['value'][:4]), int(i.release['value'][-5:-3]), int(i.release['value'][8:]))
            if dtimedate_format not in date_release:
                date_release.append(dtimedate_format)
            # если фильтр Дистрибьюторы
            if f_obj == 'distr':
                if i.distributor['value'] in distrib_list:
                    create_film_dict(i)
            else:
                '''
                # если фильтр Источники
                if source == 'ФильмРу':
                    if i['source'].encode('utf-8') == source:
                        create_film_dict(i)
                elif source == 'Кинометро':
                    if i['source'].encode('utf-8') == source:
                        create_film_dict(i)
                elif not source:
                    # если фильтр Дата Релиза
                    if release:
                        if str(dtimedate_format) == release:
                            create_film_dict(i)
                    # если нет фильтра
                    else:
                        create_film_dict(i)
               '''
                if source == 'Кинометро':
                    create_film_dict(i)
                elif not source:
                    # если фильтр Дата Релиза
                    if release:
                        if str(dtimedate_format) == release:
                            create_film_dict(i)
                    # если нет фильтра
                    else:
                        create_film_dict(i)
    # сортировка дат релизов
    #date_release = sorted(set(date_release), key=lambda d: map(int, d.split('-')))
    date_release.sort()

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, sorted(f, key=operator.itemgetter('name')), 15)
    resp = render_to_response('release_parser/film_list_form.html', {'f': f, 'p': p, 'distr': distr, 'sources': sources, 'date_release': date_release, 'fil': fil, 'page': page}, context_instance=RequestContext(request))
    # ставлю куки с данными фильтра
    resp.set_cookie("filter_name", f_name)
    resp.set_cookie("filter_value", f_value)
    return resp

def get_name_ru(fkid, original=False):
    name_ru = None
    name_en = None
    film_name = FilmsName.objects.using('afisha').filter(film_id__id=fkid, status=1)
    for n in film_name:
        if n.type == 2:
            name_ru = n.name
        elif n.type == 1:
            name_en = n.name
    if not name_ru:
        name_ru = name_en
    if original:
        return name_ru, name_en
    return name_ru



@never_cache
def film_list_form_ajax_OLD(request, id=None):
    '''
    График кинорелизов для посетителей (Раздел Скоро)
    '''
    subscribe_me = True if 'subscribe' in request.GET else False
    
    current_site = request.current_site
    current_language = translation.get_language()
    today = datetime.date.today()
    today = today + datetime.timedelta(days=3)

    releases_dict = {}
    releases_dict2 = {}
    if current_site.domain == 'kinoafisha.in.ua':
        releases = SourceReleases.objects.select_related('film').filter(release__gte=today, source_obj__url='http://www.okino.ua/')
        for i in releases:
            if not releases_dict.get(i.film.kid):
                releases_dict[i.film.kid] = i
        releases = SourceReleases.objects.select_related('film').filter(release__gte=today, source_obj__url='http://kino-teatr.ua/')
        for i in releases:
            if not releases_dict.get(i.film.kid):
                releases_dict2[i.film.kid] = i
    else:
        releases = ReleasesRelations.objects.select_related('release').filter(release__release_date__gte=today, rel_double=False, rel_ignore=False)
        for i in releases:
            if not releases_dict.get(i.film_kid):
                releases_dict[i.film_kid] = i

    f_value = None
    week_id = None
    date_release = []

    # фильтрация в режиме ручного выбора фильтра
    if request.POST and request.POST.get('release') and request.POST.get('release_week'):
        # фильтр Дата Релиза
        f_value = request.POST['release']
        week_data = request.POST['release_week'].split('/')
        try:
            week_id = int(week_data[0])
            if f_value != week_data[1]:
                week_id = None
        except ValueError: pass
        
        f_value = datetime.date(int(f_value[:4]), int(f_value[-2:]), 1)

    # фильтрация на основе сохраненного ранее выбора фильтра (в сессии)
    if not f_value:
        if request.session.get('%s_release_filter_data' % current_site.domain):
            session_value = request.session['%s_release_filter_data' % current_site.domain].split(';')
            f_value, week_id = (session_value[0], session_value[1]) if len(session_value) > 1 else (None, None)
            try:
                week_id = int(week_id)
            except (ValueError, TypeError):
                week_id = None
            if f_value:
                try:
                    f_value = datetime.date(int(f_value[:4]), int(f_value[-5:-3]), int(f_value[8:]))
                except ValueError:
                    f_value = None

    weeks_dict = {}
    if current_site.domain == 'kinoafisha.in.ua':
        date_release = [i.release for i in releases_dict.values()]
        date_release2 = [i.release for i in releases_dict2.values()]
        date_release = list(set(date_release + date_release2))
    else:
        date_release = list(set([i.release.release_date for i in releases_dict.values()]))


    date_release.sort()

    date_month_release = {}
    for i in date_release:
        date_key = '%s %s' % (calendar.month_name[i.month], i.year)
        if date_key not in date_month_release:
            weeks = calendar.Calendar(0).monthdayscalendar(i.year, i.month)
            date_month_release[date_key] = {'month': i, 'weeks': weeks}

    date_month_release = dictsort(date_month_release.values(), 'month')

    if not f_value:
        f_value = date_release[0]

    weeks = calendar.Calendar(0).monthdayscalendar(int(str(f_value)[:4]), int(str(f_value)[-5:-3]))

    fnames_dict = {}

    keys = releases_dict.keys() + releases_dict2.keys()

    t = ''
    uk_films = []
    
    if current_site.domain == 'kinoafisha.in.ua':
        t = 'kua_'
        if current_language == 'uk':
            uk_sources = ('http://www.okino.ua/', 'http://kino-teatr.ua/')
            film_name = SourceFilms.objects.select_related('source_obj').filter(source_obj__url__in=uk_sources, kid__in=keys)

            for n in film_name:
                '''
                if n.source_obj.url == 'http://www.okino.ua/' and n.name_alter:
                    release_d = releases_dict.get(n.kid).release
                    if fnames_dict.get(n.kid):
                        fnames_dict[n.kid]['names'].append(n.name_alter)
                    else:
                        fnames_dict[n.kid] = {'names': [n.name_alter], 'genres': [], 'rate_imdb': [], 'release': release_d}
                    if re.findall(ur'[а-яА-Я]', n.name_alter):
                        uk_films.append(n.kid)
                elif n.source_obj.url == 'http://kino-teatr.ua/':
                '''
                release_d = releases_dict.get(n.kid)
                release_d = release_d.release if release_d else releases_dict2.get(n.kid).release
                if fnames_dict.get(n.kid):
                    fnames_dict[n.kid]['names'].append(n.name)
                else:
                    fnames_dict[n.kid] = {'names': [n.name], 'genres': [], 'rate_imdb': [], 'release': release_d, 'obj': None}
                if re.findall(ur'[а-яА-Я]', n.name):
                    uk_films.append(n.kid)

            for dic in [releases_dict, releases_dict2]:
                for k, v in dic.iteritems():
                    if not fnames_dict.get(k):
                        nname = v.film.name
                        fnames_dict[k] = {'names': [nname], 'genres': [], 'rate_imdb': [], 'release': v.release, 'obj': None}
                        if re.findall(ur'[а-яА-Я]', nname):
                            uk_films.append(k)

    film_name = FilmsName.objects.using('afisha').select_related('film_id', 'film_id__genre1', 'film_id__genre2', 'film_id__genre3', 'film_id__imdb').filter(type__in=(1,2), film_id__id__in=keys, status=1).order_by('-type')

    for n in film_name:
        if n.film_id_id not in uk_films:

            if fnames_dict.get(n.film_id_id):
                if not fnames_dict[n.film_id_id]['names']:
                    fnames_dict[n.film_id_id]['names'].append(n.name.strip())
            else:
                '''
                if current_site.domain == 'kinoafisha.in.ua':
                    release_d = releases_dict.get(n.film_id_id)
                    release_d = release_d.release if release_d else releases_dict2.get(n.film_id_id).release
                else:
                '''
                release_d = releases_dict.get(n.film_id_id).release.release_date
                fnames_dict[n.film_id_id] = {'names': [n.name.strip()], 'genres': [], 'rate_imdb': n.film_id.imdb, 'release': release_d, 'obj': n.film_id}
        else:
            fnames_dict[n.film_id_id]['rate_imdb'] = n.film_id.imdb

        if not fnames_dict[n.film_id_id]['genres']:
            genres = [n.film_id.genre1_id, n.film_id.genre2_id, n.film_id.genre3_id]
            genres = [n.film_id.genre1, n.film_id.genre2, n.film_id.genre3]
            for i in genres:
                if i:
                    fnames_dict[n.film_id_id]['genres'].append(i.name)

    kinoinfo_film = []
    frates = check_int_rates_inlist(fnames_dict.keys())
    for k, v in fnames_dict.iteritems():
        for ind, w in enumerate(weeks):
            if f_value and v['release'].year == f_value.year and v['release'].month == f_value.month and v['release'].day in w:
                name_ru = (sorted(v['names'], reverse=True))
                name_ru = name_ru[0]
                rate = float(v['rate_imdb'].replace(',','.')) if v['rate_imdb'] else 0

                # получит интегральную оценку
                frate = frates.get(k)
                int_rate = frate['int_rate']
                show_ir = frate['show_ir']
                show_imdb = frate['show_imdb']
                rotten = frate['rotten']

                films = {'name': name_ru, 'kid': k, 'rate': int_rate, 'show_ir': show_ir, 'show_imdb': show_imdb, 'rotten': rotten}
                if not weeks_dict.get(ind):
                    weeks_dict[ind] = {'week': w, 'week_ind': ind, 'films': [films,]}
                else:
                    weeks_dict[ind]['films'].append(films)

    if not weeks_dict:
        request.session['%s_release_filter_data' % current_site.domain] = ''
        return HttpResponseRedirect(reverse('releases_ajax'))


    if week_id and weeks_dict.get(week_id):
        a_week = weeks_dict.get(week_id)
        active_week = week_id
    else:
        a_week = weeks_dict.iteritems().next()
        active_week = a_week[0]
        a_week = a_week[1]

    month_weeks = {}
    for k, v in weeks_dict.iteritems():
        w_list = [i for i in v['week'] if i != 0]
        week_first_day = w_list[0]
        week_last_day = w_list[-1]
        month_weeks[k] = {'range': '%s-%s' % (week_first_day, week_last_day), 'date': f_value}

    p = sorted(a_week['films'], key=operator.itemgetter('rate'), reverse=True)

    first_load_film = p[0]['kid']

    if id:
        first_load_film = id
    sess_data = '%s;%s' % (f_value, active_week)
    request.session['%s_release_filter_data' % current_site.domain] = sess_data

    template = 'release_parser/%sfilm_list_form_ajax.html' % ''
    return render_to_response(template, {'p': p, 'date_release': date_release, 'f_value': f_value, 'first_load_film': first_load_film, 'dmonth': date_month_release, 'month_weeks': month_weeks, 'active_week': active_week, 'subscribe_me': subscribe_me}, context_instance=RequestContext(request))






@never_cache
def film_list_form_ajax(request, id=None):
    '''
    График кинорелизов для посетителей (Раздел Скоро)
    '''
    subscribe_me = True if 'subscribe' in request.GET else False
    
    current_site = request.current_site
    current_language = translation.get_language()
    today = datetime.date.today()
    today = today + datetime.timedelta(days=3)

    releases_dict = {}
    for i in Film.objects.using('afisha').only('id', 'date').filter(date__gte=today):
        if not releases_dict.get(i.id):
            releases_dict[i.id] = i.date.date()
    '''
    releases = ReleasesRelations.objects.select_related('release').filter(release__release_date__gte=today, rel_double=False, rel_ignore=False)
    for i in releases:
        if not releases_dict.get(i.film_kid):
            releases_dict[i.film_kid] = i
    '''
    f_value = None
    week_id = None
    
    # фильтрация в режиме ручного выбора фильтра
    if request.POST and request.POST.get('release') and request.POST.get('release_week'):
        # фильтр Дата Релиза
        f_value = request.POST['release']
        week_data = request.POST['release_week'].split('/')
        try:
            week_id = int(week_data[0])
            if f_value != week_data[1]:
                week_id = None
        except ValueError: pass
        
        f_value = datetime.date(int(f_value[:4]), int(f_value[-2:]), 1)

    # фильтрация на основе сохраненного ранее выбора фильтра (в сессии)
    if not f_value:
        sess_filter = request.session.get('%s_release_filter_data' % current_site.domain)
        if sess_filter:
            session_value = sess_filter.split(';')
            f_value, week_id = (session_value[0], session_value[1]) if len(session_value) > 1 else (None, None)
            try:
                week_id = int(week_id)
            except (ValueError, TypeError):
                week_id = None
            if f_value:
                try:
                    f_value = datetime.date(int(f_value[:4]), int(f_value[-5:-3]), int(f_value[8:]))
                except ValueError:
                    f_value = None

    weeks_dict = {}
    date_release = list(set([i for i in releases_dict.values()]))
    date_release.sort()

    date_month_release = {}
    for i in date_release:
        date_key = '%s %s' % (calendar.month_name[i.month], i.year)
        if date_key not in date_month_release:
            weeks = calendar.Calendar(0).monthdayscalendar(i.year, i.month)
            date_month_release[date_key] = {'month': i, 'weeks': weeks}

    date_month_release = dictsort(date_month_release.values(), 'month')

    if not f_value:
        f_value = date_release[0]

    weeks = calendar.Calendar(0).monthdayscalendar(int(str(f_value)[:4]), int(str(f_value)[-5:-3]))

    fnames_dict = {}

    t = ''
    film_name = FilmsName.objects.using('afisha').select_related('film_id', 'film_id__genre1', 'film_id__genre2', 'film_id__genre3', 'film_id__imdb').filter(type__in=(1,2), film_id__id__in=releases_dict.keys(), status=1).order_by('-type')

    for n in film_name:

        if fnames_dict.get(n.film_id_id):
            if not fnames_dict[n.film_id_id]['names']:
                fnames_dict[n.film_id_id]['names'].append(n.name.strip())
        else:
            release_d = releases_dict.get(n.film_id_id)
            fnames_dict[n.film_id_id] = {'names': [n.name.strip()], 'genres': [], 'rate_imdb': n.film_id.imdb, 'release': release_d, 'obj': n.film_id}
        

        if not fnames_dict[n.film_id_id]['genres']:
            genres = [n.film_id.genre1_id, n.film_id.genre2_id, n.film_id.genre3_id]
            genres = [n.film_id.genre1, n.film_id.genre2, n.film_id.genre3]
            for i in genres:
                if i:
                    fnames_dict[n.film_id_id]['genres'].append(i.name)

    kinoinfo_film = []
    frates = check_int_rates_inlist(fnames_dict.keys())
    for k, v in fnames_dict.iteritems():
        for ind, w in enumerate(weeks):
            if f_value and v['release'].year == f_value.year and v['release'].month == f_value.month and v['release'].day in w:
                name_ru = (sorted(v['names'], reverse=True))
                name_ru = name_ru[0]
                rate = float(v['rate_imdb'].replace(',','.')) if v['rate_imdb'] else 0

                # получит интегральную оценку
                frate = frates.get(k)
                int_rate = frate['int_rate']
                show_ir = frate['show_ir']
                show_imdb = frate['show_imdb']
                rotten = frate['rotten']

                films = {'name': name_ru, 'kid': k, 'rate': int_rate, 'show_ir': show_ir, 'show_imdb': show_imdb, 'rotten': rotten}
                if not weeks_dict.get(ind):
                    weeks_dict[ind] = {'week': w, 'week_ind': ind, 'films': [films,]}
                else:
                    weeks_dict[ind]['films'].append(films)

    if not weeks_dict:
        request.session['%s_release_filter_data' % current_site.domain] = ''
        return HttpResponseRedirect(reverse('releases_ajax'))


    if week_id and weeks_dict.get(week_id):
        a_week = weeks_dict.get(week_id)
        active_week = week_id
    else:
        a_week = weeks_dict.iteritems().next()
        active_week = a_week[0]
        a_week = a_week[1]

    month_weeks = {}
    for k, v in weeks_dict.iteritems():
        w_list = [i for i in v['week'] if i != 0]
        week_first_day = w_list[0]
        week_last_day = w_list[-1]
        month_weeks[k] = {'range': '%s-%s' % (week_first_day, week_last_day), 'date': f_value}

    p = sorted(a_week['films'], key=operator.itemgetter('rate'), reverse=True)

    first_load_film = p[0]['kid']

    if id:
        first_load_film = id
    sess_data = '%s;%s' % (f_value, active_week)
    request.session['%s_release_filter_data' % current_site.domain] = sess_data

    tmplt = 'release_parser/film_list_form_ajax.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/release_parser/film_list_form_ajax.html'

    return render_to_response(tmplt, {'p': p, 'date_release': date_release, 'f_value': f_value, 'first_load_film': first_load_film, 'dmonth': date_month_release, 'month_weeks': month_weeks, 'active_week': active_week, 'subscribe_me': subscribe_me}, context_instance=RequestContext(request))










'''
def kinometro_films_pages():

    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')

    link = 'http://www.kinometro.ru/release/card/id/'

    today = datetime.date.today()

    id_from = Releases.objects.filter(release_date__gte=today).order_by('film_id')[0].film_id

    urls_for_delete = []

    # 100 - 15201

    id_to = 15401


    for index, id in enumerate(range(id_from, id_to)):
        url = '%s%s' % (link, id)
        try:
            page = urllib.urlopen(url)
        except IOError:
            page = None
        # если страница (релиз) существует у источника, то получаю страницу
        if page:
            if page.getcode() == 200:
                page_data = BeautifulSoup(page.read(), from_encoding="utf-8")
                div = page_data.find('div', {'class': 'c11'})
                film_name = div.find('p', {'class': 'ftitle'}).text.strip().encode('utf-8')
                f_name_details = re.findall(r'\(.*?\)', film_name)
                details = ''
                if f_name_details:
                    for i in f_name_details:
                        if str(i) not in details:
                            details += str(i).decode('utf-8')
                film_name = re.sub(r'\(.*?\)', '', film_name)

                # разбор названий фильмов в теге
                f_name = film_name.split('/')
                if len(f_name) == 2:
                    f_name_ru, f_name_en = (f_name[0], f_name[1])
                elif len(f_name) > 2:
                    f_name_ru, f_name_en = language_identify(f_name)
                else:
                    f_name_ru, f_name_en = (f_name[0], '')

                f_name_ru = f_name_ru.replace(' ', '').replace('"', "'").strip().decode('utf-8')
                f_name_en = f_name_en.replace(' ', '').replace('"', "'").strip().decode('utf-8')

                film_id = id
                distr_name = None
                distr_id = None
                release = None
                runtime = None
                copies = None

                for tr in div.table.tbody.find_all('tr'):

                    td = tr.find_all('td')
                    # получение дистрибьютора
                    if td[0].text.encode('utf-8') == 'Дистрибьютор:':
                        distr = td[1].text.encode('utf-8').split('/')
                        distr_name1, distr_name2 = (distr[0].strip().decode('utf-8'), distr[1].strip().decode('utf-8')) if len(distr) > 1 else (distr[0].strip().decode('utf-8'), None)
                        tag_a = td[1].findAll('a')
                        if len(tag_a) > 1:
                            distr_id1, distr_id2 = (tag_a[0].get('href'), tag_a[1].get('href'))
                        elif len(tag_a) < 1:
                            distr_id1, distr_id2 = (None, None)
                        elif len(tag_a) == 1:
                            t = td[1].prettify().split(' /')
                            d_id = tag_a[0].get('href')
                            distr_id1 = None
                            distr_id2 = None
                            if len(t) > 1:
                                if d_id in t[0]:
                                    distr_id1 = d_id
                                elif d_id in t[1]:
                                    distr_id2 = d_id
                            else:
                                distr_id1 = d_id
                        if distr_id1:
                            distr_id1 = distr_id1.replace('/distributor/show/id/','').encode('utf-8')
                        if distr_id2:
                            distr_id2 = distr_id2.replace('/distributor/show/id/','').encode('utf-8')
                    # получение даты релиза
                    elif td[0].text.encode('utf-8') == 'Дата начала проката в России:':
                        release = td[1].text.strip().encode('utf-8')
                    # получение хронометража
                    elif td[0].text.encode('utf-8') == 'Хронометраж:':
                        runtime = td[1].text.strip().encode('utf-8').replace(' минут', '').replace(' минуты', '').replace('~', '')
                    # получение кол-ва копий
                    elif td[0].text.encode('utf-8') == 'Количество копий:':
                        copies = td[1].text.strip().encode('utf-8').replace('~', '')

                if release:
                    # приведение даты к виду гггг.мм.дд
                    release = re.sub(r'\(.*?\)', '', release).strip()
                    release = datetime.date(int(release[-4:]), int(release[3:-5]), int(release[:2]))

                # если такой записи нет в БД, то создаю, если есть то получаю этот объект и дальше обновляю в нем данные
                obj, created = Releases.objects.get_or_create(
                    url=url,
                    defaults={
                        'name_ru': f_name_ru,
                        'name_en': f_name_en,
                        'details': details,
                        'film_id': film_id,
                        'url': url,
                        'release_date': release,
                        'distributor1': distr_name1,
                        'distributor1_id': distr_id1,
                        'distributor2': distr_name2,
                        'distributor2_id': distr_id2,
                        'copies': copies,
                        'runtime': runtime,
                        }
                    )

                # обновление данных у объекта
                if not created:
                    if obj.name_ru != f_name_ru:
                        obj.name_ru = f_name_ru
                    if obj.name_en != f_name_en:
                        obj.name_en = f_name_en
                    if obj.details != details:
                        obj.details = details
                    if obj.release_date != release:
                        obj.release_date = release
                    if obj.distributor1 != distr_name1:
                        obj.distributor1 = distr_name1
                    if obj.distributor1_id != distr_id1:
                        obj.distributor1_id = distr_id1
                    if obj.distributor2 != distr_name2:
                        obj.distributor2 = distr_name2
                    if obj.distributor2_id != distr_id2:
                        obj.distributor2_id = distr_id2
                    if obj.copies != copies:
                        obj.copies = copies
                    if obj.runtime != runtime:
                        obj.runtime = runtime
                    obj.save()
            elif page.getcode() == 404:
                # несущесвующий/удаленный id у источника
                urls_for_delete.append(url)


        # на каждом 130 обращении к источнику делаю паузу в 3 секунды
        if (index + 1) % 130 == 0:
            time.sleep(3.0)

    #Releases.objects.filter(url__in=urls_for_delete).delete()

    xml_for_delete = ''
    for_delete = Releases.objects.filter(url__in=urls_for_delete)
    for i in for_delete:
        xml_for_delete += '<film name_ru="%s" name_en="%s" release_id="%s" url="%s"></film>' % (i.name_ru, i.name_en, i.id, i.url)

    create_dump_file('release_film_for_delete', settings.API_DUMP_PATH, xml_for_delete.encode('utf-8'))

    cron_success('html', 'kinometro', 'releases', 'Релизы')
    time.sleep(2.0)
    return time.time()-t1
'''


@only_superuser
@never_cache
def kinoafisha_release_update(request):

    checker = []
    if request.POST:
        checker = request.POST.getlist('checker')

    year = datetime.date.today().year
    release_date = datetime.date(year, 1, 1)
    release_rel = ReleasesRelations.objects.select_related('release').filter(release__release_date__gte=release_date, rel_double=False, rel_ignore=False)

    films_date = {}
    for i in release_rel:
        release = datetime.datetime(i.release.release_date.year, i.release.release_date.month, i.release.release_date.day, 0, 0, 0)
        films_date[i.film_kid] = {'date': release, 'sid': i.release.film_id}

    xml = open('%s/dump_release_film_for_delete.xml' % settings.API_DUMP_PATH, 'r')
    xml_data = BeautifulSoup(xml.read(), from_encoding="utf-8")
    xml.close()

    # удаленные у источника
    release_id = []
    for i in xml_data.findAll('film'):
        release_id.append(int(i['release_id']))

    for_del = []
    release_del = []
    release_rel_del = ReleasesRelations.objects.filter(release__id__in=release_id, rel_double=False, rel_ignore=False)
    for i in release_rel_del:
        if checker:
            if str(i.film_kid) in checker:
                for_del.append(i.film_kid)
                release_del.append(i.id)
        films_date[i.film_kid] = {'date': '*', 'sid': i.release.film_id}

    # если есть удаленные у источника
    if for_del:
        release_rel_del = ReleasesRelations.objects.filter(film_kid__in=for_del, rel_double=False, rel_ignore=False)
        if release_rel_del:
            releases_id = []
            for i in release_rel_del:
                #films_date[i.film_kid] = {'date': '*', 'sid': i.release.film_id}
                releases_id.append(i.release_id)

            SubscriptionRelease.objects.filter(release__id__in=release_del).delete()
            release_rel_del.delete()
            Releases.objects.filter(id__in=releases_id).delete()

    if checker:
        films = Film.objects.using('afisha').filter(pk__in=checker)
    else:
        films = Film.objects.using('afisha').filter(pk__in=films_date.keys())

    data = []
    for i in films:
        release = films_date.get(i.id)
        if release:
            if release['date'] == '*':
                if checker:
                    i.date = None
                    i.save()
                else:
                    name_ru, name_en = get_name_ru(i.id, True)
                    data.append({'sid': release['sid'], 'old': i.date, 'new': None, 'color': 'red', 'id': i.id, 'name_ru': name_ru, 'name_en': name_en})
            else:
                idates = []
                if i.date:
                    idates = [
                        i.date,
                        i.date + datetime.timedelta(days=1),
                        i.date + datetime.timedelta(days=2),
                        i.date - datetime.timedelta(days=1),
                        i.date - datetime.timedelta(days=2),
                    ]
                if release['date'] not in idates:
                    if checker:
                        i.date = release['date']
                        i.save()
                    else:
                        name_ru, name_en = get_name_ru(i.id, True)
                        if i.date:
                            data.append({'sid': release['sid'], 'old': i.date, 'new': release['date'], 'color': 'black', 'id': i.id, 'name_ru': name_ru, 'name_en': name_en})
                        else:
                            data.append({'sid': release['sid'], 'old': i.date, 'new': release['date'], 'color': 'green', 'id': i.id, 'name_ru': name_ru, 'name_en': name_en})

    if request.POST:
        return HttpResponseRedirect(reverse('kinoafisha_release_update'))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, data, 17)
    return render_to_response('release_parser/kinoafisha_release_update.html', {'p': p, 'page': page}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def kinoafisha_cinemaplex_release_update(request):

    checker = []
    if request.POST:
        checker = request.POST.getlist('checker')

    year = datetime.date.today().year
    release_date = datetime.date(year, 1, 1)
    release_rel = list(SourceReleases.objects.filter(source_obj__url='http://cinemaplex.ru/', release__gte=release_date, film__rel_double=False, film__rel_ignore=False).values('release', 'film__kid'))

    films_date = {}
    for i in release_rel:
        release = datetime.datetime(i['release'].year, i['release'].month, i['release'].day, 0, 0, 0)
        films_date[i['film__kid']] = {'date': release, 'sid': ''}


    if checker:
        films = Film.objects.using('afisha').filter(pk__in=checker)
    else:
        films = Film.objects.using('afisha').filter(pk__in=films_date.keys())

    data = []
    for i in films:
        release = films_date.get(i.id)
        if release:
            idates = []
            if i.date:
                idates = [
                    i.date,
                    i.date + datetime.timedelta(days=1),
                    i.date + datetime.timedelta(days=2),
                    i.date - datetime.timedelta(days=1),
                    i.date - datetime.timedelta(days=2),
                ]
            if release['date'] not in idates:
                if checker:
                    i.date = release['date']
                    i.save()
                else:
                    name_ru, name_en = get_name_ru(i.id, True)
                    if i.date:
                        data.append({'sid': release['sid'], 'old': i.date, 'new': release['date'], 'color': 'black', 'id': i.id, 'name_ru': name_ru, 'name_en': name_en})
                    else:
                        data.append({'sid': release['sid'], 'old': i.date, 'new': release['date'], 'color': 'green', 'id': i.id, 'name_ru': name_ru, 'name_en': name_en})

    if request.POST:
        return HttpResponseRedirect(reverse('kinoafisha_cinemaplex_release_update'))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, data, 17)
    return render_to_response('release_parser/kinoafisha_release_update.html', {'p': p, 'page': page}, context_instance=RequestContext(request))




@only_superuser
@never_cache
def runtime_copy_to_kinoafisha(request):
    '''
    Экспорт хронометраж и копии в Киноафишу
    '''
    today = datetime.date.today()

    # выборка релизов
    film_releases = ReleasesRelations.objects.select_related('release').filter(release__release_date__gte=today, rel_double=False, rel_ignore=False)

    afisha_films = Film.objects.using('afisha').filter(date__gt=today)
    afisha_films_copy = FilmSound.objects.using('afisha').select_related('film_id').filter(film_id__date__gt=today)

    # словарь фильм:хронометраж
    films_runtime = {}
    for i in afisha_films:
        films_runtime[i.id] = {'run': i.runtime, 'obj': i}

    films_copies = {}
    films_copies_del = []

    films_ids = []

    # словарь фильм:копии
    for i in afisha_films_copy:
        if films_copies.get(i.film_id_id):
            films_copies_del.append(i.film_id_id)
        films_copies[i.film_id_id] = {'copy': i.num, 'obj': i}


    films_ids = set(films_runtime.keys() + films_copies.keys())

    films_names = FilmsName.objects.using('afisha').filter(film_id__id__in=films_ids, status=1, type=2)
    films_names_dict = {}
    for i in films_names:
        if not films_names_dict.get(i.film_id_id):
            films_names_dict[i.film_id_id] = i.name

    # если у фильма больше одного типа копий, исключаю этот фильм
    for i in set(films_copies_del):
        del films_copies[i]

    l1 = []
    l2 = []

    data = []
    not_found_dict = {}

    for i in film_releases:
        kid = i.film_kid
        copies = i.release.copies
        runtime = i.release.runtime

        # если у релиза указан хронометраж, и он не равен хронометражу на киноафише, то делаю замену
        if runtime:
            afisha_runtime = films_runtime.get(kid)
            if afisha_runtime and afisha_runtime['run'] != str(runtime):
                if request.POST.get(u'save'):
                    afisha_runtime['obj'].runtime = runtime
                    afisha_runtime['obj'].save()
                fname = films_names_dict.get(kid)
                data.append({'type': 1, 'kid': kid, 'name': fname, 'current': afisha_runtime['run'], 'new': runtime})
                #link = 'http://www.kinoafisha.ru/index.php3?id1=%s&status=1' % kid
                #l1.append('<a href="%s" target="_blank">%s</a> %s = %s<br />' % (link, link, afisha_runtime['run'], runtime))

        # если у релиза указано кол-во копий, и оно не равно кол-ву на киноафише, то делаю замену
        if copies:
            afisha_copy = films_copies.get(kid)
            if afisha_copy:
                if afisha_copy['copy'] != copies:
                    if request.POST.get(u'save'):
                        afisha_copy['obj'].num = copies
                        afisha_copy['obj'].save()
                    fname = films_names_dict.get(kid)
                    data.append({'type': 2, 'kid': kid, 'name': fname, 'current': afisha_copy['copy'], 'new': copies})
                    #link = 'http://www.kinoafisha.ru/index.php3?id1=%s&status=1' % kid
                    #l2.append('<a href="%s" target="_blank">%s</a> %s = %s<br />' % (link, link, afisha_copy['copy'], copies))
            else:
                not_found_dict[kid] = copies


    not_found_copies = Film.objects.using('afisha').filter(pk__in=not_found_dict.keys(), date__gt=today)

    # если на киноафише нет копий у фильма, то добавляю копии от источника
    # задаю копиям правильный тип (закадровый, субтитры и др.)
    for i in not_found_copies:
        # 2 - ru, 43 - ua
        copy_type = None
        copies = not_found_dict.get(i.id)

        if i.country_id != 2 and i.country2_id != 2 and i.country_id != 43 and i.country2_id != 43:
            if copies >= 100:
                copy_type = 1
            elif copies < 20:
                copy_type = 2
            elif copies >= 20 and copies < 100:
                copy_type = 3
        if i.country_id == 2 or i.country_id == 43:
            if i.country2_id == 2 or i.country2_id == 43 or not i.country2_id:
                if copies >= 100:
                    copy_type = 4

        if copy_type:
            if request.POST.get(u'save'):
                FilmSound.objects.using('afisha').create(film_id=i, type_sound_id=copy_type, num=copies)
            fname = films_names_dict.get(i.id)
            data.append({'type': 2, 'kid': i.id, 'name': fname, 'current': '', 'new': copies})
            #link = 'http://www.kinoafisha.ru/index.php3?id1=%s&status=1' % i.id
            #l2.append('<a href="%s" target="_blank">%s</a>None = %s / %s<br />' % (link, link, copies, copy_type))


    if request.POST.get(u'save'):
        return HttpResponseRedirect(reverse('runtime_copy_to_kinoafisha'))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, data, 17)

    return render_to_response('release_parser/runtime_copy_to_kinoafisha.html', {'p': p, 'page': page}, context_instance=RequestContext(request))



def schedules_export(source, autors, hflag):
    '''
    Экспорт репертуаров в киноафишу
    '''
    from release_parser.schedules import datetime_to_str, str_to_datetime
    from release_parser.kinohod import create_schedule_data_range2
    from release_parser.kinobit_cmc import afisha_dict

    log = ''
    extended_log = ''
    films = {}
    times = {}
    movies = {}
    halls = {}
    saved_schedules = {}



    # создание записей schedule и session в БД киноафиши
    def create_schedule_session(schedule_listt, logger, log, flag):
        time_counter = 0
        datax = {}
        for i in schedule_listt:
            # получаю объект зал
            hall_obj =  halls.get(i['hall'])
            if not hall_obj:
                try:
                    hall_obj = AfishaHalls.objects.using('afisha').get(pk=i['hall'])
                    halls[i['hall']] = hall_obj
                except AfishaHalls.DoesNotExist: pass

            # получаю объект кинотеатр
            movie_obj = movies.get(i['movie'])
            if not movie_obj:
                try:
                    movie_obj = Movie.objects.using('afisha').get(pk=i['movie'])
                    movies[i['movie']] = movie_obj
                except Movie.DoesNotExist: pass

            # получаю объект фильм
            film_obj = films.get(i['film'])
            if not film_obj:
                try:
                    film_obj = Film.objects.using('afisha').get(pk=i['film'])
                    films[i['film']] = film_obj
                except Film.DoesNotExist: pass

            if hall_obj and movie_obj and film_obj:
                # создаю шедул
                s = Schedule.objects.using('afisha').create(
                    movie_id = movie_obj,
                    film_id = film_obj,
                    hall_id = hall_obj,
                    date_from = i['from'],
                    date_to = i['to'],
                    autor = source.code,
                    user_id = 0
                )

                # создаю сессион
                time_txt = ''
                for t in i['time']:
                    try:
                        time_counter += 1

                        time_obj = times.get(t)
                        if not time_obj:
                            time_obj = SessionList.objects.using('afisha').get(time=t)
                            times[t] = time_obj
                        sess_obj = AfishaSession.objects.using('afisha').create(
                            schedule_id = s,
                            session_list_id = time_obj,
                            price1 = 0,
                            price2 = 0
                        )

                        delta = i['to'] - i['from']
                        for ti in range(delta.days + 1):
                            d = i['from'] + datetime.timedelta(days=ti)
                            if hflag:
                                key = '%s%s%s%s%s' % (i['film'], i['movie'], i['hall'], d, t)
                            else:
                                key = '%s%s%s%s' % (i['film'], i['movie'], d, t)
                            saved_schedules[key] = sess_obj.id
                        t = '%s' % t
                        time_txt += '%s ' % t[:5]
                    except SessionList.DoesNotExist:
                        pass

                if time_counter % 50 == 0:
                    time.sleep(1.0)

                # запись в переменную лога
                if logger:
                    log += '<movie kid="%s" film_kid="%s" from="%s" to="%s" time="%s" flag="%s"></movie>' % (movie_obj.id, film_obj.id, i['from'], i['to'], time_txt, flag)
        return log

    today = datetime.date.today()

    # ШАГ 0
    # получаю минимальное и максимальное значение дата-время у источника
    kinoinfo_date_list = list(SourceSchedules.objects.filter(dtime__gte=today, source_obj=source).exclude(film__source_id=0).values_list('dtime', flat=True).order_by('dtime'))
    kinoinfo_date_list2 = [int(datetime_to_str(i)) for i in kinoinfo_date_list]
    kinoinfo_date_list2 = sorted(kinoinfo_date_list2)
    min_datetime, max_datetime = (kinoinfo_date_list2[0], kinoinfo_date_list2[-1]) if kinoinfo_date_list2 else (None, None)

    kinoinfo_cinema_list = list(SourceSchedules.objects.filter(dtime__gte=today, source_obj=source).exclude(film__source_id=0).distinct('cinema').values_list('cinema__cinema__code', flat=True))
    
    # ШАГ 1
    # выбираем из БД Киноафиши сеансы с датой начала больше-равно текущей. (источник = любой)
    # и формируем массив: датавремя сеанса-кинотеатр-зал-фильм-источник
    # выбрал сеансы у которых конечная дата равна или больше текущей
    afisha_obj = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id').filter(schedule_id__date_to__gte=today, schedule_id__movie_id__id__in=set(kinoinfo_cinema_list), schedule_id__autor__in=autors).order_by('session_list_id__time')

    cinema_list_for_kinoinfo = set([i.schedule_id.movie_id_id for i in afisha_obj])
    # список кинотеатров с источником 0, для лога
    cinema_list_source_0 = set([i.schedule_id.movie_id_id for i in afisha_obj if i.schedule_id.autor == 0])


    # формирую массив данных из queryset
    afisha_schedule = afisha_dict(afisha_obj)
    # получаю список id сессион для удаления
    afisha_session_del = [i.id for i in afisha_obj]
    # получаю список id шедул для удаления
    afisha_schedule_del = [i.schedule_id_id for i in afisha_obj]

    # удаляю сессион
    AfishaSession.objects.using('afisha').filter(pk__in=afisha_session_del).delete()
    # удаляю шедул
    Schedule.objects.using('afisha').filter(pk__in=set(afisha_schedule_del)).delete()

    cinema_count_del = [i.schedule_id.movie_id_id for i in afisha_obj]
    session_count_del = len(afisha_session_del)
    session_count_save = 0
    cinema_count_save = []

    # ШАГ 2
    # сеансы с датой меньше текущей для возврата на Киноафишу
    schedule_low_today = []
    # часть массива для дальнейшего использования
    good_data = []
    for i in afisha_schedule:
        if i['date'].date() < today:
            # готовим массив для записи обратно в киноафишу
            if i['movie'] not in cinema_count_save: # подсчет кол-ва кинотеатров в которых сеансы
                cinema_count_save.append(i['movie'])
            schedule_low_today.append(i)
        else:
            good_data.append(i)

    session_count_save += len(schedule_low_today) # подсчет кол-ва сеансов для записи

    # запись обратно в киноафишу
    schedule_listt = create_schedule_data_range2(schedule_low_today)
    log += create_schedule_session(schedule_listt, False, log, 0)

    # ШАГ 3
    # выборка периода  с новыми сеансами  (между мин и макс дат источника)
    # и удаление их из массива и с Киноафиши(очистка места под новый репертуар)
    schedule_for_delete = []
    schedule_to_kinoafisha = []
    if min_datetime:
        for i in good_data:
            idate = datetime_to_str(i['date'])
            if idate >= min_datetime and idate <= max_datetime:
                # для удаления с киноафиши
                schedule_for_delete.append(i)
            else:
                if i['movie'] not in cinema_count_save: # подсчет кол-ва кинотеатров в которых сеансы
                    cinema_count_save.append(i['movie'])
                # для возврата на киноафишу в 5 шаге
                schedule_to_kinoafisha.append(i)
    else:
        return '<info cinema_del="0" session_del="0" cinema_save="0" session_save="0"></info>'

    session_count_save += len(schedule_to_kinoafisha) # подсчет кол-ва сеансов для записи

    # удалить с киноафиши
    afisha_session_del = [i['obj'].id for i in schedule_for_delete]
    afisha_schedule_del = [i['obj'].schedule_id_id for i in schedule_for_delete]
    AfishaSession.objects.using('afisha').filter(pk__in=afisha_session_del).delete()
    Schedule.objects.using('afisha').filter(pk__in=set(afisha_schedule_del)).delete()

    cinema_count_del2 = [i['obj'].schedule_id.movie_id_id for i in schedule_for_delete]
    session_count_del2 = len(afisha_session_del)
    session_count_del = session_count_del + session_count_del2 # общее кол-во удаленных сеансов
    cinema_count_del = len(set(cinema_count_del + cinema_count_del2)) # общее кол-во кинотеатров где удалены сеансы

    # ШАГ 4
    # подготовка и запись сеансов из источника на киноафишу в очищенный период
    kinoinfo_data = SourceSchedules.objects.select_related('cinema', 'cinema__cinema', 'film').filter(dtime__gte=today, source_obj=source).exclude(film__source_id=0).order_by('dtime')

    cinema_halls = {}
    cinema_hall_none = []

    log_schedule_count = 0
    log_schedule_sale_count = 0
    log_films_list = []
    log_cinema_list = []

    kinoinfo_list = []
    for i in kinoinfo_data:
        cinema_code = i.cinema.cinema.code

        if cinema_code not in cinema_count_save: # подсчет кол-ва кинотеатров в которых сеансы
            cinema_count_save.append(cinema_code)

        if i.hall:
            hobj = i.hall
        else:
            hobj = cinema_halls.get(cinema_code)
            if not hobj and cinema_code not in cinema_hall_none:
                try:
                    hobj = AfishaHalls.objects.using('afisha').get(movie__id=cinema_code, id_name__id=999).id
                    cinema_halls[cinema_code] = hobj
                except AfishaHalls.DoesNotExist:
                    cinema_hall_none.append(cinema_code)

        if hobj:
            log_films_list.append(i.film.kid)
            log_cinema_list.append(cinema_code)
            log_schedule_count += 1

            kinoinfo_list.append({'film': i.film.kid, 'movie': cinema_code, 'hall': hobj, 'date': i.dtime})

    log_films_list = len(set(log_films_list))
    log_cinema_list = len(set(log_cinema_list))

    session_count_save += len(kinoinfo_list) # подсчет кол-ва сеансов для записи

    # записываем на киноафишу
    schedule_listt = create_schedule_data_range2(kinoinfo_list)
    log = create_schedule_session(schedule_listt, True, log, 1)

    # ШАГ 5
    if schedule_to_kinoafisha:
        # записываем на кинафишу
        schedule_listt = create_schedule_data_range2(schedule_to_kinoafisha)
        log = create_schedule_session(schedule_listt, True, log, 2)

    # ШАГ 6
    # связь сеансов источника с сеансами киноафиши
    source_schedules = list(SourceSchedules.objects.filter(dtime__gte=today, source_obj=source).exclude(film__source_id=0).values('cinema__cinema__code', 'film__kid', 'hall', 'dtime', 'id'))
    for i in source_schedules:
        if hflag:
            key = '%s%s%s%s%s' % (i['film__kid'], i['cinema__cinema__code'], i['hall'], i['dtime'].date(), i['dtime'].time())
        else:
            key = '%s%s%s%s' % (i['film__kid'], i['cinema__cinema__code'], i['dtime'].date(), i['dtime'].time())

        sess_obj = saved_schedules.get(key)
        if sess_obj:
            SessionsAfishaRelations.objects.create(
                kid = sess_obj,
                source = source,
                schedule_id = i['id'],
            )

    cinema_count_save = len(cinema_count_save)

    log += '<info cinema_del="%s" session_del="%s" cinema_save="%s" session_save="%s"></info>' % (cinema_count_del, session_count_del, cinema_count_save, session_count_save)

    cinemalist = ''
    for i in cinema_list_source_0:
        cinemalist += '<id>%s</id>' % i
    log += '<cinemalist>%s</cinemalist>' % cinemalist

    return log



def schedules_feed(city):

    now = datetime.datetime.now()
    #now = datetime.datetime(2013, 9, 17) # -------------- !!!!!!!!!

    now = now - datetime.timedelta(hours=1)

    tomorrow = now.date() + datetime.timedelta(days=1) # -------------- !!!!!!!!!(days=100)

    films_kid = list(SourceSchedules.objects.filter(dtime__gte=now, dtime__lt=tomorrow, cinema__cinema__city__id=city).values_list('film__kid', flat=True).distinct('film__kid'))

    films = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__in=films_kid, status=1, type=2).order_by('-film_id__imdb')[:5]
    films_dict = {}
    for i in films:
        films_dict[i.film_id_id] = i

    schedules = SourceSchedules.objects.select_related('film', 'cinema').filter(dtime__gte=now, dtime__lt=tomorrow, cinema__cinema__city__id=city, film__kid__in=films_dict.keys()).exclude(film__source_id=0)

    film_cinema = {}
    film_sch = {}
    for i in schedules:
        schedule_time = i.dtime.time().strftime('%H:%M')

        if film_sch.get(i.film.kid):
            film_sch[i.film.kid]['times'].append(schedule_time)
        else:
            film_sch[i.film.kid] = {'times': [schedule_time], 'obj': i, 'cinema': i.cinema.cinema_id}

    return film_sch.values(), films_dict



def releases_feed(domain, user_interface_type=None):

    limit = 15 if user_interface_type is None else 5

    today = datetime.date.today()#
    #today =datetime.datetime(2013, 2, 17)#

    today = today + datetime.timedelta(days=3)

    releases_dict = {}

    
    releases = Film.objects.using('afisha').filter(date__gte=today).order_by('date')[:limit]
    for i in releases:
        releases_dict[i.id] = {'release': i.date}


    film_name = FilmsName.objects.using('afisha').filter(type=2, film_id__id__in=releases_dict.keys(), status=1).order_by('-type')

    releases_dict2 = {}
    release_date = None
    poster = None


    for ind, i in enumerate(film_name):
        film_info = {}
        films_data = get_film_data(int(i.film_id_id))
        # получаю маленький постер для вывода на главную
        if films_data['posters']:
            poster = films_data['posters']
        # компаную данные для выводка в подсказку при наведении
        if films_data['country']:
            film_info[1] = films_data['country'] + ", "
        if films_data['year']:
            film_info[2] = films_data['year'] + ", "
        if films_data['runtime']:
            film_info[3] = films_data['runtime'] + ", "
        '''
        if films_data['film_genres'][1]:
            film_info[4] = films_data['film_genres'][1].name + ", " + "\n"
        if films_data['film_genres'][1] and films_data['film_genres'][2]:
            film_info[4] = films_data['film_genres'][1].name + " / " + films_data['film_genres'][2].name + ", " + "\n"
        if films_data['film_genres'][1] and films_data['film_genres'][2] and films_data['film_genres'][3]:
            film_info[4] = films_data['film_genres'][1].name + " / " + films_data['film_genres'][2].name + " / " + films_data['film_genres'][3].name + ", " + "\n"
        '''
        if films_data['description']:
            film_info[5] = films_data['description'][:100]
        film_info = OrderedDict(sorted(film_info.items(), key=lambda t: t[0]))
        # получаю оценки к фильму
        int_rate, show_ir, show_imdb, rotten = check_int_rates(int(i.film_id_id))
        # заполняю словарь и предаю обратно
        releases_dict2[i.film_id_id] = {

            'name': i.name,
            'kid': int(i.film_id_id),
            'release': releases_dict[i.film_id_id]['release'],
            'poster': poster,
            'film_info':film_info,
            'rating': int_rate,
            'show_ir': show_ir,
            'show_imdb': show_imdb,
            'rotten': rotten,
        }

    return sorted(releases_dict2.values(), key=operator.itemgetter('release'))


def mass_email_sender():
    '''
    Оповещение юзеров по email о релизах в кинотеатрах их городов
    '''
    import locale
    from django.core.mail import get_connection, EmailMultiAlternatives
    from django.template.defaultfilters import date as tmp_date

    t1 = time.time()

    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    today = datetime.date.today()
    #today = datetime.date(2013, 7, 17) # -------------- !!!!!!!!!

    # РАССЫЛКА СЕАНСОВ
    subr = SubscriptionRelease.objects.select_related('release', 'release__release', 'profile', 'profile__user').\
        filter(notified=False)

    users = {}
    cities = []
    films_ids = []
    for i in subr:
        user_city = i.profile.person.city.kid
        fid = i.release.film_kid if i.release else i.kid
        films_ids.append(fid)

        if users.get(i.profile_id):
            users[i.profile_id]['films'].append(fid)
            users[i.profile_id]['subr_id'].append(i.id)
        else:
            users[i.profile_id] = {
                'email': i.profile.user.email, 'city': user_city, 'profile': i.profile_id,
                'films': [fid], 'subr_id': [i.id]
            }

        if user_city not in cities:
            cities.append(user_city)

    messages = {}
    subr_id = []
    films_notified = []

    if cities:
        ci_names = {}
        cities_obj = City.objects.filter(kid__in=cities)
        for i in cities_obj:
            for j in i.name.filter(status=1):
                ci_names[i.kid] = j.name

        films_ids = set(films_ids)

        films_obj = FilmsName.objects.using('afisha').filter(film_id__in=films_ids, status=1, type=2)

        films = {}
        for i in films_obj:
            films[i.film_id_id] = {'name': i.name, 'kid': i.film_id_id}

        if films:
            schedules = AfishaSession.objects.using('afisha').select_related(
                'schedule_id', 'session_list_id', 'schedule_id__movie_id'
            ).filter(
                schedule_id__film_id__id__in=films.keys(),
                schedule_id__movie_id__city__id__in=cities,
                schedule_id__date_from__gte=today
            ).order_by('schedule_id__date_from')

            cinemas_id = []
            sch = {}
            for s in schedules:
                if sch.get(s.schedule_id.film_id_id):
                    if sch[s.schedule_id.film_id_id].get(s.schedule_id.movie_id.city_id):
                        my_item = next((item for item in sch[s.schedule_id.film_id_id][s.schedule_id.movie_id.city_id] if item['movie_id'] == s.schedule_id.movie_id_id), None)
                        if not my_item:
                            sch[s.schedule_id.film_id_id][s.schedule_id.movie_id.city_id].append({'movie_id': s.schedule_id.movie_id_id, 'date': s.schedule_id.date_from, 'time': s.session_list_id.time})
                    else:
                        sch[s.schedule_id.film_id_id][s.schedule_id.movie_id.city_id] = [{'movie_id': s.schedule_id.movie_id_id, 'date': s.schedule_id.date_from, 'time': s.session_list_id.time}]
                else:
                    sch[s.schedule_id.film_id_id] = {s.schedule_id.movie_id.city_id: [{'movie_id': s.schedule_id.movie_id_id, 'date': s.schedule_id.date_from, 'time': s.session_list_id.time}]}
                cinemas_id.append(s.schedule_id.movie_id_id)

            cinema_obj = Movie.objects.using('afisha').filter(pk__in=set(cinemas_id))
            cinema_dict = {}
            for i in cinema_obj:
                cinema_dict[i.id] = {'name': i.name, 'address': i.address}

            for u in users.values():
                city = u['city']
                city_name = ci_names.get(city)
                f_kid = u['films']
                subr_id = subr_id + u['subr_id']

                msg_header = u'<div>В Вашем городе %s будут следующие показы:<br />' % city_name

                for key, value in sch.iteritems():
                    if key in f_kid and sch[key].get(city):
                        films_notified.append(key)
                        msg = ''
                        cinemas = sch[key].get(city)
                        film_name = films.get(key)['name']
                        afisha_link = u'<b>%s</b>' % film_name
                        cinema_info = u''
                        for c in cinemas:
                            cin = cinema_dict.get(c['movie_id'])
                            if cin:
                                sch_date = tmp_date(c['date'], "j E")
                                #open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write(str(type(sch_date)) + '\t' + str(type(cin['name'])) + '\t' + str(type(cin['address'])) + '\n')
                                cinema_info += u'%s в кинотеатре &laquo;%s&raquo; (<span style="font-size: 12px;">%s</span>)<br />' % (sch_date, cin['name'], cin['address'])

                        msg += u'<span style="display: block; background: #F5F5F5; padding: 10px; border-bottom: 1px dotted #999999;">'
                        msg += u'%s<br />' % afisha_link
                        msg += u'%s</span>' % cinema_info

                        if messages.get(u['email']):
                            msg_main = messages.get(u['email'])
                            msg_main = msg_main.replace(u'</div>', '')
                            msg_main += msg
                            messages[u['email']] = msg_main + u'</div>'
                        else:
                            messages[u['email']] = msg_header + msg + u'</div>'


    # РАССЫЛКА ТОРРЕНТОВ
    sub_topics = list(SubscriptionTopics.objects.filter(notified=False).distinct('kid').values_list('kid', flat=True))
    torrents = {}
    for i in Torrents.objects.filter(film__in=sub_topics).exclude(path=None):
        if not torrents.get(i.film):
            torrents[i.film] = {'0': None, '1': None, '2': None}
        q = i.quality_avg if i.quality_avg else '1'
        torrents[i.film][q] = i

    films_names = {}
    for i in FilmsName.objects.using('afisha').filter(film_id__in=torrents.keys(), status=1, type=2):
        films_names[i.film_id_id] = {'name': i.name, 'kid': i.film_id_id}

    topics = SubscriptionTopics.objects.select_related('profile', 'profile__user').filter(notified=False)

    topics_users = {}
    for i in topics:
        torrent_tmp = torrents.get(i.kid)
        if torrent_tmp:
            # если не указано качество (для старых подписок), то устанавливаю '1' - хорошее
            tquality = i.quality if i.quality else '1'
            # если качество хорошее или HD
            if tquality in ('1', '2'):
                torrent = torrent_tmp.get(tquality)
            # если качество любое, то сначала пытаюсь взять Хорошее или HD, ну или на последок Плохое
            else:
                torrent = torrent_tmp.get('1')
                if not torrent:
                    torrent = torrent_tmp.get('2')
                if not torrent:
                    torrent = torrent_tmp.get('0')

            if torrent:
                uemail = i.profile.user.email
                if not topics_users.get(uemail):
                    topics_users[uemail] = {
                        'torrent': [], 'email': uemail, 'profile': i.profile, 'films': [], 'subr_id': []
                    }
                topics_users[uemail]['torrent'].append(torrent)
                topics_users[uemail]['films'].append(i.kid)
                topics_users[uemail]['subr_id'].append(i.id)

    topic_notified = []
    topic_messages = {}

    if topics_users:
        tusers = {}
        for i in TorrentsUsers.objects.filter(torrent__film__in=torrents.keys()):
            tusers[i.torrent_id] = i

        tfilms = {}
        for i in FilmsName.objects.using('afisha').filter(film_id__id__in=sub_topics, status=1, type=2):
            tfilms[i.film_id_id] = i.name

        for i in topics_users.values():
            topic_msg_body = u''
            for j in i['films']:
                topic_notified.append(j)
                fname = tfilms.get(j)
                topic_msg_body += u'<span style="display: block; background: #F5F5F5; padding: 10px; border-bottom: 1px dotted #999999;"><b>%s</b></span>' % fname

            if topic_msg_body:
                topic_msg_body = u'<div>В сети доступны фильмы для скачивания: <br />%s</div>' % topic_msg_body

                if i['torrent']:
                    topic_msg_body += u'Торрент-файлы прикреплены к данному письму.'
                if not topic_messages.get(i['email']):
                    topic_messages[i['email']] = {'msg': topic_msg_body, 'torrent': [], 'profile': i['profile']}
                for t in i['torrent']:
                    tuser = tusers.get(t.id)
                    topic_messages[i['email']]['torrent'].append({'file': t, 'user': tuser})

    '''
    topics_users = {}
    sub_topics = []
    topics = SubscriptionTopics.objects.filter(notified=False)
    for i in topics:
        uemail = i.profile.user.email
        if topics_users.get(uemail):
            topics_users[uemail]['films'].append(i.kid)
            topics_users[uemail]['subr_id'].append(i.id)
        else:
            topics_users[uemail] = {'email': uemail, 'profile': i.profile_id, 'films': [i.kid], 'subr_id': [i.id]}
        sub_topics.append(i.kid)
    
    sourcefilms = SourceFilms.objects.filter(source_obj__url='http://rutracker.org/', kid__in=set(sub_topics))
    rutracker = {}
    for i in sourcefilms:
        rutracker_url = u'http://rutracker.org/forum/viewtopic.php?t=%s' % i.source_id
        if rutracker.get(i.kid):
            rutracker[i.kid].append(rutracker_url)
        else:
            rutracker[i.kid] = [rutracker_url]

    tfilms = {}
    for i in FilmsName.objects.using('afisha').filter(film_id__id__in=rutracker.keys(), status=1, type=2):
        tfilms[i.film_id_id] = i.name
               
    topic_notified = []
    topic_messages = {}
    for i in topics_users.values():
        topic_msg_body = u''
        for j in i['films']:
            ru = rutracker.get(j)
            if ru:
                topic_notified.append(j)
                fname = tfilms.get(j)
                topic_msg_body += u'<span style="display: block; background: #F5F5F5; padding: 10px; border-bottom: 1px dotted #999999;"><b>%s</b>:<br />' % fname
                for r in ru:
                    topic_msg_body += u'<div style="font-size: 12px;">%s</div>' % r
                topic_msg_body += u'</span>'
                
        if topic_msg_body:
            topic_msg_body = u'<div>В сети доступны фильмы для скачивания: <br />%s</div>' % topic_msg_body
            topic_messages[i['email']] = topic_msg_body
    '''
    emails_notified = []
    messages_data = []

    for k, v in messages.iteritems():
        v = u'<div style="font-size: 14px; color: #333333;">Вы получили это письмо потому, что подписались на релиз на сайте kinoinfo.ru<br /><br />%s' % v
        topic = topic_messages.get(k)
        if topic:
            v += '<br />%s' % topic
            emails_notified.append(k)
        v += u'</div>'
        messages_data.append({'msg': v, 'email': k})

    for k, v in topic_messages.iteritems():
        if k not in emails_notified:
            vmsg = u'<div style="font-size: 14px; color: #333333;">Вы получили это письмо потому, что подписались на релиз на сайте kinoinfo.ru<br /><br />%s</div>' % v['msg']
            v['email'] = k
            v['msg'] = vmsg
            messages_data.append(v)

    if messages_data:
        connection = get_connection()
        connection.open()

        for i in messages_data:
            add_files = []
            for t in i.get('torrent', []):
                #if t['user']:
                #    t['user'].got = True
                #    t['user'].save()
                #else:
                tuser_obj, tuser_obj_created = TorrentsUsers.objects.get_or_create(
                    torrent=t['file'],
                    profile=i['profile'],
                    defaults={
                        'torrent': t['file'],
                        'profile': i['profile'],
                        'got': True,
                    })
                if not tuser_obj_created:
                    tuser_obj.got = True
                    tuser_obj.save()

                add_file = '%s%s' % (settings.MEDIA_ROOT, t['file'].path)
                add_files.append(add_file)

                # сообщение во внутреннюю почту
                current_site = DjangoSite.objects.get(domain='kinoinfo.ru')

                msg_from = Profile.objects.get(user__last_name='SYSTEM')
                msg_to = i['profile']
                fname = films_names.get(t['file'].film, '-')
                msg = u'Для фильма <a href="http://kinoinfo.ru/film/%s/" target="_blank">%s</a> доступен торрент-файл, <a onclick="get_torrent_file(%s)">скачать</a>' % (fname['kid'], fname['name'], t['file'].id)

                try:
                    dialog_exist = DialogMessages.objects.filter(readers__user=msg_to, readers__message__autor=msg_from).order_by('-id')[0]
                except IndexError:
                    dialog_exist = None

                msg_obj = News.objects.create(
                    title='Сообщение',
                    text=msg,
                    autor=msg_from,
                    site=current_site,
                    subdomain='0',
                    reader_type='1',
                )

                reader = NewsReaders.objects.create(user=msg_to, status='0', message=msg_obj)

                if dialog_exist:
                    dialog_exist.readers.add(reader)
                else:
                    dialog_obj = DialogMessages()
                    dialog_obj.save()
                    dialog_obj.readers.add(reader)

            email = EmailMultiAlternatives(
                "Кино в Вашем городе", i['msg'], settings.DEFAULT_FROM_EMAIL, [i['email']], connection=connection
            )
            for af in add_files:
                email.attach_file(af, mimetype='application/x-bittorrent')
            email.attach_alternative(i['msg'], "text/html")
            try:
                email.send()
            except:
                pass

        connection.close()

    SubscriptionRelease.objects.filter(release__film_kid__in=set(films_notified)).update(notified=True)
    SubscriptionRelease.objects.filter(kid__in=set(films_notified)).update(notified=True)
    SubscriptionTopics.objects.filter(kid__in=set(topic_notified)).update(notified=True)

    time.sleep(1.0)
    return time.time() - t1


@only_superuser
@never_cache
def cron_log(request, log):
    f = open('%s/cron_log_%s.txt' % (settings.CRON_LOG_PATH, log), 'r')
    data = f.read().replace('\n', '<br />')
    f.close()
    if not data:
        data = 'нет записей'
    return HttpResponse('<div style="font-size:14px; font-family: Arial, Helvetica, Sans-Serif;">%s</div>' % data)
