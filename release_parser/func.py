#-*- coding: utf-8 -*- 
import os
import datetime
import time
import cookielib
import urllib2

from django.conf import settings

from base.models import ActionsPriceList, PaidActions


def get_imdb_id(id):
    if id:
        id = str(id)
        if len(id) < 7:
            while len(id) != 7:
                id = '0%s' % id
        return id
    return None


def get_file_modify_datetime(path, filename):
    '''
    Возвращает дату время последней модификации/создания файла
    Принимает:
    path - полный путь к файлу
    filename - название файла с расширением
    '''
    file = os.stat('%s/%s' % (path, filename))
    modify_date = time.gmtime(file.st_ctime)
    modify_date = datetime.datetime(
        modify_date.tm_year, modify_date.tm_mon, modify_date.tm_mday, modify_date.tm_hour, modify_date.tm_min, 0
    )
    return modify_date


def cron_success(type, source, filename, info):
    '''
    Создает дамп означающий успешное выполнение задания в кроне
    Принимает:
    type - тип (спарсенных) данных, если передан не html, то считает что xml
    source - источник данных, например 'okino.ua'
    filename - информативное название дампа, например 'kinohod_cities'
    info - короткое описание задания (цель) крона, например 'Города' или 'Укр. кинотеатры'
    '''
    if type == 'json':
        type = 'xml'

    path = '%s/%s__%s__%s.xml' % (settings.SUCCESS_LOG_PATH, type, source, filename)
    try:
        os.remove(path)
    except OSError:
        pass

    with open(path, 'w') as f:
        f.write('<data>%s</data>' % info)


def actions_logger(pk, obj_id, profile, act, extra=None):
    if act:
        try:
            action = ActionsPriceList.objects.get(pk=pk, allow=True)
            PaidActions.objects.create(
                action=action,
                profile=profile,
                object=obj_id,
                act=act,
                extra=extra,
            )
            return True
        except ActionsPriceList.DoesNotExist:
            pass
    return False


def give_me_cookie():
    cookie = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie), urllib2.HTTPHandler())
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1'}
    opener.addheaders = headers.items()
    return opener
