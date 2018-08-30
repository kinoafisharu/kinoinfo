#-*- coding: utf-8 -*- 
import os
import string
import datetime
import json
from django.conf import settings


# генерация системного пути
def rel(*x):
    # возвращает системный путь
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), * x)


# получить отформатированную текущую дату, время
def get_ftd_date(format):
    now = datetime.datetime.now()
    return now.strftime(format)


def json_menu():
    fileName = '{0}/{1}.json'.format(settings.KINOAFISHA_EXT, 'menu_settings')
    with open(fileName, 'r') as infile:
        json_data = json.load(infile)
    return json_data
    
def get_menu_state():
    json_data = json_menu()
    menuArr = json_data['menu']
    menu_state = {}
    for x in menuArr:
        name = '{0}_{1}'.format(x['name'],x['submenu'])
        menu_state[name] = True if x['enable'] == '1' else False
    menu_level_0 = [i['name'] for i in menuArr]
    uniq_level_0 = set(menu_level_0)

    for x in uniq_level_0:
        status = False
        name = '{0}_s00'.format(x)
        for item in menuArr:
            if item['name'] == x and item['enable'] == '1':
                status = True
        menu_state[name] = status

#    fileName = '{0}/{1}.json'.format(settings.KINOAFISHA_EXT, 'test_settings')
#    with open(fileName, 'w') as outfile:
#        outfile.write("%s\n" % str(menu_state))

    return menu_state



'''
# лог для плохих url источников
def error_url_log(id, url, cin, cit, so, action):
    path1 = 'LOG/TEMP_ERROR_LOG.txt'
    path2 = 'LOG/ERROR_LOG.txt'
    text = str(id) + '***' + str(url) + '***' + str(cin) + '***' + str(cit) + '***' + str(so) + '\n'
    if action == 'save':
        open(rel(path1), 'a').write(str(text))
        fr = open(rel(path1)).read()
        c = string.count(fr, text)
        if c == 2: # --------------- 10
            ff = open(rel(path2)).read()
            cc = string.count(ff, text)
            if cc == 0:
                open(rel(path2), 'a').write(str(text))
            del_l(fr, text, path1)
    elif action == 'del':
        del_l(open(rel(path2)).read(), text, path2)

def del_l(f, t, p):
    fi = string.replace(f, t, '')
    os.remove(rel(p))
    open(rel(p), 'w').write(fi)


# лог для sms, неизвестные города и кинотеатры
def sms_log(code, cinema, city, url, action):
    path = 'LOG/sms_log.txt'
    text = str(code) + '***' + str(city) + '***' + str(cinema) + '***' + str(url) + '\n'
    if action == 'save':
        f = open(rel(path)).read()
        c = string.count(f, text)
        if c == 0:
            open(rel(path),'a').write(str(text))
    elif action == 'del':
        del_l(open(rel(path)).read(), text, path)


def count_bad(select):
    if select == 'url':
        path = 'LOG/ERROR_LOG.txt'
    elif select == 'sms':
        path = 'LOG/sms_log.txt'
    elif select == 'sch':
        path = 'LOG/schedule_log.txt'
    f = open(rel(path),'a')
    f = open(rel(path), 'r').read()
    c = string.count(f, '\n')
    return c


# лог ошибок для сеансов SMS
def log_error_sms(obj1, status, obj_id='', obj2=''):
    path = 'LOG/sms_import_seans_log.txt'
    fdate = get_ftd_date('%Y-%m-%d')
    if obj2 != '' and status == 1:
        open(rel(path), 'a').write(str(fdate) + '\t\t У кинотеатра (id: ' \
        + str(obj_id) + ') "' + str(obj1) + '" нет зала "' + str(obj2) + '"\n')
    elif obj2 != '' and status == 2:
        open(rel(path), 'a').write(str(fdate) + '\t\t Более 1 одинаковых залов (id: ' \
        + str(obj_id) + ') "' + str(obj1) + '" зал "' + str(obj2) + '"\n')
    elif obj2 == '' and status == 1:
        open(rel(path), 'a').write(str(fdate) + '\t\t Не найден фильм "' + str(obj1) + '"\n')
    elif obj2 == '' and status == 2:
        open(rel(path), 'a').write(str(fdate) + '\t\t Более 1 фильма "' + str(obj1) + '"\n')
    return True
'''


