#-*- coding: utf-8 -*- 
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.gzip import gzip_page
from django.db.models import Q
from django.utils import simplejson

from api.models import *
from api.func import *
from base.models import *
from kinoinfo_folder.func import capit
from user_registration.func import login_counter, only_superuser, org_peoples
from release_parser.func import get_imdb_id, actions_logger

import json
from articles.views import pagination as pagi
from random import randint
from api.panel import pagination
from base.func import create_kinoafisha_button


def get_daniya_films():
    file = open('%s/daniya_films.txt' % settings.API_EX_PATH, 'r')
    films = [i for i in file.readlines()]
    file.close()
    return films


def in_group(user, name):
    """
    Проверка - состоит ли посетитель в указанной групе пользователей
    принимает user - объект пользователь, name - название группы  (например 'API')
    """
    try:
        user.groups.get(name=name)
        return True
    except: 
        return False

def is_client_api(request):
    userid = str(request.user.id)
    ip = str(get_client_ip(request))

#OFC76
#    key = request.GET.get("key", "XXXXX-XXXXXXXXX")
#    format = request.GET.get("format", "unknown_format")
#
#    fileNameTest = '{0}/{1}.json'.format(settings.API_CLIENTS_PATH, 'test_api_client')
#    with open(fileNameTest , 'a') as outfile:
#        outfile.write(str(userid) + " " + key + " " + format + " " + ip + '\n')


    json_data = json_api_user()

    known_users = [i['userid'] for i in json_data['access']]

    if userid in known_users:
        for x in json_data['access']:
            if x['userid'] == userid and x['user_is_active'] == '1':
                return True
    else:
        key = str(request.GET.get("key", ""))
        if key == "":
            return False
        else:
            known_key = [i['api_key'] for i in json_data['access']]

            if key in known_key:
                for x in json_data['access']:
                    if x['api_key'] == key and x['user_is_active'] == '1' and api_valid_ip(ip, x['ip_start'], x['ip_end']):
                        return True
            else:
                return False
    return False
        
def old_is_client_api(request):
    """
    Проверка - является ли пользователь клиентом API
    """
    if in_group(request.user, 'API'):
        return (True, None)
    else:
        if 'login' in request.GET:
            ip = get_client_ip(request)
            vip_logins = ()
            '''
            vip_logins = (
                'gruvi-9b7b338e8169db68e2f01f91c33803a4', 
                'kirich1409-33803a4e2f01f91ce8169db689b7b338',
                'google.com_118070499664784923416',
            )
            '''
            if request.GET['login'] in (vip_logins):
                return (True, request.GET['login'])
            elif identification_ip(request.GET['login'], ip):
                return (True, request.GET['login'])
    return False

def dump_logger(runtime):
    """
    Лог создания дампа
    """
    return '\nОбщее время выполнения: %5.1f сек.\n' % (time.time()-runtime)

def xml_wrapper(text):
    """
    Обварачиваю данные дампа в xml структуру 
    """
    return '<?xml version="1.0" encoding="UTF-8"?><data>%s</data>' % text

def get_dump_files(name_list, dump_path):
    dump_dict = {}
    for i in name_list:
        dump_dict[i] = {'name': i}
        if os.path.isfile('%s/dump_%s.xml' % (dump_path, i)):
            dump_dict[i]['del'] = True
            modify_date = os.stat('%s/dump_%s.xml' % (dump_path, i))
            hour = int(time.strftime('%H', time.gmtime(modify_date.st_ctime))) + 2
            f_modify = time.strftime('%d-%b' + ' ' + str(hour) + ':%M', time.gmtime(modify_date.st_ctime))
            #f_modify = time.strptime(f_modify, "%d-%b %H:%M")
            #f_modify = f_modify + datetime.timedelta(0,0,0,0,0,2)
            dump_dict[i]['modify'] = f_modify
        else:
            dump_dict[i]['del'] = False
    return dump_dict


def get_dump_films_files(path):
    import operator
    dump_list = []
    years_list = ['1990', '1990_1999', '2000_2009', '2010_2011'] + map(str, range(2012, datetime.date.today().year + 1))
    for i in years_list:
        name = 'film%s' % i
        alt_name = i.replace('_','-')
        dump = {'name': i, 'del': False, 'alt': alt_name, 'year': i}
        if os.path.isfile('%s/dump_%s.xml' % (path, name)):
            modify_date = os.stat('%s/dump_%s.xml' % (path, name))
            hour = int(time.strftime('%H', time.gmtime(modify_date.st_ctime))) + 2
            f_modify = time.strftime('%d-%b' + ' ' + str(hour) + ':%M', time.gmtime(modify_date.st_ctime))
            dump['modify'] = f_modify
            dump['del'] = True
        dump_list.append(dump)
    dump_list = sorted(dump_list, key=operator.itemgetter('alt'))
    return dump_list
    
@never_cache
def main(request):
    """
    ГЛАВНАЯ СТРАНИЦА API, вывод для клиентов api список существующих дампов
    """

    login_counter(request)
    lang, request = getUserLang(request)
    fileName = getApiDescrFileName(request)
    api_description = open(fileName,'r')
    description = api_description.read()
    api_description.close()
    return render_to_response('api/api_main.html', {'description': description, 'lang': lang, 'dev': False}, context_instance=RequestContext(request)) 


@never_cache
def api_dev(request):
    """
    для разработчиков. условия, ссылка на гит и т.д.
    """

    login_counter(request)
    lang, request = getUserLang(request)
    fileName = getApiDevFileName(request)
    api_description = open(fileName,'r')
    description = api_description.read()
    api_description.close()
    return render_to_response('api/api_main.html', {'description': description, 'lang': lang, 'dev': True}, context_instance=RequestContext(request)) 


@never_cache
def get_details(request, method):
    lang = request.session.get('django_api_language', 'ru')
    if method == 'widgets':
        code1 = '<iframe width="343" height="240" src="http://kinoinfo.ru/api/widget/schedule/?city=саратов&style=normal" frameborder="0"></iframe>'
        code2 = '<iframe width="325" height="240" src="http://kinoinfo.ru/api/widget/schedule/?city=анапа&style=small" frameborder="0"></iframe>'

        if lang == 'en':
            params = "City: city=саратов<br />Widget size: style=normal, <br />style=small"
            return render_to_response('api/api_description_widgets.html', {
                'api_title': 'Sessions',
                'api_decription': 'The widget provides a list of movies and sessions for the current number in a given city (or Moscow)', 
                'api_example': (code1, code2),
                'api_param': params,
                'api_response_details': '',
                'lang': lang,
            }, context_instance=RequestContext(request))
        else:
            params = "Город: city=саратов<br />Размер виджета: style=normal, <br />style=small"
            return render_to_response('api/api_description_widgets.html', {
                'api_title': 'Сеансы',
                'api_decription': 'В виджете представлен список фильмов и сеансов на текущее число в заданном городе (или Москве)', 
                'api_example': (code1, code2),
                'api_param': params,
                'api_response_details': '',
                'lang': lang,
            }, context_instance=RequestContext(request))

    elif method == 'button':
        warning = ''
        img = ()

        if request.POST:
            url = request.POST.get('url','').strip()
            if url:
                imdb_id = None
                film_id = None
                if 'imdb.com/title/tt' in url:
                    xurl = url.split('imdb.com/title/tt')[1].split('/')[0].replace('/','')
                    xurl = xurl.split('?')[0]
                    imdb_id = int(xurl)
                elif 'kinoafisha.ru/' in url:
                    xurl = urlparse(url)
                    if xurl.query:
                        params = parse_qs(xurl.query)
                        film_id = params.get('id1')
                        film_id = film_id[0] if film_id else None
                    else:
                        film_id = xurl.path.replace('/film/','').replace('/','')
                    
                    try:
                        film_id = int(film_id)
                    except ValueError:
                        film_id = None

                if imdb_id or film_id:
                    if imdb_id:
                        try:
                            film = Film.objects.using('afisha').get(idalldvd=imdb_id)
                        except Film.DoesNotExist:
                            try:
                                from urlparse import urlparse, parse_qs
                                from release_parser.imdb import create_film_by_imdb_id
                                film = create_film_by_imdb_id(imdb_id)
                            except:
                                film = None
                    else:
                        try:
                            film = Film.objects.using('afisha').get(pk=film_id)
                        except Film.DoesNotExist:
                            film = None

                    if film:
                        img = create_kinoafisha_button(film, imdb_id)
                    else:
                        if lang == 'ru':
                            warning = 'Фильм не найден в базе'
                        else:
                            warning = 'Film not found in database'

                else:
                    if lang == 'ru':
                        warning = 'Неверный URL'
                    else:
                        warning = 'Invalid URL'
            else:
                if lang == 'ru':
                    warning = 'Вы не ввели URL'
                else:
                    warning = 'Enter URL, plaese'

        return render_to_response('api/api_imdb_button.html', {'warning': warning, 'img': img, 'lang': lang},  context_instance=RequestContext(request))

    else:
        try:
            fileName = '{0}/{1}.xml'.format(settings.API_EX_PATH, method)
            if lang == 'en':
                try:
                    details = BeautifulSoup(open('{0}.{1}'.format(fileName, '(en)') ).read(), "html.parser")
                except:
                    details = BeautifulSoup(open(fileName).read(), "html.parser")
            else:
                details = BeautifulSoup(open(fileName).read(), "html.parser")
        except IOError:
            raise Http404
        link = 'http://%s/api/%s' % (request.get_host(), details.api_example.string)
        return render_to_response('api/api_description.html', {
            'status': 'True',
            'api_title': details.api_title.string,
            'api_decription': details.api_decription.string,
            'api_example': link,
            'api_param': details.api_param.string,
            'api_response_details': details.api_response_details.string,
#            'api_dev': details.api_dev.string,
            'lang' : lang,
        }, context_instance=RequestContext(request))


def create_dump_file(name, path, data, format='xml'):
    import codecs
    # если дамп уже существует, то удаляю его
    try:
        os.remove('%s/dump_%s.%s' % (path, name, format))
    except OSError: pass  
    # открываю файл для записи
    if isinstance(data, unicode):
        f = codecs.open('%s/dump_%s.%s' % (path, name, format), 'wb', "utf-8")
        f.write(data)
        f.close()
    else:
        with open('%s/dump_%s.%s' % (path, name, format), 'w') as f:
            f.write(data)
        


def save_dump(text, runtime, request, name, status='', format='xml', version='1'):
    '''
    Сохранение дампа
    '''
    if version in ('3', '4'):
        version_txt = '_v%s_' % version
    else:
        version_txt = ''
    
    method = '%s%s%s' % (name, version_txt, status)

    # записываю в БД это событие
    if request:
        api_logger(request, method, 1)
        
    create_dump_file(method, settings.API_DUMP_PATH, text, format)
    
    log = dump_logger(runtime) if runtime else ''
    
    if request:
        # передаю данные в шаблон
        return {'log': log, 'method': name, 'param': status, 'version': version}


def int_or_none(num):
    if num:
        try:
            num = int(num)
        except ValueError:
            num = None
        if num < 1:
            num = None
    return num


def set_limits(request):
    """
    Устанавливает ограниение на выборку в зависимости от 
    статуса юзера (клиент, посетитель, адми)
    """
    acc = is_client_api(request)
    limits = settings.API_CLIENT_LIMIT if acc else settings.API_GUEST_LIMIT
    return limits

@never_cache
@gzip_page
def show_method(request, method, ver=None):
    """
    Запускает необходимый метод и делает запись в лог об этом
    """
    name = method.__name__.replace('content_','')
    response_format = request.GET.get('format')

    banned_ips = ['176.59.215.15', ]

    ip = get_client_ip(request)
    if ip in banned_ips:
        data = 'Ваш IP %s времено заблокирован. Вы можете скачивать полный дамп данных за ежемесячную оплату или ежегодную оплату. Все вопросы пишите на адрес kinoafisharu@gmail.com\n\nYour IP %s is temporarily blocked. You can download a full dump of data for a monthly fee or annual fee. Any questions please email to kinoafisharu@gmail.com' % (ip, ip)
        if response_format == 'json':
            result = {'error': data}
        else:
            result = '<data><error>%s</error></data>' % data
    else:
        limit = set_limits(request)
        next = False


        user_ip = get_client_ip(request)

        if user_ip in ('178.62.252.63', '28.199.241.25', '188.166.119.211'): # cinepass
            next = True

        #if limit == settings.API_GUEST_LIMIT:
        #
        #else:
        #    next = True

        if not next:
            try:
                exist_requests = APILogger.objects.filter(ip=user_ip).order_by('-date')[0]
                now = datetime.datetime.now()
                if (exist_requests.date + datetime.timedelta(seconds=10)) <= now:
                    next = True
            except IndexError:
                next = True
        

        if next:
            if ver:
                result = method(limit, request, response_format, ver)
            else:
                result = method(limit, request, response_format)
            api_logger(request, name, 2)
        else:
            result = '<data><error>Превышено допустимое число запросов к API. Допустимо не более 1 запроса за 10 секунд. Все вопросы пишите на адрес kinoafisharu@gmail.com\n\nExceeded the maximum number of requests to the API. Allow not more than 1 request per 10 seconds. Any questions please email to kinoafisharu@gmail.com</error></data>'
    
    if response_format == 'json':
        response = HttpResponse(simplejson.dumps(result, ensure_ascii=False), mimetype='application/json')
        response['Content-Disposition'] = 'attachment; filename=%s.json' % name
        return response
    else:
        return render_to_response('api/api_schedule.html', {'text': result}, mimetype='application/xml')



def content_schedule(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все сеансы от сегодняшней даты
    """
    result, version = query_schedule(limits, request)
    return get_schedule(result, response_format, mk_dump, version)

def query_schedule(limits, request):
    date_from = get_formated_date('%Y-%m-%d')
    get_city = None
    get_movie = None
    version = '1'
    if request:
        get_city = request.GET.get('city')
        if get_city and u'�' in get_city:
            request.encoding = 'windows-1251'
            get_city = request.GET.get('city')
        
        get_movie = request.GET.get('movie')
        version = request.GET.get('version')
    myfilter = {}
    if get_city:
        city_parts = [capit(i) for i in get_city.split(' ')]
        city_name = ' '.join(city_parts)
        
        myfilter = {'schedule_id__movie_id__city__name': city_name.strip(), 'schedule_id__movie_id__city__name': get_city}
    elif get_movie:
        try:
            get_movie = int(get_movie)
        except ValueError:
            get_movie = None
        myfilter = {'schedule_id__movie_id__id': get_movie}
    result = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__movie_id__city', 'schedule_id__film_id', 'schedule_id__hall_id', 'schedule_id__hall_id__id_name').filter(Q(schedule_id__date_from__gte=date_from) | Q(schedule_id__date_from__lt=date_from) & Q(schedule_id__date_to__gte=date_from)).filter(**myfilter).order_by('schedule_id__movie_id__city__name', 'schedule_id__movie_id__name')[:limits]
    return result, version
    
@only_superuser
@never_cache
def dump_schedule(request):
    runtime = time.time()
    result_xml, result_json = content_schedule(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'schedule')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'schedule', '', 'json')
    return HttpResponseRedirect(reverse('statistics_main'))


def get_schedule(schedule, response_format, mk_dump, version='1'):
    films_id = set([i.schedule_id.film_id_id for i in schedule])
    
    film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__in=films_id, type=2, status=1)
    #film_names = {i.film_id_id: i for i in film_name} # python 2.7+
    film_names = {}
    for i in film_name:
        film_names[i.film_id_id] = i
    
    film_ramb = FilmsRamb.objects.using('afisha').filter(id_film__in=films_id, id_source=1)
    #film_rambs = {i.id_film_id: i for i in film_ramb} # python 2.7+
    film_rambs = {}
    for i in film_ramb:
        film_rambs[i.id_film_id] = i
    
    movies_id = set([i.schedule_id.movie_id_id for i in schedule])
    cinema = ImportCinema.objects.using('afisha').filter(cinema_id__in=movies_id, script_id=100)
    #cinemas = {str(i.cinema_id): i for i in cinema} # python 2.7+
    cinemas = {}
    for i in cinema:
        cinemas[str(i.cinema_id)] = i

    city_id_old = ''
    movie_id_old = ''
    hall_id_old = ''
    schedule_id_old = ''

    text = ''
    
    # statistics
    statistics = {}
    sessions_count = schedule.count()
    sessions_count_real = 0
    sessions_sale = []
    

    doubles = []
    for i in schedule:
        unique = '%s%s%s' % (i.session_list_id.time, i.schedule_id.movie_id_id, i.schedule_id.film_id_id)
        if unique not in doubles:
            doubles.append(unique)

            def schedule_ext(text):
                text += '<hall id="%s" name="%s"><film id="%s" name="%s" idimdb="%s" rambler_id="%s"><date start="%s" finish="%s">' % (hall_id, clear_quotes(hall_name), i.schedule_id.film_id_id, clear_quotes(film_name), clear_quotes(i.schedule_id.film_id.idalldvd), ramb_id, clear_quotes(i.schedule_id.date_from), clear_quotes(i.schedule_id.date_to))
                return text

            film = film_names.get(i.schedule_id.film_id_id)
            if film:
                film_name = film.name.encode('utf-8')
            else:
                try:
                    film_name = FilmsName.objects.using('afisha').get(film_id=i.schedule_id.film_id_id, type=1, status=1)
                    film_name = film_name.name.encode('utf-8')
                except:
                    film_name = None
            
            
            city_id = str(i.schedule_id.movie_id.city_id)
            city_name = clear_quotes(i.schedule_id.movie_id.city.name)
            movie_id = str(i.schedule_id.movie_id_id)
            movie_name = clear_quotes(i.schedule_id.movie_id.name)
            hall_id = str(i.schedule_id.hall_id.id_name_id)
            hall_name = 'без указания зала' if int(i.schedule_id.hall_id.id_name_id) == 999 else i.schedule_id.hall_id.id_name.name
            schedule_id = i.schedule_id_id
            ramb_id = film_rambs.get(i.schedule_id.film_id_id)

            # statistics
            if sessions_count > settings.API_CLIENT_LIMIT:
                d_to = i.schedule_id.date_to
                d_to = datetime.date(d_to.year, d_to.month, d_to.day)
                d_from = i.schedule_id.date_from
                d_from = datetime.date(d_from.year, d_from.month, d_from.day)
                
                delta = d_to - d_from
                for day in range(delta.days + 1):
                    sessions_count_real += 1
                    
                stat_autor = statistics.get(i.schedule_id.autor)
                if stat_autor:
                    statistics[i.schedule_id.autor].append(i)
                else:
                    statistics[i.schedule_id.autor] = [i]
            
            showtime = str(i.session_list_id.time).split(':')
            showtime = '%s:%s' % (showtime[0], showtime[1])

            if ramb_id:
                ramb_id = ramb_id.id_out
            if movie_id_old != movie_id:
                movie_ramb = cinemas.get(movie_id)
                if movie_ramb:
                    movie_ramb = movie_ramb.text_ord.encode('utf-8')
                if schedule_id_old != schedule_id:
                    if schedule_id_old: text += '</date></film></hall>'
                if movie_id_old:
                    text += '</movie>'
                if city_id_old != city_id:
                    if city_id_old:
                        text += '</city>'
                    text += '<city id="%s" name="%s">' % (city_id, city_name)
                    text += '<movie id="%s" name="%s" rambler_id="%s">' % (movie_id, movie_name, movie_ramb)
                    if schedule_id_old != schedule_id:
                        text = schedule_ext(text)
                    text += '<time>%s</time>' % showtime
                else:
                    text += '<movie id="%s" name="%s" rambler_id="%s">' % (movie_id, movie_name, movie_ramb)
                    if schedule_id_old != schedule_id:
                        text = schedule_ext(text)
                    text += '<time>%s</time>' % showtime
                city_id_old = city_id
                movie_id_old = movie_id
                hall_id_old = hall_id
            else:
                if hall_id_old == hall_id:
                    if schedule_id_old != schedule_id:
                        if schedule_id_old:
                            text += '</date></film></hall>'
                        text = schedule_ext(text)
                else:
                    if schedule_id_old:
                        text += '</date></film></hall>'
                    text = schedule_ext(text)
                    
                text += '<time>%s</time>' % showtime
                hall_id_old = hall_id
                movie_id_old = movie_id
            schedule_id_old = schedule_id
        
    
    text = xml_wrapper('%s</date></film></hall></movie></city>' % text) if text else xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, from_encoding="utf-8")
        if version != '2':
            for i in data.findAll('city'):
                j_data = {
                    "city_id": int(i['id']),
                    "city_name": i['name'],
                    "movies": [],
                }
                for m in i.findAll('movie'):
                    movie_rambler_id = int(m['rambler_id']) if m['rambler_id'] != 'None' else None
                    j_data_movie = {
                        "id": int(m['id']),
                        "name": m['name'],
                        "rambler_id": movie_rambler_id,
                        "halls": [],
                    }
                    for h in m.findAll('hall'):
                        film_rambler_id = int(h.film['rambler_id']) if h.film['rambler_id'] != 'None' else None
                        imdb = int(h.film['idimdb']) if h.film['idimdb'] != 'None' else None
                        j_data_hall = {
                            "id": int(h['id']),
                            "name": h['name'],
                            "film": {
                                "id": int(h.film['id']),
                                "name": h.film['name'],
                                "imdb_id": imdb,
                                "rambler_id": film_rambler_id,
                            },
                            "date_start": h.film.date['start'],
                            "date_finish": h.film.date['finish'],
                            "time": [i.string for i in h.film.date.findAll('time')],
                        }
                        j_data_movie['halls'].append(j_data_hall)
                    j_data['movies'].append(j_data_movie)
                json_data.append(j_data)
            
        else:
            poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue__in=films_id)
            posters = {}
            for p in poster_obj:
                if posters.get(p.objpkvalue):
                    posters[p.objpkvalue].append(p)
                else:
                    posters[p.objpkvalue] = [p]

            j_films = {}
            j_schedule = {}
            for i in data.findAll('city'):
                j_city_id = int(i['id'])
                for m in data.findAll('movie'):
                    j_cinema_id = int(m['id'])
                    for h in m.findAll('hall'):
                        j_hall_id = int(h['id'])
                        j_film_id = int(h.film['id'])
                        
                        start_y, start_m, start_d = h.film.date['start'].split('-')
                        finish_y, finish_m, finish_d = h.film.date['finish'].split('-')
                        start = datetime.date(int(start_y), int(start_m), int(start_d))
                        finish = datetime.date(int(finish_y), int(finish_m), int(finish_d))
                        
                        j_cinemahall_id = '%s%s%s' % (j_cinema_id, j_hall_id, j_film_id)

                        showtimes = []                    
                        
                        delta = finish - start
                        for day in range(delta.days + 1):
                            d = start + datetime.timedelta(days=day)
                            for t in h.film.date.findAll('time'):
                                hours, minutes = t.string.split(':')
                                dtime = datetime.datetime(d.year, d.month, d.day, int(hours), int(minutes))
                                showtimes.append({'date': dtime.strftime("%Y-%m-%d %H:%M")})
                        
                        if j_schedule.get(j_cinemahall_id):
                            for show in showtimes:
                                j_schedule[j_cinemahall_id]['sessions'].append(show)
                        else:
                            j_schedule[j_cinemahall_id] = {
                                'city_id': j_city_id,
                                'cinema_id': j_cinema_id,
                                'hall_id': j_hall_id,
                                'sessions': showtimes,
                            }

                        if j_films.get(j_film_id):
                            j_films[j_film_id]["schedules"][j_cinemahall_id] = j_schedule[j_cinemahall_id]
                        else:
                            poster_path = None
                            poster = posters.get(j_film_id)
                            if poster:                                 
                                poster_path = film_poster2(poster, 'big')
                        
                            film_rambler_id = int(h.film['rambler_id']) if h.film['rambler_id'] != 'None' else None
                            imdb = int(h.film['idimdb']) if h.film['idimdb'] != 'None' else None
                            j_film_release = film_names.get(j_film_id).film_id.date
                            if j_film_release:
                                j_film_release = str(j_film_release).replace(' 00:00:00', '')
                            else:
                                j_film_release = None
                                
                            j_films[j_film_id] = {
                                'id': int(j_film_id),
                                'imdb_id': imdb,
                                'rambler_id': film_rambler_id, 
                                'name': h.film['name'], 
                                'poster': poster_path,
                                'release': j_film_release,
                                "schedules": {j_cinemahall_id: j_schedule[j_cinemahall_id]},
                            }
            
            for f in j_films.values():
                f['schedules'] = f['schedules'].values()
                json_data.append(f)
                    
    # statistics
    if sessions_count > settings.API_CLIENT_LIMIT:
        datef = get_formated_date('%Y-%m-%d')
        
        sess_ids = list(AfishaSession.objects.using('afisha').filter(Q(schedule_id__date_from__gte=datef) | Q(schedule_id__date_from__lt=datef) & Q(schedule_id__date_to__gte=datef)).values_list('id', flat=True))
        
        filter = {'kid__in': sess_ids, 'schedule__sale': True}
        
        sessions_sale = SessionsAfishaRelations.objects.select_related('schedule', 'schedule__cinema', 'schedule__cinema__cinema').filter(**filter)
        
        cinemas_sale = len(set([i.schedule.cinema_id for i in sessions_sale]))
        sessions_sale = sessions_sale.count()

        cinemas_count = []
        films_count = []
        for k, v in statistics.iteritems():
            for i in v:
                cinemas_count.append(i.schedule_id.movie_id_id)
                films_count.append(i.schedule_id.film_id_id)
        
        stat_obj = Statistics.objects.create(
            name = 'schedule',
            sessions = sessions_count_real,
            sessions_sale = sessions_sale,
            cinemas = len(set(cinemas_count)),
            cinemas_sale = cinemas_sale,
            films = len(set(films_count)),
        )

        for k, v in statistics.iteritems():
            stat_details_obj = StatisticsDetails.objects.create(
                source = k,
                cinemas = 0,
                cinemas_sale = 0,
                films = 0,
                sessions = len(v),
                sessions_sale = 0,
            )
            stat_obj.details.add(stat_details_obj)
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        # возвращаю данные
        return text

    
def content_cinema(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию о кинотеатрах
    """
    result = query_cinema(limits)
    return get_cinema(result, response_format, mk_dump)
    
def query_cinema(limits):
    result = Movie.objects.using('afisha').select_related('city', 'metro', 'set_field').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_cinema(request):
    runtime = time.time()
    result_xml, result_json = content_cinema(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'cinema')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'cinema', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
    
def get_cinema(movie, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in movie:
        seti = clear_quotes(i.set_field.name) if int(i.set_field_id) != 0 else ''
        try:
            metro = (i.metro.id, i.metro.name)
        except AttributeError:
            metro = ('', '')

        # открвыаю тег кинотеатр и заполняю данными
        text += '<cinema id="%d" name="%s" set="%s">' % (i.id, clear_quotes(i.name), seti)
        text += '<zip value="%s"></zip>' % clear_quotes(i.ind)
        text += '<address value="%s"></address>' % clear_quotes(i.address)
        text += '<phones value="%s"></phones>' % clear_quotes(i.phones.encode('utf-8'))
        text += '<techinfo value="%s"></techinfo>' % clear_quotes(i.techinfo.encode('utf-8'))
        text += '<site value="%s"></site>' % clear_links(i.site.encode('utf-8'))
        text += '<comment value="%s"></comment>' % clear_quotes(i.comment.encode('utf-8'))
        text += '<city id="%d" name="%s"></city>' % (i.city.id, clear_quotes(i.city.name))
        text += '<metro id="%s" name="%s"></metro>' % (metro[0], metro[1].encode('utf-8'))
        text += '<coordinates id="http://ru.wikipedia.org/wiki/%s"></coordinates>' % clear_quotes(i.city.name)
        text += '<yandex_map longitude="%s" latitude="%s"></yandex_map></cinema>' % (i.longitude, i.latitude)
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('cinema'):
            lon = i.yandex_map['longitude'] if i.yandex_map['longitude'] != 'None' else None
            lat = i.yandex_map['latitude'] if i.yandex_map['latitude'] != 'None' else None

            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
                "set": i['set'],
                "zip": i.zip['value'],
                "address": i.address['value'],
                "phones": i.phones['value'],
                "techinfo": i.techinfo['value'],
                "site": i.site['value'],
                "comment": i.comment['value'],
                "city_id": int(i.city['id']),
                "city_name": i.city['name'],
                "metro_id": int(i.metro['id']) if i.metro['id'] else '',
                "metro_name": i.metro['name'],
                "coordinates": i.coordinates['id'],
                "yandex_map": {
                    "longitude": lon,
                    "latitude": lat
                }
            })
            
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text
    


def content_all_films(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию о ВСЕХ фильмах
    """
    result = query_all_films(limits)
    return get_all_films(result, limits, response_format, mk_dump)


def query_all_films(limits):
    result = FilmsName.objects.using('afisha').filter(type__in=(1,2), status=1).values('name', 'film_id', 'film_id__year', 'type').order_by('film_id')[:limits]
    return result

@only_superuser
@never_cache
def dump_all_films(request):
    runtime = time.time()
    res = query_all_films(None)
    result_xml, result_json = get_all_films(res, None, None, True)
    result = save_dump(result_xml, runtime, request, 'allfilms')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False), runtime, request, 'allfilms', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_all_films(film, limits, response_format, mk_dump):

    data = {}
    for i in film:
        ntype = 'orig' if i['type'] == 1 else 'name'
        
        if not data.get(i['film_id']):
            data[i['film_id']] = {'orig': '', 'name': '', 'year': i['film_id__year']}
        data[i['film_id']][ntype] = clear_quotes(i['name'].encode('utf-8'))

    text = ''
    # начинаю формировать xml структуру
    count = 0
    for k, v in data.iteritems():
        count += 1
        if count == 501 and mk_dump:
            time.sleep(2)
            count = 0

        text += u'<film id="%s" name="%s" orig="%s" year="%s"></film>' % (k, v['name'].decode('utf-8'), v['orig'].decode('utf-8'), v['year'])
    
    
    text = xml_wrapper(text)
    
    
    if response_format == 'json' or mk_dump:
        json_data = []
        for k, v in data.iteritems():
            text_data = {
                "id": int(k),
                "name": v['name'],
                "orig": v['orig'],
                "year": int(v['year']) if v['year'] else None,
            }

            json_data.append(text_data)

    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text





def content_film(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию о фильмах
    """
    result, version = query_film(limits, request)
    return get_film(result, limits, response_format, mk_dump, version)

def query_film(limits, request):
    id = None
    imdb = None
    year = None
    name = None
    release = None
    version = '1'
    search = None
    person = None
    if request:
        id = request.GET.get('id')
        imdb = request.GET.get('imdb')
        year = request.GET.get('year')
        name = request.GET.get('name')

        if name:
            if u'�' in name:
                request.encoding = 'windows-1251'
                name = request.GET.get('name')
            else:
                name = del_separator(name.encode('utf-8'))
        
        release = request.GET.get('release')
        version = request.GET.get('version')
        search = request.GET.get('search')
        count = request.GET.get('count')
        person = request.GET.get('person_id')
        
    id = int_or_none(id)
    imdb = int_or_none(imdb)
    if release:
        try:
            release = datetime.datetime.strptime(release, "%d-%m-%Y").strftime("%Y-%m-%d")
        except ValueError:
            release = None
    myfilter = {}
    if id and not release and not imdb and not year and not name:
        myfilter = {'pk': id}
    elif imdb and release:
        # imdb + release
        myfilter = {'idalldvd': imdb, 'date': release}
    elif imdb and not release:
        # imdb
        myfilter = {'idalldvd': imdb}
    elif year and release and name:
        # year + release + name
        myfilter = {'year__exact': year, 'date': release, 'filmsname__name__iexact': name}
    elif year and release and not name:
        # year + release
        myfilter = {'year__exact': year, 'date': release}
    elif year and name and not release:
        # year + name
        myfilter = {'year__exact': year, 'filmsname__name__iexact': name}
    elif name and not year and not release:
        # name
        myfilter = {'filmsname__slug__iexact': name}
    elif year and not name and not release:
        # year
        myfilter = {'year__exact': year}
    elif release and not name and not year:
        # release
        myfilter = {'date': release}
    if name is None:
        myfilter['filmsname__status'] = 1
    
    if person and not id:
        pfilms = set(list(PersonsRelationFilms.objects.using('afisha').filter(person_id__id=person).values_list('film_id', flat=True)))
        myfilter['pk__in'] = pfilms

    # kinometro.ru
    if version == '3':
        releases = list(ReleasesRelations.objects.filter(rel_double=False, rel_ignore=False).values_list('film_kid', flat=True))
        myfilter['pk__in'] = releases
    
    # vkino.com.ua
    if version == '4':
        releases = list(SourceFilms.objects.filter(source_obj__url='http://vkino.com.ua/').values_list('kid', flat=True))
        myfilter['pk__in'] = set(releases)

    # version 5
    if version == '5':
        myfilter['pk'] = id

    if search:
        if len(search) >= 3:
            myfilter = {'filmsname__name__icontains': search}
        else:
            myfilter = None

    if myfilter is None:
        result = []
    else:
        if count and int(count) < limits:
            limits = count
        result = Film.objects.using('afisha').select_related('filmsname', 'personsrelationfilms').filter(**myfilter).distinct('pk')[:limits]
    return result, version


def get_year_films(year, version='1'):
    years = year.split('_')
    from_year, to_year = years if len(years) == 2 else (years[0], years[0])
    if to_year == '1990':
        myfilter = {'year__lt': to_year}
    elif from_year == str(datetime.date.today().year):
        myfilter = {'year__gte': from_year}
    elif from_year != str(datetime.date.today().year) and from_year == to_year:
        myfilter = {'year__exact': to_year}
    else:
        myfilter = {'year__gte': from_year, 'year__lte': to_year}
    myfilter['filmsname__status'] = 1
    
    # kinometro.ru
    if version == '3':
        releases = list(ReleasesRelations.objects.filter(rel_double=False, rel_ignore=False).values_list('film_kid', flat=True))
        myfilter['pk__in'] = set(releases)
        
    # vkino.com.ua
    if version == '4':
        releases = list(SourceFilms.objects.filter(source_obj__url='http://vkino.com.ua/').exclude(kid=None).values_list('kid', flat=True))
        myfilter['pk__in'] = set(releases)
        
    result = Film.objects.using('afisha').select_related('filmsname', 'personsrelationfilms').filter(**myfilter).distinct('pk')
    return result

@only_superuser
@never_cache
def dump_film(request, year):
    runtime = time.time()
    version = request.GET.get('version', '1')
    res = get_year_films(year, version)
    result_xml, result_json = get_film(res, None, None, True, version)
    result = save_dump(result_xml, runtime, request, 'film', year, 'xml', version)
    save_dump(simplejson.dumps(result_json, ensure_ascii=False), runtime, request, 'film', year, 'json', version)
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_film(film, limits, response_format, mk_dump, version='1'):
    text = ''

    films_id = [i.id for i in film]
    film_ext = FilmExtData.objects.using('afisha').filter(pk__in=films_id)
    # film_ext_data = {i.id: i for i in film_ext} # python 2.7+
    film_ext_data = {}
    for i in film_ext:
        film_ext_data[i.id] = i
    
    
    afisha_country = {}
    for i in AfishaCountry.objects.using('afisha').all():
        afisha_country[i.id] = i.name
    
    afisha_genre = {}
    for i in AfishaGenre.objects.using('afisha').all():
        afisha_genre[i.id] = i.name
    
    
    relations_films_dict = {}
    if version != '5':
        relations_films = list(PersonsRelationFilms.objects.using('afisha').filter(film_id__id__in=films_id, person_id__afishapersonsname__flag=1).values('film_id', 'person_id', 'person_id__afishapersonsname__name', 'type_act_id', 'status_act_id', 'person_id__imdb'))
        
        for i in relations_films:
            p_tmp = {'id': i['person_id'], 'name': i['person_id__afishapersonsname__name'], 'type': i['type_act_id'], 'status': i['status_act_id'], 'imdb': i['person_id__imdb']}
            if relations_films_dict.get(i['film_id']):
                relations_films_dict[i['film_id']].append(p_tmp)
            else:
                relations_films_dict[i['film_id']] = [p_tmp]

    fnames = FilmsName.objects.using('afisha').filter(film_id__id__in=films_id, status=1, type__in=(1, 2))
    fnames_dict = {}
    for i in fnames:
        if fnames_dict.get(i.film_id_id):
            fnames_dict[i.film_id_id].append({'type': i.type, 'name': i.name})
        else:
            fnames_dict[i.film_id_id] = [{'type': i.type, 'name': i.name}]
    
    if version in ('2', '3', '4', '5'):
        poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue__in=films_id)
        posters = {}
        for p in poster_obj:
            if posters.get(p.objpkvalue):
                posters[p.objpkvalue].append(p)
            else:
                posters[p.objpkvalue] = [p]
    
    reviews_dict = {}
    if version == '2':
        reviews = AfishaNews.objects.using('afisha').select_related('obj', 'user').filter(type=2, object_type=1, obj__id__in=films_id)
        for i in reviews:
            if reviews_dict.get(i.obj_id):
                reviews_dict[i.obj_id] += 1
            else:
                reviews_dict[i.obj_id] = 1
    
    
    if version in ('2', '3', '4', '5'):
        if version == '3':
            releases = ReleasesRelations.objects.select_related('release').filter(film_kid__in=films_id, rel_double=False, rel_ignore=False)
            releases_dict = {}
            for i in releases:
                releases_dict[i.film_kid] = i.release.film_id
        elif version == '4':
            releases = SourceFilms.objects.filter(source_obj__url='http://vkino.com.ua/', kid__in=films_id)
            releases_dict = {}
            for i in releases:
                try:
                    releases_dict[i.kid] = int(i.source_id)
                except UnicodeEncodeError: 
                    releases_dict[i.kid] = 0

        #
        trailers_rel = Objxres.objects.using('afisha').filter(objtypeid=3, objpkvalue__in=films_id)
        trailers_ids = []
        trailer_rel_list = {}
        for i in trailers_rel:
            trailers_ids.append(i.extresid_id)
            
            if trailer_rel_list.get(i.objpkvalue):
                trailer_rel_list[i.objpkvalue].append(i.extresid_id)
            else:
                trailer_rel_list[i.objpkvalue] = [i.extresid_id,]
                
        trailers = TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=trailers_ids)
        
        trailers_list = {}
        for i in trailers:
            trailers_list[i.trailer_id] = i
            

    # начинаю формировать xml структуру
    count = 0
    for i in film:
        count += 1
        if count == 501 and mk_dump:
            time.sleep(2)
            count = 0

        desc = clear_quotes(BeautifulSoup(i.description, from_encoding='utf-8').text.strip().encode('utf-8')) if i.description else ''
        comment = clear_quotes(BeautifulSoup(i.comment, from_encoding='utf-8').text.strip().encode('utf-8')) if i.comment else ''
        
        idimdb = int(i.idalldvd) if i.idalldvd is not None else 0
        imdb_value = str(i.imdb) if i.imdb is not None and i.imdb else 0
        runtime = str(i.runtime) if i.runtime else 0
        release_date = str(i.date) if i.date else ''

        genre1_name, genre1_id = (afisha_genre[i.genre1_id], i.genre1_id) if i.genre1_id else (None, None)
        genre2_name, genre2_id = (afisha_genre[i.genre2_id], i.genre2_id) if i.genre2_id else (None, None)
        genre3_name, genre3_id = (afisha_genre[i.genre3_id], i.genre3_id) if i.genre3_id else (None, None)
        
        country1_name, country1_id = (afisha_country[i.country_id], i.country_id) if i.country_id else (None, None)
        country2_name, country2_id = (afisha_country[i.country2_id], i.country2_id) if i.country2_id else (None, None)
        
        limit = age_limits(i.limits)
        
        name_ru = ''
        name_orig = ''
        
        for n in fnames_dict.get(i.id, []):
            if n['type'] == 2:
                name_ru = clear_quotes(n['name'].encode('utf-8'))
            elif n['type'] == 1:
                name_orig = clear_quotes(n['name'].encode('utf-8'))
        
        if version == '5':
            text += u'<film id="%d">' % i.id
            text += u'<rus name="%s"></rus>' % name_ru.decode('utf-8')
            text += u'<eng name="%s"></eng>' % name_orig.decode('utf-8')
            text += u'<year value="%s"></year>' % str(i.year).decode('utf-8')
            text += u'<limits value="%s"></limits>' % limit
        else:
            text += u'<film id="%d" idimdb="%s" name="%s" original="%s">' % (i.id, idimdb, name_ru.decode('utf-8'), name_orig.decode('utf-8'))
            text += u'<year value="%s"></year>' % str(i.year).decode('utf-8')
            text += u'<persons>'
            
            for p in relations_films_dict.get(i.id, []):
                if p:
                    text += u'<person id="%s" name="%s" type="%s" status="%s" imdb="%s"></person>' % (p['id'], p['name'], p['type'], p['status'], p['imdb'])  
            
            text += u'</persons>'
            
            text += u'<runtime value="%s"></runtime>' % runtime
            
        text += u'<genres>'
        if genre1_id: 
            text += u'<genre id="%s" name="%s"></genre>' % (genre1_id, genre1_name)
            
        if genre2_id: 
            text += u'<genre id="%s" name="%s"></genre>' % (genre2_id, genre2_name)
            
        if genre3_id: 
            text += u'<genre id="%s" name="%s"></genre>' % (genre3_id, genre3_name)
            
                
        text += u'</genres>'
        
        if version != '5':
            text += u'<countries>'

            if country1_id: 
                text += u'<country id="%s" name="%s"></country>' % (country1_id, country1_name)
            if country2_id: 
                text += u'<country id="%s" name="%s"></country>' % (country2_id, country2_name)
            text += u'</countries>'
        
        f_ext = film_ext_data.get(i.id)
        frate = f_ext.rate
        fvnum = f_ext.vnum
        
        if version in ('3', '4', '5'):
            if version == '3':
                kinometro = releases_dict.get(i.id)
                text += u'<kinometro id="%s"></kinometro>' % kinometro
            elif version == '4':
                vkino = releases_dict.get(i.id)
                text += u'<vkino id="%s"></vkino>' % vkino
            
            release_date = release_date.replace(' 00:00:00', '')
            
            poster_path = ''
            poster = posters.get(i.id)
            if poster:
                poster_size = 'small' if version == '5' else 'big'
                poster_path = film_poster2(poster, poster_size)
                
            text += u'<poster value="%s"></poster>' % poster_path
            
            if version != '5':
                text += u'<trailers>'
                trl = trailer_rel_list.get(i.id, [])
                for t in trl:
                    trailer = trailers_list.get(t)
                    if trailer:
                        
                        soup = BeautifulSoup(trailer.code).encode(formatter=None)
                        soup = str(soup).replace('<html><head></head><body>','').replace('</body></html>','').replace('\'"','"').replace("\"'",'"').replace("'",'"').replace('<','&lt;').replace('>','&gt;').replace('&','&amp;').replace('"','&quot;')
                        text += u'<trailer_code value="%s"></trailer_code>' % soup.decode('utf-8')
                        
                text += u'</trailers>'

        if version == '5':
            text += u'<trailers>'
        
            trl = trailer_rel_list.get(i.id, [])
            youtube_ids = {}
            for t in trl:
                trailer = trailers_list.get(t)
                if trailer:
                    code = re.findall(r'www.youtube.com/(?:v|embed)/([a-zA-Z0-9-_]+).*', trailer.code)
                    if code:
                        you_url = u'https://www.youtube.com/watch?v=%s' % code[0]
                        text += u'<url value="%s"></url>' % you_url

            text += u'</trailers>'
            
            text += u'<description value="%s"></description>' % desc.decode('utf-8')
            text += u'<ratings>'
            text += u'<rating source="kinoafisha" rate="%s" votes="%s"></rating>' % (frate, fvnum)
            text += u'<rating source="imdb" rate="%s" votes="%s"></rating>' % (imdb_value, i.imdb_votes)
            text += u'</ratings>'
            text += u'<url value="http://www.kinoafisha.ru/index.php3?status=1&amp;id1=%s"></url>' % i.id
            text += u'</film>'
        else:
            text += u'<rate value="%s"></rate>' % frate
            text += u'<votes value="%s"></votes>' % fvnum
            text += u'<imdb value="%s"></imdb><imdb_votes value="%s"></imdb_votes>' % (imdb_value, i.imdb_votes)
            text += u'<site value="%s"></site>' % clear_links(i.site.encode('utf-8'))
            
            text += u'<description value="%s"></description>' % desc.decode('utf-8')

            text += u'<limits value="%s"></limits>' % limit
            
            text += u'<comment value="%s"></comment>' % comment.decode('utf-8')
                
            text += u'<datelastupd value="%s"></datelastupd>' % clear_quotes(i.datelastupd)
            
            text += u'<date value="%s"></date></film>' % release_date

    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html5lib")
        for i in data.findAll('film'):
            if version == '5':
                text_data = {
                    "id": int(i['id']),
                    "rus": i.rus['name'],
                    "eng": i.eng['name'],
                    "year": int(i.year['value']) if i.year['value'] else None,
                    "limits": i.limits['value'],
                    "poster": i.poster['value'],
                    "url": i.url['value'],
                    'description': i.description['value'],
                    "ratings": [],
                    'genres': [],
                    'trailers': [],
                }
            else:
                try:
                    runtime = int(i.runtime['value']) if int(i.runtime['value']) else None
                except ValueError:
                    runtime = None
                text_data = {
                    "id": int(i['id']),
                    "imdb_id": int(i['idimdb']),
                    "name": i['name'],
                    "original": i['original'],
                    "year": int(i.year['value']) if i.year['value'] else None,
                    "runtime": runtime,
                    "site": i.site['value'],
                    "description": i.description['value'],
                    "comment": i.comment['value'],
                    "persons": [],
                    "genres": [],
                    "countries": [],
                    "ratings": [],
                }
                
                release = i.date['value'].replace(' 00:00:00', '')
                datelastupd = i.datelastupd.get('value', '0000-00-00 00:00:00')

            if version not in ('2', '5'):
                text_data["limits"] = i.limits['value']
                text_data["release"] = release
                text_data["datelastupd"] = datelastupd
                kinoafisha_rate = i.rate['value']
            else:
                youtube_ids = {}
                if version == '5':
                    text_data["trailers"] = [tr_url['value'] for tr_url in i.trailers.findAll('url')]
                else:
                    trl = trailer_rel_list.get(int(i['id']), [])
                    
                    for t in trl:
                        trailer = trailers_list.get(t)
                        if trailer:
                            code = re.findall(r'www.youtube.com/(?:v|embed)/([a-zA-Z0-9-_]+).*', trailer.code)
                            if code:
                                if youtube_ids.get(int(i['id'])):
                                    youtube_ids[int(i['id'])].append(code[0])
                                else:
                                    youtube_ids[int(i['id'])] = [code[0]]
                                    
                    youtube_ids = youtube_ids.values()[0] if youtube_ids else []
                
                    text_data["trailers"] = youtube_ids
                
                if version != '5':
                    text_data["limits"] = i.limits['value'].replace('+','') if i.limits['value'] else '-1'
                    
                    kinoafisha_rate = "%0.1f" % float(i.rate['value'])
                    
                    poster_path = None
                    poster = posters.get(int(i['id']))
                    if poster:                                 
                        poster_path = film_poster2(poster, 'big')
                        
                    text_data["poster"] = poster_path
                    
                    reviews_count = reviews_dict.get(int(i['id']), 0)
                    text_data["reviews"] = reviews_count

                    text_data["release"] = release
                    
                    if datelastupd != 'None':
                        upd = datelastupd
                        
                    else:
                        upd = None
                    text_data["datelastupd"] = upd
            
            if version in ('3', '4'):
                if version == '3':
                    text_data["kinometro"] = int(i.kinometro['id'])
                elif version == '4':
                    text_data["vkino"] = int(i.vkino['id'])
                    
                text_data["poster"] = i.poster['value']
                
                text_data["trailers"] = [tr['value'] for tr in i.trailers.findAll('trailer_code')]
            
                
            if version != '5':
                for j in i.findAll('person'):
                    j_person = {
                        "id": int(j['id']),
                        "name": j['name'],
                        "type": int(j['type']),
                        "imdb_id": int(j['imdb']),
                    }
                    if version != '2':
                        try:
                            jstatus = int(j['status'])
                        except UnicodeEncodeError:
                            jstatus = 0
                        j_person["status"] = jstatus
                    text_data["persons"].append(j_person)
            
            for j in i.findAll('genre'):
                if version != '2':
                    text_data["genres"].append({
                        "id": int(j['id']),
                        "name": j['name'],
                    })
                else:
                     text_data["genres"].append(j['name'])
                     
            if version == '5':
                for ra in i.ratings.findAll('rating'):
                    if ra['source'] == 'kinoafisha':
                        source_rate = "%0.1f" % float(ra['rate'])
                    else:
                        source_rate = ra['rate']
                        
                    text_data["ratings"].append({
                        "source": ra['source'],
                        "rate": source_rate,
                        "votes": int(ra['votes'])
                    })
                
            else:
                for j in i.findAll('country'):
                    if version != '2':
                        text_data["countries"].append({
                            "id": int(j['id']),
                            "name": j['name'],
                        })
                    else:
                        text_data["countries"].append(j['name'])

                text_data["ratings"].append({
                    "source": "kinoinfo",
                    "rate": kinoafisha_rate,
                    "votes": int(i.votes['value'])
                })
                
                text_data["ratings"].append({
                    "source": "imdb",
                    "rate": i.imdb['value'].replace(',','.'),
                    "votes": int(i.imdb_votes['value'])
                })

            json_data.append(text_data)

    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_persons(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает инфо. о персонах
    """
    result = query_persons(limits)
    return get_persons(result, response_format, mk_dump)
    
def query_persons(limits):
    result = AfishaPersons.objects.using('afisha').select_related('country').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_persons(request):
    runtime = time.time()
    result_xml, result_json = content_persons(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'persons')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'persons', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))


def get_persons(persons, response_format, mk_dump):
    text = ''
    
    persons_id = [i.id for i in persons]
    person1 = AfishaPersonsName.objects.using('afisha').filter(person_id__in=persons_id, flag=1)
    person2 = AfishaPersonsName.objects.using('afisha').filter(person_id__in=persons_id, flag=2)
    # name1 = {i.person_id_id: i for i in person1} # python 2.7+
    # name2 = {i.person_id_id: i for i in person2} # python 2.7+
    name1 = {}
    for i in person1:
        name1[i.person_id_id] = i
    name2 = {}
    for i in person2:
        name2[i.person_id_id] = i
   
    # начинаю формировать xml структуру
    for i in persons:
        name_ru = name1.get(i.id).name.encode('utf-8') if i.id in name1 else ''
        name_en = name2.get(i.id).name.encode('utf-8') if i.id in name2 else ''
        country_id, country_name = (int(i.country.id), i.country.name) if i.country else ('', '')
        # открываю тег персона и заполняю данными
        text += '<persons id="%d" name="%s" name_en="%s"><birth_year value="%s"></birth_year><birth_month value="%s"></birth_month><birth_day value="%s"></birth_day><male value="%s"></male><imdb id="%s"></imdb>' % (i.id, clear_quotes(name_ru), clear_quotes(name_en), clear_quotes(i.birth_year), clear_quotes(i.birth_mounth), clear_quotes(i.birth_day), clear_quotes(i.male), clear_quotes(i.imdb))
        text += '<country id="%s" name="%s"></country></persons>' % (clear_quotes(country_id), clear_quotes(country_name))
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('persons'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
                "name_en": i['name_en'],
                "birth_year": int(i.birth_year['value']),
                "birth_month": int(i.birth_month['value']),
                "birth_day": int(i.birth_day['value']),
                "male": int(i.male['value']),
                "imdb_id": int(i.imdb['id']),
                "country_id": int(i.country['id']) if i.country['id'] else '',
                "country_name": i.country['name'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_hall(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию о залах
    """
    result = query_hall(limits)
    return get_hall(result, response_format, mk_dump)
    
def query_hall(limits):
    result = AfishaHalls.objects.using('afisha').select_related('id_name', 'movie').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_hall(request):
    runtime = time.time()
    result_xml, result_json = content_hall(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'hall')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'hall', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_hall(hall, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in hall:
        movie_id = int(i.movie.id) if i.movie else None
        movie_name = i.movie.name if i.movie else None

        # открываю тег зал и заполняю данными
        text += '<hall id="%d" name="%s" id_name="%s"><places value="%s"></places><format value="%s"></format><cinema id="%s" value="%s"></cinema></hall>' % (i.id, clear_quotes(i.id_name.name), i.id_name.id, i.places, i.format, movie_id, clear_quotes(movie_name))
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('hall'):
            json_data.append({
                "id": int(i['id']),
                "name_id": int(i['id_name']),
                "name": i['name'],
                "places": int(i.places['value']),
                "format": int(i.format['value']),
                "cinema_id": int(i.cinema['id']) if i.cinema['id'] != 'None' else '',
                "cinema_name": i.cinema['value'],
            })
            
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_country_dir(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все названия стран
    """
    result = query_country_dir(limits)
    return get_country_dir(result, response_format, mk_dump)

def query_country_dir(limits):
    result = AfishaCountry.objects.using('afisha').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_country_dir(request):
    runtime = time.time()
    result_xml, result_json = content_country_dir(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'country_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'country_dir', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))

def get_country_dir(country, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in country:
        # тег страна и заполняю данными
        text += '<country id="%s" name="%s" name_en="%s"></country>' % (i.id, clear_quotes(i.name), clear_quotes(i.name_en))
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('country'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
                "name_en": i['name_en'],
            })
            
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_city_dir(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все названия городов
    """
    result = query_city_dir(limits)
    return get_city_dir(result, response_format, mk_dump)
    
def query_city_dir(limits):
    result = AfishaCity.objects.using('afisha').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_city_dir(request):
    runtime = time.time()
    result_xml, result_json = content_city_dir(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'city_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'city_dir', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_city_dir(city, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in city:
        # тег город и заполняю данными
        text += '<city id="%s" name="%s"></city>' % (i.id, clear_quotes(i.name))
            
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('city'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
            })
            
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text

  
def content_hall_dir(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все названия залов
    """
    result = query_hall_dir(limits)
    return get_hall_dir(result, response_format, mk_dump)
    
def query_hall_dir(limits):
    result = AfishaHall.objects.using('afisha').all().order_by('pk')[:limits]
    return result

@only_superuser
@never_cache
def dump_hall_dir(request):
    runtime = time.time()
    result_xml, result_json = content_hall_dir(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'hall_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'hall_dir', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))

def get_hall_dir(hall, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in hall:
        # тег зал и заполняю данными
        text += '<hall id="%s" name="%s"></hall>' % (i.id, clear_quotes(i.name))
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('hall'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text
        

def content_genre_dir(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все названия жанров фильмов
    """
    result = query_genre_dir(limits)
    return get_genre_dir(result, response_format, mk_dump)
    
def query_genre_dir(limits):
    result = AfishaGenre.objects.using('afisha').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_genre_dir(request):
    runtime = time.time()
    result_xml, result_json = content_genre_dir(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'genre_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'genre_dir', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    

def get_genre_dir(genre, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in genre:
        # тег жанр и заполняю данными
        text += '<genre id="%s" name="%s" name_en="%s"></genre>' % (i.id, clear_quotes(i.name), clear_quotes(i.name_en))
    
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('genre'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
                "name_en": i['name_en'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_metro_dir(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает все названия станций метро
    """
    result = query_metro_dir(limits)
    return get_metro_dir(result, response_format, mk_dump)
    
def query_metro_dir(limits):
    result = AfishaMetro.objects.using('afisha').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_metro_dir(request):
    runtime = time.time()
    result_xml, result_json = content_metro_dir(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'metro_dir')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'metro_dir', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
    
def get_metro_dir(metro, response_format, mk_dump):
    text = ''
    # начинаю формировать xml структуру
    for i in metro:
        # тег метро и заполняю данными
        text += '<metro id="%s" name="%s"></metro>' % (i.id, clear_quotes(i.name))
            
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('metro'):
            json_data.append({
                "id": int(i['id']),
                "name": i['name'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_theater(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию о кинотеатрах
    """
    result = query_theater(limits)
    return get_theater(result, response_format, mk_dump)
    
def query_theater(limits):
    result = Movie.objects.using('afisha').select_related('city').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_theater(request):
    runtime = time.time()
    result_xml, result_json = content_theater(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'theater')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'theater', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_theater(movie, response_format, mk_dump):
    text = '<?xml version="1.0" encoding="UTF-8"?><houses>'
    # все xml данные буду записывать в 'text'
    # начинаю формировать xml структуру
    for i in movie:
        info = i.techinfo.encode('utf-8')
        # Извлекаю кол-во залов в кинотеатре
        screens_temp = re.findall('(\d+ залов|\d+ зала|\d+ зал)', info)
        lon = i.longitude if i.longitude else ''
        lat = i.latitude if i.latitude else ''
        if screens_temp:
            screens = re.findall('\d+', screens_temp[0])
        else:
            screens_temp = re.findall('Четырехзальный', info)
            if screens_temp:
                screens = 4
            else:
                screens_temp = re.findall('Зрительный зал', info)
                screens = 1 if screens_temp else None
        if screens:
            screens = str(screens).replace("['", "").replace("']", "")
        # Извлекаю кол-во мест в зале
        seating_temp = re.findall('(\d+?[\+\d+]+ места,|\d+?[\+\d+]+ место,)', info)
        if seating_temp:
            seating = re.findall('\d+', seating_temp[0])
        else:
            seating_temp = re.findall('посадочных мест- 800', info)
            if seating_temp:
                seating = 800
                screens = 1
            else:
                seating_temp = re.findall('(\d+?[\+\d+]+|\d+?[\+\d+]+?\(3D\)|\d+?[\+\d+]+ посадочных) мест', info)
                seating = re.findall('\d+', seating_temp[0]) if seating_temp else None
        if seating:
            seating = str(seating).replace("['", "").replace("']", "").replace("'", "")
        # Извлекаю звук зала
        sound_temp = re.findall('звук: [\w+\ ]+', info)
        sound = sound_temp[0].replace('звук:','').strip() if sound_temp else None
        if seating:
            try:
                seating = int(seating)
                screens = 1
            except ValueError: pass        
        afisha_link = clear_quotes('http://www.kinoafisha.ru/index.php3?status=2&id2=%d' % (i.id))
        
        text += '<theater><theater_name>%s</theater_name><theater_id>%d</theater_id><theater_address>%s</theater_address><theater_city>%s</theater_city><theater_state>RU</theater_state><theater_zip>%s</theater_zip><theater_phone>%s</theater_phone><theater_attributes></theater_attributes><theater_county>RUS</theater_county><theater_ticketing>%s</theater_ticketing><theater_url>%s</theater_url><theater_closed_reason></theater_closed_reason><theater_location></theater_location><theater_market></theater_market><theater_screens>%s</theater_screens><theater_seating>%s</theater_seating><theater_adult></theater_adult><theater_child></theater_child><theater_senior></theater_senior><theater_sound>%s</theater_sound><theater_lat>%s</theater_lat><theater_lon>%s</theater_lon></theater>' % (clear_quotes(i.name), i.id, clear_quotes(i.address), clear_quotes(i.city.name), clear_quotes(i.ind.encode('utf-8')), clear_quotes(i.phones.encode('utf-8')), afisha_link, clear_links(i.site.encode('utf-8')), screens, seating, sound, lat, lon)
    
    
    text += '</houses>'
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('theater'):
            json_data.append({
                "theater_id": int(i.theater_id.string),
                "theater_name": i.theater_name.string,
                "theater_address": i.theater_address.string,
                "theater_city": i.theater_city.string,
                "theater_state": i.theater_state.string,
                "theater_zip": i.theater_zip.string,
                "theater_phone": i.theater_phone.string,
                "theater_attributes": "",
                "theater_county": i.theater_county.string,
                "theater_ticketing": i.theater_ticketing.string,
                "theater_url": i.theater_url.string,
                "theater_closed_reason": "",
                "theater_location": "",
                "theater_market": "",
                "theater_screens": int(i.theater_screens.string) if i.theater_screens.string != 'None' else None,
                "theater_seating": i.theater_seating.string,
                "theater_adult": "",
                "theater_child": "",
                "theater_senior": "",
                "theater_sound": i.theater_sound.string if i.theater_sound.string else '',
                "theater_lat": i.theater_lat.string if i.theater_lat.string else None,
                "theater_lon": i.theater_lon.string if i.theater_lon.string else None,
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text



def content_screens(limits, request, response_format, ver=1, mk_dump=False):
    """
    Метод возвращает информацию о сеансах
    """
    result = query_screens(limits)
    return get_screens(result, ver, response_format, mk_dump)

def query_screens(limits):
    date_from = get_formated_date('%Y-%m-%d')
    films = get_daniya_films()
    result = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__film_id').filter(schedule_id__date_to__gte=date_from, schedule_id__film_id__id__in=films).order_by('schedule_id__movie_id', 'schedule_id__date_from')[:limits]
    return result

@only_superuser
@never_cache
def dump_screens(request, ver=1):
    runtime = time.time()
    result_xml, result_json = content_screens(None, request, None, ver, True)
    dump_name = 'screens_v2' if ver == 2 else 'screens'
    result = save_dump(result_xml, runtime, request, dump_name)
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, dump_name, '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))

def get_screens(schedule, ver, response_format, mk_dump):
    import calendar
    from datetime import timedelta

    today = datetime.datetime.now().date()
    sess_dict = {}
    
    if ver == 2:
        afisha_sess_id = [i.id for i in schedule]
        sources = ('http://www.rambler.ru/', 'http://kinohod.ru/')
        sess = SessionsAfishaRelations.objects.select_related('source', 'schedule', 'schedule__cinema').filter(source__url__in=sources, kid__in=afisha_sess_id)
        for i in sess:
            if sess_dict.get(i.kid):
                sess_dict[i.kid].append({'schedule': i.schedule, 'source': i.source})
            else:
                sess_dict[i.kid] = [{'schedule': i.schedule, 'source': i.source}]

    
    def time_am_pm(show_time):
        time_d = clear_quotes(i.session_list_id.time).split(':')
        hour = int(time_d[0])
        if (hour == 12 and int(time_d[1]) == 0) or hour < 12:
            xM = 'AM'
        elif (hour == 12 and int(time_d[1]) > 0) or hour > 12:
            hour = hour - 12
            xM = 'PM'
        return '%s:%s %s' % (hour, time_d[1], xM)
    
    def screens_ext(i, mytime):
        date_start = str(i.schedule_id.date_from).split('-')
        date_finish = str(i.schedule_id.date_to).split('-')
        currentdate = datetime.date(int(date_start[0]), int(date_start[1]), int(date_start[2]))
        enddate = datetime.date(int(date_finish[0]), int(date_finish[1]), int(date_finish[2]))
        t = ''
        while currentdate <= enddate:
            t += '<show_date date="%s">' % str(currentdate).replace('-','')
            if ver == 1:
                t += '<showtimes>%s</showtimes>' % mytime
            else:
                for k, v in mytime.iteritems():
                    s = sess_dict.get(v['id'], {})
                    kinohod_data = ''
                    rambler_data = ''
                    rambler_cine = ''
                    for j in s:
                        if j['schedule'].dtime.date() == currentdate:
                            if j['source'].url == 'http://kinohod.ru/':
                                kinohod_data = j['schedule'].source_id.encode('utf-8')
                            elif j['source'].url == 'http://www.rambler.ru/':
                                rambler_data = j['schedule'].source_id.encode('utf-8')
                                rambler_cine = j['schedule'].cinema.source_id.encode('utf-8')
                    t += '<showtimes kinohod="%s" rambler="%s" rambler_theater="%s">%s</showtimes>' % (kinohod_data, rambler_data, rambler_cine, k)
            t += '<show_attributes></show_attributes>\
                <show_passes></show_passes><show_festival></show_festival>\
                <show_with></show_with><show_sound></show_sound>\
                <show_comments></show_comments></show_date>'
            currentdate += datetime.timedelta(days=1)
        return t
        
    films = get_daniya_films()
    film_name = FilmsName.objects.using('afisha').filter(film_id__id__in=films, type=2, status=1) 
    # film_names = {i.film_id_id: i for i in film_name} # python 2.7+
    film_names = {}
    for i in film_name:
        film_names[i.film_id_id] = i

    # все xml данные буду записывать в 'text'
    text = '<?xml version="1.0" encoding="UTF-8"?><times>'
    theater_id_old = ''
    schedule_id_old = ''
    schedule_old = ''
    
    mytime = '' if ver == 1 else {}
    show_date = ''
    for i in schedule:
        theater_id = clear_quotes(i.schedule_id.movie_id_id)
        film = film_names.get(i.schedule_id.film_id_id)
        schedule_id = i.schedule_id_id
        if schedule_id_old != schedule_id:
            if schedule_id_old:
                text += '%s</showtime>' % screens_ext(schedule_old, mytime)
                mytime = '' if ver == 1 else {}
            text += '<showtime><movie_name>%s</movie_name><movie_id>%s</movie_id><theater_id>%s</theater_id>' % (clear_quotes(film.name.encode('utf-8')), clear_quotes(i.schedule_id.film_id.idalldvd), theater_id)
            if ver == 1:
                mytime += time_am_pm(i.session_list_id.time)
            else:
                mytime[time_am_pm(i.session_list_id.time)] = {'time': i.session_list_id.time, 'id': i.id}
            show_date = i
        else:
            if ver == 1:
                mytime += ', '
                mytime += time_am_pm(i.session_list_id.time)
            else:
                mytime[time_am_pm(i.session_list_id.time)] = {'time': i.session_list_id.time, 'id': i.id}
            show_date = i
        schedule_id_old = schedule_id
        schedule_old = i
        
    if show_date:
        text += '%s</showtime></times>' % screens_ext(show_date, mytime)
    else:
         text += '</times>'

    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, from_encoding="utf-8")
        for i in data.findAll('showtime'):
            j_data = {
                "movie_name": i.movie_name.string,
                "movie_id": int(i.movie_id.string),
                "theater_id": int(i.theater_id.string),
                "show_dates": [],
                
            }
            for j in i.findAll('show_date'):
                jd = {
                    "date": int(j['date']),
                    "showtimes": [],
                    "show_attributes": "",
                    "show_passes": "",
                    "show_festival": "",
                    "show_with": "",
                    "show_sound": "",
                    "show_comments": "",
                }
                if ver == 1:
                    jd['showtimes'] = [t for t in j.showtimes.string.split(', ')]
                else:
                    for s in j.findAll('showtimes'):
                        jd['showtimes'].append({
                            'time': s.string, 
                            'kinohod': int(s['kinohod']) if s['kinohod'] else '',
                            'rambler': int(s['rambler']) if s['rambler'] else '',
                            'rambler_theater': int(s['rambler_theater']) if s['rambler_theater'] else '',
                        })
                    
                j_data['show_dates'].append(jd)
            json_data.append(j_data)


    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_imovie(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию об указанных фильмах
    """
    result = query_imovie(limits)
    return get_imovie(result, response_format, mk_dump)
    
def query_imovie(limits):
    films = get_daniya_films()
    result = FilmsName.objects.using('afisha').select_related('film_id').filter(type=2, status=1, film_id__in=films)[:limits]
    return result

@only_superuser
@never_cache
def dump_imovie(request):
    runtime = time.time()
    result_xml, result_json = content_imovie(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'imovie')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'imovie', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))

def get_imovie(film, response_format, mk_dump):
    # все xml данные буду записывать в 'text', добавил в 'text' xml заголовок
    text = '<?xml version="1.0" encoding="UTF-8"?><movies>'
    # начинаю формировать xml структуру
    for i in film:
        film_date = i.film_id.date.strftime("%B %d, %Y") if i.film_id.date else None
        imdb = int(i.film_id.idalldvd) if i.film_id.idalldvd else ''
        text += '<movie><title>%s</title><movie_id>%s</movie_id><release_date id="1" notes="Nationwide">%s</release_date><synopsis><P>%s</P></synopsis></movie>' % (clear_quotes(i.name.encode('utf-8')), imdb, film_date, clear_quotes(i.film_id.description.encode('utf-8')))
            
    text += '</movies>'

    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('movie'):
            release = i.release_date.string if i.release_date.string != 'None' else ''
            json_data.append({
                "movie_id": int(i.movie_id.string),
                "title": i.title.string,
                "release": {"id": 1, "notes": "Nationwide", "date": release},
                "synopsis": i.synopsis.p.string,
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text



def content_films_name(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию об указанных фильмах
    """
    result = query_films_name(limits)
    return get_films_name(result, response_format, mk_dump)
    
def query_films_name(limits):
    result = FilmsName.objects.using('afisha').select_related('film_id').all()[:limits]
    return result

@only_superuser
@never_cache
def dump_films_name(request):
    runtime = time.time()
    result_xml, result_json = content_films_name(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'films_name')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'films_name', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_films_name(films, response_format, mk_dump):
    # все xml данные буду записывать в 'text'
    text = '<?xml version="1.0" encoding="UTF-8"?><films_name>'
    # начинаю формировать xml структуру
    for i in films:
        imdb = int(i.film_id.idalldvd) if i.film_id.idalldvd else ''
        text += '<id id_film="%d" imdb="%s"><name id="%d" value="%s"></name><type value="%s"></type><status value="%s"></status><slug value="%s"></slug></id>' % (i.film_id.id, imdb, i.id, clear_quotes(i.name.encode('utf-8')), i.type, i.status, clear_quotes(i.slug.encode('utf-8')))
    
    text += '</films_name>'
    
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('id'):
            name_tag = i.find('name')
            json_data.append({
                "id": int(i['id_film']),
                "imdb_id": int(i['imdb']) if i['imdb'] else '',
                "name": name_tag['value'],
                "name_id": int(name_tag['id']),
                "type": int(i.type['value']),
                "status": int(i.status['value']),
                "slug": i.slug['value'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_imdb_rate(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию об указанных фильмах
    """
    result = query_imdb_rate(limits, request)
    return get_imdb_rate(result, response_format, mk_dump)
    
def query_imdb_rate(limits, request):
    imdb = None
    if request:
        imdb = int_or_none(request.GET.get('imdb'))
    myfilter = {}
    if imdb:
        myfilter = {'idalldvd': imdb}
    result = Film.objects.using('afisha').filter(**myfilter).order_by('pk')[:limits]
    return result

@only_superuser
@never_cache
def dump_imdb_rate(request):
    runtime = time.time()
    result_xml, result_json = content_imdb_rate(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'imdb_rate')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'imdb_rate', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
    
def get_imdb_rate(imdb_rate, response_format, mk_dump):
    # все xml данные буду записывать в 'text'
    text = '<?xml version="1.0" encoding="UTF-8"?><imdb_rate>'
    # начинаю формировать xml структуру
    for i in imdb_rate:
        imdb = int(i.idalldvd) if i.idalldvd else ''
        text += '<film id="%d" imdb="%s" imdb_rate="%s" imdb_votes="%s"></film>' % (i.id, imdb, clear_quotes(i.imdb), i.imdb_votes)
        
    text += '</imdb_rate>'
        
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('film'):
            
            json_data.append({
                "id": int(i['id']),
                "imdb_id": int(i['imdb']) if i['imdb'] else None,
                "imdb_rate": i['imdb_rate'].replace(',','.') if i['imdb_rate'] else None,
                "imdb_votes": int(i['imdb_votes']),
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text



def content_movie_reviews(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает информацию об указанных фильмах
    """
    result = query_movie_reviews(limits, request)
    return get_movie_reviews(result, response_format, mk_dump)

def query_movie_reviews(limits, request):
    id = None
    if request:
        id = int_or_none(request.GET.get('id'))
    myfilter = {}
    if id:
        myfilter = {'obj__id': id}
    result = AfishaNews.objects.using('afisha').select_related('obj', 'user').filter(**myfilter).filter(type=2, object_type=1).order_by('date_time')[:limits]
    return result

@only_superuser
@never_cache
def dump_movie_reviews(request):
    runtime = time.time()
    result_xml, result_json = content_movie_reviews(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'movie_reviews')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'movie_reviews', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_movie_reviews(reviews, response_format, mk_dump):
    from django.utils.html import strip_tags, escape
    text = ''
    
    #reviews_film = {i.id: i.obj.id for i in reviews} # python 2.7+
    reviews_film = {}
    for i in reviews:
        reviews_film[i.id] = i.obj_id
    film_name = FilmsName.objects.using('afisha').filter(film_id__in=reviews_film.values(), type=2, status=1)
    film_vote = FilmVotes.objects.using('afisha').filter(pk__in=reviews_film.keys())
    #film_names = {f.film_id_id: f for f in film_name} # python 2.7+
    film_names = {}
    for f in film_name:
        film_names[f.film_id_id] = f.name.encode('utf-8')
    #film_votes = {f.id: f.rate_1 + f.rate_2 + f.rate_3 for i in film_vote} # python 2.7+
    film_votes = {}
    for f in film_vote:
        film_votes[f.id] = f.rate_1 + f.rate_2 + f.rate_3
    
    # начинаю формировать xml структуру
    for i in reviews:
        name = film_names.get(i.obj_id)
        if name:
            try: 
                firstname = i.user.firstname.encode('utf-8') if i.user.firstname else ''
                lastname = i.user.lastname.encode('utf-8') if i.user.lastname else ''
            except RegisteredUsers.DoesNotExist:
                firstname = ''
                lastname = ''
            
            content = strip_tags(i.content)
            content = escape(content)
            
            content = re.sub(r'\{[\w*\W*]+\}', '', content)
            
            content = content.replace('Normal 0','').replace('false','').replace('true','')
            content = content.replace('RU X-NONE X-NONE','').replace('MicrosoftInternetExplorer4','')
            content = content.replace('/* Style Definitions */','').replace('table.MsoNormalTable','')

            content = content.strip()

            rate = film_votes.get(i.id)
            title = i.name.encode('utf-8').replace('&', '&#38;').strip()
            imdb = int(i.obj.idalldvd) if i.obj.idalldvd else ''
            text += '<movie id="%s" imdb="%s" name="%s"> \
                <master_movie id="%s" firstname="%s" lastname="%s"></master_movie> \
                <review_date>%s</review_date><review_title>%s</review_title> \
                <rate>%s</rate><review_text>%s</review_text></movie>' % (
                i.obj_id, imdb, name, i.user_id, firstname, 
                lastname, i.date_time, title, rate, content.encode('utf-8'))
    
    text = xml_wrapper(text)
        
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('movie'):
            json_data.append({
                "id": int(i['id']),
                "imdb_id": int(i['imdb']) if i['imdb'] else None, 
                "name": i['name'],
                "master_movie_id": int(i.master_movie['id']),
                "master_movie_firstname": i.master_movie['firstname'],
                "master_movie_lastname": i.master_movie['lastname'],
                "review_date": i.review_date.string, 
                "review_title": i.review_title.string,
                "review_rate": int(i.rate.string) if i.rate.string != 'None' else None,
                "review_text": i.review_text.string,
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text

    

def content_film_posters(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает постеры фильмов
    """
    result = query_film_posters(limits, request)
    return get_film_posters(result, response_format, mk_dump)
   
def query_film_posters(limits, request):
    id = None
    if request:
        id = int_or_none(request.GET.get('id'))
    myfilter = {}
    if id:
        myfilter = {'pk': id}
    result = Film.objects.using('afisha').filter(**myfilter).order_by('pk')[:limits]
    return result

@only_superuser
@never_cache
def dump_film_posters(request):
    runtime = time.time()
    result_xml, result_json = content_film_posters(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'film_posters')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'film_posters', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))

def film_poster(poster):
    if poster.extresid:
        file_name = clear_quotes(poster.extresid.filename.replace('_small',''))
        img = re.findall('\d{0,}', file_name)
        step_gr = 1000
        iterat = step_gr
        group = '1'                          
        j = 1
        while int(img[0]) >= (iterat - step_gr) and iterat < int(img[0]):
            j += 1
            group = j
            iterat += step_gr
            
        #if poster.extresid.filepath:
        poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
    else:
        poster_path = ''
    return poster_path


def film_poster2(poster_obj, size='small', slide=False):
    posters = []
    
    poster = None
    for i in poster_obj:
        if i.extresid:
            file_name = i.extresid.filename
            img = re.findall('\d{0,}', file_name)
            step_gr = 1000
            iterat = step_gr
            group = '1'                          
            j = 1
            while int(img[0]) > (iterat - step_gr) and iterat <= int(img[0]):
                j += 1
                group = j
                iterat += step_gr

            if i.extresid.filepath:
                if 'poster' in i.extresid.filepath:
                    poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                    if 'small' in poster_path:
                        if size == 'big':
                            poster_path = poster_path.replace('_small','')
                        if 't' in i.extresid.info:
                            poster = poster_path
                        else:
                            posters.append(poster_path)

                else:
                    poster_path = 'http://slides.kinoafisha.ru/%s/%s' % (group, file_name)
                    if 'small' in poster_path:
                        posters.append(poster_path)
                            
            else:
                poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                if 'small' in poster_path:
                    if size == 'big':
                        poster_path = poster_path.replace('_small','')
                    if 't' in i.extresid.info:
                        poster = poster_path
                    else:
                        posters.append(poster_path)

    if poster:
        posters = poster
    else:
        if not slide:
            posters.sort()
            if len(posters) > 0:
                posters = posters[0]
    
    return posters




def get_film_posters(film, response_format, mk_dump):
    text = ''
    films_id = [i.id for i in film]
    
    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue__in=films_id)
    posters = {}
    for p in poster_obj:
        if posters.get(p.objpkvalue):
            posters[p.objpkvalue].append(p)
        else:
            posters[p.objpkvalue] = [p]
        
    # лог создания дампа буду записвать в 'log'
    for i in film:
        imdb = int(i.idalldvd) if i.idalldvd else ''
        poster_path = ''
        poster = posters.get(i.id)
        if poster:                                 
            poster_path = film_poster2(poster, 'big')
                
        text += '<film id="%s" imdb="%s">' % (i.id, imdb)
        text += '<poster path="%s"></poster>' % poster_path
        text += '</film>'
    
    
    text = xml_wrapper(text)
        
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('film'):
            json_data.append({
                "film_id": int(i['id']),
                "imdb_id": int(i['imdb']) if i['imdb'] else None, 
                "poster": i.poster['path'],
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text


def content_film_trailers(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает трейлеры к фильмам
    """
    result, version = query_film_trailers(limits, request)
    return get_film_trailers(result, response_format, mk_dump, version)
   
def query_film_trailers(limits, request):
    version = '1'
    id = None
    if request:
        id = int_or_none(request.GET.get('id'))
        version = request.GET.get('version', '1')
    myfilter = {}
    if id:
        myfilter = {'pk': id}
    result = Film.objects.using('afisha').filter(**myfilter).order_by('-pk')[:limits]
    return result, version

@only_superuser
@never_cache
def dump_film_trailers(request):
    runtime = time.time()
    version = request.GET.get('version', '1')
    result_xml, result_json = content_film_trailers(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'film_trailers', version)
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'film_trailers', '', 'json', version)
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_film_trailers(film, response_format, mk_dump, version='1'):
    text = ''
    
    films_id = [i.id for i in film] # id фильмов
    
    trailers_rel = Objxres.objects.using('afisha').filter(objtypeid=3, objpkvalue__in=films_id)
    trailers_ids = []
    trailer_rel_list = {}
    for i in trailers_rel:
        trailers_ids.append(i.extresid_id)
        
        if trailer_rel_list.get(i.objpkvalue):
            trailer_rel_list[i.objpkvalue].append(i.extresid_id)
        else:
            trailer_rel_list[i.objpkvalue] = [i.extresid_id,]
            
    trailers = TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=trailers_ids)
    
    trailers_list = {}
    for i in trailers:
        trailers_list[i.trailer_id] = i

    youtube_ids = {}

    # лог создания дампа буду записвать в 'log'
    for i in film:
        trl = trailer_rel_list.get(i.id, [])
        imdb = int(i.idalldvd) if i.idalldvd else None
        text += '<film id="%s" imdb="%s">' % (i.id, imdb)
        for t in trl:
            trailer = trailers_list.get(t)
            if trailer:
                code = re.findall(r'www.youtube.com/(?:v|embed)/([a-zA-Z0-9-_]+).*', trailer.code)
                if code:
                    if youtube_ids.get(i.id):
                        youtube_ids[i.id].append(code[0])
                    else:
                        youtube_ids[i.id] = [code[0]]

                soup = BeautifulSoup(trailer.code).encode(formatter=None)
                soup = str(soup).replace('<html><head></head><body>','').replace('</body></html>','').replace('\'"','"').replace("\"'",'"').replace("'",'"').replace('<','&lt;').replace('>','&gt;').replace('&','&amp;').replace('"','&quot;')
                text += '<trailer_code value="%s"></trailer_code>' % soup
        text += '</film>'
                
    text = xml_wrapper(text)
        
    if response_format == 'json' or mk_dump:
        json_data = []
        j_data = []
        
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('film'):
            
            j_imdb = int(i['imdb']) if i['imdb'] != 'None' else None
            film_id = int(i['id'])
            
            if version == '1':
                
                j_temp = {
                    "film_id": film_id,
                    "imdb_id": j_imdb, 
                    "trailer": [],
                }
                for j in i.findAll('trailer_code'):
                    j_temp["trailer"].append(j['value'])
                    
                json_data.append(j_temp)
                
            elif version == '2':
                t = youtube_ids.get(film_id)
                
                if film_id not in j_data:
                    j_data.append(film_id)
                    json_data.append({
                        "film_id": film_id, 
                        "imdb_id": j_imdb, 
                        "trailer": t,
                    })
            
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text

def content_releases_ua(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает релизы Украины
    """
    result = query_releases_ua(limits)
    return get_releases_ua(result, response_format, mk_dump)
   
def query_releases_ua(limits):
    today = datetime.date.today()
    sources_list = ('http://www.okino.ua/', 'http://kino-teatr.ua/')
    result = SourceReleases.objects.select_related('film', 'source_obj').filter(source_obj__url__in=sources_list, release__gte=today).exclude(film__kid=None).order_by('distributor')[:limits]
    #result = Okinoua.objects.all()[:limits]
    return result

@only_superuser
@never_cache
def dump_releases_ua(request):
    runtime = time.time()
    result_xml, result_json = content_releases_ua(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'releases_ua')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'releases_ua', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_releases_ua(releases, response_format, mk_dump):
    text = ''
    
    current_site = DjangoSite.objects.get_current()
    films_id = set([i.film.kid for i in releases]) # id фильмов
    #return HttpResponse(str(len(set(films_id))))
    raspishi = RaspishiRelations.objects.filter(kid__in=films_id).distinct('kid')
    raspishi_dict = {}
    for i in raspishi:
        raspishi_dict[i.kid] = i.rid
    
    films = FilmsName.objects.select_related('film_id').using('afisha').filter(film_id__id__in=films_id, status=1, type=2)
    
    uk_film_name = [i for i in releases]

    distrib = {}
    uk_film_name_dict = {}
    for i in uk_film_name:
        if i.source_obj.url == 'http://kino-teatr.ua/':
            uk_film_name_dict[i.film.kid] = i
        if i.distributor:
            distrib[i.film.kid] = i.distributor
    
    uk_posters = UkrainePosters.objects.filter(kid__in=films_id)
    uk_posters_dict = {}
    for i in uk_posters:
        uk_posters_dict[i.kid] = i.poster
    
    films_dict = {}
    for i in films:
        imdb = get_imdb_id(i.film_id.idalldvd)
        films_dict[i.film_id_id] = {'imdb': imdb, 'name': i.name.replace('"', "'")}
    
    # лог создания дампа буду записвать в 'log'
    for i in releases:
        
        f = films_dict.get(i.film.kid, {'imdb': '', 'name': ''})
        rid = raspishi_dict.get(i.film.kid, '')
        
        distributor = distrib.get(i.film.kid, '')
        if distributor:
            distributor = distributor.replace('&', '&amp;') 
        
        description = ''
        name = ''
        
        ua_data = uk_film_name_dict.get(i.film.kid)
        if ua_data:
            name = ua_data.film.name.replace('&', '&amp;').replace('"', "'")
            description = ua_data.film.text
            if description in (u'Проект оголошений', u'Підготовка до зйомок'):
                description = ''
                
        poster = uk_posters_dict.get(i.film.kid, '')
        if poster:
            poster = str(poster).split('/')[-1:][0]
            poster = 'http://%s/upload/films/posters/uk/%s' % (current_site.domain, poster)
        
        #if i.film.name_ua:
        #    name = i.film.name_ua.replace('&', '&amp;')
        
        text += '<film kinoafisha_id="%s" imdb="%s" raspishi_id="%s">' % (i.film.kid, f['imdb'], rid)
        text += '<names ru="%s" ua="%s"></names>' % (f['name'].strip(), name.strip())
        text += '<release value="%s"></release>' % i.release
        text += '<distributor value="%s"></distributor>' % distributor
        text += '<poster value="%s"></poster>' % poster
        text += '<description>%s</description>' % description
        text += '</film>'

        
    text = xml_wrapper(text.encode('utf-8'))
        
    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, "html.parser")
        for i in data.findAll('film'):
            json_data.append({
                "id": int(i['kinoafisha_id']),
                "imdb_id": int(i['imdb']) if i['imdb'] and i['imdb'] != 'None' else None, 
                "raspishi_id": int(i['raspishi_id']) if i['raspishi_id'] else None, 
                "name_ru": i.names['ru'],
                "name_ua": i.names['ua'],
                "release": i.release['value'],
                "distributor": i.distributor['value'],
                "poster": i.poster['value'],
                "description": i.description.string,
            })
    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text
        




def content_schedule_v2(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает сеансы по параметрам
    """
    result, date_from = query_schedule_v2(limits, request)
    return get_schedule_v2(result, response_format, mk_dump, date_from)


def query_schedule_v2(limits, request):
    today = datetime.date.today().strftime("%Y-%m-%d")

    myfilter = {}
    date_from = None
    if request:
        movies_param = request.GET.get('cinemas')
        date_param = request.GET.get('date')

        if date_param:
            try:
                date_from = datetime.datetime.strptime(date_param, "%d-%m-%Y").strftime("%Y-%m-%d")
            except ValueError:
                date_from = None
        else:
            date_from = today

        myfilter['schedule_id__date_to__gte'] = date_from
        myfilter['schedule_id__date_from__lte'] = date_from

        movies = []
        if movies_param:
            for i in movies_param.split(' '):
                try:
                    movies.append(int(i))
                except ValueError: pass
            myfilter['schedule_id__movie_id__id__in'] = movies[:5]
    else:
        myfilter['schedule_id__date_to__gte'] = today

    result = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__movie_id__city', 'schedule_id__film_id', 'schedule_id__hall_id', 'schedule_id__hall_id__id_name').filter(**myfilter).order_by('schedule_id__movie_id__name')[:limits]
    return result, date_from

@only_superuser
@never_cache
def dump_schedule_v2(request):
    runtime = time.time()
    result_xml, result_json = content_schedule_v2(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'schedule_v2')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'schedule_v2', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_schedule_v2(schedules, response_format, mk_dump, date_from):

    text = ''
    
    films_id = set([i.schedule_id.film_id_id for i in schedules])
    films_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__id__in=films_id, status=1, type=2)
    films_name_dict = {}
    for i in films_name:
        films_name_dict[i.film_id_id] = {'name': i.name.strip(), 'imdb': i.film_id.idalldvd}
    

    doubles = []

    movie_old = ''
    film_old = ''
    for i in schedules:
        unique = '%s%s%s' % (i.session_list_id.time, i.schedule_id.movie_id_id, i.schedule_id.film_id_id)
        if unique not in doubles:
            doubles.append(unique)

            showtime = str(i.session_list_id.time).split(':')
            showtime = '%s:%s' % (showtime[0], showtime[1])

            if i.schedule_id.movie_id_id != movie_old:
                if movie_old != '':
                    text += '</film></cinema>'
                film = films_name_dict.get(i.schedule_id.film_id_id)
                text += '<cinema id="%s">' % i.schedule_id.movie_id_id
                text += '<film id="%s" imdb_id="%s" name="%s">' % (i.schedule_id.film_id_id, film['imdb'], film['name'].encode('utf-8'))
                text += '<time>%s</time>' % showtime
            else:
                if i.schedule_id.film_id_id != film_old:
                    text += '</film>'
                    film = films_name_dict.get(i.schedule_id.film_id_id)
                    text += '<film id="%s" imdb_id="%s" name="%s">' % (i.schedule_id.film_id_id, film['imdb'], film['name'].encode('utf-8'))
                text += '<time>%s</time>' % showtime
                
            film_old = i.schedule_id.film_id_id
            movie_old = i.schedule_id.movie_id_id
        
    if text:
        text += '</film></cinema>'
    
    text = '<date>%s</date>%s' % (date_from, text)
        
    text = xml_wrapper(text)
    
    if response_format == 'json' or mk_dump:
        data = BeautifulSoup(text, "html.parser")
        showdate = data.find('date').string

        json_data = {
            'date': showdate, 
            'cinemas': [],
        }
        for i in data.findAll('cinema'):
            j_cinema = {
                "id": int(i['id']),
                "films": [],
            }
            for j in i.findAll('film'):
                j_film = {
                    "id": int(j['id']),
                    "imdb_id": int(j['imdb_id']) if j['imdb_id'] != 'None' else None,
                    "name": j['name'],
                    "times": [t.string for t in j.findAll('time')],
                }
                j_cinema['films'].append(j_film)
            json_data['cinemas'].append(j_cinema)

    
    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text




def content_schedule_v4(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает сеансы по параметрам
    """
    result = query_schedule_v4(limits, request)
    return get_schedule_v4(result, response_format, mk_dump)


def query_schedule_v4(limits, request):
    today = datetime.date.today()

    myfilter = {}
    if request:
        movies_param = request.GET.get('cinemas')
        date_param = request.GET.get('date')

        if date_param:
            try:
                date_from = datetime.datetime.strptime(date_param, "%d-%m-%Y")
            except ValueError:
                date_from = today
        else:
            date_from = today

        day1 = today + datetime.timedelta(days=1)

        myfilter['dtime__gte'] = date_from
        myfilter['dtime__lt'] = day1

        movies = []
        if movies_param:
            for i in movies_param.split(' '):
                try:
                    movies.append(int(i))
                except ValueError: pass
            myfilter['cinema__cinema__code__in'] = movies[:5]
    else:
        pass

    day14 = today + datetime.timedelta(days=14)
    myfilter['dtime__gte'] = today
    myfilter['dtime__lt'] = day14

    if limits == settings.API_CLIENT_LIMIT:
        limits = None

    result = list(SourceSchedules.objects.filter(**myfilter).exclude(film__source_id=0).values('film__kid', 'cinema__cinema__code', 'dtime')[:limits])
    
    return result


@only_superuser
@never_cache
def dump_schedule_v4(request):
    runtime = time.time()
    result_xml, result_json = content_schedule_v4(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'schedule_v4')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'schedule_v4', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))
    
def get_schedule_v4(schedules, response_format, mk_dump):

    films = {}
    data = {}
    for i in schedules:
        if not data.get(i['cinema__cinema__code']):
            data[i['cinema__cinema__code']] = {}
        if not data[i['cinema__cinema__code']].get(i['film__kid']):
            data[i['cinema__cinema__code']][i['film__kid']] = {}
        if not data[i['cinema__cinema__code']][i['film__kid']].get(i['dtime'].date()):
            data[i['cinema__cinema__code']][i['film__kid']][i['dtime'].date()] = []
        data[i['cinema__cinema__code']][i['film__kid']][i['dtime'].date()].append(i['dtime'].time().strftime('%H:%M'))
        films[i['film__kid']] = ''

    fdata = {}
    for i in list(FilmsName.objects.using('afisha').filter(film_id__id__in=films.keys(), status=1, type=2).values('film_id', 'name', 'film_id__idalldvd')):
        fdata[i['film_id']] = {'name': i['name'], 'imdb': i['film_id__idalldvd']}
    
    
    text = ''
    cinemas_list = []

    for cinema_id, films in data.iteritems():
        text += '<cinema id="%s">' % cinema_id

        json_cinema = {'id': cinema_id, 'films': []}
        for film_id, days in films.iteritems():
            f = fdata.get(film_id)
            if f:
                text += '<film id="%s" imdb_id="%s" name="%s">' % (film_id, f['imdb'], f['name'].encode('utf-8'))

                json_film = {'id': film_id, 'imdb_id': f['imdb'], 'name': f['name'], 'showtime': []}

                for day, times in days.iteritems():
                    sorted_time = sorted(set(times))
                    times_txt = ', '.join(sorted_time)
                    text += '<showtime date="%s" time="%s"></showtime>' % (day, times_txt)

                    json_film['showtime'].append({'date': str(day), 'time': sorted_time})

                text += '</film>'

                json_cinema['films'].append(json_film)

        text += '</cinema>'

        cinemas_list.append(json_cinema)

    text = xml_wrapper(text)
    
    json_data = {'cinemas': cinemas_list} if cinemas_list else {}

    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        return text
    
    return text











@never_cache
@gzip_page
def content_actions_log(request):

    SECRET_KEY = 'z0L7j9S1g'
    
    secret = request.GET.get('secret')
    action = request.GET.get('action')
    profile = request.GET.get('profile')
    fobject = request.GET.get('object')
    act = request.GET.get('act')
    
    errors = []
    
    if SECRET_KEY != secret:
        errors.append(u'Неверный параметр secret')
    
    if action not in ('12', '13'):
        errors.append(u'Неверный параметр action')
    
    try:
        profile = int(profile)
        try:
            profile = Profile.objects.get(user__id=profile)
        except Profile.DoesNotExist:
            errors.append(u'Profile Does Not Exist')
    except ValueError:
        errors.append(u'Неверный параметр profile')
        
    try:
        fobject = int(fobject)
    except ValueError:
        errors.append(u'Неверный параметр object')
    
    if act not in ('1', '2' , '3'):
        errors.append(u'Неверный параметр act')
    
    if not errors:
        ok = actions_logger(action, fobject, profile, act, extra=None)
        if not ok:
            errors.append(u'Произошла Ошибка')

    status = 'Error' if errors else 'OK'
    
    result = {'status': status, 'errors': errors}
    
    response = HttpResponse(simplejson.dumps(result, ensure_ascii=False))

    return response


def content_schedule_v3(limits, request, response_format, mk_dump=False):
    """
    Метод возвращает сеансы по параметрам
    """
    result, date_from = query_schedule_v3(limits, request)
    return get_schedule_v3(result, response_format, mk_dump, date_from)

def query_schedule_v3(limits, request):
    date_from = datetime.date.today()
    city = request.GET.get('city')
    cinema = request.GET.get('cinema')
    myfilter = {'schedule_id__movie_id__city__id': 1}
    if cinema:
        myfilter = {'schedule_id__movie_id': cinema}
    if city:
        myfilter = {'schedule_id__movie_id__city__id': city}
    result = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__movie_id__city', 'schedule_id__film_id', 'schedule_id__hall_id', 'schedule_id__hall_id__id_name').filter(Q(schedule_id__date_from__gte=date_from) | Q(schedule_id__date_from__lt=date_from) & Q(schedule_id__date_to__gte=date_from)).filter(**myfilter).order_by('schedule_id__movie_id__name')[:limits]
    return result, date_from

@only_superuser
@never_cache
def dump_schedule_v3(request):
    runtime = time.time()
    result_xml, result_json = content_schedule_v3(None, request, None, True)
    result = save_dump(result_xml, runtime, request, 'schedule_v3')
    save_dump(simplejson.dumps(result_json, ensure_ascii=False).encode('utf-8'), runtime, request, 'schedule_v3', '', 'json')
    return render_to_response('api/api_create_dump.html', result, context_instance=RequestContext(request))


def get_schedule_v3(schedule, response_format, mk_dump, date_from):
    future = date_from + datetime.timedelta(days=3)

    films_id = [i.schedule_id.film_id_id for i in schedule]
    
    film_name = FilmsName.objects.using('afisha').select_related('film_id').filter(film_id__in=films_id, type=2, status=1)
    film_names = {}
    for i in film_name:
        film_names[i.film_id_id] = i
    
    movies_id = [i.schedule_id.movie_id_id for i in schedule]
    cinema = ImportCinema.objects.using('afisha').filter(cinema_id__in=set(movies_id), script_id=100)
    cinemas = {}
    for i in cinema:
        cinemas[str(i.cinema_id)] = i

    city_id_old = ''
    movie_id_old = ''
    schedule_id_old = ''

    text = ''

    for i in schedule:
        
        def schedule_ext(text):
            text += '<film id="%s" name="%s"><date_start value="%s"></date_start><date_finish value="%s"></date_finish>' % (i.schedule_id.film_id_id, clear_quotes(film_name), clear_quotes(i.schedule_id.date_from), clear_quotes(i.schedule_id.date_to))
            return text

        film = film_names.get(i.schedule_id.film_id_id)
        if film:
            film_name = film.name.encode('utf-8')
        else:
            try:
                film_name = FilmsName.objects.using('afisha').get(film_id=i.schedule_id.film_id_id, type=1, status=1)
                film_name = film_name.name.encode('utf-8')
            except:
                film_name = None
        
        if i.schedule_id.date_to <= future:
            city_id = str(i.schedule_id.movie_id.city_id)
            city_name = clear_quotes(i.schedule_id.movie_id.city.name)
            movie_id = str(i.schedule_id.movie_id_id)
            movie_name = clear_quotes(i.schedule_id.movie_id.name)
            
            schedule_id = i.schedule_id_id

            showtime = str(i.session_list_id.time).split(':')
            showtime = '%s:%s' % (showtime[0], showtime[1])

            if movie_id_old != movie_id:
                
                if schedule_id_old != schedule_id:
                    if schedule_id_old: text += '</film>'
                if movie_id_old:
                    text += '</movie>'
                if city_id_old != city_id:
                    if city_id_old:
                        text += '</city>'
                    text += '<city id="%s" name="%s">' % (city_id, city_name)
                    text += '<movie id="%s" name="%s">' % (movie_id, movie_name)
                    if schedule_id_old != schedule_id:
                        text = schedule_ext(text)
                    text += '<time>%s</time>' % showtime
                else:
                    text += '<movie id="%s" name="%s">' % (movie_id, movie_name)
                    if schedule_id_old != schedule_id:
                        text = schedule_ext(text)
                    text += '<time>%s</time>' % showtime
                city_id_old = city_id
                movie_id_old = movie_id
            else:
                if schedule_id_old != schedule_id:
                    if schedule_id_old:
                        text += '</film>'
                    text = schedule_ext(text)

                text += '<time>%s</time>' % showtime
                movie_id_old = movie_id
            schedule_id_old = schedule_id
        
    
    text = xml_wrapper('%s</film></movie></city>' % text) if text else xml_wrapper(text)


    if response_format == 'json' or mk_dump:
        json_data = []
        data = BeautifulSoup(text, from_encoding="utf-8")
        
        for i in data.findAll('city'):
            j_data = {
                "city_id": int(i['id']),
                "city_name": i['name'],
                "movies": [],
            }
            for m in i.findAll('movie'):
                j_data_movie = {
                    "id": int(m['id']),
                    "name": m['name'],
                    "films": [],
                }
                for f in m.findAll('film'):
                    j_data_film = {
                        "id": int(f['id']),
                        "name": f['name'],
                        "date_start": f.date_start['value'],
                        "date_finish": f.date_finish['value'],
                        "time": [i.string for i in f.findAll('time')],
                    }
                    j_data_movie['films'].append(j_data_film)
                j_data['movies'].append(j_data_movie)
            json_data.append(j_data)

    if mk_dump:
        return text, json_data
    elif response_format == 'json':
        return json_data
    else:
        # возвращаю данные
        return text




def give_me_dump_please(request, method, param, free=False):
    response_format = request.GET.get('format')
    version = request.GET.get('version', '')
    if version:
        version = '_v%s' % version
    if param and method != 'film':
        version += '_'
    format = 'xml'
    if response_format == 'json':
        format = 'json'
    # сущесвует ли запрашиваемый дамп, если да, то:
    if os.path.isfile('%s/dump_%s%s%s.%s' % (settings.API_DUMP_PATH, method, version, param, format)):
        # выбераю файл
        f = open('%s/dump_%s%s%s.%s' % (settings.API_DUMP_PATH, method, version, param, format), 'r')
        # задаю тип файла
        response = HttpResponse(f.read(), mimetype='application/%s' % format)
        # задаю имя файла
        response['Content-Disposition'] = 'attachment; filename=%s%s%s.%s' % (method, version, param, format)
        f.close()
        # записываю в БД это событие
        if not free:
            api_logger(request, '%s%s%s' % (method, version, param), 3)
        return response
    # если запрашиваемого дампа не существует, то
    else:
        # записываю в БД это событие
        if not free:
            api_logger(request, '%s%s%s' % (method, version, param), 4)
        raise Http404



def get_film_data(id, many=False):
    ids = id if many else [id,]

    film_list = []
    
    # фильм
    films = Film.objects.using('afisha').select_related('genre1', 'genre2', 'genre3', 'country', 'country2', 'prokat1', 'prokat2').filter(pk__in=ids)
    
            
    for film in films:
        # рейтинг
        afisha_rate = ''
        afisha_num = ''
        try:
            film_ext = FilmExtData.objects.using('afisha').only('vnum', 'rate').get(pk=film.id)
            afisha_rate = film_ext.rate
            afisha_num = film_ext.vnum
        except FilmExtData.DoesNotExist: pass

        # персоны
        persons = PersonsRelationFilms.objects.using('afisha').select_related('person_id', 'type_act_id').filter(film_id=film, status_act_id__id=1)
        persons_id = [i.person_id_id for i in persons]
        
        persons_name = AfishaPersonsName.objects.using('afisha').filter(person_id__id__in=persons_id, flag__in=(1,2))
        persons_name_dict = {}
        for i in persons_name:
            if not persons_name_dict.get(i.person_id_id):
                persons_name_dict[i.person_id_id] = {'name': [{'flag': i.flag, 'name': i.name}]}
            else:
                persons_name_dict[i.person_id_id]['name'].append({'flag': i.flag, 'name': i.name})
        
        ppp = {'directors': [], 'actors': [], 'other_person': []}

        for i in persons:
            pers = persons_name_dict.get(i.person_id_id)

            xxx = {'type': i.type_act_id_id, 'type_name': i.type_act_id.type_act, 'imdb': i.person_id.imdb, 'id': i.person_id_id}
            empty_name = {'name': [{'flag': '', 'name': ''}]}
            
            pers_dict = dict(pers.items() + xxx.items()) if pers else dict(empty_name.items() + xxx.items())

            if i.type_act_id_id == 3:
                ppp['directors'].append(pers_dict)
            elif i.type_act_id_id == 1:
                ppp['actors'].append(pers_dict)
            else:
                ppp['other_person'].append(pers_dict)
            
        # постеры и трейлеры
        trailers = []
        posters = []
        slides = []
        poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(
            objtypeid__in=[301, 300, 3], 
            objpkvalue=film.id
        )
        
        tr_ids = [i.extresid_id for i in poster_obj if i.objtypeid == 3]
        trailer_tmp = TrailerInfo.objects.using('afisha').only('trailer_id', 'code').filter(trailer_id__in=tr_ids)
        trailer_dict = {}
        for i in trailer_tmp:
            trailer_dict[i.trailer_id] = i
            
        poster = None
        for i in poster_obj:
            if i.objtypeid == 3:
                trailer = trailer_dict.get(i.extresid_id)
                if trailer:
                    trailer_id = trailer.trailer_id
                    trailer_code = trailer.code.replace('&#034;', '"')
                    trailers.append({'code': trailer_code, 'id': trailer_id})
            else:
                if i.extresid:
                    file_name = i.extresid.filename
                    img = re.findall('\d{0,}', file_name)
                    step_gr = 1000
                    iterat = step_gr
                    group = '1'                          
                    j = 1
                    while int(img[0]) > (iterat - step_gr) and iterat <= int(img[0]):
                        j += 1
                        group = j
                        iterat += step_gr

                    if i.extresid.filepath:
                        if 'poster' in i.extresid.filepath:
                            poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                            #if 'small' in poster_path:
                            #    posters.append(poster_path)
                            
                            if 'small' in poster_path:
                                if 't' in i.extresid.info:
                                    poster = poster_path
                                else:
                                    posters.append(poster_path)
                        else:
                            poster_path = 'http://slides.kinoafisha.ru/%s/%s' % (group, file_name)
                            #if len(slides) < 35 and 'small' in poster_path:
                            #page = urllib.urlopen(poster_path)
                            #if page.getcode() == 200:
                            
                            #if 'small' in poster_path:
                            #    slides.append(poster_path)
                            
                            if 'small' in poster_path:
                                slides.append(poster_path)
                    else:
                        poster_path = 'http://posters.kinoafisha.ru/%s/%s' % (group, file_name)
                        #if 'small' in poster_path:
                        #    posters.append(poster_path)
                        
                        #if 'small' in poster_path and 't' in i.extresid.info:
                        #     posters.append(poster_path)
                        
                        if 'small' in poster_path:
                            if 't' in i.extresid.info:
                                poster = poster_path
                            else:
                                posters.append(poster_path)
        
        if poster:
            posters = poster
        else:
            posters.sort()
            if len(posters) > 0:
                posters = posters[0]
        
        # названия фильма
        name_ru = ''
        name_en = ''
        fnames = FilmsName.objects.using('afisha').only('name', 'status', 'type').filter(film_id=film, type__in=(1,2), status=1)
        for i in fnames:
            if i.type == 1:
                name_en = i.name.strip()
            elif i.type == 2:
                name_ru = i.name.strip()
        if not name_ru:
            name_ru = name_en
        if not name_en:
            name_en = name_ru
            
        # жанры
        film_genres = [film.genre1, film.genre2, film.genre3]
        genres = {}
        for i in film_genres:
            if i:
                genres[i.id] = i.name

        # страны
        country = ""
        if film.country:
            country = film.country.name 

        film_countries = [film.country, film.country2]
        countries = {}
        for i in film_countries:
            if i:
                countries[i.id] = i.name 

        # дистрибьюторы
        distributors = []
        distr_1, distr_1_id = (film.prokat1.name, int(film.prokat1_id)) if film.prokat1 else (None, None)
        distr_2, distr_2_id = (film.prokat2.name, int(film.prokat2_id)) if film.prokat2 else (None, None)
        if distr_1:
            distributors.append({'id': distr_1_id, 'name': distr_1})
        if distr_2:
            distributors.append({'id': distr_2_id, 'name': distr_2})


        imdb_rate, imdb_num = (film.imdb.encode('utf-8'), film.imdb_votes) if film.imdb_votes else ('', '')
        comment = film.comment if film.comment else ''
        limits = film.limits if film.limits else ''
        description = film.description if film.description else ''
        runtime = film.runtime.encode('utf-8') if film.runtime else ''
        idalldvd = get_imdb_id(film.idalldvd) if film.idalldvd else ''
        site = clear_links(film.site.encode('utf-8')) if film.site else ''
        release = film.date if film.date else ''

        film_data = {
            'name_ru': name_ru, 
            'name_en': name_en,
            'year': film.year,
            'idimdb': idalldvd,
            'afisha_rate': afisha_rate,
            'afisha_num': afisha_num,
            'imdb_rate': imdb_rate,
            'imdb_num': imdb_num,
            'comment': comment,
            'description': description,
            'limits': limits,
            'runtime': runtime,
            'directors': ppp['directors'],
            'actors': ppp['actors'],
            'other_person': ppp['other_person'],
            'posters': posters,
            'slides': slides,
            'trailers': trailers,
            'genres': genres,
            'countries': countries,
            'site': site,
            'release': release,
            'distributors': distributors,
            'object': film,
	        'country': country,
	        'film_genres':film_genres,
        }
        film_list.append(film_data)
    
    
    data = film_list 
    if not many and film_list:
        data = film_list[0]
            
    return data



@never_cache
def mobile_film(request, id):
    from user_registration.func import md5_string_generate
    
    response_format = request.GET.get('format')
    
    text = [] if response_format == 'json' else u''
    
    try:
        basewidth = int(request.GET.get('width')) if request.GET.get('width') else None
        if basewidth < 10 or basewidth > 2400:
            basewidth = None
    except ValueError:
        basewidth = None

    result = get_film_data(id)

    xml_url = ''
    
    if result['posters'] and basewidth:
        url = result['posters'].replace('_small','')
        img = resize_image(basewidth, url)
        if img:
            img_name = md5_string_generate(url)
            path = '%s/api_img_tmp/%s.jpg' % (settings.MEDIA_ROOT, img_name)
            img.save(path)
            xml_url = 'http://%s%sapi_img_tmp/%s.jpg' % (request.get_host(), settings.MEDIA_URL, img_name)
    
    if result:
        reviews = AfishaNews.objects.using('afisha').select_related('obj', 'user').filter(type=2, object_type=1, obj__id=id)
        reviews_count = reviews.count()

        reviews_dict = {}
        for i in reviews:
            reviews_dict[i.id] = i

        film_vote = FilmVotes.objects.using('afisha').filter(pk__in=reviews_dict.keys())

        film_votes = {}
        for i in film_vote:
            film_votes[i.id] = i.rate_1 + i.rate_2 + i.rate_3

        youtube_id = []
        for i in result['trailers']:
            code = re.findall(r'www.youtube.com/(?:v|embed)/([a-zA-Z0-9-]+).*', i['code'])
            if code:
                youtube_id.append(code[0])
        
        '''
        for k, v in reviews_dict.iteritems():
            try: 
                firstname = v.user.firstname if v.user.firstname else ''
                lastname = v.user.lastname if v.user.lastname else ''
            except RegisteredUsers.DoesNotExist:
                firstname = None
                lastname = None
            rate = film_votes.get(k)
            reviews_tag += '<reviewer firstname="%s" lastname="%s" rate="%s"></reviewer>' % (firstname, lastname, rate)
        reviews_tag += u'</reviews>'
        '''
        
        if result['description']:
            desc = re.sub(r'<[^>]*>', '', result['description'])
            desc = desc.replace('&', "&amp;")
        else:
            desc = ''
            
        if result['comment']:
            comm = re.sub(r'<[^>]*>', '', result['comment'])
            comm = comm.replace('&', "&amp;")
        else:
            comm = ''
        
        runtime = result['runtime'] if result['runtime'] else ''
        rate = result['afisha_rate'] if result['afisha_num'] else ''
        votes = result['afisha_num'] if result['afisha_num'] else ''
        imdb_rate = result['imdb_rate'] if result['imdb_num'] else ''
        imdb_votes = result['imdb_num'] if result['imdb_num'] else ''
        site = result['site'] if result['site'] else ''
        limits = age_limits(result['limits']) if result['limits'] else ''
        release = result['release'] if result['release'] else ''
        poster = result['posters'].replace('_small','') if result['posters'] else ''
        
        
        if response_format == 'json':
            text = {
                "id": id, 
                "imdb_id": result['idimdb'],
                "name": result['name_ru'],
                "original": result['name_en'],
                "year": result['year'],
                "persons": [],
                "genres": [],
                "countries": [],
                "ratings": [],
                "trailers_count": len(youtube_id),
                "trailers": [],
                'runtime': runtime,
                'site': site,
                'description': desc,
                'limits': limits,
                'comment': comm,
                'release': str(release),
                'poster': poster,
                'resized_poster': xml_url,
                "reviews": reviews_count,
            }
        else:
            text += u'<film id="%s" idimdb="%s" name="%s" original="%s">' % (id, result['idimdb'], result['name_ru'], result['name_en'])
            text += u'<year value="%s"></year>' % result['year']
            text += u'<persons>'
            

        for i in [result['directors'], result['actors'], result['other_person']]:
            for v in i:
                if response_format == 'json':
                    text['persons'].append({
                        "id": v['id'],
                        "name": v['name'][0]['name'],
                        "type": v['type'],
                        "status": 1,
                        "imdb_id": v['imdb'],
                    })
                else:
                    text += u'<person id="%s" name="%s" type="%s" status="1" imdb="%s"></person>' % (v['id'], v['name'][0]['name'], v['type'], v['imdb'])
                    
        if response_format != 'json':
            text += u'</persons>'
            text += u'<runtime value="%s"></runtime>' % runtime
            text += u'<genres>'
        
        
        for k, v in result['genres'].iteritems():
            if response_format == 'json':
                text['genres'].append({
                    "id": k,
                    "name": v.decode('utf-8'),
                })
            else:
                text += u'<genre id="%s" name="%s"></genre>' % (k, v.decode('utf-8'))
            
        if response_format != 'json':
            text += u'</genres>'
            text += u'<countries>'
            
        for k, v in result['countries'].iteritems():
            if response_format == 'json':
                text['countries'].append({
                    "id": k,
                    "name": v.decode('utf-8'),
                })
            else:
                text += u'<country id="%s" name="%s"></country>' % (k, v.decode('utf-8'))

        if response_format == 'json':
            text['ratings'].append({
                "source": "kinoinfo",
                "rate": rate,
                "votes": votes,
            })
            text['ratings'].append({
                "source": "imdb",
                "rate": imdb_rate,
                "votes": imdb_votes,
            })

        else:
            text += u'</countries>'
            text += u'<rate value="%s"></rate>' % rate
            text += u'<votes value="%s"></votes>' % votes
            text += u'<imdb value="%s"></imdb>' % imdb_rate
            text += u'<imdb_votes value="%s"></imdb_votes>' % imdb_votes
            text += u'<site value="%s"></site>' % site
            text += u'<description value="%s"></description>' % desc
            text += u'<limits value="%s"></limits>' % limits
            text += u'<comment value="%s"></comment>' % comm
            text += u'<date value="%s"></date>' % release
            text += u'<poster value="%s"></poster>' % poster
            text += u'<resized_poster value="%s"></resized_poster>' % xml_url
            text += u'<trailers count="%s">' % len(youtube_id)
            text += u'<reviews count="%s"></reviews>' % reviews_count
            
        for i in youtube_id:
            if response_format == 'json':
                text['trailers'].append(i)
            else:
                text += u'<trailer>%s</trailer>' % i
                #text += u'<trailer value="%s"></trailer>' % i.replace('\'"','"').replace("\"'",'"').replace("'",'"').replace('<','&lt;').replace('>','&gt;').replace('&','&amp;').replace('"','&quot;')
                

        if response_format == 'json':
            return render_to_response('api/api_schedule.html', {'text': simplejson.dumps(text)}, mimetype='application/json')
        else:
            '''
            для получения валидного кода трейлера из xml, необходимо заменить: 
            &amp;   =   &
            &lt;    =   <
            &gt;    =   >
            &quot;  =   "
            '''
            text += u'</trailers>'
            text += u'</film>'

            text =  xml_wrapper(text)
            return render_to_response('api/api_schedule.html', {'text': text}, mimetype='application/xml')

    raise Http404


@never_cache
def cities_relations(request):
    cities = City.objects.all()
    text = ''
    for i in cities:
        text += u'<city kinoafisha="%s" kinoinfo="%s"></city>' % (i.kid, i.id)
    text =  xml_wrapper(text)
    return render_to_response('api/api_schedule.html', {'text': text}, mimetype='application/xml') 

@never_cache
@gzip_page
def download(request, method, param=''):
    """
    ЗАГРУЗКА ДАМПОВ 
    """
    if is_client_api(request):
        return give_me_dump_please(request, method, param)
    else: 
        version = request.GET.get('version', '')
        api_logger(request, '%s%s%s' % (method, version, param), 5)
        raise Http404



def api_img_tmp_delete():
    t1 = time.time()
    start_time = datetime.datetime.now().strftime('%H:%M:%S')
    
    path = '%s/api_img_tmp/' % settings.MEDIA_ROOT
    for i in os.listdir(path):
        try:
            os.remove('%s/%s' % (path, i))
        except OSError: pass

    time.sleep(2.0)
    return time.time()-t1


@only_superuser
@never_cache
def cron_func(request, method):
    result = method()
    return HttpResponse(result)

"""
@only_superuser
@never_cache
def screens_kinohod_stat(request):
    
    #Статистика импорта киноход
    
    today = datetime.date.today()
    
    #kinohod = KinohodSchedules.objects.filter(dtime__gte=today)
    kinohod_cinema = len(set([i.cinema_id for i in kinohod]))
    kinohod_films = len(set([i.film_id for i in kinohod]))
    
    kinohod_count = kinohod.count()
    #kinohod_sale = KinohodSchedules.objects.filter(dtime__gte=today, sale=True).count()

    sess_count = query_screens(None)
    sess_cinema = len(set([i.schedule_id.movie_id_id for i in sess_count]))
    sess_films = len(set([i.schedule_id.film_id_id for i in sess_count]))
    sess_count = sess_count.count()

    #sess_kinohod = AfishaSession.objects.using('afisha').filter(schedule_id__date_to__gte=today, schedule_id__film_id__id__in=[6752, 11349, 28652, 12552, 28720, 29911, 21736, 29446, 29977, 29979, 30597, 29762, 25928, 30415, 29973, 31246]).exclude(kinohod=None).count()
    
    log = '<b>От %s</b><br /><br />Сеансов от киноход: %s<br />С онлайн продажей: %s<br />Кинотеатров: %s<br />Фильмов: %s<br /><br />' % (today, kinohod_count, kinohod_sale, kinohod_cinema, kinohod_films)
    
    sess_kinohod = list(AfishaSession.objects.using('afisha').filter(schedule_id__date_to__gte=today, schedule_id__film_id__id__in=[6752, 11349, 28652, 12552, 28720, 29911, 21736, 29446, 29977, 29979, 30597, 29762, 25928, 30415, 29973, 31246]).exclude(kinohod=None).values_list('kinohod', flat=True))

    #sess_kinohod_sale = KinohodSchedules.objects.filter(dtime__gte=today, sale=True, kinohod_id__in=sess_kinohod).count()

    log += 'Сеансов в screens v2: %s<br />С онлайн продажей: %s<br />Кинотеатров: %s<br />Фильмов: %s<br />' % (sess_count, sess_kinohod_sale, sess_cinema, sess_films)
    
    return HttpResponse(str(log))
"""


@only_superuser
@never_cache
def statistics_main(request):
    today = datetime.date.today()
    date_to = today + datetime.timedelta(days=1)
    date_from = today - datetime.timedelta(days=8)
    statistics_data = Statistics.objects.filter(dtime__gte=date_from, dtime__lt=date_to, name='schedule').order_by('-dtime')
    
    sources = ImportSources.objects.all()
    sources_dict = {}
    for i in sources:
        sources_dict[i.code] = i
    
    statistics = {'cinemas': [], 'sessions': [], 'films': [], 'pie': []}
    last_dump_date = None
    
    if statistics_data.count():
        dates = []
        for i in statistics_data:
            dtime = i.dtime.date()
            if dtime not in dates:
                statistics['cinemas'].append([dtime, i.cinemas, i.cinemas_sale])
                statistics['sessions'].append([dtime, i.sessions, i.sessions_sale])
                statistics['films'].append([dtime, i.films])
                dates.append(dtime)
        
        for i in statistics_data[0].details.all():
            source = sources_dict.get(i.source)
            source = source.source.encode('utf-8') if source else i.source
                
            statistics['pie'].append([str(source), i.sessions])
        
        statistics['cinemas'].sort()
        statistics['sessions'].sort()
        statistics['films'].sort()

        last_dump_date = statistics_data[0].dtime.date()
    
    return render_to_response('api/statistics_main.html', {'statistics': statistics, 'statistics_data': statistics_data, 'last_dump_date': last_dump_date}, context_instance=RequestContext(request))


@never_cache
def switch_to_en(request):
    login_counter(request)
    lang = 'en'
    try:
        request.session['django_api_language'] = lang
    except:
        pass
    fileName = getApiDescrFileName(request, 'en')
    api_description = open(fileName,'r')
    description = api_description.read()
    api_description.close()
    return render_to_response('api/api_main.html', {'description': description, 'lang': lang}, context_instance=RequestContext(request)) 


@never_cache
def switch_to_ru(request):
    login_counter(request)
    lang = 'ru'
    try:
        request.session['django_api_language'] = lang
    except:
        pass
    fileName = getApiDescrFileName(request, 'ru')
    api_description = open(fileName,'r')
    description = api_description.read()
    api_description.close()
    return render_to_response('api/api_main.html', {'description': description, 'lang': lang}, context_instance=RequestContext(request)) 



@only_superuser
@never_cache
def set_api_cron(request):

#    return render_to_response('404.html', context_instance=RequestContext(request))

    cronLine = []
    strNum = 0
    with open(CRON_FILE, 'r') as infile:
        for line in infile:
            strNum += 1
            if 'cron_dump_' in line:
                enabled = True
                if line[0] == "#":
                    line = line.replace('#','')
                    enabled = False                    
                cronLine.append({'id': strNum, 'cmd': line, 'enabled': enabled})
    if request.POST:
#        NEW_CRON_FILE = CRON_FILE + '.new'
        chkList = [int(i) for i in request.POST.getlist('checker')]
        newcron = []
        strNum = 0
        with open(CRON_FILE, 'r') as infile:
             for newline in infile:
                 strNum +=1
                 if 'cron_dump_' in newline:
                     newline = newline.replace('#','')
                     if strNum in chkList:
                         newcron.append(newline)
                     else:
                         newcron.append("#%s" % newline)
                 else:
                      newcron.append(newline)
        with open(CRON_FILE, 'w') as outfile:
             for line in newcron:
                 outfile.write("%s" % line)        
        return HttpResponseRedirect(reverse('set_api_cron'))

    return render_to_response('api/api_cron.html', {'cronlines': cronLine}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def dump_visible(request, method=None):
    if method is None:
            raise Http404
    
    fileName = '{0}/{1}.json'.format(settings.API_CLIENTS_PATH, 'api_settings')
    with open(fileName, 'r') as infile:
        json_data = json.load(infile)

#    accessDict = {}
#    accessDict['name'] = str(method)
#    accessDict['cron'] = ''
#    accessDict['enable'] = '1'

    cronName = ''
    newState = False
    for x in json_data['method']:
        if x['name'] == str(method):
            x['enable'] = '0' if x['enable'] == '1' else '1'
            newState = True if x['enable'] == '1'else False
            cronName = x['cron'] 
    if cronName:
        method_status_change(str(cronName), newState)

    with open(fileName, 'w') as outfile:
        outfile.write(json.dumps(json_data))


#    with open(fileName, 'w') as outfile:
#        try:
#
#            json_data['method'].append(accessDict)
#
#            jsonData = json.dumps(json_data) 
#            outfile.write("%s\n" % jsonData)
#        except:
#            raise Http404


    login_counter(request)
    lang, request = getUserLang(request)
    fileName = getApiDescrFileName(request)
    api_description = open(fileName,'r')
    description = api_description.read()
    api_description.close()
    return render_to_response('api/api_main.html', {'description': description, 'lang': lang, 'dev': False}, context_instance=RequestContext(request)) 



@only_superuser
@never_cache
def api_users_2017(request):

    groups = {
        '1': {'id': '1', 'name': 'Суперюзеры', 'filter': {'user__is_superuser': True}}, 
        '2': {'id': '2', 'name': 'API клиенты', 'filter': {'user__groups': 1}}, 
        '3': {'id': '3', 'name': 'Aвторизованные', 'filter': 'exclude'},
        '4': {'id': '4', 'name': 'Остальные', 'filter': 'other'},
        '5': {'id': '5', 'name': 'Результат поиска', 'filter': {}},
    }
    
    group = None
    search = None
    date_now, date_past = (None, None)

    if request.POST:
        if 'search_btn' in request.POST:
            search = request.POST.get('user_search').strip()
            if 'date_btn' in request.POST:
                group = '4'
                date_now = request.POST.get('date_to', '').split('-')
                date_past = request.POST.get('date_from', '').split('-')
                if date_now and date_past:
                    date_now = datetime.datetime(int(date_now[2]), int(date_now[1]), int(date_now[0]), 23, 59, 59)
                    date_past = datetime.date(int(date_past[2]), int(date_past[1]), int(date_past[0]))
                else:
                    date_now, date_past = (None, None)
        else:
            group = request.POST.get('user_group')


    if not group and not search:
        search = request.session.get('filter_api_users_2__search')
        
    if search:
        group = '5'
    else:
        del groups['5']


    groups_list = groups.values()
    
    if not group:
        group = request.session.get('filter_api_users_2__group', groups_list[0]['id'])
        if not search and group == '5':
            group = groups_list[0]['id']
    
    
    filter = groups.get(group)

    filter = filter['filter']

    if search:
        users = Profile.objects.select_related('user').only('user', 'id').filter(Q(accounts__login__icontains = search) | Q(accounts__nickname__icontains = search) | Q(accounts__email__icontains = search) | Q(accounts__fullname__icontains = search) | Q(person__name__name__icontains = search, person__name__status=1, person__name__language__id=1)).distinct('user__id').order_by('user__id')[:100]
    else:
        if filter == 'exclude':
            users = Profile.objects.select_related('user').exclude(accounts=None).distinct('user__id').order_by('user__id')
        elif filter == 'other':
            if not date_past:
                date_now = datetime.datetime.now()
                date_past = date_now - datetime.timedelta(days=2)
            
            users = Profile.objects.select_related('user').filter(accounts=None, user__is_superuser=False, user__date_joined__gte=date_past, user__date_joined__lte=date_now).distinct('user__id').order_by('user__id')
        else:
            users = Profile.objects.select_related('user').filter(**filter).distinct('user__id').order_by('user__id')


    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, users, 15)
    

    peoples = set([i for i in p.object_list])

    groups = {}
    for i in list(Group.objects.filter(name='API', user__profile__in=peoples).values_list('user', flat=True)):
        groups[i] = True

    users_x = []
    for i in org_peoples(peoples):
        i['api_client'] = groups.get(i['id'], False)
        users_x.append(i)

    request.session['filter_api_users_2__group'] = group
    request.session['filter_api_users_2__search'] = search
    
    mlist_count = len(request.session.get('users_merge_list', []))
    
    tmplt = 'music/admin_users.html' if request.subdomain else 'api/user_controls_2017.html'
    
    return render_to_response(tmplt, {'groups': groups_list, 'group': group, 'p': p, 'page': page, 'search': search, 'users_x': users_x, 'date_now': date_now, 'date_past': date_past, 'mlist_count': mlist_count}, context_instance=RequestContext(request))



#@only_superuser
@never_cache
def api_users_2017_new(request):

    groups = {
        '1': {'id': '1', 'name': 'Суперюзеры', 'filter': {'user__is_superuser': True}}, 
        '2': {'id': '2', 'name': 'API клиенты', 'filter': {'user__groups': 1}}, 
        '3': {'id': '3', 'name': 'Aвторизованные', 'filter': 'exclude'},
        '4': {'id': '4', 'name': 'Остальные', 'filter': 'other'},
        '5': {'id': '5', 'name': 'Результат поиска', 'filter': {}},
    }
    
    group = None
    date_now, date_past = (None, None)


#by OFC76
    group = '2'

    groups_list = groups.values()
    
    
    filter = groups.get(group)

    filter = {'user__groups': 1}

    users = Profile.objects.select_related('user').filter(**filter).distinct('user__id').order_by('user__id')


    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
        
    p, page = pagi(page, users, 15)
    

    peoples = set([i for i in p.object_list])

    groups = {}
    for i in list(Group.objects.filter(name='API', user__profile__in=peoples).values_list('user', flat=True)):
        groups[i] = True

    users_x = []
    for i in org_peoples(peoples):
        i['api_client'] = groups.get(i['id'], False)
        i['is_active'] = apiuser_is_active(i['id'])
        i['key'] = apiuser_key(i['id'])
        try:
            request_list = APILogger.objects.filter(user__id=i['id']).order_by('-date')
            i['last'] = datetime.datetime.strftime(request_list[0].date, '%d-%m-%Y')
        except:
            i['last'] = 'None'

        users_x.append(i)

      
    tmplt = 'api/user_controls_2017_new.html'
    
    return render_to_response(tmplt, {'groups': groups_list, 'group': group, 'p': p, 'page': page, 'users_x': users_x, 'date_now': date_now, 'date_past': date_past}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def unblock_api_user(request, userid=''):
    id = int(userid)
    api_user = User.objects.get(pk=id)
    try:
        x = Profile.objects.select_related('user').filter(user__id=id).distinct('user__id').order_by('user__id')
        y = set([i for i in x])
        api_user_name = org_peoples(y)[0]['name']
    except:
        api_user_name = id

    json_data = json_api_user()

    known_users = [i['userid'] for i in json_data['access']]

    if userid in known_users:
        for x in json_data['access']:
            if x['userid'] == userid:
                api_user_is_active = x['user_is_active']
                api_user_is_active = True if api_user_is_active == '1' else False
                api_key = x['api_key']
                ip_start = x['ip_start']
                ip_end = x['ip_end']
    else:
        api_key = '{0}-{1}'.format(userid, randint(10**9, (10**10)-1))
        ip_start = '0.0.0.0'
        ip_end = '255.255.255.255'
        api_user_is_active = False
    tmplt = 'api/user_api_access.html'
    return render_to_response(tmplt, {'userid': userid, 'ip_start': ip_start, 'ip_end': ip_end, 'api_user_is_active': api_user_is_active, 'api_key' : api_key, 'api_user' : api_user, 'api_user_name': api_user_name}, context_instance=RequestContext(request))



@only_superuser
@never_cache
def api_user_edit(request):

    if request.POST:
        id = request.POST.get("userid", "")
        user_is_active = request.POST.get("user_is_active", "")
        user_is_active = '1' if user_is_active == 'on' else '0'

        api_key = request.POST.get("api_key", "")
        if api_key == "":
            api_key = '{0}-{1}'.format(id, randint(10**9, (10**10)-1))   
        ip_start = request.POST.get("ip_start", "")
        ip_end = request.POST.get("ip_end", "")


        if not check_api_ip_range(ip_start, ip_end):
            raise Http404

        json_data = json_api_user()

        known_users = [i['userid'] for i in json_data['access']]

        if id in known_users:
            for x in json_data['access']:
                if x['userid'] == id:
                    x['user_is_active'] = user_is_active
                    x['api_key'] = api_key
                    x['ip_start'] = ip_start
                    x['ip_end'] = ip_end
        else:
            accessDict = {}
            accessDict['userid'] = id
            accessDict['user_is_active'] = user_is_active
            accessDict['api_key'] = api_key
            accessDict['ip_start'] = ip_start
            accessDict['ip_end'] = ip_end
#            accessArr = []
#            accessArr.append(accessDict)
#            json_data['access'] = accessArr
            json_data['access'].append(accessDict)

        fileName = '{0}/{1}.json'.format(settings.API_CLIENTS_PATH, 'api_client')
        with open(fileName, 'w') as outfile:
            outfile.write(json.dumps(json_data))
    
    return HttpResponseRedirect(reverse('api_users_2017_new'))
#    raise Http404



@only_superuser
@never_cache 
def get_user_request_list2017(request, rows=100):
    '''
    Вывод лога обращений к API
    '''
    request_list = APILogger.objects.all().order_by('-date')[:rows]
    result = {'status': 'request_list'}
    p = pagination(request, request_list, 250)
    return render_to_response('api/api_calls_log2017.html', {'result': result, 'content': request_list, 'p': p}, context_instance=RequestContext(request))


@only_superuser
@never_cache 
def get_one_user_request_list(request, id='7518740', rows=500):
    '''
    Вывод лога обращений к API
    '''
    request_list = APILogger.objects.filter(user__id=id).order_by('-date')[:rows]
    result = {'status': 'request_list'}
    p = pagination(request, request_list, 250)
    return render_to_response('api/api_one_calls_log.html', {'result': result, 'content': request_list, 'p': p, 'userid': id}, context_instance=RequestContext(request))

