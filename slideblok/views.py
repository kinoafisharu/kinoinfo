#-*- coding: utf-8 -*-
import collections
import operator
import datetime
import time

from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.template.context import RequestContext
from django.db.models import Q

from bs4 import BeautifulSoup
from collections import OrderedDict

from base.models import *
from release_parser.views import schedules_feed, releases_feed
from release_parser.ajax import get_film_likes
from api.func import age_limits
from api.views import get_film_data, film_poster2
from api.models import *
from user_registration.func import login_counter, org_peoples
from news.views import cut_description
from movie_online.views import get_film_player
from release_parser.kinoafisha_admin import boxoffice_func
from articles.views import pagination as pagi
from movie_online.IR import check_int_rates_inlist


def tofirstdayinisoweek(year, week):
    ret = datetime.datetime.strptime('%04d-%02d-1' % (year, week), '%Y-%W-%w')
    if datetime.date(year, 1, 4).isoweekday() > 4:
        ret -= datetime.timedelta(days=7)
    return ret

def get_cityName(request):
    return 1 

def get_data_show(kid_list):
    # получение описания
    dic_temp_film_info = {}
    films = Film.objects.using('afisha').select_related('country', 'genre1', 'genre3', 'genre2').filter(id__in=kid_list)
    for i in films:
        film_info = {}
        if i.country:
            film_info[1] = i.country.name + ", "
        if i.year:
            film_info[2] = i.year + ", "

        if i.runtime:
            film_info[3] = i.runtime + ", "
        if i.genre1:
            film_info[4] = i.genre1.name + ", " + "\n"
        if i.genre1 and i.genre2:
            film_info[4] = i.genre1.name + " / " + i.genre2.name + ", " + "\n"
        if i.genre1 and i.genre2 and i.genre3:
            film_info[4] = i.genre1.name + " / " + i.genre2.name + " / " + i.genre3.name + ", " + "\n"
        if i.description:
            film_info[5] = i.description[:100] + "..."

        film_info = OrderedDict(sorted(film_info.items(), key=lambda t: t[0]))
        dic_temp_film_info[int(i.id)] = film_info

    dic_film_info = {}
    for i in kid_list:
        try:
            dic_film_info[i] = dic_temp_film_info[i]
        except:
            dic_film_info[i] = None

    # получение рейтингов
    #int_rate  = 0
    #show_ir   = 0
    #dic_film_rate = {'int_rate': 0, 'show_ir': 0}
    #for i in kid_list:
        #dic_film_rate[i] = {'int_rate': 0, 'show_ir': 0}
    #IR = IntegralRating.objects.filter(afisha_id__in = kid_list)
    #for i in IR:
        #if i.i_rate:
            #int_rate = i.i_rate
            #show_ir = i.i_rate
        #else:
            #show_ir = None

        #if int_rate  >= 7.5:
            #int_rate = 5
        #elif int_rate  < 7.5 and int_rate  >= 6:
            #int_rate = 4
        #elif int_rate  < 6 and int_rate  >= 5:
            #int_rate = 3
        #elif int_rate  < 5 and int_rate  > 0:
            #int_rate = 2
        #elif int_rate  == 0:
            #int_rate = 0
        #dic_film_rate[int(i.afisha_id)] = {'int_rate':int_rate , 'show_ir':show_ir}

    return dic_film_info#, dic_film_rate


@never_cache
#@debug_timer
def main(request):
    REG_ID = re.compile(r'^\d+')

    film_param = REG_ID.findall(request.GET.get('status', ''))
    film_id = REG_ID.findall(request.GET.get('id1', ''))

    if film_param and int(film_param[0]) == 1 and film_id:
        #return get_film_func(request, film_id[0])
        return HttpResponseRedirect(reverse('get_film', kwargs={'id': film_id[0]}))
    else:
        return main_page(request)


# КИНОАФИША # - на базе киноинфо
def releasedata(films_dict, descriptions_dict, persons=False, likes=False, trailers=False, reviews=True, poster_size='big', check_opinions=False):

    f = Film.objects.using('afisha').select_related('genre1', 'genre2', 'genre3', 'country', 'country2').filter(pk__in=films_dict.keys())

    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid__in=[301, 300], objpkvalue__in=films_dict.keys())
    posters = {}
    for p in poster_obj:
        if posters.get(p.objpkvalue):
            if p.objtypeid == 301:
                posters[p.objpkvalue]['poster'].append(p)
            else:
                posters[p.objpkvalue]['slides'].append(p)
        else:
            posters[p.objpkvalue] = {'poster': [], 'slides': []}
            if p.objtypeid == 301:
                posters[p.objpkvalue]['poster'].append(p)
            else:
                posters[p.objpkvalue]['slides'].append(p)

    fnames = FilmsName.objects.using('afisha').filter(film_id__id__in=films_dict.keys(), status=1, type__in=(1, 2)).order_by('-type')
    fnames_dict = {}
    for i in fnames:
        if not fnames_dict.get(i.film_id_id):
            fnames_dict[i.film_id_id] = []
        fnames_dict[i.film_id_id].append({'type': i.type, 'name': i.name})

    # трейлеры
    ftrailers = {}
    if trailers:
        trailers_ids = {}
        for i in Objxres.objects.using('afisha').filter(objtypeid=3, objpkvalue__in=films_dict.keys()):
            trailers_ids[i.extresid_id] = i.objpkvalue

        for i in TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=trailers_ids.keys()):
            trailer_id = i.trailer_id
            trailer_code = i.code.replace('&#034;', '"')
            pkvalue = trailers_ids.get(trailer_id)
            if pkvalue in ftrailers:
                if ftrailers[pkvalue]['id'] > trailer_id:
                    continue
            ftrailers[pkvalue] = {'code': trailer_code, 'id': trailer_id}

    # рейтинг
    ratings = check_int_rates_inlist(films_dict.keys())

    likes_data = {}
    if likes:
        likes_data = get_film_likes(films_dict.keys())

    # рецензии
    reviews_film_dict = {}
    if reviews:
        authors_ids = []
        reviews_dict = {}
        reviews_list = list(AfishaNews.objects.using('afisha').filter(type=2, object_type=1, obj__id__in=films_dict.keys()).values('id', 'name', 'content', 'date_time', 'user', 'user__sex', 'user__firstname', 'user__lastname', 'obj'))
        for r in reviews_list:
            txt_cut = cut_description(r['content'], False, 200)

            avatar = None
            if r['user'] == 3354:
                avatar = 'http://slides.kinoafisha.ru/7/6890-004.jpg'
            elif r['user'] == 2:
                avatar = 'http://slides.kinoafisha.ru/7/6890-003.jpg'
            elif r['user'] == 3043:
                avatar = 'http://slides.kinoafisha.ru/7/6890-002.jpg'
            else:
                if r['user__sex'] == 2:
                    avatar = 'http://slides.kinoafisha.ru/7/6890-001.jpg'
                else:
                    avatar = 'http://slides.kinoafisha.ru/7/6890-005.jpg'

            reviews_dict[r['id']] = {'txt': r['content'], 'txt_cut': txt_cut, 'date': r['date_time'], 'user': r['user'], 'user_firstname': r['user__firstname'], 'user_lastname': r['user__lastname'], 'avatar': avatar, 'title': r['name'], 'rate': '', 'film': r['obj'], 'kinoinfo_id': None}

            authors_ids.append(r['user'])

        kinoinfo_reviews = {}
        for kr in list(News.objects.select_related('autor').filter(visible=True, reader_type='14', kid__in=reviews_dict.keys()).values('id', 'kid')):
            kinoinfo_reviews[kr['kid']] = kr['id']

        for fv in FilmVotes.objects.using('afisha').filter(pk__in=reviews_dict.keys()):
            rate_sum = fv.rate_1 + fv.rate_2 + fv.rate_3
            if rate_sum == 9:
                reviews_dict[fv.id]['rate'] = 'превосходно'
            if rate_sum == 8:
                reviews_dict[fv.id]['rate'] = 'отлично'
            elif rate_sum == 7:
                reviews_dict[fv.id]['rate'] = 'хорошо'
            elif rate_sum == 6:
                reviews_dict[fv.id]['rate'] = 'неплохо'
            elif rate_sum == 5:
                reviews_dict[fv.id]['rate'] = 'плохо'
            elif rate_sum == 4:
                reviews_dict[fv.id]['rate'] = 'совсем плохо'
            elif rate_sum == 3:
                reviews_dict[fv.id]['rate'] = 'полный провал'

        profiles_dict = {}
        for pr in list(Profile.objects.filter(kid__in=set(authors_ids), auth_status=True).values('kid', 'user')):
            profiles_dict[pr['kid']] = pr['user']

        for k, v in reviews_dict.iteritems():
            if not reviews_film_dict.get(v['film']):
                reviews_film_dict[v['film']] = []

            author_id = profiles_dict.get(v['user'])
            v['author_id'] = author_id
            kinoinfo_id = kinoinfo_reviews.get(k)
            v['kinoinfo_id'] = kinoinfo_id
            reviews_film_dict[v['film']].append(v)

    # персоны
    persons_dict = {}
    if persons:
        # связи фильм - персона
        persons = PersonsRelationFilms.objects.using('afisha').select_related('person_id', 'type_act_id').filter(film_id__id__in=films_dict.keys(), status_act_id__id=1)
        persons_id = set([i.person_id_id for i in persons])

        # имена рус. и англ.
        persons_name = AfishaPersonsName.objects.using('afisha').filter(person_id__id__in=persons_id)
        persons_name_dict = {}
        for i in persons_name:
            if not persons_name_dict.get(i.person_id_id):
                persons_name_dict[i.person_id_id] = {'name': [], 'parental': ''}
            persons_name_dict[i.person_id_id]['name'].append({'flag': i.flag, 'name': i.name})

        # имена в род.падеже
        for i in list(NamePerson.objects.filter(person__kid__in=persons_name_dict.keys(), status=3, language__id=1).order_by('-id').values('person__kid', 'name')):
            persons_name_dict[i['person__kid']]['parental'] = i['name']

        # фото персон
        extresids = {}
        for i in list(Objxres.objects.using('afisha').filter(objtypeid=302, objpkvalue__in=persons_id).values('extresid', 'objpkvalue')):
            extresids[int(i['extresid'])] = int(i['objpkvalue'])

        person_photos = {}
        for i in Extres.objects.using('afisha').filter(extresid__in=extresids.keys(), filename__icontains='small', info__icontains='*t'):
            pkid = extresids.get(i.extresid)
            if pkid:
                person_photos[pkid] = 'http://persons.nodomain.kinoafisha.ru/%s' % i.filename

        for i in persons:
            if not persons_dict.get(i.film_id_id):
                persons_dict[i.film_id_id] = {'directors': [], 'actors': [], 'other_person': []}

            pers_name = persons_name_dict.get(i.person_id_id, {'name': [], 'parental': ''})
            pname = pers_name['parental'] if i.type_act_id_id == 3 else ''

            if not pname:
                for p in pers_name['name']:
                    pname = p['name']
                    if p['flag'] == 1:
                        break

            pphoto = person_photos.get(i.person_id_id)

            pdata = {
                'type': i.type_act_id_id,
                'type_name': i.type_act_id.type_act,
                'imdb': i.person_id.imdb,
                'id': i.person_id_id,
                'name': pname,
                'poster': pphoto,
            }

            if i.type_act_id_id == 3:
                persons_dict[i.film_id_id]['directors'].append(pdata)
            elif i.type_act_id_id == 1:
                persons_dict[i.film_id_id]['actors'].append(pdata)
            else:
                persons_dict[i.film_id_id]['other_person'].append(pdata)

    # отзывы зрителей
    opinions_films = {}
    if check_opinions:
        for i in NewsFilms.objects.select_related('message').filter(kid__in=films_dict.keys(), message__visible=True):
            if not opinions_films.get(i.kid):
                opinions_films[i.kid] = {'objs': [], 'avg': 0, 'rates': [], 'count': 0, 'my_rate': None, 'my_opinion': None}
            opinions_films[i.kid]['objs'].append(i)
            if i.rate:
                opinions_films[i.kid]['rates'].append(i.rate)

        for k, v in opinions_films.iteritems():
            for i in v['objs']:
                if i.message.text:
                    opinions_films[k]['count'] += 1

            vrates = opinions_films[k]['rates']
            if opinions_films[k]['rates']:
                opinions_films[k]['avg'] = '%1.1f' % (float(sum(vrates)) / len(vrates))

    data = []
    for i in f:
        poster_path = ''
        poster = posters.get(i.id)
        if poster and poster['poster']:
            poster_path = film_poster2(poster['poster'], poster_size)

        slides_tmp = []
        if poster and poster['slides']:
            slides_tmp = film_poster2(poster['slides'], poster_size, True)

        slides = []
        for ind, s in enumerate(slides_tmp):
            if poster_size == 'small':
                slides.append((s, s))
            else:
                slides.append((s.replace('_small', ''), s))
            if ind == 2:
                break

        slides_count = len(slides)

        range_to = 3 - slides_count
        for r in range(range_to):
            slides.append(('', ''))

        rate = ratings.get(i.id)
        rating = {'rate': rate['int_rate'], 'show_ir': rate['show_ir'], 'show_imdb': rate['show_imdb'], 'rotten': rate['rotten']}

        flikes = likes_data.get(i.id)

        desc = i.description.encode('utf-8') if i.description else ''
        idimdb = int(i.idalldvd) if i.idalldvd is not None else 0
        release_date = films_dict.get(i.id)
        release_date = release_date.get('release') if release_date.get('release') else ''
        if not release_date:
            release_date = i.date if i.date else ''

        genre1_name = i.genre1.name if int(i.genre1_id) != 0 else None
        genre2_name = i.genre2.name if int(i.genre2_id) != 0 else None
        genre3_name = i.genre3.name if int(i.genre3_id) != 0 else None
        country1_name = i.country.name if int(i.country_id) != 0 else None
        country2_name = i.country2.name if int(i.country2_id) != 0 else None
        limit = age_limits(i.limits)

        countries = [j for j in (country1_name, country2_name) if j]

        genres = [j for j in (genre1_name, genre2_name, genre3_name) if j]

        fnames = fnames_dict.get(i.id, [{'name': '', 'type': 2}])
        fname = ''
        for n in fnames:
            fname = n['name']
            if n['type'] == 2:
                break

        trailer = ftrailers.get(i.id)

        trailer_code = ''
        trailer_img = ''
        trailer_id = ''
        if trailer:
            trailer = BeautifulSoup(trailer['code'], from_encoding='utf-8')
            for tr in trailer.findAll(['iframe', 'object', 'embed']):
                tr['width'] = 250
                tr['height'] = 150
                src = tr.get('src')
                if src:
                    try:
                        trailer_id = src.split('/embed/')[1].split('?')[0].replace('/', '')
                    except IndexError:
                        trailer_id = src.split('/v/')[1].split('?')[0].replace('/', '')
                else:
                    src = tr.findAll('param', limit=1)[0].get('value')
                    trailer_id = src.split('/v/')[1].split('?')[0].replace('/', '')

                trailer_img = u'http://img.youtube.com/vi/%s/mqdefault.jpg' % trailer_id
            trailer_code = str(trailer).replace('<html><head></head><body>', '').replace('</body></html>', '')
        trailer = trailer_code

        reviews_data = reviews_film_dict.get(i.id)

        descript = ''
        descript_cut = ''
        if i.description:
            descript = i.description
            descript_cut = cut_description(descript, False, 180)

        if descript == descript_cut:
            descript_cut = ''

        descript_after = descriptions_dict.get(str(i.id), '')

        actors = persons_dict.get(i.id)

        fopinions = opinions_films.get(i.id, {})

        data.append({
            'posters': poster_path,
            'id': i.id,
            'name_ru': fname,
            'year': i.year,
            'limit': limit,
            'idimdb': idimdb,
            'desc': desc,
            'release_date': release_date,
            'countries': countries,
            'genres': genres,
            'runtime': i.runtime,
            'reviews': reviews_data,
            'likes': flikes,
            'rating': rating,
            'descript': descript,
            'descript_cut': descript_cut,
            'descript_after': descript_after,
            'rate': rating['rate'],
            'show_ir': rating['show_ir'],
            'trailer': trailer,
            'trailer_img': trailer_img,
            'trailer_id': trailer_id,
            'slides': slides,
            'persons': actors,
            'opinions': fopinions,
        })

    return data


def main_page(request):
    all_films_list = []
    current_site = request.current_site

    user_block_type1 = 0
    user_block_type2 = 0
    user_block_type3 = 0
    user_block_type4 = 0

    if not request.user.is_anonymous():
        profile = request.profile
        # для каждого блока "Slideblock" получаем отдельные значения
        # установленного пользовательского интрефейса
        interface = profile.personinterface
        user_block_type1 = interface.option1
        user_block_type2 = interface.option2
        user_block_type3 = interface.option3
        user_block_type4 = interface.option4

        login_counter(request)

    city_id = request.current_user_city_id
    city_name = request.current_user_city

    ############# собераю айдишники для передачи в функцию обработчик ##################
    ####################################################################################

    # list [новинки_рутрекера] ####################################
    films_rutracker = SourceFilms.objects.filter(source_obj__url='http://rutracker.org/').order_by('-text')[:20]
    films_kids_rutracker = {}
    for i in films_rutracker:
        if len(films_kids_rutracker.keys()) < 5:
            if not films_kids_rutracker.get(i.kid):
                films_kids_rutracker[i.kid] = i
        else:
            break

    # list [смотреть_онлайн] ########################################
    online_films_dic = {}
    films_online = MovieMegogo.objects.only('title', 'year', 'genres', 'afisha_id').exclude(Q(afisha_id=0) | Q(afisha_id=None)).order_by('?')[:5]
    for i in films_online:
        online_films_dic[i.afisha_id] = {'title': i.title, 'year': i.year, 'genres': i.genres, 'kid': i.afisha_id}

    # list [сеансы] ################################################
    schedules = {}
    films_dict = {}
    if city_id:
        schedules, films_dict = schedules_feed(city_id)

    all_films_list = set(all_films_list + films_dict.keys() + films_kids_rutracker.keys() + online_films_dic.keys())

    ############## передаю собранные айдишники в функцию обработчик ####################
    all_about_films = get_data_show(all_films_list)
    rating_dic = check_int_rates_inlist(all_films_list)
    ####################################################################################

    # НОВИНКИ РУТРЕКЕРА #

    torrents_kids = list(Torrents.objects.exclude(path=None).order_by('-id').distinct('film').values('id', 'film')[:100])

    '''
    torrents_releases = []
    for i in Film.objects.using('afisha').filter(pk__in=torrents_kids).values('pk', 'date'):
        if i['date']:
            torrents_releases.append({'pk': i['pk'], 'date': i['date'].date()})
    '''
    torrents_films_dict = {}
    for i in list(sorted(torrents_kids, key=operator.itemgetter('id'), reverse=True))[:5]:
        torrents_films_dict[i['film']] = {}

    torrents_release_data = releasedata(torrents_films_dict, {}, persons=False, likes=False, trailers=False, reviews=False, poster_size='small')
    #for i in torrents_release_data:
    #    torrents_films_dict[i['id']]['obj'] = i

    rutracker_films_list = torrents_release_data

    '''
    rutracker_films_list = []
    for i in films_kids_rutracker.values():
        dtime = None
        if i.text:
            d, t = i.text.split()
            year, month, day = d.split('-')
            hour, minute, sec = t.split(':')
            dtime = datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(sec))

        films_data = get_film_data(int(i.kid))
        #rating, show_ir, show_imdb, rotten = check_int_rates(int(i.kid))###########################
        poster = None
        name_ru = None
        if films_data:
            poster = films_data['posters']
            name_ru = films_data['name_ru']

        # описание в подсказке
        film_info = all_about_films.get(int(i.kid))

        rutracker_films_list.append({
            'source': i,
            'kinoafisha': name_ru,
            'dtime': dtime,
            'film_info': film_info,
            'poster': poster,
            'rating': rating_dic[int(i.kid)]['int_rate'],
            'show_ir': rating_dic[int(i.kid)]['show_ir'],
            'show_imdb':rating_dic[int(i.kid)]['show_imdb'],
            'rotten': rating_dic[int(i.kid)]['rotten']
        })

    rutracker_films_list = sorted(rutracker_films_list, key=operator.itemgetter('dtime'), reverse=True)
    '''

    # СЕАНСЫ #
    for i in schedules:
        #  название фильма из сеансов
        obj = films_dict.get(i['obj'].film.kid)
        name = BeautifulSoup(obj.name)
        name = str(name).replace('<html><head></head><body>', '').replace('</body></html>', '')
        i['name'] = name
        i['imdb'] = obj.film_id.imdb
        i['kid'] = int(i['obj'].film.kid)
        films_data = get_film_data(int(i['obj'].film.kid))
        # получаю маленький постер для вывода на главную
        if films_data['posters']:
            i['poster'] = films_data['posters']
        # описание в подсказке
        i['film_info'] = all_about_films[int(i['obj'].film.kid)]
        # рейтинги
        i['rating'] = rating_dic[int(i['obj'].film.kid)]['int_rate']
        i['show_ir'] = rating_dic[int(i['obj'].film.kid)]['show_ir']
        i['show_imdb'] = rating_dic[int(i['obj'].film.kid)]['show_imdb']
        i['rotten'] = rating_dic[int(i['obj'].film.kid)]['rotten']
        # готовлю 2 списка времени сеансов: один урезанный вывожу сразу, второй как дополнение в подсказке
        times = ''
        times2 = ''
        # и еще 2 списка отдельно для графического интерфейса
        times_grafic_interface = ''
        times_grafic_interface2 = ''
        times_cnt = 1

        for t in sorted(list(set(i['times']))):
            if times:
                times_cnt += 1
            if times_cnt <= 12:
                times += '%s' % t
                times += ', '
            else:
                # наполняю второй - полный список
                times2 += '%s' % t
                times2 += ', '

            # для 2 интерфейса
            if times_cnt <= 2:
                times_grafic_interface += '%s' % t
                times_grafic_interface += ', '
            if times_cnt > 2 and times_cnt <= 4:
                times_grafic_interface2 += '%s' % t
                times_grafic_interface2 += ', '

        # убераю ненужную запятую в конце
        f1 = len(times) - 2
        times = times[:f1]
        f2 = len(times2) - 2
        times2 = times2[:f2]
        f3 = len(times_grafic_interface) - 2
        times_grafic_interface = times_grafic_interface[:f3]
        f4 = len(times_grafic_interface2) - 2
        times_grafic_interface2 = times_grafic_interface2[:f4]

        if times_cnt > 12:
            times = times + ' . . . '
        # сохраняю полученное расписание
        i['times'] = times
        i['times2'] = times2
        i['times_grafic_interface'] = times_grafic_interface
        i['times_grafic_interface2'] = times_grafic_interface2

    schedules = sorted(schedules, key=operator.itemgetter('rating'), reverse=True)

    # РЕЛИЗЫ #
    releases = releases_feed(current_site.domain, user_block_type2)

    # СМОТРЕТЬ ОН-ЛАЙН #
    online_films_list = []

    for k, i in online_films_dic.items():
        poster = None
        film_info = None
        films_data = get_film_data(int(k))
        # картинка
        poster = None
        if films_data:
            poster = films_data['posters']

        #rating, show_ir, show_imdb, rotten = check_int_rates(int(i))
        film_info = all_about_films[int(k)]

        online_films_list.append({
            'title': i['title'],
            'year': i['year'],
            'genres': i['genres'],
            'kid': i['kid'],
            'film_info': film_info,
            'poster': poster,
            'rating': rating_dic[int(k)]['int_rate'],
            'show_ir': rating_dic[int(k)]['show_ir'],
            'show_imdb': rating_dic[int(k)]['show_imdb'],
            'rotten': rating_dic[int(k)]['rotten'],
        })
    online_films_list = sorted(online_films_list, key=operator.itemgetter('rating'), reverse=True)

    tmplt = 'slideblock/blocks_main.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoinfo.ru':
        tmplt = 'mobile/slideblock/blocks_main.html'

    return render_to_response(tmplt, {'rutracker_films': rutracker_films_list, 'user_block_type1': user_block_type1, 'user_block_type2': user_block_type2,'user_block_type3': user_block_type3, 'user_block_type4': user_block_type4, 'online_films': online_films_list, 'city_id': city_id, 'city_name': city_name, 'schedules': schedules, 'releases': releases}, context_instance=RequestContext(request))


@never_cache
def week_releases_func(request, rtype, mobile=False):
    timer = time.time()

    if request.POST:
        if request.user.is_superuser:
            note = request.POST.get('note')
            position = request.POST.get('position')
            week_num = request.POST.get('week')

            if note or note == '':
                note_tmp = BeautifulSoup(note, from_encoding='utf-8').text.strip()
                if not note_tmp:
                    note = ''

                current_site = request.current_site
                news, created = News.objects.get_or_create(
                    reader_type='13',
                    title=position,
                    extra=week_num,
                    defaults={
                        'reader_type': '13',
                        'title': position,
                        'text': note,
                        'visible': True,
                        'autor': request.user.get_profile(),
                        'site': current_site,
                        'subdomain': '0',
                        'extra': week_num,
                    })
                if not created:
                    news.text = note
                    news.save()

                return HttpResponseRedirect(reverse('kinoafisha_main'))

    city_id = request.current_user_city_id

    today = datetime.datetime.today().date()
    day7 = today + datetime.timedelta(days=7)

    current_week = today.isocalendar()[1]
#by OFC076
    target_year = today.isocalendar()[0]
    first_day_of_current_week = tofirstdayinisoweek(target_year, current_week).date()
#    first_day_of_current_week = tofirstdayinisoweek(today.year, current_week).date()
    last_day_of_current_week = first_day_of_current_week + datetime.timedelta(days=6)

    first_day_of_past_week = first_day_of_current_week - datetime.timedelta(days=7)
    last_day_of_past_week = first_day_of_current_week - datetime.timedelta(days=1)

#    if today.year < first_day_of_current_week.year:
#        first_day_of_current_week = datetime.date(today.year, first_day_of_current_week.month, first_day_of_current_week.day)
#    if today.year < last_day_of_past_week.year:
#        last_day_of_current_week = datetime.date((last_day_of_current_week.year - 1), last_day_of_current_week.month, last_day_of_current_week.day)

#    if today.year < last_day_of_past_week.year:
#        first_day_of_past_week = datetime.date(today.year - 1, first_day_of_past_week.month, first_day_of_past_week.day)
#        last_day_of_past_week = datetime.date((last_day_of_past_week.year - 1), last_day_of_past_week.month, last_day_of_past_week.day)

    if rtype == 'future':
        filter = {'date__gte': first_day_of_current_week, 'date__lte': last_day_of_current_week}
        page_title = u'Выходят на этой неделе'
    elif rtype == 'past':
        page_title = u'Вышли на прошлой неделе'
        filter = {'date__gte': first_day_of_past_week, 'date__lte': last_day_of_past_week}
    else:
        page_title = u'Сеансы'
        day7 = today + datetime.timedelta(days=30)

        today = datetime.datetime.now()
        film_list = set(list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lt=day7, cinema__city__city__id=city_id, cinema__cinema__name__status=1, cinema__cinema__city__name__status=1).exclude(film__source_id=0).distinct('film__kid').values_list('film__kid', flat=True)))

        filter = {'pk__in': film_list}

    films = Film.objects.using('afisha').only('id', 'date').filter(**filter)

    #films = ReleasesRelations.objects.select_related('release').filter(
    #    release__release_date__gte=first_day_of_current_week, 
    #    release__release_date__lte=last_day_of_current_week
    #)

    films_dict = {}
    week = None
    for i in films:
        if not films_dict.get(i.id):
            films_dict[i.id] = {'obj': i, 'release': i.date, 'cinemas': [], 'tickets': {'status': False, 'kinohod': '', 'rambler': ''}}
            if not week:
                week = i.date.isocalendar()[1]

    kinoinfo_dict = {}

    #cache.clear()
    cached_page = ''

    if city_id:
        today = datetime.datetime.now()
        cache_add = '' if rtype == 'future' else rtype

        if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
            cache.delete('ka_kinoinfo_dict_%s%s' % (city_id, cache_add))


        is_cached = cache.get('ka_kinoinfo_dict_%s%s' % (city_id, cache_add), 'nocaсhed')

        if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
            cached_page = False

            xfilms = SourceSchedules.objects.filter(dtime__gte=today, dtime__lt=day7, cinema__city__city__id=city_id, film__kid__in=films_dict.keys(), cinema__cinema__name__status=1, cinema__cinema__city__name__status=1).exclude(film__source_id=0).values('film__kid', 'cinema__cinema', 'cinema__city__name', 'cinema__cinema__name__name', 'dtime', 'sale', 'film__name', 'film__source_id', 'cinema__city__source_id',  'cinema__cinema__city__name__name', 'source_obj__url')

            for i in xfilms:
                t = i['dtime']

                if kinoinfo_dict.get(i['film__kid']):
                    if kinoinfo_dict[i['film__kid']]['cinemas'].get(i['cinema__cinema']):
                        kinoinfo_dict[i['film__kid']]['cinemas'][i['cinema__cinema']]['schedules'].append(t)
                    else:
                        kinoinfo_dict[i['film__kid']]['cinemas'][i['cinema__cinema']] = {
                            'name': i['cinema__cinema__name__name'],
                            'id': i['cinema__cinema'],
                            'schedules': [t],
                        }
                else:
                    kinoinfo_dict[i['film__kid']] = {
                        'cinemas': {
                            i['cinema__cinema']: {
                                'name': i['cinema__cinema__name__name'],
                                'id': i['cinema__cinema'],
                                'schedules': [t],
                            },
                        },
                        'tickets': {'status': False, 'kinohod': '', 'rambler': ''},
                    }

                if i['source_obj__url'] in ('http://kinohod.ru/', 'http://www.rambler.ru/') and i['sale'] == True:
                    kinoinfo_dict[i['film__kid']]['tickets']['status'] = True

                    if i['source_obj__url'] == 'http://kinohod.ru/':
                        #tickets = u'<a href="http://kinohod.ru/" class="kh_boxoffice" ticket movie="%s" city="%s"></a>' % (i['film__name'], i['cinema__cinema__city__name__name'])
                        tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % (
                            i['film__source_id'], i['film__source_id'], i['cinema__city__name'])
                        kinoinfo_dict[i['film__kid']]['tickets']['kinohod'] = tickets
                    else:
                        tickets = u'<rb:movie key="%s" movieName="" cityName="" movieID="%s" cityID="%s" xmlns:rb="http://kassa.rambler.ru"></rb:movie>' % (settings.RAMBLER_TICKET_KEY, i['film__source_id'], i['cinema__city__source_id'])
                        kinoinfo_dict[i['film__kid']]['tickets']['rambler'] = tickets

            cache.set('ka_kinoinfo_dict_%s%s' % (city_id, cache_add), kinoinfo_dict, 60*60*12)
        else:
            kinoinfo_dict = is_cached
            cached_page = True

        for k, v in kinoinfo_dict.iteritems():
            if films_dict.get(k):
                films_dict[k]['cinemas'] = v['cinemas'].values()
                films_dict[k]['tickets'] = v['tickets']

        '''
        for i in films_dict.keys():
            schedules = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lt=day7, cinema__cinema__name__status=1,  cinema__city__city__id=city_id, film__kid=i).exclude(film__source_id=0).values('cinema__cinema', 'cinema__cinema__name__name').distinct('cinema__cinema__city'))
            
            in_cinema = kinoinfo_dict.get(i)
            for schedule in schedules:
                times = [v for k,v in in_cinema.items() if k == schedule['cinema__cinema']][0]
                films_dict[i]['cinemas'].append({
                    'name': schedule['cinema__cinema__name__name'],
                    'id': schedule['cinema__cinema'],
                    'schedules': set(times),
                })
        '''

    # описания вверху, внизу и к каждому релизу
    descriptions = News.objects.filter(reader_type='13', title__in=films_dict.keys() + ['top', 'bottom'], extra=week)

    descript_bottom = ''
    descript_top = ''
    descriptions_dict = {}
    for i in descriptions:
        title = i.title.encode('utf-8')
        if i.title.encode('utf-8') == 'top':
            descript_top = i.text
        elif i.title.encode('utf-8') == 'bottom':
            descript_bottom = i.text
        else:
            descriptions_dict[title] = i.text

    tinymce_ids = []

    data = releasedata(films_dict, descriptions_dict, persons=True, likes=True, trailers=True, check_opinions=True)

    for i in data:
        tmp = films_dict.get(i['id'])
        #i['cinemas'] = tmp['cinemas']

        if request.profile:
            for j in i['opinions'].get('objs', []):
                if j.rate and j.message.autor_id == request.profile.id:
                    i['opinions']['my_rate'] = j.rate
                if str(j.message) == "отзыв" and j.message.autor_id == request.profile.id:
                    i['opinions']['my_opinion'] = True 

        cinemas_list = []
        for cinema in tmp['cinemas']:
            cinema_dates = {}
            for j in set(cinema['schedules']):
                day = j.date()

                if not cinema_dates.get(day):
                    cinema_dates[day] = {'day': day, 'time': [], 'dtime': j}
                cinema_dates[day]['time'].append(j)
                cinema_dates[day]['time'] = sorted(cinema_dates[day]['time'])
            cinema_dates = sorted(cinema_dates.values(), key=operator.itemgetter('day'))
            cinemas_list.append({'name': cinema['name'], 'id': cinema['id'], 'schedules': cinema_dates})

        i['cinemas'] = sorted(cinemas_list, key=operator.itemgetter('name'))
        i['tickets'] = tmp['tickets']
        tinymce_ids.append(i['id'])

    data = sorted(data, key=operator.itemgetter('rate'), reverse=True)

    timer = '%5.2f' % (time.time()-timer)

    tmplt = 'kinoafisha/week_releases.html'
    if mobile:
        tmplt = 'mobile/kinoafisha/week_releases.html'

    return render_to_response(tmplt, {'data': data, 'kinohod_key': settings.KINOHOD_APIKEY_CLIENT, 'descript_top': descript_top, 'descript_bottom': descript_bottom, 'week': week, 'tinymce_ids': tinymce_ids, 'release': True, 'timer': timer, 'cached_page': cached_page, 'page_title': page_title,}, context_instance=RequestContext(request))


@never_cache
def week_releases(request, rtype):

    REG_ID = re.compile(r'^\d+')

    film_param = REG_ID.findall(request.GET.get('status', ''))
    film_id = REG_ID.findall(request.GET.get('id1', ''))

    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        return week_releases_func(request, rtype, mobile=True)
    else:
        if film_param and int(film_param[0]) == 1 and film_id:
            return HttpResponseRedirect(reverse('get_film', kwargs={'id': film_id[0]}))
            #return get_film_func(request, film_id[0])
        else:
            return week_releases_func(request, rtype)


@never_cache
def soon(request):
    timer = time.time()

    today = datetime.datetime.today().date()
    day21 = today + datetime.timedelta(days=21)

    current_week = today.isocalendar()[1]
#by OFC076
    target_year = today.isocalendar()[0]
    first_day_of_current_week = tofirstdayinisoweek(target_year, current_week).date()
#    first_day_of_current_week = tofirstdayinisoweek(today.year, current_week).date()
    from_date = first_day_of_current_week + datetime.timedelta(days=7)

#    if today.year < from_date.year:
#        from_date = datetime.date(today.year, from_date.month, from_date.day)

    films_dict = {}
    films = Film.objects.using('afisha').only('id', 'date').filter(date__gte=from_date, date__lte=day21)
    #films = ReleasesRelations.objects.select_related('release').filter(release__release_date__gte=from_date, release__release_date__lte=day21)

    week = None
    for i in films:
        if not films_dict.get(i.id):
            films_dict[i.id] = {'obj': i, 'release': i.date, 'tickets': ''}
            if not week:
                week = i.date.isocalendar()[1]

    # описания вверху, внизу и к каждому релизу
    descriptions = News.objects.filter(reader_type='13', title__in=films_dict.keys() + ['top', 'bottom'], extra=week)

    descript_bottom = ''
    descript_top = ''
    descriptions_dict = {}
    for i in descriptions:
        title = i.title.encode('utf-8')
        if i.title.encode('utf-8') == 'top':
            descript_top = i.text
        elif i.title.encode('utf-8') == 'bottom':
            descript_bottom = i.text
        else:
            descriptions_dict[title] = i.text

    #cache.clear()
    cached_page = ''

    if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
        cache.delete('ka__soon__releasedata')

    is_cached = cache.get('ka__soon__releasedata', 'nocaсhed')

    if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
        cached_page = False

        data = releasedata(films_dict, descriptions_dict, persons=True, likes=True, trailers=True, check_opinions=True)

        for i in data:
            if request.profile:
                for j in i['opinions'].get('objs', []):
                    if j.rate and j.message.autor_id == request.profile.id:
                        i['opinions']['my_rate'] = j.rate

            tmp = films_dict.get(i['id'])
            i['tickets'] = tmp['tickets']

        data = sorted(data, key=operator.itemgetter('release_date'))

        cache.set('ka__soon__releasedata', data, 60 * 60 * 12)
    else:
        data = is_cached
        cached_page = True

    timer = '%5.2f' % (time.time() - timer)

    tmplt = 'kinoafisha/week_releases.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/week_releases.html'

    return render_to_response(tmplt, {'data': data, 'soon': True, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


@never_cache
def soon_fr(request):
    timer = time.time()
    cached_page = False

    today_date = datetime.datetime.today()
    current_year = today_date.year
    from_year = current_year - 1
    to_year = current_year + 1
    today = today_date.date()
    day21 = today + datetime.timedelta(days=21)

    current_week = today.isocalendar()[1]
#by OFC076
    target_year = today.isocalendar()[0]
    first_day_of_current_week = tofirstdayinisoweek(target_year, current_week).date()
#    first_day_of_current_week = tofirstdayinisoweek(today.year, current_week).date()
    from_date = first_day_of_current_week + datetime.timedelta(days=7)

#    if today.year < from_date.year:
#        from_date = datetime.date(today.year, from_date.month, from_date.day)

    films_dict = {}
    films = SourceFilms.objects.filter(extra__gte=from_date, extra__lte=day21, source_obj__url='http://www.yo-video.net/').exclude(kid=None)

    week = None
    for i in films:
        if not films_dict.get(i.kid):
            films_dict[i.kid] = {'obj': i, 'release': i.extra, 'tickets': ''}
            if not week:
                year, month, day = i.extra.split('-')
                release_date = datetime.date(int(year), int(month), int(day))
                week = release_date.isocalendar()[1]

    data_tmp = releasedata(films_dict, {}, persons=True, likes=True, trailers=True, check_opinions=True)
    data = []
    for i in data_tmp:
        if request.profile:
            for j in i['opinions'].get('objs', []):
                if j.rate and j.message.autor_id == request.profile.id:
                    i['opinions']['my_rate'] = j.rate

        if int(i['year']) <= to_year and int(i['year']) >= from_year:
            if not i['name_ru']:
                try:
                    name_en = FilmsName.objects.using('afisha').get(film_id__id=i['id'], status=1, type=1)
                except FilmsName.DoesNotExist:
                    name_en = None
                i['name_en'] = name_en
            data.append(i)

        tmp = films_dict.get(i['id'])
        i['tickets'] = tmp['tickets']

    data = sorted(data, key=operator.itemgetter('release_date'))

    timer = '%5.2f' % (time.time() - timer)

    tmplt = 'kinoafisha/week_releases.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/week_releases.html'

    return render_to_response(tmplt, {'data': data, 'fr': True, 'soon': True, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


@never_cache
def boxoffice(request, country):
    timer = time.time()
    cached_page = False

    country_name = None
    if country == 'russia':
        country_name = 'Россия'
    if country == 'usa':
        country_name = 'США'

    if country_name:
        #is_cached = cache.get('ka__boxoffice__%s' % country, 'nocaсhed')
        is_cached = 'nocaсhed'
        if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
            #cached_page = False

            data = boxoffice_func(request, country_name)

            #cache.set('ka__boxoffice__%s' % country, data, 60*60*12)
        else:
            #data = is_cached
            cached_page = True

        data['weekend_first'] = data['weekend'] - datetime.timedelta(days=2)

        data['country'] = country

        tmplt = 'kinoafisha/boxoffice.html'
        if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
            tmplt = 'mobile/kinoafisha/boxoffice.html'

        timer = '%5.2f' % (time.time() - timer)
        data['timer'] = timer
        data['cached_page'] = cached_page
        return render_to_response(tmplt, data, context_instance=RequestContext(request))
    else:
        raise Http404


@never_cache
def online(request):
    timer = time.time()
    cached_page = False

    online_films_dic = {}
    films_online = MovieMegogo.objects.exclude(Q(afisha_id=0) | Q(afisha_id=None)).filter(rel_ignore=False).order_by('?')[:5]
    for i in films_online:
        player, psource = get_film_player(i.afisha_id)
        online_films_dic[i.afisha_id] = {'obj': i, 'player': player, 'tickets': ''}

    data = releasedata(online_films_dic, {}, persons=True, likes=True, trailers=False)
    for i in data:
        if request.profile:
            for j in i['opinions'].get('objs', []):
                if j.rate and j.message.autor_id == request.profile.id:
                    i['opinions']['my_rate'] = j.rate

        pl = online_films_dic.get(i['id'])
        i['trailer'] = pl['player']
        i['tickets'] = pl['tickets']

    timer = '%5.2f' % (time.time() - timer)

    tmplt = 'kinoafisha/week_releases.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/week_releases.html'

    return render_to_response(tmplt, {'data': data, 'online': True, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


def reviews_func(request, id):
    from news.views import create_news

    subdomain = request.subdomain
    if not subdomain:
        subdomain = 0

    access = True if request.user.is_superuser or request.is_admin else False

    if request.POST:
        if access:
            delete = request.POST.get('del')
            if delete and delete == '1':
                filter = {'pk': id, 'reader_type': '21'}
                News.objects.get(**filter).delete()
                return HttpResponseRedirect(reverse('kinoafisha_reviews'))
            else:
                name = request.POST.get('news_title', ' ')
                text = request.POST.get('text', '')
                visible = request.POST.get('visible', False)
                edit = int(request.POST.get('edit'))

                if text:
                    if edit:
                        filter = {'pk': edit, 'subdomain': subdomain, 'reader_type': '21'}
                        news = News.objects.get(**filter)
                        news.title = name
                        news.text = text
                        news.visible = visible
                        news.save()
                        return HttpResponseRedirect(reverse('kinoafisha_reviews', kwargs={'id': id}))
                    else:
                        news = create_news(request, [], name, text, '21', 0, None, visible)
                        return HttpResponseRedirect(reverse('kinoafisha_reviews'))

    filter = {'reader_type__in': ('14', 21)}
    if not request.user.is_superuser:
        filter['visible'] = True
    if id:
        filter['pk'] = id

    kinoinfo_reviews = News.objects.filter(**filter).order_by('-dtime')

    if id and not kinoinfo_reviews:
        raise Http404

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, kinoinfo_reviews, 50)

    films_ids = set([int(i.extra) for i in p.object_list if i.extra])

    films_name = FilmsName.objects.using('afisha').filter(status=1, type=2, film_id__id__in=films_ids)
    names = {}
    for i in films_name:
        names[i.film_id_id] = i.name

    reviews_dict = []

    all_ids = [i.autor.id for i in p.object_list]
    data_persons = collections.defaultdict(list)
    for o in Person.objects.filter(profile__pk__in=all_ids).values(
        'id',
        'city',
        'country',
        'profile',
        'profile__pk',
        'profile__kid',
        'profile__user',
        'profile__phone',
        'profile__folder',
        'profile__show_profile',
        'profile__user__last_name',
        'profile__user__first_name',
        'profile__user__date_joined',
        'profile__user__is_superuser',
    ):
        data_persons[o['profile__pk']].append(o)
    data_cities = collections.defaultdict(list)
    for o in NameCity.objects.filter(city__person__profile__pk__in=all_ids, status=1).values(
        'name',
        'city',
        'city__person__profile__pk',
    ):
        data_cities[o['city__person__profile__pk']].append(o)
    data_accs = collections.defaultdict(list)
    for o in Accounts.objects.filter(profile__pk__in=all_ids).values(
        'login',
        'avatar',
        'profile',
        'fullname',
        'nickname',
        'profile__pk',
    ):
        data_accs[o['profile__pk']].append(o)
    data_names = collections.defaultdict(list)
    for o in NamePerson.objects.filter(person__profile__pk__in=all_ids, status=1).order_by('id').values(
        'name',
        'person__profile',
        'person__profile__pk',
    ):
        data_names[o['person__profile__pk']].append(o)

    for i in p.object_list:
        autor = org_peoples([i.autor], data_persons, data_cities, data_accs, data_names)
        # autor = org_peoples([i.autor])

        if autor:
            autor = autor[0]
            if i.autor_nick == 1:
                if i.autor.user.first_name:
                    autor['fio'] = i.autor.user.first_name
                    autor['show'] = '2'
            elif i.autor_nick == 2:
                autor['fio'] = ''
                autor['short_name'] = ''

        film_name, film_id = (names.get(int(i.extra)), i.extra) if i.extra else (None, None)

        description = cut_description(i.text, True, 80)

        reviews_dict.append({'title': i.title, 'user': autor, 'date': i.dtime, 'kinoinfo': False, 'film_id': i.extra,
                             'film_name': film_name, 'id': i.id, 'obj': i, 'text': i.text, 'description': description})
    tmplt = 'kinoafisha/reviews.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/reviews.html'

    return render_to_response(tmplt, {'news_data': reviews_dict, 'p': p, 'page': page, 'id': id},
                              context_instance=RequestContext(request))


@never_cache
def reviews(request, id=None):
    return reviews_func(request, id)


def kinoafisha_news_func(request, ntype, id):
    from news.views import create_news

    urls = {
        '17': ('Архив Киноафиши', 'kinoafisha_news'),
        '18': ('Новости мирового кино', 'kinoafisha_world_news'),
        '19': ('Новости российского кинопоказа', 'kinoafisha_russia_news'),
    }

    current_site = request.current_site

    if current_site.domain != 'kinoafisha.ru':
        raise Http404

    subdomain = request.subdomain
    if not subdomain:
        subdomain = 0

    access = True if request.user.is_superuser or request.is_admin else False

    url = urls.get(ntype)

    if request.POST and ntype:
        if access:
            delete = request.POST.get('del')
            if delete and delete == '1':
                filter = {'pk': id}
                if ntype == '17':
                    filter['reader_type__in'] = ('17', '20')
                News.objects.get(**filter).delete()
                return HttpResponseRedirect(reverse('kinoafisha_news'))
            else:
                name = request.POST.get('news_title', ' ')
                text = request.POST.get('text', '')
                visible = request.POST.get('visible', False)
                edit = int(request.POST.get('edit'))

                if text:
                    if edit:
                        filter = {'pk': edit, 'subdomain': subdomain}
                        if ntype == '17':
                            filter['reader_type__in'] = ('17', '20')
                        news = News.objects.get(**filter)
                        news.title = name
                        news.text = text
                        news.visible = visible
                        news.save()
                        if ntype in ('17', '20'):
                            return HttpResponseRedirect(reverse(url[1], kwargs={'id': id}))
                        elif ntype == '18':
                            return HttpResponseRedirect(reverse(url[1], kwargs={'id': id}))
                        elif ntype == '19':
                            return HttpResponseRedirect(reverse(url[1], kwargs={'id': id}))
                    else:
                        news = create_news(request, [], name, text, ntype, 0, None, visible)
                        return HttpResponseRedirect(reverse(url[1]))

    filter = {}
    if ntype:
        if ntype == '17':
            filter = {'reader_type__in': ('17', '20')}
        else:
            filter = {'reader_type': ntype}
        if id:
            filter['pk'] = id
    else:
        filter = {'reader_type__in': ('14', '17', '20'), 'kid': id}
        url = urls.get('17')

    if not access:
        filter['visible'] = True

    news = News.objects.filter(**filter).order_by('-dtime')

    if id and not news:
        raise Http404

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, news, 20)

    news_data = []
    for ind, i in enumerate(p.object_list):
        text = i.text.replace('&#034;', '"').replace('[spoller]', '').replace('[/spoller]', '')
        text = text.replace('www.kinoafisha.ru/posters', 'posters.kinoafisha.ru')
        text = text.replace('www.kinoafisha.ru/slides', 'slides.kinoafisha.ru')
        title = i.title.replace('&#034;', '"')
        description = cut_description(i.text, True, 250)
        news_data.append({'obj': i, 'text': text, 'title': title, 'description': description, 'date': i.dtime})

    tmplt = 'kinoafisha/news.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/news.html'

    return render_to_response(tmplt, {'news_data': news_data, 'id': id, 'p': p, 'page': page, 'ntype': ntype, 'page_title': url[0]}, context_instance=RequestContext(request))


@never_cache
def kinoafisha_news(request, ntype, id=None):
    return kinoafisha_news_func(request, ntype, id)


def old_boxoffice(request):
    current_site = request.current_site
    if current_site.domain != 'kinoafisha.ru':
        raise Http404

    id_co = request.GET.get('id_co')
    if id_co:
        country = 'usa' if id_co == '1' else 'russia'
    else:
        country = 'russia'
    return HttpResponseRedirect(reverse('boxoffice', kwargs={'country': country}))


@never_cache
def schedules(request):
    timer = time.time()
    cached_page = ''

    from django.db.models import Max

    today = datetime.datetime.now()

    # с 6 утра до 12, с 12:05 до 18 - день, с 18:05 до 22 - вечер, после 22 - ночь
    day_part = ''
    day_class = ''

    set_date = request.GET.get('date')
    if set_date:
        try:
            set_day, set_month, set_year = set_date.split('.')
            set_date = datetime.datetime(int(set_year), int(set_month), int(set_day), 0, 0, 0)
        except ValueError:
            set_date = today
    else:
        set_date = today

    city_id = request.current_user_city_id

    if set_date.date() < today.date() or set_date.date() == today.date():
        set_date = today

    if set_date.date() > today.date():
        day_part, day_class = (u'Утренние', 'part_morning')
        set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 6, 0, 0)
    else:
        if today.hour >= 6 and today.hour < 12:
            day_part, day_class = (u'Утренние', 'part_morning')
        elif today.hour >= 12 and today.hour < 18:
            day_part, day_class = (u'Дневные', 'part_day')
        elif today.hour >= 18 and today.hour < 22:
            day_part, day_class = (u'Вечерние', 'part_evening')
        else:
            day_part, day_class = (u'Ночные', 'part_night')

    filter = {
        'dtime__gte': today.date(),
        'cinema__city__city__id': city_id,
    }

    last_day = SourceSchedules.objects.filter(**filter).aggregate(Max('dtime')).get('dtime__max')
    #last_day = None
    last_day = last_day.date() if last_day else today.date()

    days_range = []
    while today.date() <= last_day:
        days_range.append(today.date())
        today = today + datetime.timedelta(days=1)

    today = datetime.datetime.now()

    filter['dtime__gte'] = set_date
    filter['cinema__cinema__name__status'] = 1
    filter['cinema__cinema__city__name__status'] = 1

    if set_date.date() != today.date():
        nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 12, 0, 0)
    else:
        if day_part == u'Утренние':
            nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 12, 0, 0)
        elif day_part == u'Дневные':
            nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 18, 0, 0)
        elif day_part == u'Вечерние':
            nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 22, 0, 0)
        elif day_part == u'Ночные':
            nextday = set_date + datetime.timedelta(days=1)
            nextday = datetime.datetime(nextday.year, nextday.month, nextday.day, 6, 0, 0)

    filter['dtime__lt'] = nextday

    film_list = set(list(SourceSchedules.objects.filter(**filter).exclude(film__source_id=0).distinct('film__kid').values_list('film__kid', flat=True)))

    while not film_list:
        if day_part == u'Утренние':
            day_part, day_class = (u'Дневные', 'part_day')
            set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 12, 0, 0)
            nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 18, 0, 0)
        elif day_part == u'Дневные':
            day_part, day_class = (u'Вечерние', 'part_evening')
            set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 18, 0, 0)
            nextday = datetime.datetime(set_date.year, set_date.month, set_date.day, 22, 0, 0)
        elif day_part == u'Вечерние':
            day_part, day_class = (u'Ночные', 'part_night')
            set_date = datetime.datetime(set_date.year, set_date.month, set_date.day, 22, 0, 0)
            nextday = set_date + datetime.timedelta(days=1)
            nextday = datetime.datetime(nextday.year, nextday.month, nextday.day, 6, 0, 0)
        else:
            break

        filter['dtime__gte'] = set_date
        filter['dtime__lt'] = nextday
        film_list = set(list(SourceSchedules.objects.filter(**filter).exclude(film__source_id=0).distinct('film__kid').values_list('film__kid', flat=True)))

    #film_list = []

    xfilm = {}
    for i in film_list:
        xfilm[i] = {}

    data = releasedata(xfilm, {}, persons=False, likes=False, trailers=False, reviews=False, poster_size='small')

    films_dict = {}
    for i in data:
        txt_cut = cut_description(i['descript'], True, 150)
        i['descript_cut'] = txt_cut
        films_dict[i['id']] = i

    schedules = []

    if city_id:

        filter['film__kid__in'] = films_dict.keys()
        sch = SourceSchedules.objects.filter(**filter).exclude(film__source_id=0).values('film__kid', 'cinema__city__name', 'film__source_id', 'cinema__cinema', 'cinema__cinema__name__name', 'dtime', 'sale', 'film__name', 'cinema__cinema__city__name__name', 'source_obj__url').distinct('cinema__cinema__city')
        #sch = []

        for i in sch:
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
            tickets = ''

            if i['source_obj__url'] == 'http://kinohod.ru/' and i['sale'] == True:
                #tickets = u'<a href="http://kinohod.ru/" class="kh_boxoffice" ticket movie="%s" city="%s"></a>' % (i['film__name'], i['cinema__cinema__city__name__name'])
                tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % (
                    i['film__source_id'], i['film__source_id'], i['cinema__city__name'])

            schedules.append({
                'date': showdate,
                'dtime': i['dtime'],
                'film': film,
                'cinema': cinema,
                'cinema_size': cinema_size,
                'tickets': tickets,
            })

    schedules = sorted(schedules, key=operator.itemgetter('dtime'))

    page_title = u'Сеансы'

    timer = '%5.2f' % (time.time() - timer)

    tmplt = 'kinoafisha/schedules.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/schedules.html'

    return render_to_response(tmplt, {'data': schedules, 'kinohod_key': settings.KINOHOD_APIKEY_CLIENT, 'page_title': page_title, 'lday': [], 'set_date': set_date, 'days_range': days_range, 'day_part': day_part, 'day_class': day_class, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


@never_cache
def best_schedules(request):
    timer = time.time()

    city_id = request.current_user_city_id
#
#    fileNameTest = '{0}/{1}.txt'.format(settings.API_CLIENTS_PATH, 'test_slider')
#    with open(fileNameTest , 'a') as outfile:
#        outfile.write('city_id ' + str(city_id)  + '\n')
#
    #cache.clear()
    cached_page = ''

    films_list = {}
    if city_id:
        if request.GET.get('cache') == 'refresh' and request.user.is_superuser:
            cache.delete('ka__best_schedules__films_list_%s' % city_id)

        is_cached = cache.get('ka__best_schedules__films_list_%s' % city_id, 'nocaсhed')

        if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
            cached_page = False
#
#            fileNameTest = '{0}/{1}.txt'.format(settings.API_CLIENTS_PATH, 'test_slider')
#            with open(fileNameTest , 'a') as outfile:
#                outfile.write(str("no_cache")  + '\n')
#
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)

            films_kid = list(SourceSchedules.objects.select_related('film').filter(dtime__gte=today, dtime__lt=tomorrow, cinema__city__city__id=city_id).exclude(film__source_id=0).values_list('film__kid', flat=True).distinct('kid'))

            rates = check_int_rates_inlist(films_kid)

            rates = sorted(rates.values(), key=operator.itemgetter('review_rate'), reverse=True)

            kids = [i['kid'] for i in rates[:5] if i['int_rate'] > 3]

            films = SourceSchedules.objects.select_related('film', 'cinema', 'cinema__cinema', 'source_obj').filter(dtime__gte=today, dtime__lt=tomorrow, cinema__city__city__id=city_id, film__kid__in=kids).exclude(film__source_id=0)
#
#            fileNameTest = '{0}/{1}.txt'.format(settings.API_CLIENTS_PATH, 'test_slider')
#            with open(fileNameTest , 'a') as outfile:
#                outfile.write('len(films) ' + str(len(films))  + '\n')
#
            kinoinfo_dict = {}
            for i in films:
                t = i.dtime

                if kinoinfo_dict.get(i.film.kid):
                    if kinoinfo_dict[i.film.kid].get(i.cinema.cinema_id):
                        kinoinfo_dict[i.film.kid][i.cinema.cinema_id].append(t)
                        kinoinfo_dict[i.film.kid][i.cinema.cinema_id].sort()
                    else:
                        kinoinfo_dict[i.film.kid][i.cinema.cinema_id] = [t]
                else:
                    kinoinfo_dict[i.film.kid] = {i.cinema.cinema_id: [t]}

            films_list = {}
            for i in kids:
                schedules = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lt=tomorrow, cinema__cinema__name__status=1,  cinema__city__city__id=city_id, film__kid=i, cinema__cinema__city__name__status=1).exclude(film__source_id=0).values('cinema__cinema', 'cinema__cinema__name__name', 'film__name', 'film__source_id', 'cinema__city__name', 'cinema__city__source_id', 'cinema__cinema__city__name__name', 'source_obj__url', 'sale').distinct('cinema__cinema__city'))

                films_list[i] = {'cinemas': [], 'tickets': {'status': False, 'kinohod': '', 'rambler': ''}}

                in_cinema = kinoinfo_dict.get(i)
                for schedule in schedules:
                    try:
                        times = [v for k, v in in_cinema.items() if k == schedule['cinema__cinema']][0]
                        times = sorted(set(times))
                        films_list[i]['cinemas'].append({
                            'name': schedule['cinema__cinema__name__name'],
                            'id': schedule['cinema__cinema'],
                            'schedules': times,
                        })

                        if schedule['source_obj__url'] in ('http://kinohod.ru/', 'http://www.rambler.ru/') and schedule['sale'] == True:
                            films_list[i]['tickets']['status'] = True

                            if schedule['source_obj__url'] == 'http://kinohod.ru/':
                                #tickets = u'<a href="http://kinohod.ru/" class="kh_boxoffice" ticket movie="%s" city="%s"></a>' % (schedule['film__name'], schedule['cinema__cinema__city__name__name'])
#
#                                fileNameTest = '{0}/{1}.txt'.format(settings.API_CLIENTS_PATH, 'test_slider')
#                                with open(fileNameTest , 'a') as outfile:
#                                    outfile.write('i = ' + str(i)  + '\n')
#
#comment OFC076 2018-01-17                                tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % ( i['film__source_id'], i['film__source_id'], i['cinema__city__name'])
                                tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % ( schedule['film__source_id'], schedule['film__source_id'], schedule['cinema__city__name'])

                                films_list[i]['tickets']['kinohod'] = tickets
                            else:
                                tickets = u'<rb:movie key="%s" movieName="" cityName="" movieID="%s" cityID="%s" xmlns:rb="http://kassa.rambler.ru"></rb:movie>' % (settings.RAMBLER_TICKET_KEY, schedule['film__source_id'], schedule['cinema__city__source_id'])
                                films_list[i]['tickets']['rambler'] = tickets
                    except IndexError:
                        pass

            cache.set('ka__best_schedules__films_list_%s' % city_id, films_list, 60 * 60 * 3)
        else:
            films_list = is_cached
            cached_page = True

    data = releasedata(films_list, {}, persons=True, likes=True, trailers=True, check_opinions=True)
    for i in data:
        if request.profile:
            for j in i['opinions'].get('objs', []):
                if j.rate and j.message.autor_id == request.profile.id:
                    i['opinions']['my_rate'] = j.rate

        cinemas = films_list.get(i['id'])
        i['cinemas'] = cinemas['cinemas']
        i['tickets'] = cinemas['tickets']

    data = sorted(data, key=operator.itemgetter('show_ir'), reverse=True)

    timer = '%5.2f' % (time.time() - timer)

    tmplt = 'kinoafisha/week_releases.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/week_releases.html'

    return render_to_response(tmplt, {'data': data, 'best': True, 'timer': timer, 'cached_page': cached_page}, context_instance=RequestContext(request))


@never_cache
def best_top250(request):
    dates = list(Top250.objects.all().values_list('date_upd', flat=True).order_by('date_upd').distinct('date_upd'))

    set_date = ''
    if not set_date:
        set_date = dates[-1]

    kids = list(Top250.objects.select_related('film').filter(date_upd=set_date).values_list('film__kid', flat=True))

    year = request.POST.get('year')
    genre = request.POST.get('genre')
    country = request.POST.get('country')

    filter = {'film_id__id__in': kids, 'type': 2, 'status': 1}

    names = FilmsName.objects.using('afisha').select_related('film_id').filter(**filter)

    years = []
    genres_ids = []
    country_ids = []
    names_dict = {}
    for i in names:
        years.append(i.film_id.year)
        genres_ids.append(i.film_id.genre1_id)
        genres_ids.append(i.film_id.genre2_id)
        genres_ids.append(i.film_id.genre2_id)
        country_ids.append(i.film_id.country_id)
        country_ids.append(i.film_id.country2_id)

        if not year and not country and not genre:
            names_dict[i.film_id_id] = i.name

    if year or country or genre:
        if year:
            filter['film_id__year__exact'] = year

        q_filter1 = {}
        q_filter2 = {}
        q_filter3 = {}

        if country:
            country = int(country)
            q_filter1 = {'film_id__country__id': country}
            q_filter2 = {'film_id__country2__id': country}

        if genre:
            genre = int(genre)
            q_filter1 = {'film_id__genre1__id': genre}
            q_filter2 = {'film_id__genre2__id': genre}
            q_filter3 = {'film_id__genre3__id': genre}

        names2 = FilmsName.objects.using('afisha').select_related('film_id').filter(Q(**q_filter1) | Q(**q_filter2) | Q(**q_filter3), **filter)
        for i in names2:
            names_dict[i.film_id_id] = i.name

    genres_objs = AfishaGenre.objects.using('afisha').filter(pk__in=set(genres_ids)).order_by('name')
    genres = []
    for i in genres_objs:
        genres.append({'id': i.id, 'name': i.name})

    countries_objs = AfishaCountry.objects.using('afisha').filter(pk__in=set(country_ids)).order_by('name')
    countries = []
    for i in countries_objs:
        countries.append({'id': i.id, 'name': i.name})

    years = set(years)
    years = sorted(years, reverse=True)

    awards = list(Awards.objects.filter(awardsrelations__kid__in=names_dict.keys()).values('awards__name_en', 'year', 'awardsrelations__kid', 'type', 'fest__name_en'))

    awards_dict = {}
    for i in awards:
        type_fest = u'номинация' if i['type'] == '1' else u'награда'

        txt = '%s %s, %s: %s\n' % (i['fest__name_en'], i['year'], type_fest, i['awards__name_en'])

        if awards_dict.get(int(i['awardsrelations__kid'])):
            awards_dict[int(i['awardsrelations__kid'])].append(txt)
        else:
            awards_dict[int(i['awardsrelations__kid'])] = [txt]

    top = []
    tops = Top250.objects.select_related('film').filter(date_upd=set_date, film__kid__in=names_dict.keys()).order_by('position')
    for i in tops:
        name = names_dict.get(i.film.kid)
        if not name:
            name = i.film.name

        awards_data = awards_dict.get(i.film.kid)

        top.append({'name': name, 'obj': i, 'awards': awards_data})

    tmplt = 'kinoafisha/top250.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/top250.html'

    return render_to_response(tmplt, {'data': top, 'date_upd': set_date, 'years': years, 'genres': genres, 'countries': countries, 'year': year, 'country': country, 'genre': genre}, context_instance=RequestContext(request))


@never_cache
def opinions(request):

    opinions_list = []

    filmsnews = NewsFilms.objects.select_related('message', 'message__autor').filter(message__visible=True).order_by('-message__dtime').exclude(Q(message__text=None) | Q(message__text=''))

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1

    p, page = pagi(page, filmsnews, 50)

    authors = []
    films = []
    for i in p.object_list:
        authors.append(i.message.autor)
        films.append(i.kid)

    films_names = list(FilmsName.objects.using('afisha').filter(type__in=(1, 2), status=1, film_id__id__in=films).values("film_id", "name", "type"))

    films_dict = {}
    for i in films_names:
        if not films_dict.get(i['film_id']):
            films_dict[i['film_id']] = {'name_en': None, 'name_ru': None, 'id': i['film_id']}
        if i['type'] == 1:
            films_dict[i['film_id']]['name_en'] = i['name'].strip()
        else:
            films_dict[i['film_id']]['name_ru'] = i['name'].strip()

    authors_dict = org_peoples(set(authors), dic=True)
    films = set(films)

    source_films = {}
    for i in SourceFilms.objects.filter(kid__in=films, source_obj__url='http://www.kino.ru/'):
        source_films[i.kid] = i

    for i in p.object_list:
        film = films_dict.get(i.kid)
        if film:
            author = authors_dict.get(i.message.autor.user_id)

            nick = 'Аноним'
            if author:
                nick = author['name']
                if i.message.autor_nick == 1 and author['nickname']:
                    nick = author['nickname']

            source_film = source_films.get(i.kid)

            if i.source_obj_id and source_film:
                url = 'http://www.kino.ru/film/%s/comments/%s' % (source_film.source_id.replace('film_', 'forum_'), i.source_id)
            else:
                url = None

            txt = i.message.text
            spam = True if u'http' in txt else False

            opinions_list.append({'date': i.message.dtime, 'film': film, 'spam': spam, 'nick': nick, 'full_txt': txt, 'source': url, 'source_name': 'kino.ru', 'id': i.id, 'rate': i.rate})

    opinions_list = sorted(opinions_list, key=operator.itemgetter('date'), reverse=True)

    tmplt = 'kinoafisha/opinions.html'
    if request.subdomain == 'm' and request.current_site.domain == 'kinoafisha.ru':
        tmplt = 'mobile/kinoafisha/opinions.html'

    return render_to_response(tmplt, {'opinions': opinions_list, 'p': p, 'page': page}, context_instance=RequestContext(request))


@never_cache
def old_kinoafisha(request):
    REG_ID = re.compile(ur'^\d+')

    status = REG_ID.findall(request.GET.get('status', ''))

    id = REG_ID.findall(request.GET.get('id', ''))
    id1 = REG_ID.findall(request.GET.get('id1', ''))
    id5 = REG_ID.findall(request.GET.get('id5', ''))

    if status:
        # Темы и обсуждения
        if status[0] == '111' and id:
            #return kinoafisha_news_func(request, None, id[0])
            return HttpResponseRedirect(reverse('kinoafisha_news', kwargs={'id': id[0]}))
        # Фильмы
        elif status[0] == '1' and id1:
            #return get_film_func(request, id1[0])
            return HttpResponseRedirect(reverse('get_film', kwargs={'id': id1[0]}))
        # Персоны
        elif status[0] == '5' and id5:
            #return get_person_func(request, id5[0])
            return HttpResponseRedirect(reverse('get_person', kwargs={'id': id5[0]}))

    return HttpResponseRedirect(reverse('kinoafisha_main'))


@never_cache
def rambler_test(request):
    return render_to_response('kinoafisha/rambler_test.html', {}, context_instance=RequestContext(request))

def yandex(request):
    return render_to_response('kinoafisha/yandex_4318c3791bcdbc7f.html')

def google_verify(request):
    return render_to_response('kinoafisha/google3f3c67d1889fcc48.html')


#OFC076
#def is_not_func():
#fileName = '{0}/{1}.json'.format(settings.KINOAFISHA_EXT, 'test_settings')
#with open(fileName, 'a') as outfile:
#    outfile.write("my!\n")
