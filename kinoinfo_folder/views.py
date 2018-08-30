#-*- coding: utf-8 -*-
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import never_cache
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from bs4 import BeautifulSoup
from base.models_dic import *
from base.models import *
from kinoinfo_folder.func import *
import urllib
import datetime
import time
import calendar
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from user_registration.func import login_counter

login='free_dump_key_9d6m12y'
now = datetime.datetime.now()
fdate = now.strftime('%Y-%m-%d %H:%M:%S')


@never_cache
def main(request):
    """
    Главная страница, навигация
    """
    if not request.user.is_anonymous(): login_counter(request)
    return render_to_response('kai/main.html', context_instance=RequestContext(request)) 


def save_dir(request, af, ki):
    '''
    Импорт справочников Страны, Жанры, Метро, Сети, Статус участия персоны, Тип участия персоны
    '''
    # получаю все объекты справочника
    obj = af.objects.using('afisha').all()
    for i in obj:
        if ki == StatusAct: name = i.status_act
        elif ki == Action: name = i.type_act
        else: name = i.name
        # если такого объекта в БД нет, то сохраняю
        try: ki.objects.get(name=name)
        except ki.DoesNotExist: ki_model(name=name).save()
        except ki.MultipleObjectsReturned: pass
    return HttpResponseRedirect(reverse("main_kai"))


def save_city_dir(request):
    '''
    Импорт справочника Города
    '''
    # получаю все объекты справочника
    city = AfishaCity.objects.using('afisha').all()
    # получаю объект русского языка
    lang = Language.objects.get(pk=1)
    city_phone_code = 0 # КОД ГОРОДА ------------------
    def save(status, name):
        return NameCity.objects.create(status=status, language=lang, name=name)
    for i in city:
        # если такого названия в БД нет, то сохраняю
        try: City.objects.get(name__name=i.name)
        except City.DoesNotExist: 
            city = City.objects.create(phone_code=city_phone_code)
            # сохраняю название
            name1 = save(1, i.name)
            # очищаю название от спец символов
            slug_name = low(del_separator(i.name))
            # сохраняю очищенное название
            name2 = save(2, slug_name)
            # создаю связь объект-названия
            city.name.add(name1, name2)
        except City.MultipleObjectsReturned: pass
    return HttpResponseRedirect(reverse("main_kai"))


def save_street_type_dir(request):
    '''
    Импорт справочника Тип улицы
    '''
    # получаю данные из подготовленного дампа
    dump_file = open(rel('dumps/street_type_dir.xml'), 'r').read()
    soup = BeautifulSoup(dump_file, from_encoding="utf-8")
    for tag in soup.findAll('st_type'):
        st_type_id = tag['id']
        st_type_name = tag['name'].encode('utf-8')
        # если такого типа улицы в БД нет, то сохраняю
        try: StreetType.objects.get(name=st_type_name)
        except StreetType.DoesNotExist: StreetType(id=st_type_id, name=st_type_name).save()
        except StreetType.MultipleObjectsReturned: pass
        for a in tag.findAll('st_atype'):
            # если такого альтернативного названия типа улицы в БД нет, то сохраняю
            st_atype_name = a['name'].encode('utf-8')
            try: AlterStreetType.objects.get(name=st_atype_name)
            except AlterStreetType.DoesNotExist: AlterStreetType(value_id=st_type_id, name=st_atype_name).save()
            except AlterStreetType.MultipleObjectsReturned: pass
    return HttpResponseRedirect(reverse("main_kai"))


def save_lang_dir(request):
    '''
    Импорт справочника Языки
    '''
    # получаю данные из подготовленного дампа
    dump_file = open(rel('dumps/lang_dir.xml'), 'r').read()
    soup = BeautifulSoup(dump_file, from_encoding="utf-8")
    for tag in soup.findAll('lang'):
        lang_id = tag['id']
        lang_name = tag['name'].encode('utf-8')
        # если такого языка в БД нет, то сохраняю
        try: Language.objects.get(name=lang_name) 
        except Language.DoesNotExist: Language(id=lang_id, name=lang_name).save()
        except Language.MultipleObjectsReturned: pass
    return HttpResponseRedirect(reverse("main_kai"))


def save_country_lang_rel(request):
    '''
    Импорт связь стран с языком
    '''
    # получаю данные из подготовленного дампа
    dump_file = open(rel('dumps/country_lang_rel.xml'), 'r').read()
    soup = BeautifulSoup(dump_file, from_encoding="utf-8")
    for tag in soup.findAll('country'):
        country = tag['name']
        lang = tag['lang']
        # получаю объекты страны и языка
        country_obj = Country.objects.get(name=country)
        lang_obj = Language.objects.get(name=lang)
        # если связи нет, то создаю
        try: LanguageCountry.objects.get(country=country_obj, language=lang_obj)
        except LanguageCountry.DoesNotExist: LanguageCountry(country=country_obj, language=lang_obj).save()
    return HttpResponseRedirect(reverse("main_kai"))


def save_sources_dir(request):
    '''
    Импорт названий источников
    '''
    # получаю данные из подготовленного дампа
    dump_file = open(rel('dumps/import_sources.xml'), 'r').read()
    soup = BeautifulSoup(dump_file, from_encoding="utf-8")
    for tag in soup.findAll('source'):
        url = tag['url']
        name = tag['name']
        # если такого названия в БД нет, то сохраняю
        try: ImportSources.objects.get(url=url, source=name)
        except ImportSources.DoesNotExist: ImportSources(url=url, source=name).save()
    return HttpResponseRedirect(reverse("main_kai"))


def save_persons(request):
    '''
    Импорт персон
    '''
    # получаю все объекты персон
    persons_name = AfishaPersonsName.objects.using('afisha').select_related('person_id', 'person_id__country').all()
    # получаю все объекты языков
    langu = Language.objects.all()
    # записываю языки в список (что бы обращаться к списку а не к БД)
    lang_list = [l for l in langu]
    # получаю все объекты стран
    countrys = Country.objects.all()
    # записываю страны в словарь (что бы обращаться к словарю а не к БД)
    # country_d = {c.name: c for c in countrys if c} # python 2.7+
    country_dict = {}
    for c in countrys:
        country_dict[c.name.encode('utf-8')] = c
        
    def save_name(i):
        # сохраняю имя персоны если нет и возвращаю
        status, lang = (1, lang_list[0]) if i.flag == 1 else (2, lang_list[1])
        try: names = NamePerson.objects.get(language=lang, name=i.name)
        except NamePerson.DoesNotExist: names = NamePerson.objects.create(status=status, language=lang, name=i.name)
        return names
        
    for i in persons_name:
        # если есть персона в БД получаю объект персоны
        try: person = Person.objects.get(kid=i.person_id_id)
        # если нет персоны в БД
        except Person.DoesNotExist:
            # получаю дату рождения персоны
            birthday = None
            if int(i.person_id.birth_year) != 0:
                persons_b_month = '{0:0=2d}'.format(i.person_id.birth_mounth)
                persons_b_day = '{0:0=2d}'.format(i.person_id.birth_day)
                birthday = '%s-%s-%s' % (i.person_id.birth_year, persons_b_month, persons_b_day)
            # получаю страну персоны
            country = None
            if int(i.person_id.country_id) != 0 and i.person_id.country.name in country_dict:
                country = country_dict.get(i.person_id.country.name, '')
            # сохраняю персону
            person = Person.objects.create(iid=i.person_id.imdb, kid=i.person_id_id, male=i.person_id.male, born=birthday, country=country)
        # сохраняю имя
        name = save_name(i)
        try: Person.objects.get(name=name)
        except Person.DoesNotExist: person.name.add(name)
        except Person.MultipleObjectsReturned: pass
    return HttpResponseRedirect(reverse("main_kai"))


def save_films_name(request, year):
    '''
    Импорт названий фильмов
    '''
    # получаю год/диапозон
    years = year.split('_')
    from_year, to_year = years if len(years) == 2 else (years[0], years[0])
    # формирую запрос в зависимости от года
    if year == '2012': myfilter = {'{0}__{1}'.format('film_id__year', 'gte'): year,}
    elif year == '1990': myfilter = {'{0}__{1}'.format('film_id__year', 'lt'): year,}
    else: myfilter = {'{0}__{1}'.format('film_id__year', 'gte'): from_year, '{0}__{1}'.format('film_id__year', 'lte'): to_year,}
    # получаю все объекты названий фильмов по заданному году
    film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(**myfilter)
    '''
    if year == '2012': film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__gte=year)
    elif year == '1990': film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__lt=year)
    else: film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__gte=from_year, film_id__year__lte=to_year)
    '''
    # получаю объекты фильмов
    films = FilmsSources.objects.select_related('id_films').filter(source__source='Киноафиша')
    # записываю фильмы в словарь (что бы обращаться к словарю а не к БД)
    #films_dic = {f.id_films_sources: f.id_films for f in films} # python 2.7+
    films_dic = {}
    for f in films:
        films_dic[f.id_films_sources] = f.id_films

    def save_f(film, f_name, status, language):
        # если нет названия фильма в БД, то сохраняю и устанавливаю связь объект-название
        try: name = NameProduct.objects.get(status=status, language=language, name=f_name.strip())
        except NameProduct.DoesNotExist: name = NameProduct.objects.create(status=status, language=language, name=f_name.strip())
        try: Films.objects.get(name=name)
        except Films.DoesNotExist: film.name.add(name)

    for i in film_name:
        # определяю на каком языке название фильма
        # type:   1 - оригинал названия, 2 - русское название, 3 - международное название
        # status: 1 - утвержденное, 2 - временное, 5 - альтернативное
        lang = None
        stat = None
        if i.type == 2 and i.status == 1: stat = 1 # яз = русс, стат = главн.
        elif i.type == 2 and (i.status == 2 or i.status == 5): stat = 0 # яз = русс, стат = альтер.
        elif i.type == 1 and i.status == 1: stat = 1 # яз = ?, стат = главн.
        elif i.type == 1 and (i.status == 2 or i.status == 5): stat = 0 # яз = ?, стат = альтер.
        elif i.type == 3 and i.status == 2: stat = 0
        film = films_dic.get(i.film_id_id, None)
        if film and stat != None:
            if stat == 1:
                # очищаю название от html тегов, привожу в кодировку utf-8
                name = BeautifulSoup(i.name.encode('utf-8')).encode(formatter=None)
                name = name.replace('<html><body><p>','').replace('</p></body></html>','')
                # очищаю от формата изображения
                n = del_screen_type(name)
                # очищаю от спец.символов, привожу к нижнему регистру
                n = low(del_separator(n))
                # сохраняю очищенное название
                save_f(film, n, 2, lang)
            # сохраняю оригинальное название
            save_f(film, i.name, stat, lang)
    return HttpResponseRedirect(reverse("main_kai"))


def save_film(request, year):
    '''
    Импорт фильмов
    '''
    # получаю год/диапозон
    years = year.split('_')
    from_year, to_year = years if len(years) == 2 else (years[0], years[0])
    # формирую запрос в зависимости от года
    if year == '2012': myfilter = {'{0}__{1}'.format('year', 'gte'): year,}
    elif year == '1990': myfilter = {'{0}__{1}'.format('year', 'lt'): year,}
    else: myfilter = {'{0}__{1}'.format('year', 'gte'): from_year, '{0}__{1}'.format('year', 'lte'): to_year,}
    # получаю все объекты фильмов по заданному году
    films = Film.objects.using('afisha').select_related('country', 'country2', 'genre1', 'genre2', 'genre3').filter(**myfilter)
    '''
    if year == '2012': films = Film.objects.using('afisha').select_related('country', 'country2', 'genre1', 'genre2', 'genre3').filter(year__gte=year)
    elif year == '1990': films = Film.objects.using('afisha').select_related('country', 'country2', 'genre1', 'genre2', 'genre3').filter(year__lt=year)
    else: films = Film.objects.using('afisha').select_related('country', 'country2', 'genre1', 'genre2', 'genre3').filter(year__gte=from_year, year__lte=to_year)
    '''
    # получаю все объекты типов/статусов персон
    relations = PersonsRelationFilms.objects.using('afisha').select_related('type_act_id', 'status_act_id').all()
    # получаю объекты персон
    actors = Person.objects.all()
    # записываю персоны в словарь (что бы обращаться к словарю а не к БД)
    # actors_dict = {ac.id: ac for ac in actors} # python 2.7+
    actors_dict = {}
    for ac in actors:
        actors_dict[ac.id] = ac
    # получаю объекты типов персон
    actions = Action.objects.all()
    # записываю типы в словарь (что бы обращаться к словарю а не к БД)
    # actions_dict = {a.name: a for a in actions} # python 2.7+
    actions_dict = {}
    for a in actions:
        actions_dict[a.name] = a
    # получаю объекты статусов персон
    status_act = StatusAct.objects.all()
    # записываю статусы в словарь (что бы обращаться к словарю а не к БД)
    # status_dict = {s.name: s for s in status_act} # python 2.7+
    status_dict = {}
    for s in status_act:
        status_dict[s.name] = s
    # получаю объекты жанров
    genres_obj = Genre.objects.all()
    # записываю жанры в словарь (что бы обращаться к словарю а не к БД)
    # genres_dict = {g.name: g for g in genres} # python 2.7+
    genres_dict = {}
    for g in genres_obj:
        genres_dict[g.name.encode('utf-8')] = g
    # получаю объекты стран
    countrys_obj = Country.objects.all()
    # записываю страны в словарь (что бы обращаться к словарю а не к БД)
    # countrys_dict = {co.name: co for co in countrys_obj} # python 2.7+
    countrys_dict = {}
    for co in countrys_obj:
        countrys_dict[co.name.encode('utf-8')] = co
    # получаю объекты источников
    imp_sources = ImportSources.objects.all()
    # записываю истоники в словарь (что бы обращаться к словарю а не к БД)
    # imp_sources_dict = {imp.source: imp for imp in imp_sources} # python 2.7+
    imp_sources_dict = {}
    for imp in imp_sources:
        imp_sources_dict[imp.source.encode('utf-8')] = imp
    '''
    def get_lang_for_name(countrys):
        lang = None
        if countrys[0]:
            try:
                country = LanguageCountry.objects.get(country__name=countrys[0])
                lang = country.language_id
            except LanguageCountry.DoesNotExist: pass
        return lang
    '''
    def save_budget(comment):
        # получаю/сохраняю бюджет фильма
        bu_sum = get_budget(comment)
        budget = None
        if bu_sum[0]:
            try: budget = Budget.objects.get(budget=bu_sum[0], currency=bu_sum[1])
            except Budget.DoesNotExist: budget = Budget.objects.create(budget=bu_sum[0], currency=bu_sum[1])
        return budget

    def save_runtime(runtime):
        # получаю/сохраняю хронометраж фильма
        film_runtime = re.sub('\D','', runtime)
        run = None
        if film_runtime != '' and film_runtime != '0':
            try: run = Runtime.objects.get(runtime=film_runtime)
            except Runtime.DoesNotExist: run = Runtime.objects.create(runtime=film_runtime) 
        return run

    def save_films_sources(id_obj, film_obj, source_name):
        # связь фильма с источником
        source = imp_sources_dict.get(source_name, '')
        FilmsSources(id_films_sources=id_obj, id_films=film_obj, source=source).save()

    def limits(film_limits):
        # ограничения по возрасту
        limit = None
        if film_limits and film_limits != '':
            if '13' in film_limits: limit = 'PG'
            elif '16' in film_limits: limit = 'PG-13'
            elif '18' in film_limits: limit = 'R'
            elif '21' in film_limits: limit = 'NC-17'
            else: limit = 'G'
        return limit

    def film_type(genres):
        # тип фильма
        ftype= None
        for ge in genres:
            if ge:
                if 'Animation' in ge.name_en:
                    ftype = 'A'
                    break
                elif 'Musical' in ge.name_en or 'Music' in ge.name_en:
                    ftype = 'M'
                    break
                elif 'Documentary' in ge.name_en:
                    ftype = 'D'
                    break
                else:
                    ftype = 'I'
        return ftype
            
    for i in films:
        if i.year != '':
            # получаю данные о фильме
            comment = 'None' if i.comment is None else i.comment.encode('utf-8')
            genre1_name = i.genre1 if int(i.genre1_id) != 0 else None
            genre2_name = i.genre2 if int(i.genre2_id) != 0 else None
            genre3_name = i.genre3 if int(i.genre3_id) != 0 else None
            genres = (genre1_name, genre2_name, genre3_name)
            country1_name = i.country.name if int(i.country_id) != 0 else None
            country2_name = i.country2.name if int(i.country2_id) != 0 else None
            countrys = (country1_name, country2_name)
            # если фильма нет, то сохраняю
            try: film = FilmsSources.objects.get(id_films_sources=i.id, source__source='Киноафиша')
            except FilmsSources.DoesNotExist:
                # получаю ограничения по возрасту
                limit = limits(i.limits)
                # получаю бюджет
                budget = save_budget(comment)
                # получаю хронометраж
                run = save_runtime(i.runtime)
                # получаю тип
                ftype = film_type(genres)
                # сохраняю фильм
                film = Films.objects.create(release_start=None, release_end=str(i.year) + '-12-31', rated=limit, budget=budget, image_parameter=None, sound_parameter=None, film_type=ftype, note=i.description, runtime=run)
                # связываю с жанрами
                for g in genres:
                    if g:
                        genre = genres_dict.get(g.name, '')
                        film.genre.add(genre)
                # связываю со странами
                for c in countrys:
                    if c:
                        country = countrys_dict.get(c, '')
                        film.countrys.add(country)
                # связываю с персонами
                for j in relations:
                    if j.film_id_id == i.id:
                        if j.person_id_id in actors_dict:
                            actor = actors_dict.get(j.person_id_id, '')
                            action = actions_dict.get(j.type_act_id.type_act, '')
                            status_act = status_dict.get(j.status_act_id.status_act, '')
                            RelationFP.objects.create(person=actor, status_act=status_act, action=action, product=film)
                # связываю с источником
                save_films_sources(i.id, film, 'Киноафиша')
                id_imdb = i.idalldvd if i.idalldvd and i.idalldvd != 0 else None
                rating = float(i.imdb.replace(',','.')) if i.imdb and i.imdb != '' else None
                # запись инфо imdb
                if id_imdb:
                    try: IMDB.objects.get(id_imdb=id_imdb)
                    except IMDB.DoesNotExist: IMDB(id_imdb=id_imdb, rating=rating).save()
                    save_films_sources(id_imdb, film, 'IMDb')
    return HttpResponseRedirect(reverse("main_kai"))


def save_cinema(request):
    '''
    Импорт кинотеатров
    '''
    from api.func import clear_links
    # получаю все объекты кинотеатров
    cinema = Movie.objects.using('afisha').select_related('city', 'metro', 'set_field').all()
    # получаю объект русского языка
    lang = Language.objects.get(pk=1)
    # получаю объекты метро
    metro = Metro.objects.all()
    # записываю метро в словарь (что бы обращаться к словарю а не к БД)
    # metro_dict = {m.name: m for m in metro} # python 2.7+
    metro_dict = {}
    for m in metro:
        metro_dict[m.name.encode('utf-8')] = m
    # получаю объекты сетей кинотеатров
    circuit = CinemaCircuit.objects.all()
    # записываю сети в словарь (что бы обращаться к словарю а не к БД)
    # circuit_dict = {ci.name: ci for ci in circuit} # python 2.7+
    circuit_dict = {}
    for ci in circuit:
        circuit_dict[ci.name.encode('utf-8')] = ci
    # получаю объекты типа улиц
    s_type_obj = StreetType.objects.all()
    # записываю типы в словарь (что бы обращаться к словарю а не к БД)
    # s_type_dict = {s.name: s for s in s_type_obj} # python 2.7+
    s_type_dict = {}
    for s in s_type_obj:
        s_type_dict[s.name.encode('utf-8')] = s
    types = []
    char_house = None
    num_house = None
    street = None
    # регулярное выражение для поиска телефоных номерв
    reg_phone = '[?\+\d\s]*[\(\d+?\-\)]*\s*?[\d?\-?\–?\—?\ ]+'
    # регулярное выражение для поиска типа телефоных номерв
    reg_type = 'авто|заказ|касс|брон|факс|справ|админ|директор|бух'
    # регулярное выражение для поиска типа улицы
    reg_street_type = 'ул\.|ул\,|Ул\.|улица|^ул|пл\.|пл\,|Площадь|площадь|пр\.|Пр\.|пр\-т|Пр\-т|проспект|просп|бульвар|набережная|наб|ш\.|шоссе|Шоссе|пер\,|пер\.|переулок|аллея|микрорайон|Микрорайон|мкр|микр\.|квартал|квл|километр|км|проезд|пр\-д|тракт|парк'
    # получаю типы улиц из БД
    steet_types = StreetType.objects.all()
    for s in steet_types:
        # название типа улицы и id типа записываю в список как одно выражение
        types.append('%s+%s' % (s, s.id))
        # получаю альтернативные названия типов улиц для конкретного типа улицы
        try: street_alter_types = AlterStreetType.objects.filter(value=s.id)
        except AlterStreetType: street_alter_types = ''
        types = ['%s+%s' % (st, s.id) for st in street_alter_types]
        # название альт.типа улицы и id альт.типа записываю в список как одно выражение
    #files = {str(st_ty).replace('.', '\.').replace(',', '\,').replace('-', '\-'): st_ty for st_ty in types} # python 2.7+
    files = {}
    for st_ty in types:
        files[str(st_ty).replace('.', '\.').replace(',', '\,').replace('-', '\-')] = st_ty
    def get_phone(res, res_type):
        # доп.метод для обработки тел.номеров
        list_phones = []
        res_type = res_type[0] if res_type else None
        res = res[0] if res else None
        if len(res) < 2: res = None
        res = str(res).replace(' -','').replace(' –','').replace(' —','').strip()
        return (res, res_type)
        
    def save_name_cinema(status, name):
        # получение/сохранение названий кинотеатров
        try: cin_name = NameCinema.objects.get(status=status, name=i.name)
        except NameCinema.DoesNotExist: cin_name = NameCinema.objects.create(status=status, language=lang, name=name)
        return cin_name
        
    for i in cinema:
        # открытие
        # если найдена инф. о открытии кинотеатра
        if re.findall('Открыт|открыт|открытия', i.comment.encode('utf-8')):
            # получаю месяц открытия (файл 'func.py')
            month = get_month(i.comment.encode('utf-8'))
            # нахожу день открытия
            find_day = re.findall(' \d{1,2} ', i.comment.encode('utf-8'))
            day = '{0:0=2d}'.format(int(find_day[0].strip())) if find_day else '01' # ----------------
            # нахожу год открытия
            year = re.findall(' \d{4}', i.comment.encode('utf-8'))
            year = year[0].strip() if year else 0
            # если есть год, строю всю дату открытия
            opening = '%s-%s-%s 08:00:00' % (year, month, day) if int(year) != 0 else None
        # если не найдена инф. о открытии кинотеатра, то даты открытия нет
        else: opening = None

        # адреса
        # использую рег.выражение для поиска типа улицы
        result_reg_street_type = re.findall(reg_street_type, i.address)
        # получаю тип улицы (файл 'func.py')
        street_type = streettype(result_reg_street_type)
        # удаляю тип улицы из общего адреса
        street = re.sub(reg_street_type, '', i.address)
        # если есть знак препинания, то
        if re.findall('\,', street):
            # по нему разбиваю адрес
            street_and_house = street.split(',')
            # получаю номер дома
            try:
                number_house = street_and_house[1]
                # если дробный номер дома получаю его
                num_house = re.findall('\d{0,}\/?\d{1,}', number_house)
                if num_house:
                    num_house = num_house[0]
                    # если есть буква дома, то получаю ее
                    char_house = re.findall('[а-яА-Я]{2}$', number_house)
                else:
                    street = re.sub(reg_street_type, '', number_house)
                    try: number_house = street_and_house[1]
                    except IndexError: num_house = None
                    char_house = None
                    street_name = street_and_house[0]
                char_house = char_house[0] if char_house else None
            except IndexError: pass
            street_name = street_and_house[0]
        else:
            num_house = re.findall('\d{0,}\/?\d{1,}$', street)
            num_house = num_house[0] if num_house else None
            street_name = re.sub('\d{0,}\/?\d{1,}$','', street)
        if char_house: char_house = str(char_house).replace('«', '').replace('»', '')
        # очищаю название улицы от лишних знаков препинания и пробелов
        street_name = street = re.sub(' \.', '', street_name)
        street_name = street = re.sub('^\.', '', street_name)
        street_name = street_name.strip()
        if street_name == '' or street_name == '.' or street_name == '..':
            street_type = None

        # телефоны
        phone_dic = {}
        def find_phone(phone):
            # ищу тел.номера используя рег.выражение
            result_reg_phone = re.findall(reg_phone, phone)
            # ищу тип телефона используя рег.выражение
            result_reg_type = re.findall(reg_type, phone)
            # обработка тел.номеров
            result_phone = get_phone(result_reg_phone, result_reg_type)
            # создаю словарь телефонов и их типов
            return {result_phone[0]: get_type_phone(result_phone[1])}

        # если есть номер телефона
        if i.phones != '':
            # если есть знак препинания, то
            if re.findall('\,', i.phones.encode('utf-8')):
                # по нему разбиваю телефон
                cinema_phone = i.phones.encode('utf-8').split(',')
                try:
                    for ph in cinema_phone:
                        phone_dic.update(find_phone(ph))
                except: pass
            # если нет знака препинания, то
            else: phone_dic.update(find_phone(i.phones.encode('utf-8')))

        # город
        # получаю объект город для кинотеатра
        try: city = City.objects.get(name__name=i.city.name)
        except City.DesNotExist: city = None
        # метро
        # получаю объект метро для кинотеатра
        try: metro = metro_dict.get(i.metro.name, None)
        except AttributeError: metro = None
        # сайт
        # получаю объект сайт для кинотетра
        site = None 
        if i.site != '':
            url = clear_links(i.site.encode('utf-8'))
            try: site = Site.objects.get(url=url)
            except Site.DoesNotExist: site = Site.objects.create(url=url, site_type='O')

        # получаю тип улицы
        if street_type: s_type = s_type_dict.get(street_type, None)
        # получаю сеть кинотеатра
        try: ci_set = circuit_dict.get(i.set_field.name, None)
        except AttributeError: ci_set = None

        # сохраняю название кинотеатра
        cin_name1 = save_name_cinema(1, i.name)
        # очищаю название от спец.символов и привожу в нижний регистр
        slug_name = low(del_separator(i.name))
        # сохраняю очищенное название кинотеатра
        cin_name2 = save_name_cinema(2, slug_name)

        if city:
            # если нет кинотеатра записываю
            try: Cinema.objects.get(code=i.id)
            except Cinema.DoesNotExist:
                cin = Cinema.objects.create(city=city, cinema_circuit=ci_set, street_type=s_type, street_name=street_name, number_housing=None, number_hous=num_house, letter_housing=char_house, zip=i.ind, opening=opening, note=i.comment, code=i.id)
                # создаю связь объект-название
                cin.name.add(cin_name1, cin_name2)
                # связываю с метро
                if metro: cin.metro.add(metro)
                # связываю с сайтом
                if site: cin.site.add(site)
                # связываю с телефоном
                for key, val in phone_dic.iteritems():
                    try: cin.phone.add(Phone.objects.get(phone=key))
                    except Phone.DoesNotExist:
                        phone = Phone.objects.create(phone=key, phone_type=val)
                        cin.phone.add(phone)
    return HttpResponseRedirect(reverse("main_kai"))


def create_hallname(status, lang, name):
    '''
    Получение/сохранение названия зала
    '''
    try: hname = NameHall.objects.get(status=status, language=lang, name=name)
    except NameHall.DoesNotExist: hname = NameHall.objects.create(status=status, language=lang, name=name)
    return hname

def create_hall(names, number, places, cinema):
    '''
    Получение/сохранение зала
    '''
    try: hall = Hall.objects.get(name=names[0], number=number, cinema=cinema)
    except Hall.DoesNotExist:
        hall = Hall.objects.create(number=number, screen_size_w=None, screen_size_h=None, seats=places,  image_format='', sound_format='', max_price=None, min_price=None, cinema=cinema)
        # создаю связь объект-название
        if len(names) == 2: hall.name.add(names[0], names[1])
        else: hall.name.add(names[0])
    return hall

def save_hall(request):
    '''
    Импорт залов
    '''
    # получаю все объекты залов
    halls = AfishaHalls.objects.using('afisha').select_related('id_name', 'movie').all()
    # получаю объект русского языка
    lang = Language.objects.get(pk=1)
    # получаю объекты кинотеатров
    cinema_obj = Cinema.objects.all()
    # записываю кинотеатры в словарь (что бы обращаться к словарю а не к БД)
    # cinema_dict = {c.code: c for c in cinema} # python 2.7+
    cinema_dict = {}
    for c in cinema_obj:
        cinema_dict[c.code] = c
    count = 1
    old_cinema = ''
    for i in halls:
        hall_name = i.id_name.name
        hall_cinema_id = i.movie_id
        number = 0
        # если зал не указан
        if 'без указания зала' in hall_name: name = hall_name
        # если название зала подходит под шаблон 'Зал №1'
        elif re.findall('Зал №|зал №', hall_name):
            number = re.findall('\d+$', hall_name)
            number = number[0] if number else 1
            name = 'Зал'
        # если есть название зала 
        else:
            if old_cinema == hall_cinema_id: count += 1 
            name = hall_name
        old_cinema = hall_cinema_id
        cinema = cinema_dict.get(hall_cinema_id, None)
        if cinema:
            # сохраняю название зала
            name1 = create_hallname(1, lang, name)
            # очщаю название зала от спец.символов и привожу к нижнему регистру
            slug_name = low(del_separator(name))
            # сохраняю очищенное название зала
            name2 = create_hallname(2, lang, slug_name)
            # сохраняю зал
            create_hall((name1, name2), number, i.places, cinema)
    return HttpResponseRedirect(reverse("main_kai"))


def get_hall_obj(num, name, movie, lang):
    '''
    Получение объекта Зал
    '''
    hall = None
    try: hall = Hall.objects.get(name__name=name, number=num, cinema=movie)
    except Hall.DoesNotExist:
        if name == 'без указания зала':
            name1 = create_hallname(1, lang, 'без указания зала')
            name2 = create_hallname(2, lang, 'безуказаниязала')
            hall = create_hall((name1, name2), 0, 0, cinema)
    return hall

def get_pars_hall(hall_name):
    '''
    Получение названия/номера зала
    '''
    num = 0
    name = hall_name
    if 'без указания зала' in hall_name:
        name = hall_name
    elif re.findall('Зал №|зал №', hall_name):
        num = re.findall('\d+$', hall_name)
        num = num[0] if num else 1
        name = 'Зал'
    return {'num': num, 'name': name}


def save_schedule(sch_date, hall, film, film_name):
    '''
    Сохранение сеанса
    '''
    try: demo = Demonstration.objects.get(name=film_name, time=sch_date, place=hall)
    except Demonstration.DoesNotExist:
        demo = Demonstration.objects.create(name=film_name, time=sch_date, place=hall)
        session = Session.objects.create(demonstration=demo, number=1, average_price=None, number_people=None)
        session.film.add(film)


def save_kai_sch(request):
    '''
    Импорт сеансов
    '''
    from django.db.models import Q
    # получаю объект русского языка
    lang = Language.objects.get(pk=1)
    # получаю объекты кинотеатров
    cinema_obj = Cinema.objects.all()
    # записываю кинотеатры в словарь (что бы обращаться к словарю а не к БД)
    # cinema_dict = {c.code: c for c in cinema} # python 2.7+
    cinema_dict = {}
    for c in cinema_obj:
        cinema_dict[c.code] = c
    # получаю объекты источников фильмов
    films_sources = FilmsSources.objects.filter(source__source='Киноафиша')
    # записываю источники фильмов в словарь (что бы обращаться к словарю а не к БД)
    # films_sources_dict = {f.code: f for f in films_sources} # python 2.7+
    films_sources_dict = {}
    for f in films_sources:
        films_sources_dict[f.id_films_sources] = f
    now = datetime.datetime.now()
    date_now = now.strftime('%Y-%m-%d')
    fdate = now.strftime('%Y-%m-%d %H:%M:%S')
    # получаю все объекты сеансов
    schedule_obj = Schedule.objects.using('afisha').select_related('movie_id', 'movie_id__city', 'film_id', 'hall_id', 'hall_id__id_name').filter(Q(date_from__gte=date_now) | Q(date_from__lt=date_now) & Q(date_to__gte=date_now)).order_by('date_from')
    # получаю объекты названий фильмов
    film_name = FilmsName.objects.using('afisha').filter(type=2, status=1)
    # записываю названия фильмов в словарь (что бы обращаться к словарю а не к БД)
    #film_names = {f.film_id_id: f for f in film_name} # python 2.7+
    film_names_dict = {}
    for f in film_name:
        film_names_dict[f.film_id_id] = f
    # получаю последний день текущего месяца
    day = calendar.monthrange(int(now.strftime('%Y')), int(now.strftime('%m')))[1]
    def schedule(day_from, day_to, year, month, time):
        # обработка сеансов, если сеанс на текущую или на следующие даты то сохраняю
        while day_from < (day_to + 1):
            day = '{0:0=2d}'.format(day_from)
            day_from += 1
            schedule_date = '%s-%s-%s %s' % (year, month, day, time)
            if schedule_date >= fdate:
                save_schedule(schedule_date, hall, film.id_films, film_name)

    for i in schedule_obj:
        city_name = i.movie_id.city.name
        # получаю объект города
        try: city = City.objects.get(name__name=city_name)
        except City.DoesNotExist: city = None
        if city:
            movie_id = i.movie_id_id
            # получаю объект кинотеатра
            cinema = cinema_dict.get(movie_id, None)
            if cinema:
                # получаю объект зала
                hall_name = 'без указания зала' if int(i.hall_id_id) == 999 else i.hall_id.id_name.name
                hall_data = get_pars_hall(hall_name.strip())
                hall = get_hall_obj(hall_data['num'], hall_data['name'], cinema, lang)
                if hall:
                    # получаю объект названия фильма
                    film_name = film_names_dict.get(i.film_id_id, None)
                    film_name = film_name.name
                    # получаю объект фильма
                    film = films_sources_dict.get(i.film_id_id, None)
                    if film:
                        # получаю дату
                        date_from = str(i.date_from).split('-')
                        date_to = str(i.date_to).split('-')
                        session = AfishaSession.objects.using('afisha').filter(schedule_id=i.id).order_by('session_list_id')
                        for s in session:
                            # получаю время
                            times = SessionList.objects.using('afisha').get(id=s.session_list_id)
                            time = times.time
                            # если сеансы заканчиваются в след.месяце
                            if date_from[1] < date_to[1]:
                                # от начальной даты до конца месяца
                                # передаю переменнные: день (начало сеансов), последний день в этом месяце, 
                                # год, месяц (в котором сеансы), время сеанса
                                schedule(int(date_from[2]), int(day), date_from[0], date_from[1], time)
                                # от начала месяца до конечной даты
                                schedule(1, int(date_to[2]), date_from[0], date_to[1], time)
                            #  от начальной даты до конечной даты
                            else: schedule(int(date_from[2]), int(date_to[2]), date_from[0], date_from[1], time)
                    # если нет фильма запись в лог
                    else: logger(**{'event': 1, 'code': 4, 'bad_obj': film_name.encode('utf-8'), 'obj1': i.film_id_id})
                # если нет зала запись в лог
                else: logger(**{'event': 1, 'code': 3, 'bad_obj': hall_data['name'], 'obj1': cinema.encode('utf-8').strip(), 'obj2': movie_id, 'obj3': city.name.encode('utf-8')})
            # если нет кинотеатра запись в лог
            else: logger(**{'event': 1, 'code': 2, 'bad_obj': cinema.encode('utf-8').strip(), 'obj1': city.name.encode('utf-8'), 'obj2': movie_id})
        # если нет города запись в лог
        else: logger(**{'event': 1, 'code': 1, 'bad_obj': city.name, 'obj1': city.id})

    '''
    def schedule(day_from, day_to, year, month, time):
        while day_from < (day_to + 1):
            day = '{0:0=2d}'.format(day_from)
            day_from += 1
            schedule_date = '%s-%s-%s %s' % (year, month, day, time.encode('utf-8').strip())
            if schedule_date >= fdate:
                save_schedule(schedule_date, hall, film.id_films, film_name)                    

    for tag in soup.findAll('city'):
        city = get_city_obj(tag['name'].encode('utf-8'))
        if city:
            for m in tag.findAll('movie'):
                movie = get_cinema_obj(m['id'])
                if movie:
                    for h in m.findAll('hall'):
                        hall_id = h['id']
                        hall_data = get_pars_hall(h['name'].encode('utf-8').strip())
                        hall = get_hall_obj(hall_data['num'], hall_data['name'], movie)
                        if hall:
                            for f in h.findAll('film'):
                                film_name = f['name'].encode('utf-8').strip()
                                film = get_film_obj(f['id'])
                                if film:
                                    for d in f.findAll('date'):
                                        date_from = d['start'].encode('utf-8').split('-')
                                        date_to = d['finish'].encode('utf-8').split('-')
                                        for t in d.findAll('time'):
                                            time = t.string
                                            # если сеансы заканчиваются в след.месяце
                                            if date_from[1] < date_to[1]:
                                                # от начальной даты до конца месяца
                                                # передаю переменнные: день (начало сеансов), последний день в этом месяце, 
                                                # год, месяц (в котором сеансы), время сеанса
                                                schedule(int(date_from[2]), int(day), date_from[0], date_from[1], time)
                                                # от начала месяца до конечной даты
                                                schedule(1, int(date_to[2]), date_from[0], date_to[1], time)
                                            else:
                                                #  от начальной даты до конечной даты
                                                schedule(int(date_from[2]), int(date_to[2]), date_from[0], date_from[1], time)
                                else:
                                    logger(**{'event': 1, 'code': 4, 'bad_obj': film_name, 'obj1': f['id']})
                        else:
                            logger(**{'event': 1, 'code': 3, 'bad_obj': hall_data['name'], 'obj1': m['name'].encode('utf-8').strip(), 'obj2': m['id'], 'obj3': city.name.encode('utf-8')})
                else:
                    logger(**{'event': 1, 'code': 2, 'bad_obj': m['name'].encode('utf-8').strip(), 'obj1': city.name.encode('utf-8'), 'obj2': m['id']})
        else:
            logger(**{'event': 1, 'code': 1, 'bad_obj': city.name, 'obj1': city.id})
    '''
    return HttpResponseRedirect(reverse("main_kai"))




@never_cache
def get_log(request, event):
    '''
    вывод лога
    '''
    if not request.user.is_anonymous(): login_counter(request)
    log = Logger.objects.filter(event=event)
    log_count = log.count()
    return render_to_response('kai/test_logger.html', {'log': log, 'log_count': log_count, 'event': int(event)}, context_instance=RequestContext(request))


@never_cache
def clear_log(request):
    '''
    очистка лога
    '''
    if request.method == 'POST':
        event_flag = request.POST['event']
        Logger.objects.filter(event=event_flag).delete()
    return HttpResponseRedirect(reverse("get_log", kwargs={'event': event_flag}))


def get_schedule(request):
    '''
    вывод сенсов с фильтами по городу и кинотеатру
    '''
    if not request.user.is_anonymous(): login_counter(request)
    # получаю объекты сеансов
    schedule = Session.objects.select_related('demonstration', 'demonstration__place', 'demonstration__place__cinema', 'demonstration__place__cinema__city').filter(demonstration__time__gte=fdate)
    de = []
    ci = []
    sch = []
    city_id = None
    cinema_id = None
    # выборка городов в которых есть сеансы
    for i in schedule.order_by('demonstration__place__cinema__city__name__name'):
        if i.demonstration.place.cinema.city not in de: de.append(i.demonstration.place.cinema.city)
    if request.method == 'POST':
        # если редактором выбран город, выборка кинотеатров в этом городе где есть сеансы
        if 'city' in request.POST and request.POST['city'] != '':
            city_id = int(request.POST['city'])
            for i in schedule.order_by('demonstration__place__cinema__name__name'):
                if i.demonstration.place.cinema.city_id == city_id and i.demonstration.place.cinema not in ci: 
                    ci.append(i.demonstration.place.cinema)
            # если редактором выбран кинотеатр, выборка сеансов в этом кинотеатре
            if 'cinema' in request.POST and request.POST['cinema'] != '':
                try:
                    cinema_id = int(request.POST['cinema'])
                    Demonstration.objects.filter(place__cinema__id = cinema_id, place__cinema__city__id = city_id)[0]
                    for i in schedule.order_by('demonstration__name', 'demonstration__time'):
                        if i.demonstration.place.cinema_id == cinema_id: sch.append(i)
                except IndexError: pass
    return render_to_response('kai/test_schedule.html', {'city': de, 'city_id': city_id, 'cinema': ci, 'cinema_id': cinema_id, 'schedule': sch}, context_instance=RequestContext(request))
    
    
    
#################### --- тестовые методы

def get_server_ip(request):
    '''
    ip сервера
    '''
    import socket
    return HttpResponse(socket.gethostbyname(request.META['SERVER_NAME']))
 

def del_schedule(request):
    '''
    удаление сеансов
    '''
    if request.method == 'POST':
        Demonstration.objects.all().delete()
        Session.objects.all().delete()
    return HttpResponseRedirect(reverse("get_schedule"), context_instance=RequestContext(request))
    
    
@never_cache
def get_films(request):
    '''
    вывод фильмов 2012 (100 шт)
    '''
    if not request.user.is_anonymous(): login_counter(request)
    film = FilmsSources.objects.select_related(depth=3).filter(source__source='Киноафиша', id_films__release_end='2012-12-31')[:100]
    #imdb_rel = FilmsSources.objects.select_related(depth=1).filter(source__source='IMDb')
    #imdb = IMDB.objects.all()
    return render_to_response('kai/test_films.html', {'film': film}, context_instance=RequestContext(request))
    
@never_cache
def get_cinema(request):
    '''
    вывод кинотеатров (100 шт)
    '''
    if not request.user.is_anonymous(): login_counter(request)
    cinema = Cinema.objects.select_related(depth=2).all()[:100]
    halls = Hall.objects.select_related(depth=1).all()
    return render_to_response('kai/test_cinema.html', {'cinema': cinema, 'halls': halls}, context_instance=RequestContext(request))

'''    
@never_cache
def get_schedule(request):
    schedule = Session.objects.select_related(depth=3).order_by('demonstration__place__cinema__city__name', 'demonstration__place__cinema__name', 'demonstration__time').all()[:100]
    return render_to_response('kai/test_schedule.html', {'schedule': schedule}, context_instance=RequestContext(request))
'''
    
    

def save_films_name2(request, year):
    '''
    тестовый метод сохроанения только названий фильмов, без связей
    '''
    years = year.split('_')
    from_year, to_year = years if len(years) == 2 else (years[0], years[0])
    if year == '2012': film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__gte=year)
    elif year == '1990': film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__lt=year)
    else: film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__year__gte=from_year, film_id__year__lte=to_year)
    def save_f(f_name, status, language):
        try: NameProduct.objects.get(status=status, language=language, name=f_name.strip())
        except NameProduct.DoesNotExist: NameProduct.objects.create(status=status, language=language, name=f_name.strip())
    errors = ''
    for i in film_name:
        lang = None
        stat = None
        if i.type == 2 and i.status == 1: stat = 1 # яз = русс, стат = главн.
        elif i.type == 2 and (i.status == 2 or i.status == 5): stat = 0 # яз = русс, стат = альтер.
        elif i.type == 1 and i.status == 1: stat = 1 # яз = ?, стат = главн.
        elif i.type == 1 and (i.status == 2 or i.status == 5): stat = 0 # яз = ?, стат = альтер.
        elif i.type == 3 and i.status == 2: stat = 0
        if stat != None:
            try:
                if stat == 1:
                    name = BeautifulSoup(i.name)
                    name = name.encode('utf-8').replace('<html><body><p>','').replace('</p></body></html>','').replace('&amp;', '&')
                    n = del_screen_type(name)
                    n = low(del_separator(n))
                    save_f(n, 2, lang)
                save_f(i.name, stat, lang)
            except:
                errors += str(i.name) + '<hr />'
    if errors:
        return HttpResponse(errors)
    return HttpResponseRedirect(reverse("main_kai"))

@never_cache
def get_film_names(request):
    '''
    выод названий фильмов
    '''
    film = NameProduct.objects.filter(status=1)
    text = ''
    for i in film:
        text += str(i.name.encode('utf-8')) + '<br />'
    return HttpResponse(text)

@never_cache
def test_search_name(request):
    '''
    тест. измерение скорости поиска фильма в старой и новой БД
    '''
    if 'q' in request.GET:
        ch = True if 'db' in request.GET else False
        q = request.GET['q']
        if ch:
            t1 = time.time()
            try:
                film = FilmsName.objects.using('afisha').filter(name=q)[0]
                msg = 'Найден'
            except IndexError: msg = 'НЕ найден'
            runtime = time.time()-t1
        else:
            t1 = time.time()
            try:
                film = NameProduct.objects.filter(name=q)[0]
                msg = 'Найден'
            except IndexError: msg = 'НЕ найден'
            runtime = time.time()-t1
        return render_to_response('kai/test_search_time.html', {'msg': msg, 'runtime': runtime, 'q': q, 'ch': ch}, context_instance=RequestContext(request))
    return render_to_response('kai/test_search_time.html', context_instance=RequestContext(request))
            

### ---- конец тестовые методы


