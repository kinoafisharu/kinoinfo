#-*- coding: utf-8 -*-
import operator
import os
import time
import urllib

from django.conf import settings
from django.views.decorators.cache import never_cache
from user_registration.func import only_superuser
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def debug_timer(f):
    """.Функция декоратор @timer
        Используется для определения время выполнения запроса или любой функции
    """
    def tmp(*args, **kwargs):

        t = time.time()
        res = f(*args, **kwargs)
        send = "request time - %.2f .min" % ((float(time.time()-t))/60)
       #!!!!!# error_func(send)
        return res
    return tmp


def debug_logs(send, **kwargs):
    """.Функция используется для вывовда данных в лог
    """
    my_path = '%s/%s' % (settings.API_EX_PATH, 'movie_online/error_log.txt')

    # если в содержимом передают параметр для отчистки логов
    if send=="clear_logs":
        text_log = open(my_path, 'w')
        try:
            text_log.writelines("")  # записываем полученные данные в лог
        finally:
            text_log.close()

    else:
        text_log = open(my_path, 'a')  # открываем файл с логами, для записи в конец файла (атрибут "а")
        log_size = os.path.getsize(my_path)  # получаем размер файла с логами
        text_log.seek(log_size)  # переходим в конец файла, что бы каждый раз данные при записи дописывались, не накладываясь друг на друга
        try:
            text_log.writelines("%s" % send + '\n')  # записываем полученные данные в лог
        finally:
            text_log.close()


@never_cache
@only_superuser
@debug_timer
def create(request, method):
    """.Создает запрос, для функций без (request)
        Используется для ручных запросов, вместо 'cron'
    """
    result = method() # запуск выполнения
    # если при выполнении ошибка, сообщение об ошибке
    if result:
        return HttpResponse('Ошибка %s' % result)
    # иначе редирект на страницу вывода логов
    else:
        return HttpResponseRedirect(reverse('movie_logs'))



