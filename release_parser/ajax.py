# -*- coding: utf-8 -*- 
import datetime
import operator

from django.utils import simplejson, translation
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.conf import settings
from django.template.defaultfilters import date as tmp_date
from django.core.cache import cache

from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup

from base.models import *
from base.models_dic import *
from api.models import *
from api.views import get_film_data
from api.func import age_limits, get_client_ip, get_country_by_ip
from film.ajax import get_film_details_data
from release_parser.func import get_imdb_id, actions_logger
from user_registration.ajax import get_subscription_status, add_email_to_exist_profile
from movie_online.views import get_film_player
from movie_online.IR import check_int_rates


@dajaxice_register
def get_data(request, value, kid, type, all_data):
    try:
        if request.user.is_superuser:
            if type == 'film':
                names = value.split(' @ ')
                if kid == '*' and len(names) > 1:
                    myfilter1 = {}
                    myfilter2 = {}
                    if names[0] != '*':
                        myfilter1 = {'slug__icontains': names[0].encode('utf-8'), 'status': 1}
                    if names[1] != '*':
                        myfilter2 = {'slug__icontains': names[1].encode('utf-8'), 'status': 1}

                    film = FilmsName.objects.using('afisha').filter(Q(**myfilter1) | Q(**myfilter2)).values('type', 'status', 'name', 'film_id__year', 'film_id__idalldvd')
                else:
                    film = FilmsName.objects.using('afisha').filter(name__icontains=value, status=1).values('type', 'status', 'name', 'film_id__year', 'film_id__idalldvd', 'film_id__id')

                films = {}
                for i in film:
                    if not films.get(i['film_id__id']):
                        films[i['film_id__id']] = {'id': i['film_id__id'], 'ru': '', 'en': '', 'year': i['film_id__year'], 'imdb': i['film_id__idalldvd']}

                    if i['type'] == 1:
                        films[i['film_id__id']]['en'] = i['name']
                    elif i['type'] == 2:
                        films[i['film_id__id']]['ru'] = i['name']

                f = {}
                for i in sorted(films.values(), key=operator.itemgetter('year')):
                    name = i['ru'] if i['ru'] else i['en']
                    f[i['id']] = '%s (year: %s imdb: %s)' % (name, i['year'], i['imdb'])

                return simplejson.dumps({
                    'status': 'True',
                    'content': f
                })
            elif type == 'city':
                city = City.objects.select_related('country').filter(name__name__icontains=value).distinct('pk')
                counter = city.count()
                if counter:
                    f = {}
                    for i in city:
                        for j in i.name.all():
                            if j.status == 1:
                                name = j.name
                        country_name = i.country.name if i.country else None
                        f[i.id] = '%s (%s)' % (name, country_name)
                    return simplejson.dumps({
                        'status': 'True',
                        'content': f
                    })
            elif type == 'cinema':
                city_kid = kid.split(' @ ')
                city_kid = city_kid[2]
                myfilter = {}
                if not all_data:
                    myfilter = {'city__kid': city_kid}
                cinema = Cinema.objects.select_related('city').filter(name__name__icontains=value).filter(**myfilter).distinct('pk')
                counter = cinema.count()
                if counter:
                    f = {}
                    for i in cinema:
                        for j in i.name.all():
                            if j.status == 1:
                                name = j.name
                        for j in i.city.name.all():
                            if j.status == 1:
                                city = j.name
                        f[i.code] = '%s @ %s' % (name, city)
                    return simplejson.dumps({
                        'status': 'True',
                        'content': f
                    })
            elif type == 'hall':
                cinema_kid = kid.split(' @ ')
                cinema_kid = cinema_kid[3]
                myfilter = {}
                if not all_data:
                    myfilter = {'cinema__code': cinema_kid}
                hall = Hall.objects.select_related('cinema').filter(name__name__icontains=value).filter(**myfilter).distinct('pk')
                counter = hall.count()
                if counter:
                    f = {}
                    for i in hall:
                        for j in i.name.all():
                            if j.status == 1:
                                name = j.name
                        for j in i.cinema.name.all():
                            if j.status == 1:
                                cinema = j.name
                        for j in i.cinema.city.name.all():
                            if j.status == 1:
                                city = j.name
                        f[i.id] = '%s @ %s @ %s' % (name, cinema, city)
                    return simplejson.dumps({
                        'status': 'True',
                        'content': f
                    })
            elif type == 'person':
                person = Person.objects.filter(name__name__icontains=value).exclude(kid=None).distinct('pk')
                counter = person.count()
                if counter:
                    f = {}
                    for i in person:
                        name_ru = ''
                        name_en = ''
                        for j in i.name.all():
                            if j.status == 1:
                                if j.language.name == u'Английский':
                                    name_en = j.name
                                elif j.language.name == u'Русский':
                                    name_ru = j.name

                        f[i.kid] = '%s / %s' % (name_ru, name_en)
                    return simplejson.dumps({
                        'status': 'True',
                        'content': f
                    })
            elif type == 'country':
                country = Country.objects.filter(Q(name__icontains=value) | Q(name_en__icontains=value)).distinct('pk')
                counter = country.count()
                if counter:
                    f = {}
                    for i in country:
                        f[i.kid] = '%s / %s' % (i.name, i.name_en)
                    return simplejson.dumps({
                        'status': 'True',
                        'content': f
                    })
        return simplejson.dumps({'status': 'False'})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def get_film_schedule(request, fkid, ckid):
    try:
        now = datetime.datetime.now()
        today = datetime.date.today()

        time_now = now.time()

        next_month = today + datetime.timedelta(days=14)

        sch = SourceSchedules.objects.select_related('film', 'cinema', 'cinema__cinema', 'cinema__city', 'source_obj').filter(dtime__gte=today, dtime__lte=next_month, cinema__cinema__id=ckid, film__kid=fkid).exclude(film__source_id=0)

        kinoinfo_dict = {}
        time_links = {}
        for i in sch:
            d = tmp_date(i.dtime.date(), 'd b').encode('utf-8')
            t = i.dtime.time()

            if i.extra:
                key = '%s%s' % (d, t)
                if not time_links.get(key):
                    time_links[key] = i

            if kinoinfo_dict.get(d):
                kinoinfo_dict[d]['times'].append(t)
            else:
                kinoinfo_dict[d] = {'date': i.dtime.date(), 'times': [t]}

        kinohod_tickets = ''
        rambler_tickets = ''

        if not kinohod_tickets:
            cinema = Cinema.objects.select_related('city').get(pk=ckid)

            sch = list(SourceSchedules.objects.filter(dtime__gte=today, dtime__lte=next_month, cinema__city__city=cinema.city, film__kid=fkid, source_obj__url__in=('http://kinohod.ru/', 'http://www.rambler.ru/'), sale=True).exclude(film__source_id=0).distinct('source_obj').values('film__name', 'cinema__city__name', 'film__source_id', 'cinema__city__source_id', 'source_obj__url'))

            for i in sch:
                if i['source_obj__url'] == 'http://kinohod.ru/':
                    #kinohod_tickets = u'<a href="http://kinohod.ru/" class="kh_boxoffice" ticket movie="%s" city="%s"></a>' % (i['film__name'], i['cinema__city__name'])
                    kinohod_tickets = u'<a href="http://kinohod.ru/movie/%s/" class="kh_boxoffice" kh:ticket kh:widget="movie" kh:id="%s" kh:city="%s"><span>Билеты</span></a>' % (
                        i['film__source_id'], i['film__source_id'], i['cinema__city__name'])
                else:
                    rambler_tickets = u'<rb:movie key="%s" movieName="" cityName="" movieID="%s" cityID="%s" xmlns:rb="http://kassa.rambler.ru"></rb:movie>' % (settings.RAMBLER_TICKET_KEY, i['film__source_id'], i['cinema__city__source_id'])

        kinohod_key = settings.KINOHOD_APIKEY_CLIENT if kinohod_tickets else ''

        schedules = []
        for k, v in kinoinfo_dict.iteritems():
            times = ''
            for t in sorted(set(v['times'])):
                key = '%s%s' % (k, t)
                link = time_links.get(key)
                if times:
                    times += ', '

                if today == v['date'] and time_now > t:
                    link = None

                if link:
                    #times += "<a href='%s'>%s</a>" % (link.extra, t.strftime("%H:%M"))
                    times += "<a id='%s' title='Купить билет' class='ticket_widget'>%s</a>" % (link.id, t.strftime("%H:%M"))
                else:
                    times += t.strftime("%H:%M")

            schedules.append({'dates': str(k), 'times': times, 'date': str(v['date'])})

        schedules = sorted(schedules, key=operator.itemgetter('date'))
        return simplejson.dumps({
            'status': 'True',
            'schedules': schedules,
            'kinohod_tickets': kinohod_tickets,
            'kinohod_key': kinohod_key,
            'rambler_tickets': rambler_tickets,
        })

    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def buy_ticket(request, id):
    try:
        try:
            sch = SourceSchedules.objects.select_related('film', 'cinema', 'cinema__city').get(pk=id)
            link = sch.extra

            if request.user.is_authenticated():

                ip = get_client_ip(request)

                if ip == '127.0.0.1':
                    ip = '91.224.86.255' # для локальной машины

                profile = request.user.get_profile()

                country = get_country_by_ip(ip)

                BuyTicketStatistic.objects.create(
                    profile=profile,
                    country=country,
                    session=sch,
                )

                # Оплачиваемое действие

                #current_site = RequestContext(request).get('current_site')
                #if current_site.domain == 'kinoafisha.in.ua':
                try:
                    action = ActionsPriceList.objects.get(pk=3, allow=True)
                    extra = '%s, %s, %s, %s' % (sch.dtime.strftime("%d.%m.%Y %H:%M"), country.name.encode('utf-8'), sch.cinema.city.name.encode('utf-8'), sch.cinema.name.encode('utf-8'))
                    PaidActions.objects.create(
                        action=action,
                        profile=profile,
                        object=sch.film.kid,
                        extra=extra,
                    )
                except ActionsPriceList.DoesNotExist:
                    pass

        except SourceSchedules.DoesNotExist:
            link = None

        return simplejson.dumps({
            'result': link,
        })

    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def save_city_choice(request, city):
    try:
        city = City.objects.get(pk=city)
    except City.DoesNotExist:
        city = None
    if city and city.country:
        user = request.user.get_profile().person
        user.city = city
        user.country = city.country
        user.save()


def get_film_likes(kid):
    if isinstance(kid, list):
        return_one = False
    else:
        return_one = True
        kid = (kid,)

    data = {}
    for i in kid:
        data[int(i)] = {
            'count_likes': 0,
            'count_dislikes': 0,
            'likes_cinema': 0,
            'likes_home': 0,
            'likes_recommend': 0,
            'dislikes_seen': 0,
            'dislikes_recommend': 0,
        }

    for i in Likes.objects.filter(film__in=kid):
        if i.evaluation == 1:
            data[i.film]['likes_cinema'] += 1
        elif i.evaluation == 2:
            data[i.film]['likes_home'] += 1
        elif i.evaluation == 3:
            data[i.film]['likes_recommend'] += 1
        elif i.evaluation == 4:
            data[i.film]['dislikes_seen'] += 1
        elif i.evaluation == 5:
            data[i.film]['dislikes_recommend'] += 1

    for i in data.keys():
        data[i]['count_likes'] = data[i]['likes_cinema'] + data[i]['likes_home'] + data[i]['likes_recommend']
        data[i]['count_dislikes'] = data[i]['dislikes_seen'] + data[i]['dislikes_recommend']

    if return_one:
        return data.values()[0]
    else:
        return data


@never_cache
@dajaxice_register
def likes(request, take_eval, kid, email=False, quality=''):
    try:
        from user_registration.views import get_usercard

        evals = {
            u'Хочу смотреть в кинотеатре': 1,
            u'Хочу посмотреть дома': 2,
            u'Смотрел - рекомендую': 3,
            u'Не буду смотреть': 4,
            u'Смотрел - не рекомендую': 5,
        }

        eval_film = evals.get(take_eval)
        if eval_film:
            card = get_usercard(request.user)
            profile = card['profile']
            next = True
            id = None

            if eval_film in (1, 2):
                if eval_film == 1 and not card['city'] or not card['email']:
                    next = False
                elif eval_film == 2 and not card['email']:
                    next = False
            elif eval_film == 3:
                id = 1
            elif eval_film == 4:
                id = 18
            elif eval_film == 5:
                id = 17

            if email and email.strip() and not card['email']:
                email = email.strip()

                add_to_profile = add_email_to_exist_profile(email, profile)
                if add_to_profile:
                    if not profile.user.email:
                        profile.user.email = email
                        profile.user.save()
                    next = True
                else:
                    html = u'<div>Такой E-Mail уже существует в системе, <a href="/user/login/">авторизуйтесь</a> используя его.</div>'
                    return simplejson.dumps({
                        'status': False,
                        'email_block': html,
                    })

            act = None
            get_torrent = False
            try:
                like = Likes.objects.get(personinterface=profile.personinterface, film=kid)
                if like.evaluation != eval_film:
                    act = '2'
                    like.evaluation = eval_film
                    like.save()
                    get_torrent = True
            except (Likes.DoesNotExist, Likes.MultipleObjectsReturned):
                Likes.objects.filter(personinterface=profile.personinterface, film=kid).delete()
                like = Likes.objects.create(evaluation=eval_film, film=kid)
                profile.personinterface.likes.add(like)
                act = '1'
                get_torrent = True

            if eval_film == 2:
                if not quality:
                    quality = '1'

                interface = request.profile.personinterface
                price = 100
                if interface.money >= price:
                    act = None

                    st, st_created = SubscriptionTopics.objects.get_or_create(
                        profile=profile,
                        kid=kid,
                        defaults={
                            'profile': profile,
                            'kid': kid,
                            'quality': quality,
                        })

                    if not st_created and not st.notified and st.quality != quality:
                        st.quality = quality
                        st.save()
                    '''
                    if get_torrent:
                        try:
                            torrent = Torrents.objects.get(film=kid)
                            TorrentsUsers.objects.get_or_create(
                                torrent = torrent,
                                profile = profile,
                                defaults = {
                                    'torrent': torrent,
                                    'profile': profile,
                                })
                        except Torrents.DoesNotExist:
                            pass
                    '''

            likes = get_film_likes(kid)
            likes['id'] = kid
            likes['cancel'] = False
            likes['status'] = True

            # если юзер выбрал "Cмотрел - рекомендую"/"Не буду смотреть"/"Не рекомендую", то удаляю подписки
            if eval_film in (3, 4, 5):
                subr = get_subscription_status(kid, profile)
                if subr:
                    subr.delete()
                SubscriptionTopics.objects.filter(profile=profile, kid=kid).delete()
                likes['cancel'] = True

            if not next:
                html_add = u'в кинотеатре' if eval_film == 1 else u'в сети'

                html = u'''
                    <div>
                    <p id="email_likes_note">Если Вы хотите получить уведомление о выходе фильма %s на свой мейл,
                    введите его сюда</p><br />
                    <input type="text" id="email_likes" placeholder="E-Mail" />
                    <input type="button" id="email_likes_btn" value="ОК" /> <span id="email_likes_warnign"></span>
                    <input type="hidden" id="film_likes" value="%s" />
                    <input type="hidden" id="tquality" value="%s" />
                    <input type="hidden" id="eval_likes" value="%s" />
                    </div>
                    ''' % (html_add, kid, quality, take_eval)

                likes['email_block'] = html

            if id:
                actions_logger(id, kid, profile, act)

                action = ActionsPriceList.objects.get(pk=id, allow=True)
                paid = PaidActions.objects.get(
                    action=action,
                    profile=profile,
                    object=kid,
                    act=act
                )

                paid.number = 1
                paid.save()

                interface = profile.personinterface
                if paid.act == '1':
                    price = action.price
                elif paid.act == '2':
                    price = action.price_edit
                elif paid.act == '3':
                    price = action.price_delete

                interface.money += float(price)
                interface.save()

            return simplejson.dumps(likes)

    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def get_film(request, id, val=None):
    try:
        mobile = False
        if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
            mobile = True

        current_language = translation.get_language()
        current_site = request.current_site

        is_cached = cache.get('get_film__%s' % id, 'nocaсhed')

        if is_cached == 'nocaсhed': # объекта нет в кэше, значит создаем
            film = get_film_data(id)
            if not film:
                return simplejson.dumps({'status': 'False'})
            cache.set('get_film__%s' % id, film, 60 * 60 * 4)
        else:
            film = is_cached

        film = get_film_data(id)

        if film:
            subscriptions_accept = True
            description = ''
            poster = ''
            uk_name_person = []
            name = ''
            okino = False
            if current_site.domain == 'kinoafisha.in.ua':
                try:
                    ReleasesRelations.objects.get(film_kid=id, rel_double=False, rel_ignore=False)
                except ReleasesRelations.DoesNotExist:
                    subscriptions_accept = False
                except ReleasesRelations.MultipleObjectsReturned:
                    pass

                if current_language == 'uk':
                    actors_ids = [i['id'] for i in film['actors']]
                    uk_name_person = list(NamePerson.objects.filter(person__kid__in=actors_ids, status=1, language__name='Украинский').values('person__kid', 'name'))

                    try:
                        source_film = SourceFilms.objects.select_related('source_obj').filter(kid=id, source_obj__url='http://kino-teatr.ua/')[0]
                    except IndexError:
                        try:
                            source_film = SourceFilms.objects.select_related('source_obj').filter(kid=id, source_obj__url='http://www.okino.ua/')[0]
                        except IndexError:
                            try:
                                source_film = Okinoua.objects.filter(kid=id)[0]
                                okino = True
                            except IndexError:
                                source_film = None

                    if source_film:
                        if okino:
                            name = source_film.name_ua
                        else:
                            name = source_film.name
                            if source_film.source_obj.url == 'http://kino-teatr.ua/' and source_film.text:
                                description = source_film.text.encode('utf-8')
                                if description == 'Проект оголошений':
                                    description = ''

                    try:
                        poster = UkrainePosters.objects.filter(kid=id)[0].poster
                        poster = str(poster).split('/')[-1:][0]
                        poster = '/upload/films/posters/uk/%s' % poster
                    except IndexError:
                        pass

            if not poster:
                poster = film['posters'].replace('_small', '') if film['posters'] else ''

            posters = u'<a class="fancybox" href="%s"><img src="%s" /></a>' % (poster, poster) if poster else ''

            slides = []
            for ind, i in enumerate(film['slides']):
                poster_path = u'<div class="slide"><a class="fancybox" rel="group" href="%s"><img class="fancy_slide" src="%s" /></a></div>' % (i.replace('_small',''), i)
                slides.append(poster_path)
                if ind == 2:
                    break

            slides_count = len(slides)
            trailers_count = len(film['trailers'])

            range_to = 3 - slides_count
            for i in range(range_to):
                slides.append('<div class="slide">Нет слайда</div>')

            trailer = '<div class="trailer">Нет трейлера</div>'
            for i in film['trailers']:
                trailer = '<div class="trailer">%s</div>' % i['code']
                break

            imdb_rate = film['imdb_rate'] if film['imdb_num'] else 0
            imdb_vote = film['imdb_num'] if film['imdb_num'] else 0
            afisha_rate_tag = u'<b>Оценки посетителей Киноафиши:</b> %s (%s голоса)' % (film['afisha_rate'], film['afisha_num']) if film['afisha_num'] else ''
            comment_tag = u'<b>Примечания:</b> %s' % film['comment'].replace('&#034;', '"') if film['comment'] else ''
            limit = age_limits(film['limits']) if film['limits'] else ''

            if not description:
                description = u'%s' % film['description'] if film['description'] else ''

            description_cut = ''
            if description:
                description_cut = BeautifulSoup(description, from_encoding='utf-8').text.strip().split()[:30]
                description_cut = ' '.join(description_cut)
                description_cut = '%s ...' % description_cut.rstrip(u'…').rstrip(u'...')
                description += '<br /><br />'

            runtime_tag = u'%s' % film['runtime'] if film['runtime'] else ''

            person_ids = [i['id'] for i in film['directors']]
            person_ids += [i['id'] for i in film['actors']]

            extresids = {}
            extresid = Objxres.objects.using('afisha').filter(objtypeid=302, objpkvalue__in=set(person_ids)).only('extresid', 'objpkvalue')
            for i in extresid:
                extresids[int(i.extresid_id)] = int(i.objpkvalue)

            person_photos = {}
            photos = Extres.objects.using('afisha').filter(extresid__in=extresids.keys(), filename__icontains='small', info__icontains='*t')

            for i in photos:
                pkid = extresids.get(i.extresid)
                if pkid:
                    person_photos[pkid] = 'http://persons.nodomain.kinoafisha.ru/%s' % i.filename

            directors_tag = u''
            directors_top_line = u''
            for v in film['directors']:
                pphoto = person_photos.get(int(v['id']), '')
                if pphoto:
                    if mobile:
                        pphoto = '<img src="%s" id="img_under" />' % pphoto
                    else:
                        pphoto = '<img src="%s" />' % pphoto

                if directors_tag:
                    directors_tag += u', '
                try:
                    director_afisha_link = u'/person/%s/' % v['id']
                    director_afisha_link = u'<a href="%s">%s</a>' % (director_afisha_link, v['name'][0]['name'])

                    #director_imdb = get_imdb_id(v['imdb'])
                    #director_imdb_link = u'http://www.imdb.com/name/nm%s/' % director_imdb
                    #director_imdb_link = u'<a href="%s" target="_blank">%s</a>' % (director_imdb_link, v['name'][1]['name'])
                    director_imdb_link = u'<span class="small_star">%s</span>' % v['name'][1]['name']

                    directors_tag += u'%s <span id="person_imdb_link">(%s)</span>' % (director_afisha_link, director_imdb_link)
                except IndexError:
                    director_afisha_link = u'/person/%s/' % v['id']
                    director_afisha_link = u'<a href="%s">%s</a>' % (director_afisha_link, v['name'][0]['name'])
                    directors_tag += u'%s' % director_afisha_link

                parental_name = NamePerson.objects.filter(person__kid=v['id'], status=3, language__id=1).order_by('-id')
                parental_name = parental_name[0] if parental_name else v['name'][0]['name']
                if directors_top_line:
                    directors_top_line += u' и '
                directors_top_line += u'<a href="/person/%s/">%s%s</a>' % (v['id'], pphoto, parental_name)

            if directors_tag:
                directors_tag = u'<b>Режиссер:</b> %s<br /><br />' % directors_tag

            other_person_tag = u''
            '''
            for v in film['other_person']:
                if other_person_tag:
                    other_person_tag += u', '
 
                try:
                    other_person_afisha_link = u'/person/%s/' % v['id']
                    other_person_afisha_link = u'<a href="%s">%s</a>' % (other_person_afisha_link, v['name'][0]['name'])
                    other_person_imdb_link = u'<span class="small_star">%s</span>' % v['name'][1]['name']
                    other_person_tag += u'%s <span id="person_imdb_link">(%s)</span> - %s' % (other_person_afisha_link, other_person_imdb_link, v['type_name'])
                except IndexError:
                    other_person_afisha_link = u'/person/%s/' % v['id']
                    other_person_afisha_link = u'<a href="%s">%s</a> - %s' % (other_person_afisha_link, v['name'][0]['name'], v['type_name'])
                    other_person_tag += u'%s' % other_person_afisha_link

            if other_person_tag:
                other_person_tag = u'<b>Прочие создатели:</b> %s' % other_person_tag
            '''

            countries_tag = u''
            for i in film['countries'].values():
                if countries_tag:
                    countries_tag += u' / '
                try:
                    countries_tag += u'%s' % i
                except UnicodeDecodeError:
                    countries_tag += u'%s' % i.decode('utf-8')

            genres_tag = u''
            for i in film['genres'].values():
                if genres_tag:
                    genres_tag += u' / '
                try:
                    genres_tag += u'%s' % i
                except UnicodeDecodeError:
                    genres_tag += u'%s' % i.decode('utf-8')

            distributors_tag = u''
            for i in film['distributors']:
                if distributors_tag:
                    distributors_tag += u', '
                try:
                    distributors_tag += u'%s' % i['name']
                except UnicodeDecodeError:
                    distributors_tag += u'%s' % i['name'].decode('utf-8')

            if mobile:
                if distributors_tag:
                    distributors_tag = u'<div style="margin-bottom: 10px;"><b>Дистрибьютор:</b> %s</div>' % distributors_tag
                else:
                    distributors_tag = u''
            else:
                if distributors_tag:
                    distributors_tag = u'<span class="nolink" title="%s">дистрибьютор</span>' % distributors_tag
                else:
                    distributors_tag = u'<span style="color: #666;">дистрибьютор</span>'

            voices = [int(i['id']) for i in film['other_person'] if int(i['type'] == 5)]

            actors_top_line = u''
            actors_tag = u''
            actors_count = 0
            for v in film['actors']:
                if v['id'] not in voices:
                    name_person = v['name'][0]['name']

                    pphoto = person_photos.get(int(v['id']), '')
                    if pphoto:
                        if mobile:
                            pphoto = '<img src="%s" id="img_under" />' % pphoto
                        else:
                            pphoto = '<img src="%s" />' % pphoto

                    for i in uk_name_person:
                        if i['person__kid'] == v['id']:
                            name_person = i['name']

                    if actors_tag:
                        actors_tag += u', '
                    try:
                        actor_afisha_link = u'/person/%s/' % v['id']
                        actor_afisha_link = u'<a href="%s">%s</a>' % (actor_afisha_link, name_person)

                        #actor_imdb = get_imdb_id(v['imdb'])
                        #actor_imdb_link = u'http://www.imdb.com/name/nm%s/' % actor_imdb
                        #actor_imdb_link = u'<a href="%s" target="_blank">%s</a>' % (actor_imdb_link, v['name'][1]['name'])
                        actor_imdb_link = u'<span class="small_star">%s</span>' % v['name'][1]['name']

                        actors_tag += u'%s <span id="actor_imdb_link">(%s)</span>' % (actor_afisha_link, actor_imdb_link)
                    except IndexError:
                        actor_afisha_link = u'/person/%s/' % v['id']
                        actor_afisha_link = u'<a href="%s">%s</a>' % (actor_afisha_link, name_person)
                        actors_tag += u'%s' % actor_afisha_link

                    actors_count += 1
                    if actors_count < 4:
                        if actors_top_line:
                            actors_top_line += ', '
                        actors_top_line += u'<a href="/person/%s/">%s%s</a>' % (v['id'], pphoto, name_person)

            if actors_tag:
                actors_tag = u'<b>Звезды:</b> %s<br /><br />' % actors_tag

            top_line = u''
            if actors_top_line:
                top_line = u'%s в фильме ' % actors_top_line

            if directors_top_line:
                if not actors_top_line:
                    top_line = u'Фильм '
                top_line += directors_top_line

            name_en = ''
            if not name:
                name = film['name_ru']
            if request.subdomain == 'm':
                name_ru_url = 'http://m.kinoinfo.ru/film/%s/' % id
            else:
                name_ru_url = 'http://kinoinfo.ru/film/%s/' % id
            name_ru = u'<a href="%s">%s</a>' % (name_ru_url, name)
            if film['idimdb']:
                if mobile:
                    name_en = u'<a href="http://www.imdb.com/title/tt%s" target="_blank" style="display: inline-block; margin-top: 10px;">%s</a>' % (film['idimdb'], film['name_en'])
                else:
                    name_en = u'<a href="http://www.imdb.com/title/tt%s" target="_blank">%s</a>' % (film['idimdb'], film['name_en'])

            details_tag = u''
            if countries_tag or runtime_tag or genres_tag:
                if countries_tag:
                    details_tag += countries_tag
                if genres_tag:
                    if details_tag:
                        details_tag += u', '
                    details_tag += genres_tag
                if runtime_tag:
                    if details_tag:
                        details_tag += u', '
                    details_tag += u'%s мин.' % runtime_tag
                details_tag = '%s' % details_tag

            subr = False
            if request.user.is_authenticated():
                subr = get_subscription_status(id, request.user.get_profile())
                if subr:
                    subr = True

            likes = get_film_likes(id)
            
            player = False
            if val:
                player, psource = get_film_player(id, mobile)
                if not mobile:
                    if player and request.user.is_superuser:
                        player = u'%s <div><input type="button" value="Удалить этот плеер" class="remove_online_player" id="%s__%s"/></div>' % (player, id, psource)

            rate, show_ir, show_imdb, rotten = check_int_rates(id)

            rate_text = 'Репутация фильма: '
            m_rate = ''

            if show_imdb or rotten or show_ir:
                if show_imdb:
                    rate_text += 'IMDb - %s' % show_imdb
                    if mobile:
                        m_rate += '<div>Рейтинг IMDb: %s</div>' % show_imdb
                if rotten:
                    rate_text += ' / RottenTomatoes - %s' % rotten
                    if mobile:
                        m_rate += '<div>Рейтинг RottenTomatoes: %s</div>' % rotten
                if show_ir:
                    rate_text += ' / Киномэтры - %s' % show_ir
                    if mobile:
                        m_rate += '<div>Рейтинг от Киномэтров: %s</div>' % show_ir
            else:
                rate_text += 'нет'

            if rate == 0:
                rate = '?'
                
            rate_color = ''
            if rate == 5:
                rate_color = 'border-left: 20px solid rgba(60, 179, 113, 0.8);'
            elif rate == 4:
                rate_color = 'border-left: 20px solid rgba(126, 192, 238, 0.8);'
            elif rate == 3:
                rate_color = 'border-left: 20px solid rgba(255, 218, 185, 0.8);'
            elif rate == 2:
                rate_color = 'border-left: 20px solid rgba(238, 130, 238, 0.8);'
            
            details_data = get_film_details_data(id, mobile)

            if film['release']:
                if mobile:
                    releases = u'<div style="margin-bottom: 10px;"><b>Дата релиза:</b> %s</div>' % tmp_date(film['release'], "d E Y")
                else:
                    releases = u'<span class="nolink" title="%s">дата релиза</span>' % tmp_date(film['release'], "d E Y")
            else:
                if mobile:
                    releases = ''
                if not mobile:
                    releases = u'<span style="color: #666;" >дата релиза</span>'

            subscribe_me = ''
            #if request.user.is_superuser:
            #    subscribe_me = '<br />Ссылка для подписки "Хочу смотреть в кино":\
            #    <br />http://kinoinfo.ru/releases/%s/?subscribe' % id

            likes.update(details_data)
            
            likes.update({
                'status': True,
                'player': player,
                'name_ru': name_ru,
                'name_en': name_en,
                'year': film['year'],
                'afisha_rate': afisha_rate_tag,
                'imdb_rate': imdb_rate,
                'imdb_vote': imdb_vote,
                'comment': comment_tag,
                'description': description,
                'description_cut': description_cut,
                'limits': limit,
                'runtime': runtime_tag,
                'directors': directors_tag,
                'actors': actors_tag,
                'other_person': other_person_tag,
                'top_line': top_line,
                'posters': posters,
                'slides': slides,
                'slides_count': slides_count,
                'trailers': trailer,
                'trailers_count': trailers_count,
                'countries': countries_tag,
                'details': details_tag,
                'distributors': distributors_tag,
                'id': id,
                'subscription': subr,
                'subscriptions_accept': subscriptions_accept,
                'genre': genres_tag,
                'rate': rate,
                'rate_color': rate_color,
                'rate_text': rate_text,
                'subscribe_me': subscribe_me,
                'release': releases,
                'm_rate': m_rate,
            })

            return simplejson.dumps(likes)
        else:
            return simplejson.dumps({'status': 'False'})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))
