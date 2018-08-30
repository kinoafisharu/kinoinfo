# -*- coding: utf-8 -*-
from base.funcall import *

def session_importer(request):
    ''' Импорт сеансов из таблиц киноафиши  '''
    result = {}
    cursor = connections['afisha'].cursor()

    # формируем справочник с сеансами
    cursor.execute('select id, time from session_list')
    session_dic = {}
    for row in cursor.fetchall():
        session_dic[row[0]] = row[1]

    
    # очищаем расписание
    # очищаем расписание
    # очищаем расписание
    Session.objects.all().delete()


    # достаем актуальные записи периодов
    today_str = datetime.datetime.today().strftime("%Y-%m-%d")
    cursor.execute('select movie_id, \
    film_id, \
    date_from, \
    date_to, \
    id \
    from schedule \
    where date_from>="' + today_str + '" or date_to>="' + today_str + '" \
    order by date_from')
    
    for row in cursor.fetchall():
        # достаем фильм
        film_list = []
        try:
            film = AboutFilm.objects.get(source=source_kinoafisha, sid=str(row[1]))
            film_list.append(film)
        except:
            # не нашли фильма - пропускаем
            print 'Film - ' + str(row[1])
            continue

        # достаем место
        try:
            cinema = Cinema.objects.get(code=row[0])
            place = Hall.objects.filter(cinema=cinema).order_by('name')[0]
        except:
            print 'Place - ' + str(row[0])

        press = row[2]
        finish = row[3]
        range = 10
        sch_list = []
        # формируем список дат периода
        while press <= finish:
            sch_list.append(press)
            press += datetime.timedelta(days=1)
            range = range - 1
            if not range: break
        # формируем список сеансов
        cursor.execute('select session_list_id \
        from session \
        where schedule_id="' + str(row[4]) + '"')
        sess_list = []
        for sess in cursor.fetchall():
            sess_list.append(session_dic[sess[0]])

        # цикл формирования сеансов
        for schedule in sch_list:
            if(schedule >= datetime.date.today()):
                for sess in sess_list:
                    dt = datetime.datetime.combine(schedule, sess)
                    session = Session.objects.create(place=place, time=dt)
                    session.film = film_list
                    session.save()
    return result


def hall_importer(request):
    list = []
    cursor = connections['afisha'].cursor()
    cursor.execute('select movie.techinfo, \
    movie.id, \
    movie.name, \
    city.name, \
    movie.ind, \
    movie.address, \
    movie.phones \
    from movie, city \
    where movie.city = city.id \
    order by movie.id')
    stat_hall_begin = 0
    stat_count_string = 0
    stat_count_err = 0
    stat_place_begin = 0
    stat_place_group = 0
    for row in cursor.fetchall():
        stat_count_string += 1
        temp = []
        string_f = htmldecode(row[0])
        string = string_f[0:string_f.find(u'мест') + 4]
        name_cin = htmldecode(row[2])
        addres_cin = htmldecode(row[5])
        phones_cin = htmldecode(row[6])
        # достаем (и добавляем если необходимо) город
        city = add_model_element(City, 'name', str(row[3]))
        # добавляем кинотеатр (или проверяем его наличие)
        try:
            cinema = Cinema.objects.get(name=name_cin, city=city)
        except Cinema.DoesNotExist:
            # кинотеатр не найден
            cinema = Cinema.objects.create(name=name_cin, city=city, code=row[1])
        except Cinema.MultipleObjectsReturned:
            # найдено несколько кинотеатров с одинаковыми названиями в одном городе
            pass
        else:
            # найден один кинотеатр проверяем и обновляем второстепенные параметры
            cinema.zip = str(row[4])
            # разбираем почтовый адрес
            addres_cin_list = addres_cin.split(',')

            if len(addres_cin_list) != 2:
                # нестандартное написание
                try:
                    number_hous = addres_cin_list[1].strip() + ', ' + addres_cin_list[2].strip()
                except:
                    number_hous = ''
            else:
                number_hous = addres_cin_list[1].strip()
            if (number_hous) and (len(number_hous) < 15):
                cinema.number_hous = number_hous
            else:
                pass
                str_err = '8'
                # слишком длинный номер дома
            cinema.street_name = addres_cin_list[0].strip()
        cinema.save()


        temp.append(string)
        # ищем залы в начале строки
        hall_num = 0
        try:
            for t in re.findall(u'^\d+\sзал', string, re.IGNORECASE):
                hall_num = int(t.replace(u'зал', '').strip())
            if hall_num: stat_hall_begin += 1
        except:
            hall_num = 0
        # ищем места в начале строки
        place_num = 0
        try:
            for t in re.findall(u'^\d+\sмест', string, re.IGNORECASE):
                place_num = int(t.replace(u'мест', '').strip())
            if place_num: stat_place_begin += 1
        except:
            place_num = 0
     
        # соотносим места и залы
        if (hall_num == 0) and (place_num != 0): hall_num = 1
        
        # пробуем обработает места в группе 111+111+111
        place_list = []
        if not place_num:
            for t in re.findall('[0-9]{2,3}', string):
                t = t.replace('+', '').strip()
                if t: place_list.append(int(t))

            if place_list: stat_place_group += 1

        # соотносим места и залы
        if (hall_num == 0) and (len(place_list)):
            hall_num = len(place_list)

        str_err = '100'
        if (hall_num == 1) and (place_num):
            pass
        else:
            if hall_num != len(place_list):
                str_err = '1'
                stat_count_err += 1
            else:
                if (hall_num == 0) and (place_num == 0):
                    str_err = '0'

        if (hall_num == 0) and (place_num == 0): hall_num = 1

        str_res = 'Залов: ' + str(hall_num) + ', Мест: '
        if place_num:
            str_res += str(place_num)
        else:
            for f in place_list:
                str_res += ' ' + str(f)

        temp = {}
        # достаем данные из таблиц залов
        cursor.execute("select hall.name, halls.places, halls.format  from halls, hall where \
        halls.movie='" + str(row[1]) + "' and hall.id = halls.id_name")
        str_real = ''
        count_real = 0
        for t in cursor.fetchall():
            if t:
                str_real += ' (' + t[0] + ' - ' + str(t[1]) + ') '
                count_real += 1

        str_real += ' = ' + str(count_real)

        #if hall_num:
        #    if int(hall_num) != int(count_real):
        #        str_err = '5'
        #        stat_count_err += 1
        #else:
        #    if (len(place_list)) and (len(place_list) != count_real):
        #        str_err = '5'
        #        stat_count_err += 1

        temp['table'] = str(str_real)

        temp['id'] = row[1]
        temp['name'] = name_cin
        temp['string'] = addres_cin
        #temp['string'] = string_f
        temp['res'] = str_res
        temp['err'] = str_err
        list.append(temp)

        stat = {}
        stat['stat_hall_begin'] = stat_hall_begin
        stat['stat_count_string'] = stat_count_string
        stat['stat_place_begin'] = stat_place_begin
        stat['stat_place_group'] = stat_place_group
        stat['stat_count_err'] = stat_count_err
        result = {}
        result['list'] = list
        result['stat'] = stat

        full_data = []
        # собираем данные о местах и залах в один пакет
        if(place_num == 0) and (len(place_list) == 0):
            full_data.append(['Зал 1', 0])
        else:
            if len(place_list) == 0:
                full_data.append(['Зал 1', place_num])
            else:
                num_cycle = 1
                for place_f in place_list:
                    hall_name_f = 'Зал ' + str(num_cycle)
                    full_data.append([hall_name_f, place_f])
                    num_cycle += 1

        # работаем с моделью залов
        # удаляем все залы кинотеатра
        Hall.objects.filter(cinema=cinema).delete()
        for hall_data in full_data:
            Hall.objects.create(cinema=cinema, name=hall_data[0], seats=hall_data[1])

    return result



def stat_sessioner(request):
    ''' Статистика сеансов '''
    pass

