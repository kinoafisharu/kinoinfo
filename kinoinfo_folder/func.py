#-*- coding: utf-8 -*- 
import os
import re
import string
import random
import datetime
from django.http import HttpResponse
#from base.models import AVI
from django.db import connections
from base.models import Logger

now = datetime.datetime.now()
fdate = now.strftime('%Y-%m-%d %H:%M:%S')


def rel(*x):
    '''
    Генерация системного пути, возвращает системный путь
    '''
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), * x)


def get_type_phone(t):
    '''
    Тип телефона
    '''
    if t == 'авто': return 'O'
    elif t == 'заказ' or t == 'касс' or t == 'брон': return 'K'
    elif t == 'справ': return 'S'
    elif t == 'факс': return 'F'
    elif t == 'бух': return 'B'
    elif t == 'админ': return 'A'
    elif t == 'директор': return 'D'
    return 'N'


def get_month(cinema_note):
    '''
    Месяцы
    '''
    if 'янв' in cinema_note:
        return '01'
    if 'фев' in cinema_note:
        return '02'
    if 'март' in cinema_note:
        return '03'
    if 'апре' in cinema_note:
        return '04'
    if 'май' in cinema_note or 'мае' in cinema_note or 'мая' in cinema_note:
        return '05'
    if 'июн' in cinema_note:
        return '06'
    if 'июл' in cinema_note:
        return '07'
    if 'авг' in cinema_note:
        return '08'
    if 'сентя' in cinema_note:
        return '09'
    if 'октя' in cinema_note:
        return '10'
    if 'ноя' in cinema_note:
        return '11'
    if 'декаб' in cinema_note:
        return '12'
    return '01'           

def get_month_en(month):
    if 'jan' in month:
        return 1
    if 'feb' in month:
        return 2
    if 'mar' in month:
        return 3
    if 'apr' in month:
        return 4
    if 'may' in month:
        return 5
    if 'jun' in month:
        return 6
    if 'jul' in month:
        return 7
    if 'aug' in month:
        return 8
    if 'sep' in month:
        return 9
    if 'oct' in month:
        return 10
    if 'nov' in month:
        return 11
    if 'dec' in month:
        return 12
    return None
    

def get_month_ua(month):
    if 'січ' in month:
        return 1
    if 'лют' in month:
        return 2
    if 'бер' in month:
        return 3
    if 'кві' in month:
        return 4
    if 'тра' in month:
        return 5
    if 'чер' in month:
        return 6
    if 'лип' in month:
        return 7
    if 'сер' in month:
        return 8
    if 'вер' in month:
        return 9
    if 'жов' in month:
        return 10
    if 'лис' in month:
        return 11
    if 'гру' in month:
        return 12
    return None


def streettype(res):
    '''
    Тип улицы
    '''
    if res:
        if res[0] == 'ул.' or res[0] == 'ул,' or res[0] == 'Ул' or res[0] == 'улица' or res[0] == 'ул':
            return 'улица'
        elif res[0] == 'пл.' or res[0] == 'пл,' or res[0] == 'Площадь' or res[0] == 'площадь':
            return 'площадь'
        elif res[0] == 'пр.' or res[0] == 'Пр.' or res[0] == 'пр-т' or res[0] == 'Пр-т' or res[0] == 'просп' or res[0] == 'проспект':
            return 'проспект'
        elif res[0] == 'бульвар':
            return 'бульвар'
        elif res[0] == 'наб' or res[0] == 'набережная':
            return 'набережная'
        elif res[0] == 'ш.' or res[0] == 'шоссе' or res[0] == 'Шоссе':
            return 'шоссе'
        elif res[0] == 'пер,' or res[0] == 'пер.' or res[0] == 'переулок':
            return 'переулок'
        elif res[0] == 'аллея':
            return 'аллея'
        elif res[0] == 'микрорайон' or res[0] == 'Микрорайон' or res[0] == 'мкр' or res[0] == 'микр.':
            return 'микрорайон'
        elif res[0] == 'квартал' or res[0] == 'квл':
            return 'квартал'
        elif res[0] == 'километр' or res[0] == 'км':
            return 'километр'
        elif res[0] == 'проезд' or res[0] == 'пр-д':
            return 'проезд'
        elif res[0] == 'тракт':
            return 'тракт'
        elif res[0] == 'парк':
            return 'парк'
    return None

'''
# генерация fid
def get_fid():
    fid = random.randrange(10000000000, 99999999999, 1)
    try:
        AVI.objects.get(fid=fid)
    except AVI.DoesNotExist:
        return fid
    else:
        return get_fid()
'''
    

def get_budget(film_comment):
    '''
    Бюджет фильма
    '''
    bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.\$|Бюджет\:* \d+?\,?\d+ тыс.\$|Бюджет\:* \d+?\,?\d+ млн.долларов|Бюджет\:* \d+?\,?\d+ тыс.долларов|Бюджет\:* \d+?\,?\d+ млн.канад|Бюджет\:* \d+?\,?\d+ тыс.канад', film_comment)
    if bu:
        bu = str(bu[0])
        bu_id = '$'
    else:
        bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.Fr|Бюджет\:* \d+?\,?\d+ тыс.Fr|Бюджет\:* \d+?\,?\d+ млн.франков|Бюджет\:* \d+?\,?\d+ тыс.франков', film_comment)
        if bu:
            bu = str(bu[0])
            bu_id = '$'
        else:
            bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.евро|Бюджет\:* \d+?\,?\d+ тыс.евро', film_comment)
            if bu:
                bu = str(bu[0])
                bu_id = '€'
            else:
                bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.фунтов|Бюджет\:* \d+?\,?\d+ тыс.фунтов', film_comment)
                if bu:
                    bu = str(bu[0])
                    bu_id = '$'
                else:
                    bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.шведских|Бюджет\:* \d+?\,?\d+ тыс.шведских', film_comment)
                    if bu:
                        bu = str(bu[0])
                        bu_id = '$'
                    else:
                        bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.инд.рупий|Бюджет\:* \d+?\,?\d+ тыс.инд.рупий', film_comment)
                        if bu:
                            bu = str(bu[0])
                            bu_id = '$'
                        else:
                            bu = re.findall('Бюджет\:* \d+?\,?\d+ млн.руб|Бюджет\:* \d+?\,?\d+ тыс.руб', film_comment)
                            if bu:
                                bu = str(bu[0])
                                bu_id = 'r'
                            else:
                                bu = None
                                bu_id = None
                                bu_sum = None      
    if bu:
        bu_sum = re.findall('\d?\d?\d\,?\d+', bu)
        bu_sum = bu_sum[0]
        bu_sum = bu_sum.split(',')
        bu_sum1 = bu_sum[0]
        try: bu_sum2 = bu_sum[1]
        except IndexError: bu_sum2 = None
        if bu_sum1 and bu_sum2 is None:
            bu_sum = '%s000000' % (bu_sum1)
        elif bu_sum1 and bu_sum2:
            if len(bu_sum2) == 3:
                bu_sum2 = '%s000' % (bu_sum2)
            elif len(bu_sum2) == 2:
                bu_sum2 = '%s0000' % (bu_sum2)
            elif len(bu_sum2) == 1:
                bu_sum2 = '%s00000' % (bu_sum2)
            bu_sum = int(str(bu_sum1) + str(bu_sum2))
    return (bu_sum, bu_id)


def capit(val):
    '''
    Первый символ в верхнем регистре (для кириллицы)
    '''
    try: return unicode(val.strip(), 'utf-8').capitalize().encode('utf-8')
    except TypeError: return val.strip().capitalize().encode('utf-8')

def low(val):
    '''
    Все символы в нижнем регистре (для кириллицы)
    '''
    try: return unicode(val.strip(), 'utf-8').lower().encode('utf-8')
    except TypeError: return val.strip().lower().encode('utf-8')

def uppercase(val):
    try: return unicode(val.strip(), 'utf-8').upper().encode('utf-8')
    except TypeError: return val.strip().upper().encode('utf-8')
    
def del_separator(name):
    '''
    Очистка от спец.символов
    '''
    sep = {
        '-': '', '–': '', '—': '', '.': '', ',': '', ':': '', '(': '', ')': '', '½': '', ';': '',\
        "'": '', '_': '', '?': '', '&': '', '!': '', '/': '', '`': '', '«': '', '»': '', "<": '',\
        '"': '', '*': '', "¢": "", "£": "", "¤": "", "¥": "", "¦": "", "§": "", '=': '', ">": '',\
        "¨": "", "©": "", "ª": "", "¬": "", "¯": "", "°": "", "±": "", "´": "", "µ": "", 'ё': 'е', \
        "¶": "", "·": "", "¸": "", "’": "", "¿": "", "À": "A", "Á": "A", "Â": "A", "Ã": "A", 'Ё': 'Е', \
        "Ä": "A", "Å": "A", "Æ": "Ae", "Ç": "C", "È": "E", "É": "E", "Ê": "E", "Ë": "E", \
        "Ì": "I", "Í": "I", "Î": "I", "Ï": "I", "Ð": "D", "Ñ": "N", "Ò": "O", "Ó": "O", \
        "Ô": "O", "Õ": "O", "Ö": "O", "×": "", "Ø": "O", "Ù": "U", "Ú": "U", "Û": "U", \
        "Ü": "", "Ý": "Y", "Þ": "p", "ß": "b", "à": "a", "á": "a", "â": "a", "ã": "a", \
        "ä": "a", "å": "a", "æ": "ae", "ç": "c", "è": "e", "é": "e", "ê": "e", "ë": "e", \
        "ì": "i", "í": "i", "î": "i", "ï": "i", "ð": "d", "ñ": "n", "ò": "o", "ó": "o", \
        "ô": "o", "õ": "o", "ö": "o", "÷": "", "ø": "o", "ù": "u", "ú": "u", "û": "u", \
        "ü": "", "ý": "y", "þ": "p", "ÿ": "y", "ž": "z", " ": "", ' ': '',
    }
    for k, v in sep.iteritems():
        name = name.replace(k, v)
    return name.strip()


def del_screen_type(name):
    '''
    Очистка от формата изображения
    '''
    name = name.replace('HFR','').replace('(48 fps)','').replace('_Ц','').replace('D-Box','').strip()
    name = name.replace('Dolby Atmos','').replace('48 кадров','').replace('(48fps)','')
    name = re.sub(r'(3DD|((\(В\s|\(в\s|\sВ\s|\sв\s)?(3(Д|д)|3\s?(Д|д)|2(Д|д)|\_?3\s?(D|d)|\_?2(D|d))\)?))', '', name)
    name = re.sub(r'(18|16|14|12|13|6|0)\s?\+', '', name)
    name = re.sub(r'\((большой зал|малый зал|повтор)\)', '', name)
    #name = name.replace('IMAX','').replace('imax','')
    return name 


def logger(**kwargs):
    '''
    лог ошибок
    event 1 (импорт из киноафиши):
        code: 1 - нет города, 2 - нет кинотеатра, 3 - нет зала, 4 - нет фильма
    event 2 (парсер sms.txt):
        code: 1 - нет города, 2 - нет кинотеатра
    event 3 (импорт сенсов из источников)
        code: 1 - url не доступен, 2 - для источника нет сеансов, 3 - нет фильма
    '''
    url = None
    text = None
    extra = None
    event = kwargs['event']
    code = kwargs['code']
    kinoafisha = 'http://www.kinoafisha.ru/index.php3'
    if event == 1:
        if code == 1:
            text = 'Нет города (id на киноафише "%s")' % (kwargs['obj1'])
        elif code == 2:
            text = 'В городе "%s" нет кинотеатра' % (kwargs['obj1'])
            url = '%s?id2=%s&status=2' % (kinoafisha, kwargs['obj2'])
        elif code == 3:
            url = '%s?id2=%s&status=2' % (kinoafisha, kwargs['obj2'])
            text = 'В кинотеатре "%s" (г.%s) нет зала' % (kwargs['obj1'], kwargs['obj3'])
        elif code == 4:
            url = '%s?status=1&id1=%s' % (kinoafisha, kwargs['obj1'])
            text = 'Нет фильма'
        myfilter = {'{0}'.format('text'): text, '{0}'.format('url'): url, '{0}'.format('obj_name'): kwargs['bad_obj'], '{0}'.format('event'): event, '{0}'.format('code'): code,}
    elif event == 2:
        if code == 1:
            text = 'Нет города'
            url = kwargs['obj2']
        elif code == 2:
            text = 'В городе "%s" нет кинотеатра' % (kwargs['obj1'])
            url = kwargs['obj2']
            extra = kwargs['extra']
        myfilter = {'{0}'.format('text'): text, '{0}'.format('url'): url, '{0}'.format('obj_name'): kwargs['bad_obj'], '{0}'.format('event'): event, '{0}'.format('code'): code,}
    elif event == 3:
        if code == 1:
            url = kwargs['bad_obj']
            text = 'Источник недоступен (id "%s")' % (kwargs['obj1'])
        if code == 2:
            url = kwargs['bad_obj']
            text = 'Для источника (id "%s") нет сеансов' % (kwargs['obj1'])
        if code == 3:
            url = kwargs['obj1']
            text = 'Нет фильма'
            extra = kwargs['extra']
        myfilter = {'{0}'.format('text'): text, '{0}'.format('obj_name'): kwargs['bad_obj'], '{0}'.format('event'): event, '{0}'.format('code'): code,}
    try: Logger.objects.get(**myfilter)
    except Logger.DoesNotExist: Logger(text=text, url=url, obj_name=kwargs['bad_obj'], extra=extra, event=event, code=code).save()


##################### test

def tables_list(request):
    '''
    Список таблиц в БД
    '''
    sql = "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"
    db = connections['default']
    cursor = db.cursor()
    cursor.execute(sql)
    text = ''
    for i in cursor.fetchall():
        text += str(i[1]) + '<br />'
    return HttpResponse(text)
