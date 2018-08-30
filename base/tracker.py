# -*- coding: utf-8 -*-
#from base.funcall import *
#from base.models import *
#from models import AboutFilm

def afisha_importer(i):
    '''
    Импорт данных фильмов из таблиц киноафиши
    '''
    # очищаем задействованные модели - отладочная команда
    #models = (NameFilm, Note, AboutFilm)
    #for model in models:
    #    model.objects.all().delete()

    # пишем в лог начало процесса
    logger(2, u'Started refresh film|event:x00|', 'w')

    # подключаемся r базе киноафиши
    cursor = connections['afisha'].cursor()
    #cursor.execute('set names utf8')

    # формируем справочники со странами, компаниями, прокатчиками, жанрами
    cursor.execute('select id, name from country')
    country_dic = {}
    for row in cursor.fetchall():
        country_dic[row[0]] = row[1]

    cursor.execute('select id, name from company')
    company_dic = {}
    for row in cursor.fetchall():
        company_dic[row[0]] = row[1]

    cursor.execute('select id, name from prokat')
    prokat_dic = {}
    for row in cursor.fetchall():
        prokat_dic[row[0]] = row[1]

    cursor.execute('select id, name from genre')
    genre_dic = {}
    for row in cursor.fetchall():
        genre_dic[row[0]] = row[1]
    
    # запрос фильмов на киноафише
    cursor.execute('select film.id as id,\
    film.runtime,\
    film.limits, film.date,\
    film.comment, film.description, \
    film.site,\
    film.trailers,\
    film.year,\
    film.genre1, film.genre2, film.genre3,\
    film.IdAllDVD as imdb_id, film.imdb, \
    film.imdb_votes,\
    film.country, film.country2,\
    film.company,\
    film.prokat1, film.prokat2, \
    film_ext_data.rate1, film_ext_data.rate2, film_ext_data.rate3, film_ext_data.rate, film_ext_data.vnum \
    FROM film, film_ext_data where film.id = film_ext_data.id limit 100')
    list = []

    # цикл по фильмам
    for row in cursor.fetchall():
        list_country = []
        list_genre = []
        # пробуем найти фильм в модели
        try:
            abf = AboutFilm.objects.get(source=source_kinoafisha, sid=row[0])
        except AboutFilm.MultipleObjectsReturned:
            # несколько фильмов - ошибочная ситуация - пишем в лог 
            logger(2, u'Double film|error:x50|' + str(row[0]), 'a')
            continue
        except AboutFilm.DoesNotExist:
            # фильма нет - добавляем
            # генерируем идентификатор фильма
            try:
                fid = AboutFilm.objects.order_by('-fid')[0].fid + 1
            except IndexError:
                fid = 1
            # начинаем создавать запись
            # обрабатывем длительность
            runtime_val = datetime.timedelta(seconds=int(0))
            if row[1]:
                try:
                    rtv = int(row[1])
                    if rtv < 600:
                        try:
                            runtime_val = datetime.timedelta(seconds=int(60 * rtv))
                        except (TypeError, ValueError):
                            # не удалось сформировать значение продолжительности по неизвестной причине
                            logger(2, u'Bad runtime film|error:x52|' + str(row[0]) + '->' + str(row[1]), 'a')
                    else:
                        # продолжительность слишком большая
                        logger(2, u'Bad runtime film|error:x53|' + str(row[0]) + '->' + str(row[1]), 'a')
                except:
                    # продолжительность не число
                    logger(2, u'Bad runtime film|error:x55|' + str(row[0]) + '->' + str(row[1]), 'a')
            else:
                # продолжительность не указана
                pass
                #logger(2, u'Bad runtime film|error:x54|' + str(row[0]) + '->' + str(row[1]), 'a')

            # обрабатываем год выпуска
            try:
                year_val = int(row[8])
            except:
                year_val = 1
                logger(2, u'Bad YEAR film|error:x57|' + str(row[0]) + '->' + str(row[8]), 'a')

            # создаем запись фильма
            abf = AboutFilm(fid=fid, source=source_kinoafisha, sid=row[0], \
                            time=datetime.datetime.now(), year=year_val, runtime=runtime_val, \
                            rating=row[23], votes=row[24])
            abf.save()

            # добавляем аннотацию
            if row[5]: abf.note = Note.objects.create(note=htmldecode(row[5]))
            # добавляем страны
            if row[15]: list_country.append(add_model_element(Country, 'name', country_dic[row[15]]))
            if row[16]: list_country.append(add_model_element(Country, 'name', country_dic[row[16]]))
            if list_country: abf.country = list_country
            # добавляем жанры
            if row[9]: list_genre.append(add_model_element(Genre, 'name', genre_dic[row[9]]))
            if row[10]: list_genre.append(add_model_element(Genre, 'name', genre_dic[row[10]]))
            if row[11]: list_genre.append(add_model_element(Genre, 'name', genre_dic[row[11]]))
            if list_genre: abf.genre = list_genre

            # запрашиваем названия фильма
            cursor.execute('select name, type, status, hide FROM films_name where film_id=' + str(row[0]) + ' order by status, type')
            list_n = []
            # генерируем имена фильма
            for name in cursor.fetchall():
                if name[2] == 1: status = 1
                else: status = 0
                if re.search(u"[А-я]", name[0]): lg = lang_ru
                else: lg = lang_en
                list_n.append(NameFilm.objects.create(name=htmldecode(name[0]), language=lg, status=status))
            if list_n: abf.name = list_n
            #logger(2, u'Add film|Event:x88|' + str(row[0]), 'a')


            # создаем источник  IMdb
            if row[12]:
                try:
                    AboutFilm.objects.get(source=source_imdb, sid=row[12])
                except AboutFilm.DoesNotExist:
                    #logger(2, u'Addition film IMdb|Event:x42|' + str(row[0]), 'a')
                    if row[13]: rating_val = float(row[13].replace(',', '.'))
                    else: rating_val = 0
                    abfi = AboutFilm(fid=fid, source=source_imdb, sid=row[12], time=datetime.datetime.now(), rating=rating_val, votes=row[14])
                    abfi.save()
                    #logger(2, u'Add film imdb|Event:x89|' + str(row[0]), 'a')
                except AboutFilm.MultipleObjectsReturned:
                    logger(2, u'Douwble film IMdb|Error:x42|' + str(row[0]) + '->' + str(row[12]), 'a')
                else:
                    logger(2, u'Douwble film IMdb|Error:x43|' + str(row[0]) + '->' + str(row[12]), 'a')

            
            #list.append(row[0])
        else:
            # найден один фильм - пишем в лог
            #logger(2, u'Exists film|Event:x40|' + str(row[0]), 'a')
            # достаем идентификатор фильма
            fid = abf.fid

        # обрабатываем топики
        cursor.execute('select name_link, link from films_link where film_id=' + str(row[0]))
        for link_t in cursor.fetchall():
            if link_t[1].find('http://rutracker.org/forum/viewtopic.php?t=') != -1:
                tid = int(link_t[1][link_t[1].find('.php?t=') + 7:].replace('/', ''))
                # достаём текст и дату обновления топика
                try:
                    # пробуем достать топик из таблицы топиков
                    top_pres = Topick.objects.get(topick=tid)
                    try:
                        # проверяем нет ли такого источника
                        AboutFilm.objects.get(source=source_rutracker, sid=tid)
                        #logger(2, u'Exists  topick|Error:x33|' + str(row[0]) + '->' + str(tid), 'a')
                    except AboutFilm.DoesNotExist:
                        # получили исключение - нет объекта - добавляем топик как источник
                        rf = AboutFilm(fid=fid, source=source_rutracker, sid=tid, time=top_pres.time)
                        rf.note = Note.objects.create(note=htmldecode(top_pres.text))
                        rf.save()
                        #logger(2, u'Goog add topick|Event:x36|' + str(row[0]) + '->' + str(tid), 'a')
                except:
                    #logger(2, u'LOST topick|Error:x31|' + str(row[0]) + '->' + str(tid), 'a')
                    pass


    logger(2, u'Completed refresh film|event:x10|', 'a')
    return list

def chunks(l, n):
    ''' разивка списка l на части по n штук '''
    return [l[i:i + n] for i in range(0, len(l), n)]


def blok_load(type, list, script):
    ''' загрузка данных через API треккера 
    type = 0 - загрузка раздела
    type = 1 - загрузка топиков
    script = 0 - загрузчик
    script = 1 - чистильщик
    '''
    time.sleep(0.8) 
    if type == 0:
        url_f = 'http://api.rutracker.org/forum/api.php?api_id=kinoafisha&mode=get_t_ids&f=' + str(list)
    elif type == 1:
        url_f = 'http://api.rutracker.org/forum/api.php?api_id=kinoafisha&mode=get_t_titles&t=' + ','.join(list)
    else:
        return None
    # пробуем прочитать 
    logger(script, u'Try url|event:x15|' + url_f, 'a')
    try:
        topick_srt = htmldecode(urllib.urlopen(url_f).read().decode('cp1251'))
    except (IOError):
        # не удалось прочитать
        logger(script, u'Unable to open the page|error:x03|', 'a')
        return None
    if string.find(topick_srt, 'error:') != -1:
        # трекер не работает
        logger(script, u'Tracker does not work|error:x04|', 'a')
        return None    
    if string.find(topick_srt, '<body>') != -1:
        # трекер вернул страницу с предупреждением
        logger(script, u'Tracker not return data|error:x05|', 'a')
        return None
    logger('load_topick.txt', u'Tracker successfully returned data|event:x05|', 'a')
    return topick_srt


def topick_loader(i):
    ''' загрузка топиков c rutracker.org через API '''
    logger(0, u'Started downloading topics|event:x00|', 'w')
    source_rutracker = Source.objects.get(name='Rutracker')
    # выбираем необработанные разделы
    razdels = Section.objects.filter(status='0')
    if not razdels:
        # если необработанных нет - ставим всем статус - не обработан
        razdels = Section.objects.filter(status='1')
        for razdel in razdels:
            razdel.status = '0'
            razdel.save()
        razdels = Section.objects.filter(status='0')
    for razdel in razdels[0: 2]: # не более двух разделов за один проход 
        logger(0, u'Download section topics|event:x01|' + str(razdel.section), 'a')
        # разбиваем список топиков раздела на группы
        # split(','), 100) - 100 кол-во топиков в группе
        try:
            for url_str_list in chunks(blok_load(0, razdel.section, 0).split(','), 100):
                # обрабатываем группу топиков раздела
                for topick_srting_list in chunks(blok_load(1, url_str_list, 0).split('\n'), 2):
                    # выделяем текст топика и данные (дату, размер)
                    topick_data = topick_srting_list[0].split(',')
                    topick_srting = topick_srting_list[1]
                    # проверяем наличие топика
                    try:
                        tpf = Topick.objects.get(topick=topick_data[0])
                    except Topick.MultipleObjectsReturned:
                        # несколько топиков - ошибочная ситуация - пишем в лог - и удаляем оба
                        Topick.objects.filter(topick=topick_data[0]).delete()
                        #logger(0, u'duplicate topics|error:x04|' + topick_data[0],'a')
                    except Topick.DoesNotExist:
                        #logger(0, u'Topic not found|event:x03|' + topick_data[0],'a')
                        # топика нет - добавляем
                        parse = topick_parser(topick_srting)
                        tpf = Topick(topick=topick_data[0], fresh=datetime.datetime.now(), time=datetime.datetime.fromtimestamp(float(topick_data[1])), text=topick_srting, imdb=0, size=topick_data[2], p_year=parse['year'], p_quality=parse['quality'], section=razdel)
                        # проверяем нет ли топика среди источников
                        tpf.save()
                    else:
                        # найден один такой же топик - обновляем
                        #logger(0, u'Topic has been updated|event:x04|' + topick_data[0],'a')
                        parse = topick_parser(topick_srting)
                        tpf.fresh = datetime.datetime.now()
                        tpf.time = datetime.datetime.fromtimestamp(float(topick_data[1]))
                        tpf.text = topick_srting
                        tpf.imdb = 0
                        tpf.section = razdel
                        tpf.size = topick_data[2]
                        tpf.p_year = parse['year']
                        tpf.p_quality = parse['quality']
                        # проверяем нет ли топика среди источников
                        #try:
                        #    afisha = AboutFilm.objects.get(source=source_rutracker,sid=topick_data[0])
                        #except Topick.DoesNotExist:
                        #    tpf.kinoafisha = afisha.fid
                        tpf.save()
                razdel.status = 1
                razdel.fresh = datetime.datetime.now()
                razdel.save()
        except AttributeError:
            logger(0, u'AttributeError|error:x36|', 'a')
    logger(0, u'Completed download topics|event:x10|', 'a')
    return 'finish'
    
def topick_cleaner(i):
    ''' проверка актуальности топиков c использованием rutracker.org (через API) '''
    logger(1, u'Started testing topics|event:x25|', 'w')
    # получаем все неактуальные топики
    tpf = Topick.objects.filter(fresh__lte=datetime.datetime.now() - datetime.timedelta(days=5))
    # формируем список
    list_bad_full = []
    for tid in tpf:
        list_bad_full.append(str(tid.topick))
    if list_bad_full:
        count_del = 0
        # разбиваем список на группы по n штук
        for list_b in chunks(list_bad_full, 100):
            # для каждой группы достаем топики
            list_bad_full_test = list_b
            try:
                for test in chunks(blok_load(1, list_b, 1).split('\n'), 2):
                    # исключаем топики которые вернул трекер
                    list_bad_full_test.remove(test[0].split(',')[0])

                # пробуем удалять если, список изменился
                if list_bad_full_test != list_b:
                    for del_topick in list_bad_full_test:
                        Topick.objects.get(topick=del_topick).delete()
                        count_del = count_del + 1
                        # удаляем неактульные источники торрента
                        AboutFilm.objects.filter(source=source_rutracker, sid=del_topick).delete()
                        logger(1, u'lost topick|error:x08|' + del_topick, 'a')
            except:
                logger(1, u'Run-time error|error:x35|', 'a')
                break


    logger(1, u'Completed testing topics|event:x30|', 'a')
    f = open(rel('logs/clean_topick.txt'), 'r')
    return f.readlines()

    
    