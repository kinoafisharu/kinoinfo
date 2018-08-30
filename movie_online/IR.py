#-*- coding: utf-8 -*-
import os
import time

from django.views.decorators.cache import never_cache
from django.shortcuts import redirect, render_to_response, RequestContext

from base.models import *
from api.models import *
from release_parser.func import cron_success
from user_registration.func import only_superuser
from movie_online.debug import debug_timer, debug_logs

def integral_rate(kid=None):
    """функция для вычисления интегральной оценки.

    Формаула:  ((сум_оценка_км_1 + сум_оценка_км_2 + ... )/кол-во_оценок * 2 + IMDb + RT)/4

    Сложность процесса:

    Сперва из таблицы AfishaNews по айди фильма получаем айди кинометра оценившего фильм, фильтрация:(obj__id=айди фильма, type=2, object_type=1)
    Их количество не ограниченно, по этому создается словарь, где ключ - айди фильма, а значение - список всех проголосовавших киномэтров.

    Далее необходипо по каждому айди киномэтра из списка, вытащить оценку которую они поставили фильму. Оценки храняться отдельно
    в таблице FilmVotes, всего оценок три, фильм оценивается по трем параметрам. Таким образом мы берем каждые три оценки по каждому
    оценившему киномэтру, суммируем их и подставляем в формулу - сум_оценка_км_1

    """

    # для вывовда данных в лог
    #my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_log.txt')

    #получаю массив тех данных которые уже есть базе и дальше использую эти данные, а не обращаюсь каждый раз к  базе
    ir_data = IntegralRating.objects.all()
    ir_data_dict = {}
    for i in ir_data:
        ir_data_dict[int(i.afisha_id)] = i



    if kid:
        filter_year = {'pk': kid}
    else:
        # "Новинки" - получаю список фильмов для интегральной оценки
        now_year = datetime.datetime.now().year
        new_films = now_year - 3
        filter_year = {'year__lte': now_year}

    films = {}
    for i in Film.objects.using('afisha').only('imdb', 'id').filter(**filter_year):
        films[i.id] = {'obj': i, 'r': []}

    # рейтинг от rottentomatoes
    rotten = SourceFilms.objects.filter(source_obj__url='http://www.rottentomatoes.com/', kid__in=films.keys())
    rotten_dict = {}
    for i in rotten:
        
        average, reviews, fresh, rotten = i.extra.split(';')
        try:
            average = float(average.replace('/10',''))
        except ValueError:
            average = 0
        rotten_dict[i.kid] = average

    # получаем все рецензии
    reviews = AfishaNews.objects.using('afisha').only('obj', 'id').filter(obj__id__in=films.keys(), type=2, object_type=1)
    reviews_dict = {}
    for i in reviews:
        reviews_dict[i.id] = i.obj_id

    # получаем все оценки у рецензий
    votes = FilmVotes.objects.using('afisha').filter(pk__in=reviews_dict.keys())
    for i in votes:
        film_id = reviews_dict.get(i.id)
        reviews_rate = i.rate_1 + i.rate_2 + i.rate_3
        if reviews_rate:
            films[film_id]['r'].append(reviews_rate)


    # вычисляем ИО и сохраняем
    for k, i in films.items():
        sources_count = 0

        imdb = float(i['obj'].imdb.replace(',','.')) if i['obj'].imdb else 0
        rt = rotten_dict.get(k, 0)

        if imdb:
            sources_count += 1
        if rt:
            sources_count += 1

        IR = 0
        reviewers_rate = 0

        if i['r']:
            sources_count += 2
            reviewers_rate = float(sum(i['r'])) / float(len(i['r']))
            IR = (reviewers_rate * 2 + imdb + rt) / sources_count
        elif imdb or rt:
            IR = (imdb + rt) / sources_count

        #open('ddd.txt', 'a').write(str(k) + ':\t' + str(IR) + '\n')

        ir_obj = ir_data_dict.get(int(k))
        if ir_obj:
            ir_obj.i_rate = IR
            ir_obj.trouble = None
            ir_obj.imdb = imdb
            ir_obj.reviews = reviewers_rate
            ir_obj.rotten = rt
            ir_obj.save()
        else:
            IntegralRating.objects.create(
                afisha_id = k,
                i_rate = IR,
                trouble = None,
                imdb = imdb,
                reviews = reviewers_rate,
                rotten = rt,
            )

    source = ImportSources.objects.get(url='http://www.kinoafisha.ru/')
    cron_success('import', source.dump, 'integral_ratings', 'Оценки киномэтров')



# функция для получения интегральной оценки, получает айди фильма
def check_int_rates(kid):

    int_rate = 0
    show_imdb = 0
    rotten = 0
    show_ir = 0

    # берем интегральную оценку и сохраняем в int_rate
    try:
        ir = IntegralRating.objects.get(afisha_id = kid)
        int_rate = ir.i_rate
        show_imdb = ir.imdb
        if ir.reviews:
            show_ir = "%.1f" % ir.reviews
            show_ir = show_ir.replace('.',',')
        rotten = ir.rotten
    except IntegralRating.DoesNotExist: 
        pass
    except IntegralRating.MultipleObjectsReturned:
        find_irate_flag = 0
        ir = IntegralRating.objects.filter(afisha_id = kid)
        for i in ir:
            if i.i_rate:
                find_irate_flag = 1
                int_rate = i.i_rate
                show_imdb = i.imdb
                if i.reviews:
                    show_ir = "%.1f" % i.reviews
                    show_ir = show_ir.replace('.',',')
                rotten = i.rotten
                break
        if find_irate_flag:
            pass
        else:
            ir = IntegralRating.objects.filter(afisha_id = kid)[0]
            int_rate = ir.i_rate
            show_imdb = ir.imdb
            if ir.reviews:
                show_ir = "%.1f" % ir.reviews
                show_ir = show_ir.replace('.',',')
            rotten = ir.rotten

    # возвращаем оценку по пятибальной шкале
    if int_rate >= 7.5:
        int_rate = 5
    elif int_rate < 7.5 and int_rate >= 6:
        int_rate = 4
    elif int_rate  < 6 and int_rate >= 5:
        int_rate = 3
    elif int_rate  < 5 and int_rate > 0:
        int_rate = 2
    elif int_rate  == 0:
        int_rate = 0

    return int_rate, show_ir, show_imdb, rotten




def check_int_rates_inlist(kid_list):

    ratings_dict = {}

    IR = IntegralRating.objects.filter(afisha_id__in = kid_list)
    IR_dic = {}
    for i in IR:
        int_rate = i.i_rate
        show_imdb = i.imdb if i.imdb != 0.0 else ''
        show_ir = 0
        if i.reviews:
            show_ir = "%.1f" % i.reviews
            show_ir = show_ir.replace('.',',')
        rotten = i.rotten
        IR_dic[i.afisha_id] = {"int_rate": int_rate, "show_ir": show_ir, "rotten": rotten, "show_imdb": show_imdb}


    for i in kid_list:
        int_rate = IR_dic.get(i, {'int_rate': 0})['int_rate']
        show_ir = IR_dic.get(i, {'show_ir': 0})['show_ir']
        rotten = IR_dic.get(i, {'rotten': 0})['rotten']
        show_imdb = IR_dic.get(i, {'show_imdb': 0})['show_imdb']
        review_rate = float(str(show_ir).replace(',','.'))

        # возвращаем оценку по пятибальной шкале
        if int_rate >= 7.5:
            int_rate = 5
        elif int_rate < 7.5 and int_rate >= 6:
            int_rate = 4
        elif int_rate  < 6 and int_rate >= 5:
            int_rate = 3
        elif int_rate  < 5 and int_rate > 0:
            int_rate = 2
        elif int_rate  == 0:
            int_rate = 0

        ratings_dict[i] = {
            'int_rate': int_rate,
            'show_ir': show_ir,
            'show_imdb': show_imdb,
            'rotten': rotten,
            'review_rate': review_rate,
            'kid': i,
        }
    #debug_logs(ratings_dict)
    return ratings_dict
