# -*- coding: utf-8 -*- 
import datetime
import operator

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django import db
from django.contrib.humanize.templatetags.humanize import intcomma
from django.template.defaultfilters import date as tmp_date
from django.core.cache import cache
from django.utils.html import escape
from django.db.models import Q

from bs4 import BeautifulSoup
from dajaxice.decorators import dajaxice_register

from api.views import create_dump_file
from api.models import *
from base.models import *
from kinoinfo_folder.func import low, capit, uppercase, del_separator
from user_registration.func import org_peoples, is_film_editor
from release_parser.imdb import imdb_searching, get_imdb_data
from release_parser.myhit import myhit_searching
from release_parser.func import actions_logger
from film.views import films_name_create
from movie_online.IR import integral_rate
from news.views import create_news


@dajaxice_register
def get_film_genres(request, id, arr):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        try:
            film = Film.objects.using('afisha').only("genre1", "genre2", "genre3").get(pk=id)
        except Film.DoesNotExist:
            return simplejson.dumps({'status': False})
        
        film_genres = []
        film_genres_txt = ''
        
        for i in arr:
            name, gid = low(i).split(';')
            genre = AfishaGenre.objects.using('afisha').get(name=name) if name else 0
            act = None
            
            if name:
                if film_genres_txt:
                    film_genres_txt += ' / '
                film_genres_txt += name

            # есть ид, т.е. либо изменяем либо удаляем
            if gid:
                if film.genre1_id == int(gid):
                    genre_id = gid
                    if film.genre1 != genre:
                        if genre:
                            act = '2'
                            film.genre1 = genre
                            genre_id = genre.id
                        else:
                            act = '3'
                            film.genre1_id = genre
                            genre_id = ''
                            
                    film_genres.append({'id': genre_id, 'name': name})
                elif film.genre2_id == int(gid):
                    genre_id = gid
                    if film.genre2 != genre:
                        if genre:
                            act = '2'
                            film.genre2 = genre
                            genre_id = genre.id
                        else:
                            act = '3'
                            film.genre2_id = genre
                            genre_id = ''
                    film_genres.append({'id': genre_id, 'name': name})
                    
                elif film.genre3_id == int(gid):
                    genre_id = gid
                    if film.genre3 != genre:
                        if genre:
                            act = '2'
                            film.genre3 = genre
                            genre_id = genre.id
                        else:
                            act = '3'
                            film.genre3_id = genre
                            genre_id = ''
                    film_genres.append({'id': genre_id, 'name': name})
                    
            # добавляем
            else:
                # если не пустое значение
                if genre:
                    if not film.genre1_id:
                        film.genre1 = genre
                    else:
                        if not film.genre2_id:
                            film.genre2 = genre
                        else:
                            film.genre3 = genre
                            
                    film_genres.append({'id': genre.id, 'name': name})
                    
                    act = '1'

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

            actions_logger(9, id, request.profile, act) # фильм Жанры
            
            film.save()
        
        if not film_genres_txt:
            film_genres_txt = 'жанр'
        
        return simplejson.dumps({'status': True, 'content': film_genres, 'genres': film_genres_txt})
    else:
        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_film_countries(request, id, arr):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        try:
            film = Film.objects.using('afisha').only("country", "country2").get(pk=id)
        except Film.DoesNotExist:
            return simplejson.dumps({'status': False})
        
        arr1 = [capit(low(i)) for i in arr]
        arr2 = [uppercase(i) for i in arr]
        arr = arr + arr1 + arr2
        
        countries = AfishaCountry.objects.using('afisha').filter(name__in=arr)
        
        film_countries = []
        
        act1 = None
        try:
            if film.country_id:
                if countries[0].id != film.country_id:
                    act1 = '2' if countries[0] else '3'
            else:
                if countries[0]:
                    act1 = '1'
                
            film.country = countries[0]
            film_countries.append(countries[0].name)
        except IndexError:
            if film.country1_id:
                act1 = '3'
            film.country_id = 0

        act2 = None
        try:
            if film.country2_id:
                if countries[1].id != film.country2_id:
                    act2 = '2' if countries[1] else '3'
            else:
                if countries[1]:
                    act2 = '1'
        
            film.country2 = countries[1]
            film_countries.append(countries[1].name)
        except IndexError:
            if film.country2_id:
                act2 = '3'
            film.country2_id = 0
            
        film.save()
        
        profile = request.profile
        
        cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

        actions_logger(8, id, profile, act1) # фильм Страны
        actions_logger(8, id, profile, act2) # фильм Страны

        film_countries = ' / '.join(film_countries)
        
        if not film_countries:
            film_countries = 'страна'
            
        return simplejson.dumps({'status': True, 'content': film_countries})
    else:
        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def get_film_runtime(request, id, val):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        try:
            film = Film.objects.using('afisha').only("runtime").get(pk=id)
        except Film.DoesNotExist:
            return simplejson.dumps({'status': False})
        
        if val:
            val = str(int(val))
        
        act = None
        if film.runtime:
            if val != film.runtime:
                act = '2' if val else '3'
        else:
            if val:
                act = '1'
        
        film.runtime = val
        film.save()
        
        cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

        actions_logger(10, id, request.profile, act) # фильм Хронометраж
            
        return simplejson.dumps({'status': True, 'content': val})
    else:
        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_film_year(request, id, val):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        try:
            film = Film.objects.using('afisha').only("year").get(pk=id)
        except Film.DoesNotExist:
            return simplejson.dumps({'status': False})
        
        if val and int(val) and len(val) == 4:
            film.year = int(val)
            film.save()

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

            actions_logger(6, id, request.profile, '2') # фильм Год
            
        return simplejson.dumps({'status': True, 'content': val})
    else:
        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def update_film_imdb_id(request, film_id, imdb_id):
    """

        Allows to edit film imdb id (for links)

    :param request: wsgi request data
    :param film_id: film_id where it has to update
    :param imdb_id: new imdb_id
    :return:
    """
    film_editor = is_film_editor(request)

    if not film_editor:
        return simplejson.dumps({'status':False, 'reason': 'u are not film editor'})

    try:
        film = Film.objects.get(id=film_id)
    except Exception as e:   # todo add more info about exception
        return simplejson.dumps({'status': False, 'reason': str(e)})

    try:
        imdb_id_int = int(imdb_id)
    except Exception as e:
        return simplejson.dumps({'status': False, 'reason': str(e)})

    film.idalldvd = imdb_id_int
    film.save()
    return simplejson.dumps({'status': True, 'content': imdb_id_int})


@dajaxice_register
def get_film_name(request, id, val, film_name_type=2):
    """
        Allows to edit film name from ajax request from admin panel

    :param request:
    :param id: film_id
    :param val: new film name
    :param film_name_type: type of film name (for ru is 2, for en is 1)
    :return: None
    """

    film_editor = is_film_editor(request)
    if film_editor:
        if val:
            film = FilmsName.objects.using('afisha').only("name").filter(type=film_name_type, status=1, film_id__id=id)
            slug_name = low(del_separator(val.encode('utf-8')))
            if film:
                act = None
                for i in film:
                    try:
                        if i.name != val.encode('utf-8'):
                            act = '2' if val else '3'

                        i.name = val.encode('utf-8')
                        i.slug = slug_name
                        i.save()
                    except db.backend.Database._mysql.OperationalError:
                        if i.name != val.encode('ascii', 'xmlcharrefreplace'):
                            act = '2' if val else '3'

                        i.name = val.encode('ascii', 'xmlcharrefreplace')
                        i.slug = slug_name
                        i.save()

                # cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

                actions_logger(5, id, request.profile, act) # фильм Название
            else:
                film_obj = Film.objects.using('afisha').get(pk=id)

                try:
                    _, is_created = films_name_create(film_obj, val.encode('utf-8'), film_name_type, 1, slug_name)
                except db.backend.Database._mysql.OperationalError:
                    name = val.encode('ascii', 'xmlcharrefreplace')
                    _, is_created = films_name_create(film_obj, name, film_name_type, 1, slug_name)

                actions_logger(5, id, request.profile, '1')  # фильм Название

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])
            return simplejson.dumps({'status': True, 'content': val,
                                     'film_name_type': str(film_name_type),
                                     'film_id': id})
    else:
        return simplejson.dumps({'status': False})


def exp_film_data(id):
    film = Films.objects.select_related('budget').filter(imdb_id=int(id))
    count = film.count()
    if count == 1:
        film = film[0]
        names = [{'id': i.id, 'name': i.name} for i in film.name.filter(status=1)]
        country = [{'id': i.id, 'name': i.name} for i in film.country.all()]
        genre = [{'id': i.id, 'name': i.name} for i in film.genre.all()]
        
        fp = RelationFP.objects.select_related('person', 'action').filter(films=film)
        persons = []
        for i in fp:
            pname = ''
            for j in i.person.name.filter(status=1, language__id=2):
                pname = j.name.encode('utf-8')
                
            persons.append({'id': i.person_id, 'name': pname, 'action': i.action.name})
        
        rel = []
        #for i in film.release.all():
        #    rel.append({'id': i.id, 'date': str(i.release), 'format': i.get_format_display()})
        
        distr = []
        for i in film.distributor.all():
            for j in i.name.filter(status=1):
                distr.append({'id': i.id, 'name': j.name})
                
        budget = []
        if film.budget:
            budget = [{'sum': film.budget.budget, 'cur': film.budget.currency, 'id': film.budget.id}]
            
        poster = ''
        for i in film.images.filter(status=0):
            poster = '%s%s' % (settings.MEDIA_URL, i.file.lstrip('/'))
        
        return {
            'status': True,
            'names': names,
            'country': country,
            'genre': genre,
            'year': film.year,
            'imdb': film.imdb_id,
            'imdb_rate': film.imdb_rate,
            'imdb_votes': film.imdb_votes,
            'runtime': film.runtime,
            'limit': film.rated,
            'budget': budget,
            'persons': persons,
            'release': rel,
            'distr': distr,
            'poster': poster,
            'kid': film.kid,
            'pk': film.id,
        }
    elif count > 1:
        fdata = []
        delete = []
        for i in film:
            if i.kid:
                names = [{'id': j.id, 'name': j.name} for j in i.name.all()]
                fdata.append({'id': i.id, 'kid': i.kid, 'names': names, 'year': i.year, 'imdb': id})
            else:
                delete.append(i.id)

        if delete:
            Films.objects.filter(pk__in=delete).delete()
            exp_film_data(id)
            for i in delete:
                cache.delete_many(['get_film__%s' % i, 'film__%s__fdata' % i])
        else:
            return {
                'status': True, 
                'double': True, 
                'msg': 'В БД дубли, выберте один верный вариант. Остальные будут удалены.',
                'objs': fdata
            }
    else:
        return {}


@dajaxice_register
def imdb_rel_edit(request, name):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            html = u'''
                <div>
                Укажите ссылку на страницу фильма IMDb:<br />
                <input type="text" value="" size="40" class="imdb_url" />
                <input type="button" value="Искать" class="imdb_url_btn" id="%s"/></div>
                </div>
                ''' % name

            return simplejson.dumps({'status': True, 'content': html})

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def doubles_fix(request, val, imdb):
    try:
        f = Films.objects.get(pk=val)
        for i in Films.objects.filter(imdb_id=int(imdb)).exclude(id=f.id):
            if i.kid and f.kid != i.kid:
                FilmsName.objects.using('afisha').filter(film_id__id=i.kid).delete()
                FilmExtData.objects.using('afisha').filter(id=i.kid).delete()
                Film.objects.using('afisha').filter(id=i.kid).delete()
                PaidActions.objects.filter(object=i.kid).delete()
                cache.delete_many(['get_film__%s' % i.kid, 'film__%s__fdata' % i.kid])
            i.delete()
        return simplejson.dumps({'status': True, 'redirect': True, 'kid': f.kid})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@never_cache
@dajaxice_register
def get_exp_film(request, id):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            data = exp_film_data(id)
            return simplejson.dumps(data)
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def exp_film(request, names, country, genre, distr, release, person, imdb, imdb_rate, imdb_votes, runtime, year, budget, limit, kid, pk):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            if pk:
                try:
                    pk = int(pk)
                    SourceFilms.objects.filter(pk=pk).delete()
                except ValueError: pass
                
            film_id = ''
        
            limits = {
                0: 'без ограничений',
                6: 'до 6 лет',
                12: 'до 12 лет',
                16: 'до 16 лет',
                18: 'до 18 лет',
                21: 'до 21 года',
            }

            if budget:
                budget_obj = Budget.objects.get(pk=budget)

                if len(str(budget_obj.budget)) >= 7:
                    budget = float(budget_obj.budget) / 1000000
                    budget_x = 'млн.'
                else:
                    budget = float(budget_obj.budget) / 1000
                    budget_x = 'тыс.'
                    
                dec = budget - int(str(budget).split('.')[0])
                if not dec:
                    budget = int(budget)
#                budget = 'Бюджет: %s %s%s' % (budget, budget_x, budget_obj.currency.encode('utf-8'))
                budget = '%s %s%s' % (budget, budget_x, budget_obj.currency.encode('utf-8'))

            #if release:
            #    r_obj = FilmsReleaseDate.objects.get(pk=release[0])
            #    release = r_obj.release
            #else:
            #    release = None
            
            if distr:
                try:
                    distr_obj = Distributors.objects.get(pk=distr[0])
                    distr = distr_obj.kid
                except Distributors.DoesNotExist:
                    distr = 0
            else:
                distr = 0
            
            country1 = 0
            country2 = 0
            if country:
                for ind, i in enumerate(Country.objects.filter(pk__in=country)):
                    if ind == 0:
                        country1 = i.kid
                    elif ind == 1:
                        country2 = i.kid
                        break

            genre1 = 0
            genre2 = 0
            genre3 = 0
            if genre:
                for ind, i in enumerate(Genre.objects.filter(pk__in=genre)):
                    if ind == 0:
                        genre1 = i.kid
                    elif ind == 1:
                        genre2 = i.kid
                    elif ind == 2:
                        genre3 = i.kid
                        break
            if kid:
                kid = int(kid)
                film_id = kid
                film_obj = Film.objects.using('afisha').get(id=kid)
                
                next = False
                if film_obj.idalldvd and int(film_obj.idalldvd) == int(imdb):
                    next = True
                else:
                    try:
                        film_exist = Film.objects.using('afisha').get(idalldvd=imdb)
                        FilmsName.objects.using('afisha').filter(film_id__id=kid).delete()
                        FilmExtData.objects.using('afisha').filter(id=kid).delete()
                        Films.objects.filter(kid=film_obj.id).delete()
                        film_obj.delete()
                        film_id = film_exist.id
                        link = 'http://kinoinfo.ru/film/%s/' % film_id
                        cache.delete_many(['get_film__%s' % film_obj.id, 'film__%s__fdata' % film_obj.id])
                    except Film.DoesNotExist:
                        next = True
                   

     
                if next:
                    film_obj.idalldvd = imdb
                    if runtime:
                        film_obj.runtime = runtime
                    if limit:
                        film_obj.limits = limits.get(int(limit), '')
                    if budget:
#OFC076
#                        film_obj.comment = budget
                      
#                        from settings_kinoafisha import KINOAFISHA_EXT
#                        fileName = '{0}/{1}.json'.format(KINOAFISHA_EXT, 'test_settings')
#                        with open(fileName, 'a') as outfile:
#                            outfile.write("step01!\n")

                        obj, created = FilmsBudget.objects.get_or_create(kid = kid, defaults = {'kid': kid, 'budget': budget,})
                        act = None

#                        from settings_kinoafisha import KINOAFISHA_EXT
#                        fileName = '{0}/{1}.json'.format(KINOAFISHA_EXT, 'test_settings')
#                        with open(fileName, 'a') as outfile:
#                            outfile.write("step02!\n")

                        if created:
                            act = '1'
                        else:
                            if budget != obj.budget:
                                act = '2' if budget else '3'
                            obj.budget = budget
                            obj.save()

#                        from settings_kinoafisha import KINOAFISHA_EXT
#                        fileName = '{0}/{1}.json'.format(KINOAFISHA_EXT, 'test_settings')
#                        with open(fileName, 'a') as outfile:
#                            outfile.write("step03!\n")

                        actions_logger(25, kid, request.profile, act) # фильм Бюджет
                        cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

                    if year:
                        film_obj.year = year
                    film_obj.imdb = imdb_rate
                    film_obj.imdb_votes = imdb_votes
                    if distr:
                        film_obj.company_id = distr
                    if country1:
                        film_obj.country_id = country1
                    if country2:
                        film_obj.country2_id = country2
                    if genre1:
                        film_obj.genre1_id = genre1
                    if genre2:
                        film_obj.genre2_id = genre2
                    if genre3:
                        film_obj.genre3_id = genre3
                    film_obj.datelastupd = datetime.datetime.now()
                    film_obj.save()
                    
                    link = 'http://kinoinfo.ru/film/%s/' % kid

                    Films.objects.filter(imdb_id=imdb).update(kid=kid)

                    if names:
                        name = ''
                        slug = ''
                        for i in NameFilms.objects.filter(pk__in=names):
                            if i.status == 1:
                                name = i.name
                            elif i.status == 2:
                                slug = i.name
                        
                        try:
                            name_obj, name_created = films_name_create(film_obj, name, 1, 1, slug)
                        except db.backend.Database._mysql.OperationalError:
                            name = name.encode('ascii', 'xmlcharrefreplace')
                            name_obj, name_created = films_name_create(film_obj, name, 1, 1, slug)
                        
                        FilmsName.objects.using('afisha').filter(film_id=film_obj, type=1, status=1).exclude(id=name_obj.id).delete()
                            
                    if person:
                        fp = RelationFP.objects.select_related('person', 'action', 'status_act').filter(films__imdb_id=imdb)
                        for i in fp:
                            action = PersonsTypeAct.objects.using('afisha').get(type_act=i.action.name)
                            status = PersonsStatusAct.objects.using('afisha').get(status_act=i.status_act.name)
                            prel, prel_created = PersonsRelationFilms.objects.using('afisha').get_or_create(
                                person_id_id = i.person.kid,
                                film_id = film_obj,
                                type_act_id = action,
                                status_act_id = status,
                                defaults = {
                                    'person_id_id': i.person.kid,
                                    'film_id': film_obj,
                                    'type_act_id': action,
                                    'status_act_id': status,
                                })

                    integral_rate(kid)
                    cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])
            else:
                new_id = Film.objects.using('afisha').latest('id').id + 1
            
                film_id = new_id
                now = datetime.datetime.now()
                film_obj, created = Film.objects.using('afisha').get_or_create(
                    idalldvd = int(imdb),
                    defaults = {
                        'id': new_id,
                        'idalldvd': int(imdb),
                        'year': year if year else now.year,
                        'runtime': runtime,
                        'limits': limits.get(int(limit), '') if limit else 0,
                        'comment': budget,
                        'imdb': imdb_rate,
                        'imdb_votes': imdb_votes,
                        'date': None,
                        'company_id': distr,
                        'country_id': country1,
                        'country2_id': country2,
                        'genre1_id': genre1,
                        'genre2_id': genre2,
                        'genre3_id': genre3,
                        'director1': 0,
                        'director2': 0,
                        'director3': 0,
                        'site': '',
                        'name': '',
                        'datelastupd': now,
                    })
            
                link = 'http://kinoinfo.ru/film/%s/'
                
                if not created:
                    link = link % film_obj.id
                    Films.objects.filter(imdb_id=imdb).update(kid=film_obj.id)
                    integral_rate(film_obj.id)
                    cache.delete_many(['get_film__%s' % film_obj.id, 'film__%s__fdata' % film_obj.id])
                else:
                    link = link % new_id
                    
                    Films.objects.filter(imdb_id=imdb).update(kid=new_id)
                
                    FilmExtData.objects.using('afisha').create(
                        id = new_id,
                        rate1 = 0,
                        rate2 = 0,
                        rate3 = 0,
                        rate = float(0),
                        vnum = 0,
                        opinions = '',
                    )

                    if names:
                        name = ''
                        slug = ''
                        for i in NameFilms.objects.filter(pk__in=names):
                            if i.status == 1:
                                name = i.name
                            elif i.status == 2:
                                slug = i.name
                        
                        if name:
                            try:
                                name_obj, name_created = films_name_create(film_obj, name, 1, 1, slug)
                            except db.backend.Database._mysql.OperationalError:
                                name = name.encode('ascii', 'xmlcharrefreplace')
                                name_obj, name_created = films_name_create(film_obj, name, 1, 1, slug)
                                
                            FilmsName.objects.using('afisha').filter(film_id=film_obj, type=1, status=1).exclude(id=name_obj.id).delete()
                    
                    if person:
                        fp = RelationFP.objects.select_related('person', 'action', 'status_act').filter(films__imdb_id=imdb)
                        for i in fp:
                            action = PersonsTypeAct.objects.using('afisha').get(type_act=i.action.name)
                            status = PersonsStatusAct.objects.using('afisha').get(status_act=i.status_act.name)
                            PersonsRelationFilms.objects.using('afisha').create(
                                person_id_id = i.person.kid,
                                film_id = film_obj,
                                type_act_id = action,
                                status_act_id = status,
                            )

                    integral_rate(new_id)


            # Удаляем объект из ненайденных
            xml_file = 'dump_imdb_nof_film.xml'
            with open('%s/%s' % (settings.NOF_DUMP_PATH, xml_file), 'r') as f:
                xml_nof_data = BeautifulSoup(f.read(), from_encoding="utf-8")
            for i in xml_nof_data.find_all('film', code=imdb):
                i.extract()
            xml_nof = str(xml_nof_data).replace('<html><head></head><body>','').replace('</body></html>','')
            create_dump_file('imdb_nof_film', settings.NOF_DUMP_PATH, xml_nof)

            return simplejson.dumps({
                'status': True,
                'link': link,
                'kid': film_id,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
        return simplejson.dumps({'status': False})



@dajaxice_register
def get_exist_com(request, id):
    try:
        current_site = request.current_site
        
        comments = News.objects.filter(site=current_site, reader_type='10', extra__istartswith='%s;' % id).order_by('dtime')
        
        comments_dict = {}
        comments_list = []
        authors = {}
        for i in comments:
            extra = i.extra.split(';')
            comment, answer = extra if len(extra) == 2 else (extra[0], None)

            autor = org_peoples([i.autor])[0]
            
            if i.autor_nick == 1:
                if i.autor.user.first_name:
                    autor['fio'] = i.autor.user.first_name
                    autor['show'] = '2'
            elif i.autor_nick == 2:
                autor['fio'] = ''
                autor['short_name'] = ''
            
            if autor['fio']:
                user = autor['fio']
            else:
                user = autor['short_name']

            authors[i.id] = user

            ans = None
            if answer:
                ans = authors.get(int(answer))
                
            comments_list.append({'comment': i.text, 'date': str(i.dtime), 'user': user, 'id': i.id, 'answer': ans})

        return simplejson.dumps({
            'status': True,
            'content': comments_list,
            'id': id,
        })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

def is_ascii(s):
    return all(ord(c) < 128 for c in s)


@dajaxice_register
def imdb_search(request, val, exact, more):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
        
            val = val.split(' @ ')[0]
            
            exact = True if exact == 'true' else False
            result = imdb_searching(val.encode('utf-8'), exact)
            txt = ''
            
            if more:
                cl = 'search_imdb_more'
                btn = 'Выбрать'
            else:
                cl = 'create_imdb'
                btn = 'Создать фильм'
            
            for i in result:
                persons = ''
                for j in i['persons']:
                    if persons:
                        persons += u', '
                    persons += j

                txt += '<div style="border-bottom:1px solid #CCC; padding:5px; background:#EBEBEB; min-width: 300px;"><a href="http://www.imdb.com%s" target="_blank">%s</a> (<span id="imdb_year">%s</span>) <i>%s</i><br />%s <input type="button" value="%s" id="%s" class="%s" /></div>' % (i['link'].encode('utf-8'), i['title'], i['year'], i['aka'], persons.encode('utf-8'), btn, i['id'], cl)
            
            if not txt:
                txt = '<br />Ничего не найдено<br />'
            
            txt += '<br /><div>Или укажите ссылку на страницу фильма IMDb:<br /><input type="text" value="" size="40" class="imdb_url" /> <input type="button" value="Искать" class="imdb_url_btn" id="%s"/></div>' % val.encode('utf-8')
            
            return simplejson.dumps({
                'status': True,
                'content': txt,
                'query': val,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
        return simplejson.dumps({'status': False})


@dajaxice_register
def imdb_search2(request, imdb_id, name, year, kid):
    try:
        film_editor = is_film_editor(request)
        if film_editor:

            film_name = name
            slug = low(del_separator(film_name.encode('utf-8')))
            
            film_name = film_name.encode('ascii', 'xmlcharrefreplace')
            
            xml = '<film n="%s" s="%s" y="%s" id="%s" d="" r=""></film>' % (film_name, slug, str(year).encode('utf-8'), str(imdb_id).encode('utf-8'))
            
            data = exp_film_data(imdb_id)
            
            if data:
                if data.get('double'):
                    return simplejson.dumps(data)
                else:
                    if not data['kid']:
                        RelationFP.objects.filter(films__id=data['pk']).delete()
                        Films.objects.filter(pk=data['pk']).delete()
                    elif int(data['kid']) != int(kid):
                        
                        '''
                        FilmsName.objects.using('afisha').filter(film_id__id=kid).delete()
                        FilmExtData.objects.using('afisha').filter(id=kid).delete()
                        Film.objects.using('afisha').filter(id=kid).delete()
                        RelationFP.objects.filter(films__kid=kid).delete()
                        Films.objects.filter(kid=kid).delete()
                        PaidActions.objects.filter(object=kid).delete()
                        '''
                        return simplejson.dumps({'status': True, 'redirect': True, 'kid': data['kid']})
            
            data_nof_persons, distr_nof_data, dump, good = get_imdb_data(xml, False, 1, [int(imdb_id),], True, kid)
            
            if good:
                data = exp_film_data(imdb_id)
            
                if not data:
                    data = {'status': False}
            else:
                data = {'status': False}

            if kid:
                cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

            return simplejson.dumps(data)
                
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)\n' % (dir(e), e.args))
        return simplejson.dumps({'status': False})


@dajaxice_register
def create_imdb(request, imdb_id, id, year):
    try:
        film_editor = is_film_editor(request)
        if film_editor:

            data = exp_film_data(imdb_id)
            good = 0
            if not data:
                film = SourceFilms.objects.get(pk=id)
                film_release = film.extra.encode('utf-8')
                film_name = film.name.encode('utf-8')
                slug = low(del_separator(film_name))
                xml = '<film n="%s" s="%s" y="%s" id="%s" d="" r="%s"></film>' % (film_name, slug, year, imdb_id, film_release)
                data_nof_persons, distr_nof_data, dump, good = get_imdb_data(xml, False, 3, [imdb_id,], True, film.kid)
                data = exp_film_data(imdb_id)
            
            if not data or not good:
                data = {'status': False}
            
            return simplejson.dumps(data)
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



@dajaxice_register
def myhit_search(request, val, year):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            result = myhit_searching(val.encode('utf-8'), year)
            txt = ''
            
            for i in result:
                note = i['note'] if i['note'] else ''
                persons = i['persons'] if i['persons'] else ''
                
                txt += '<div class="source_f_block">\
                    <img src="%s" class="source_f_img" />\
                    <div style="min-height: 200px;">\
                    <b>Название: </b> <a href="%s" target="_blank" class="source_f_name">%s</a><br />\
                    <b>Год: </b>%s<br />\
                    <b>Страна: </b>%s<br />\
                    <b>Режиссер: </b>%s<br />\
                    <b>Описание: </b><span class="source_f_note">%s</span><br />\
                    <input type="button" value="Выбрать для редактирования" class="source_f_edit"/>\
                    </div></div>' % (i['img'], i['link'].encode('utf-8'), i['title'], year, i['country'], persons, note.strip())
            
            return simplejson.dumps({
                'status': True,
                'content': txt,
                'query': val,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def exist_imdbfilm(request, current, exist, atype):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            if atype == '1':
                # удалить текущ. и перейти к существующ.
                kid = int(current)
                redirect = exist
            else:
                # удалить существующ. и оставить текущ.
                kid = int(exist)
                redirect = False
            
            if kid:
                FilmsName.objects.using('afisha').filter(film_id__id=kid).delete()
                FilmExtData.objects.using('afisha').filter(id=kid).delete()
                film_obj = Film.objects.using('afisha').get(id=kid)
                
                if not redirect:
                    Film.objects.using('afisha').filter(pk=current).update(idalldvd=film_obj.idalldvd)
                    
                film_obj.delete()
                
                RelationFP.objects.filter(films__kid=kid).delete()
                Films.objects.filter(kid=kid).delete()
                PaidActions.objects.filter(object=kid).delete()
            
                cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])
            return simplejson.dumps({'status': True, 'redirect': redirect})
        
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def source_create_rel(request, kid, name, note):
    try:
        film_editor = is_film_editor(request)
        if film_editor:
            if name:
                slug = low(del_separator(name.encode('utf-8')))
                
                fname, created = FilmsName.objects.using('afisha').get_or_create(
                    status = 1, 
                    type = 2,
                    film_id_id = kid,
                    defaults = {
                        'film_id_id': kid,
                        'status': 1,
                        'type': 2,
                        'name': name.strip(),
                        'slug': slug,
                    })
                
            if note:
                Film.objects.using('afisha').filter(pk=kid).update(description=note)
            
            cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

            return simplejson.dumps({
                'status': True,
            })
            
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def distributor_edit(request, kid, distr1, distr2):
    #try:
    film_editor = is_film_editor(request)
    if film_editor and kid:
        film = Film.objects.using('afisha').get(pk=kid)
        
        act1 = None
        if film.prokat1_id:
            if distr1 != str(film.prokat1_id):
                act1 = '2' if distr1 != '0' else '3'
        else:
            if distr1 and distr1 != '0':
                act = '1'
        
        act2 = None
        if film.prokat2_id:
            if distr2 != str(film.prokat2_id):
                act2 = '2' if distr2 != '0' else '3'
        else:
            if distr2 and distr2 != '0':
                act2 = '1'
                
        film.prokat1_id = distr1
        film.prokat2_id = distr2
        film.save()
        
        profile = request.profile
        
        cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

        actions_logger(14, kid, profile, act1) # фильм Дистрибьютор
        actions_logger(14, kid, profile, act2) # фильм Дистрибьютор
    
        return simplejson.dumps({
            'status': True,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def release_edit(request, kid, release, ru=True):
    try:
        film_editor = is_film_editor(request)
        if film_editor and kid:
            if release:
                day = release[:2]
                month = release[2:4]
                year = release[4:]
                release = datetime.datetime(int(year), int(month), int(day))
            else:
                release = None
                
            film = Film.objects.using('afisha').get(pk=kid)
            
            film_date = film.date
            if film_date:
                film_date = datetime.date(film.date.year, film.date.month, film.date.day)

            act = None
            if film_date:
                if release != film_date:
                    act = '2' if release else '3'
            else:
                if release:
                    act = '1'

            if ru:
                film.date = release
                film.save()
            else:
                if release:
                    release_ua, ua_created = UkrainianReleases.objects.get_or_create(
                        kid = film.id,
                        defaults = {
                            'kid': film.id,
                            'release': release,
                        })
                    if not ua_created and release_ua.release != release:
                        release_ua.release = release
                        release_ua.save()
                else:
                    UkrainianReleases.objects.filter(kid=film.id).delete()

            
            cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

            actions_logger(15, kid, request.profile, act) # фильм Дата релиза
            
            return simplejson.dumps({
                'status': True,
            })
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def sound_copy_edit(request, kid, data):
    #try:
        film_editor = is_film_editor(request)
        if film_editor and kid:
            for i in data:
                stype, scopy = i.split(';')
                act = None
                
                if not scopy:
                    try:
                        FilmSound.objects.using('afisha').get(film_id__id=kid, type_sound__id=stype).delete()
                        act = '3'
                    except FilmSound.DoesNotExist:
                        pass
                else:
                    copies, created = FilmSound.objects.using('afisha').get_or_create(
                        film_id_id = kid,
                        type_sound_id = stype,
                        defaults = {
                            'film_id_id': kid,
                            'type_sound_id': stype,
                            'num': scopy,
                        })
                        
                    if created:
                        act = '1'
                    else:
                        if copies.num and int(scopy) != copies.num:
                            act = '2'
                    
                        copies.num = scopy
                        copies.save()
                        
                cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

                actions_logger(26, kid, request.profile, act) # фильм Копии
            
            return simplejson.dumps({
                'status': True,
            })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@dajaxice_register
def budget_edit(request, kid, budget):
    #try:
    film_editor = is_film_editor(request)
    if film_editor and kid:
        obj, created = FilmsBudget.objects.get_or_create(
            kid = kid,
            defaults = {
                'kid': kid,
                'budget': budget,
            })
            
        act = None
        if created:
            if budget:
                act = '1'
        else:
            if budget != obj.budget:
                act = '2' if budget else '3'
        
            obj.budget = budget
            obj.save()

        actions_logger(25, kid, request.profile, act) # фильм Бюджет
        
        cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

        return simplejson.dumps({
            'status': True,
        })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def name_detect(request, name):
    #try:
        film_editor = is_film_editor(request)
        if film_editor and name:
            slug = low(del_separator(name.encode('utf-8')))
            
            fname = list(FilmsName.objects.using('afisha').filter(slug__icontains=slug, status=1).distinct('film_id').order_by('name').values('name', 'film_id__year', 'film_id__id'))

            fnames = []
            for i in fname:
                fnames.append({'year': i['film_id__year'], 'name': i['name'], 'id': i['film_id__id']})
            
            
            #fnames = sorted(fnames, key=operator.itemgetter('cinema__cinema__name__name'))
            names = []
            txt = ''
            for i in fnames:
                txt += u'<div style="border-bottom:1px solid #CCC; padding:5px; background:#EBEBEB; min-width: 300px;"><a href="http://kinoinfo.ru/film/%s/" target="_blank">%s</a> (<span id="imdb_year">%s</span>)</div>' % (i['id'], i['name'], i['year'])
            if txt:
                txt = u'В базе есть похожие фильмы:<br />%s' % txt

            return simplejson.dumps({
                'status': True,
                'content': txt,
            })
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def limits_edit(request, kid, limit):
    #try:
        film_editor = is_film_editor(request)
        if film_editor:
            limits = {
                0: 'без ограничений',
                6: 'до 6 лет',
                12: 'до 12 лет',
                16: 'до 16 лет',
                18: 'до 18 лет',
                21: 'до 21 года',
            }
            limit = limits.get(int(limit), '')
            
            Film.objects.using('afisha').filter(pk=kid).update(limits=limit)

            cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])
        return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def rel_name(request, kid, id, ntype):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        if ntype == '#nf':
            NotFoundFilmsRelations.objects.get(pk=id, kid=kid).delete()
        elif ntype == '#an':
            name_obj = NameFilms.objects.get(pk=id)
            rel_obj = KIFilmRelations.objects.get(kid=kid)
            rel_obj.name.remove(name_obj)

        cache.delete_many(['get_film__%s' % kid, 'film__%s__fdata' % kid])

        return simplejson.dumps({'status': True, 'id': id})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def edit_persons_name(request, person, name, id, ntype):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        name = name.strip()
        if name:
            names = {}
            if ntype == 'ru':
                names = {'status': 1, 'lang': 1, 'name': name}
            elif ntype == 'en':
                names = {'status': 1, 'lang': 2, 'name': name}
            elif ntype == 'parent':
                names = {'status': 3, 'lang': 1, 'name': name}
            
            if names:
                person_name, created = NamePerson.objects.get_or_create(
                    status = names['status'], 
                    language_id = names['lang'], 
                    name = names['name'],
                    defaults = {
                        'status': names['status'], 
                        'language_id': names['lang'], 
                        'name': names['name'],
                    })
                
                if id:
                    id = int(id)
                
                if person_name.id != id:
                    if names['status'] != 3:
                        slug, slug_created = NamePerson.objects.get_or_create(
                            status = 2, 
                            language_id = names['lang'], 
                            name = low(del_separator(names['name'].encode('utf-8'))),
                            defaults = {
                                'status': 2, 
                                'language_id': names['lang'], 
                                'name': low(del_separator(names['name'].encode('utf-8'))),
                            })
                    
                    person_obj = Person.objects.get(pk=person)
                    
                    if id:
                        old_name = NamePerson.objects.get(pk=id)
                        person_obj.name.remove(old_name)
                    
                    person_obj.name.add(person_name)
                    if names['status'] != 3:
                        person_obj.name.add(slug)
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def sources_select(request, source):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        films = SourceFilms.objects.only('name').filter(source_obj__id=source)
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def slides_poster_edit(request, kid, status):
    #try:
    film_editor = is_film_editor(request)
    if film_editor:
        id = 12 if status == 1 else 13
        actions_logger(id, kid, request.profile, '2') # фильм Кадры, Постер
    return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))



def get_film_details_data(id, mobile=False):
    opinion = '<a href="/film/%s/opinions/">мнения</a>' % id
    
    kinoinfo_film_vote = FilmsVotes.objects.filter(kid=id)
    kinoinfo_film_vote_dict = {}
    for i in kinoinfo_film_vote:
        kinoinfo_film_vote_dict[i.user] = i.rate_1 + i.rate_2 + i.rate_3

    reviews_dict = {}
    kinoinfo_reviews = News.objects.select_related('autor').filter(visible=True, reader_type='14', extra=id)
    authors = [i.autor for i in kinoinfo_reviews]
    authors_dict = org_peoples(authors, True)
    
    for i in kinoinfo_reviews:
        v = kinoinfo_film_vote_dict.get(i.autor, '')

        autor = authors_dict.get(i.autor.user_id)
        
        if i.autor_nick == 1:
            if i.autor.user.first_name:
                autor['fio'] = i.autor.user.first_name
                autor['show'] = '2'
        elif i.autor_nick == 2:
            autor['fio'] = ''
            autor['short_name'] = ''
        
        aut = autor['fio'] if autor['fio'] else autor['short_name']
        
        reviews_dict[i.id] = {'title': i.title.replace('"', '&#034;'), 'user': aut, 'rate': v}
    
    review = ''
    if reviews_dict.values():
        reviews = ''
        for i in reviews_dict.values():
            if reviews:
                reviews += ',\n'
            reviews += u'%s - %s - %s / 9' % (i['user'], i['title'], i['rate'])
        if mobile:
            review = u'<div style="margin-bottom: 10px;"><b><a href="/film/%s/reviews/" title="%s">Рецензии</a></b></div>' % (id, reviews)
        else:
            review = u'<a href="/film/%s/reviews/" title="%s">рецензии</a>' % (id, reviews)
    else:
        if not mobile:
            review = u'<span style="color: #666;">рецензии</span>'
    
    money = {'ru':  None, 'usa': None}
    gathering = BoxOffice.objects.select_related('country').filter(kid=id, country__name__in=('США', 'Россия')).order_by('date_to')
    for i in gathering:
        key = 'usa' if i.country.name == u'США' else 'ru'
        total = '%s $\n' % intcomma(i.all_sum).replace(',', ' ')
        money[key] = total
    
    gather = ''
    if money['usa']:
        gather += u'США: %s\n' % money['usa']
    if money['ru']:
        gather += u'Россия: %s\n' % money['ru']

    if gather:
        if mobile:
            gather = u'<div><b>Сборы:</b> <a href="/film/%s/boxoffice/">%s</a></div>' % (id, gather)
        else:
            gather = u'<a href="/film/%s/boxoffice/" title="%s">сборы</a>' % (id, gather)
    else:
        if not mobile:
            gather = u'<span style="color: #666;">сборы</span>'

    films_sound_copy = []
    films_copy = []
    films_sound = []
    
    films_sounds = FilmSound.objects.using('afisha').select_related('type_sound').filter(film_id=id)
    for i in films_sounds:
        films_copy.append(i.num)
        films_sound.append(i.type_sound.sound_type)
        films_sound_copy.append({
            'id': i.type_sound_id, 
            'name': i.type_sound.sound_type,
            'num': i.num,
        })
    
    copy = ''
    if films_sound_copy:
        copies = ''
        for i in films_sound_copy:
            if copies:
                copies += ', '
            copies += u'%s - %s' % (i['num'], i['name'])
        if mobile:
            copy = u'<div style="margin-bottom: 10px;"><b>Копий:</b> %s</div>' % copies
        else:
            copy = u'<span class="nolink" title="%s">копий</span>' % copies
    else:
        if not mobile:
            copy = u'<span style="color: #666;">копий</span>'

    budget = ''
    try:
        budget = FilmsBudget.objects.get(kid=id).budget
        if mobile:
            budget = u'<div style="margin-bottom: 10px;"><b>Бюджет:</b> %s</div>' % budget
        else:
            budget = u'<span class="nolink" title="%s">бюджет</a>' % budget
    except FilmsBudget.DoesNotExist:
        if not mobile:
            budget = '<span style="color: #666;">бюджет</span>'


    #releases = list(ReleasesRelations.objects.filter(film_kid=id, rel_double=False, rel_ignore=False).values_list('release__release_date', flat=True))
    #if releases:
    #    releases = u'<span class="nolink" title="%s">дата релиза</span>' % tmp_date(releases[0], "d E Y")
    #else:
    #    releases = u'<span style="color: #666;" >дата релиза</span>'
                
    return {
        'copies': copy,
        'reviews': review,
        'opinions': opinion,
        'boxoffice': gather,
        'budget': budget,
        'release': '',
    }
    

@dajaxice_register
def remove_online_player(request, id, s):
    #try:
        from movie_online.views import get_film_player
        film_editor = is_film_editor(request)
        player = ''
        status = False
        if film_editor:
            source = ImportSources.objects.get(pk=s)
            if source.url == 'http://www.tvzavr.ru/':
                SourceFilms.objects.filter(source_obj=source, kid=id).update(rel_ignore=True)
            elif source.url == 'http://megogo.net/':
                MovieMegogo.objects.filter(afisha_id=id).update(rel_ignore=True)
            elif source.url == 'http://www.now.ru/':
                Nowru.objects.filter(kid=id).update(rel_ignore=True)
            
            player, psource = get_film_player(id)
            if player:
                player = u'%s <div><input type="button" value="Удалить этот плеер" class="remove_online_player" id="%s__%s"/></div>' % (player, id, psource)
            status = True

            cache.delete_many(['get_film__%s' % id, 'film__%s__fdata' % id])

        return simplejson.dumps({'status': status, 'player': player})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

'''
@dajaxice_register
def opinion_rate_set(request, id, alt, excl, val=None):
    #try:
        if request.user.is_superuser:
            obj = NewsFilms.objects.select_related('message', 'message__autor', 'message__autor__personinterface').get(pk=id)

            if alt == 'set' and val:
                val = int(val)
                
                obj.rate = val
                
                eval_film = None
                
                if val in (2, 3):
                    # "не рекомендую"
                    eval_film = 5
                elif val in (4, 5):
                    # "рекомендую"
                    eval_film = 3
                
                interface = obj.message.autor.personinterface
                
                try:
                    like = Likes.objects.get(personinterface=interface, film=obj.kid)
                    if like.evaluation != eval_film:
                        like.evaluation = eval_film
                        like.save()
                except (Likes.DoesNotExist, Likes.MultipleObjectsReturned):
                    Likes.objects.filter(personinterface=interface, film=obj.kid).delete()
                    like = Likes.objects.create(evaluation=eval_film, film=obj.kid)
                    interface.likes.add(like)
                
            elif alt == 'del':
                msg = obj.message
                msg.visible = False
                msg.save()
                
            obj.save()

            if int(excl) == 1:
                count = NewsFilms.objects.filter(message__visible=True).exclude(rate=None).count()
            else:
                count = NewsFilms.objects.filter(message__visible=True, rate=None).count()
            
            return simplejson.dumps({'id': id, 'count': count, 'alt': alt})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
'''

@dajaxice_register
def opinion_rate_set(request, id, alt, excl, rate_1, rate_2, rate_3):
    try:
        if request.user.is_superuser:
            obj = NewsFilms.objects.select_related('message', 'message__autor', 'message__autor__personinterface').get(pk=id)

            if alt == 'set':
                rate = int(rate_1) + int(rate_2) + int(rate_3)
                if rate >= 7:
                    rate = 5
                elif rate == 6:
                    rate = 4
                elif rate == 5:
                    rate = 3
                elif rate < 5:
                    rate = 2

                obj.rate = rate
                obj.rate_1 = rate_1
                obj.rate_2 = rate_2
                obj.rate_3 = rate_3

                eval_film = None
                
                if rate in (2, 3):
                    # "не рекомендую"
                    eval_film = 5
                elif rate in (4, 5):
                    # "рекомендую"
                    eval_film = 3
                
                interface = obj.message.autor.personinterface
                
                try:
                    like = Likes.objects.get(personinterface=interface, film=obj.kid)
                    if like.evaluation != eval_film:
                        like.evaluation = eval_film
                        like.save()
                except (Likes.DoesNotExist, Likes.MultipleObjectsReturned):
                    Likes.objects.filter(personinterface=interface, film=obj.kid).delete()
                    like = Likes.objects.create(evaluation=eval_film, film=obj.kid)
                    interface.likes.add(like)
                
            elif alt == 'del':
                msg = obj.message
                msg.visible = False
                msg.save()
                
            obj.save()

            if int(excl) == 1:
                count = NewsFilms.objects.filter(message__visible=True).exclude(rate=None).count()
            else:
                count = NewsFilms.objects.filter(message__visible=True, rate=None).count()
            
            return simplejson.dumps({'id': id, 'count': count, 'alt': alt})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def person_status_edit(request, id, type, status):
    #try:
        if request.user.is_superuser:
            obj = RelationFP.objects.select_related('films', 'person', 'action', 'status_act').get(pk=id)

            afisha_type_obj = PersonsTypeAct.objects.using('afisha').get(type_act=obj.action.name)
            afisha_status_obj = PersonsStatusAct.objects.using('afisha').get(status_act=obj.status_act.name)
            
            afisha_obj = PersonsRelationFilms.objects.using('afisha').get(
                film_id__id = obj.films.kid,
                person_id__id = obj.person.kid,
                status_act_id = afisha_status_obj,
                type_act_id = afisha_type_obj,
            )

            obj.action_id = int(type)
            obj.status_act_id = int(status)
            obj.save()

            afisha_obj.status_act_id_id = int(status)
            afisha_obj.type_act_id_id = int(type)
            afisha_obj.save()
            
            cache.delete_many(['get_film__%s' % obj.films.kid, 'film__%s__fdata' % obj.films.kid])

            return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def person_rel_delete(request, id):
    #try:
        if request.user.is_superuser:
            obj = RelationFP.objects.select_related('films', 'person', 'action', 'status_act').get(pk=id)

            afisha_type_obj = PersonsTypeAct.objects.using('afisha').get(type_act=obj.action.name)
            afisha_status_obj = PersonsStatusAct.objects.using('afisha').get(status_act=obj.status_act.name)
            afisha_person = AfishaPersons.objects.using('afisha').get(pk=obj.person.kid)
            afisha_film = Film.objects.using('afisha').get(pk=obj.films.kid)

            PersonsRelationFilms.objects.using('afisha').filter(
                film_id = afisha_film,
                person_id = afisha_person,
                status_act_id = afisha_status_obj,
                type_act_id = afisha_type_obj,
            ).delete()

            cache.delete_many(['get_film__%s' % obj.films.kid, 'film__%s__fdata' % obj.films.kid])

            obj.delete()

            return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def person_rel_add(request, film, person, type, status):
    #try:
        if request.user.is_superuser:

            film_obj = Films.objects.get(id=film)
            person_obj = Person.objects.get(kid=person)
            type_obj = Action.objects.get(pk=type)
            status_obj = StatusAct.objects.get(pk=status)

            afisha_type_obj = PersonsTypeAct.objects.using('afisha').get(type_act=type_obj.name)
            afisha_status_obj = PersonsStatusAct.objects.using('afisha').get(status_act=status_obj.name)
            afisha_person = AfishaPersons.objects.using('afisha').get(pk=person_obj.kid)
            afisha_film = Film.objects.using('afisha').get(pk=film_obj.kid)

            obj, created = RelationFP.objects.get_or_create(
                films = film_obj,
                person = person_obj,
                status_act = status_obj,
                action = type_obj,
                defaults = {
                    'films': film_obj,
                    'person': person_obj,
                    'status_act': status_obj,
                    'action': type_obj,
                })

            afisha_obj, afisha_created = PersonsRelationFilms.objects.using('afisha').get_or_create(
                person_id = afisha_person,
                film_id = afisha_film,
                type_act_id = afisha_type_obj,
                status_act_id = afisha_status_obj,
                defaults = {
                    'person_id': afisha_person,
                    'film_id': afisha_film,
                    'type_act_id': afisha_type_obj,
                    'status_act_id': afisha_status_obj,
                })

            cache.delete_many(['get_film__%s' % film_obj.kid, 'film__%s__fdata' % film_obj.kid])

            html = ''
            if created:
                person_name_ru = ''
                person_name_en = ''
                for i in person_obj.name.all():
                    if i.status == 1:
                        if i.language_id == 1:
                            person_name_ru = i.name
                        else:
                            person_name_en = i.name

                person_names = u'%s / %s' % (person_name_ru, person_name_en)

                html += u'<tr id="tr_%s">' % obj.id
                html += u'<td><div><a href="/person/%s/">%s</a></div></td>' % (person_obj.id, person_names)
                html += u'<td><div class="film_person_rel_t" id="%s">%s</div></td>' % (type_obj.id, type_obj.name)
                html += u'<td><div class="film_person_rel_s" id="%s">%s</div></td>' % (status_obj.id, status_obj.name)
                html += u'<td><div class="film_person_rel_edit edit_btn"/></div></td>'
                html += u'<td><div class="film_person_rel_del delete_btn"></div></td>'
                html += u'</tr>'

            return simplejson.dumps({'content': html})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_film_opinions(request, id, show, oid=False):
#comment by OFC076
#show = 0 - create opinion. 1 - view opinion, 2 - create rate

    oid = False if oid == 'False' else oid

    try:
        html_new_opinion = u'''
           <input type="button" value="Оставить отзыв" class="opinions_text" style="display: none;" />
            <div class="opinions_text_fields org_fields">'''

        html = ''

        try:
            exist = NewsFilms.objects.select_related('message').get(kid=id, message__visible=True, message__autor=request.profile, rate_1__gt=0)
        except NewsFilms.DoesNotExist:
            exist = False

        exist_op = exist

        opinions_list = []
        if show != 2:
            

            filmsnews = NewsFilms.objects.select_related('message', 'message__autor').filter(kid=id, message__visible=True).exclude(Q(message__text=None) | Q(message__text=''))
            
            authors = set([i.message.autor for i in filmsnews])
            authors_dict = org_peoples(authors, True)

            try:
                source_film = SourceFilms.objects.get(kid=id, source_obj__url='http://www.kino.ru/')
            except SourceFilms.DoesNotExist:
                source_film = None
                
            rates = []

            for i in filmsnews:

                author = authors_dict.get(i.message.autor.user_id)
                
                nick = author['name']
                if i.message.autor_nick == 1 and author['nickname']:
                    nick = author['nickname']
                
                if i.source_obj_id and source_film:
                    url = 'http://www.kino.ru/%s#%s' % (source_film.source_id.replace('film_', 'forum_'), i.source_id)
                else:
                    url = None
                
                if i.rate:
                    rates.append(i.rate)
                
                full_txt = i.message.text

                spam = True if u'http' in full_txt else False

                opinions_list.append({'date': i.message.dtime, 'nick': nick, 'spam': spam, 'full_txt': full_txt, 'source': url, 'source_name': 'kino.ru', 'id': i.id, 'rate': i.rate})
                
            opinions_list = sorted(opinions_list, key=operator.itemgetter('date'), reverse=True)
            
            
            if opinions_list:
                for i in opinions_list:

                    spam_block = ''
                    if request.user.is_superuser:
                        if i['spam']:
                            spam_block += u'<div class="op_exclamation" title="Похоже на спам"></div>'
                        spam_block += u'<div class="delete_btn op_remove" onclick="opinion_remove(%s);" title="Удалить"></div>' % i['id']
                        spam_block += u'<div class="edit_btn op_edit" onclick="opinion_edit(%s, %s);" title="Редактировать"></div>' % (id, i['id'])

                    orate = ''
                    if i['rate']:
                        orate = u'<div class="opinion_rate" title="Оценка">%s</div>' % i['rate']
                    ourl = ''
                    if i['source']:
                        ourl += u'<em>Источник: <a href="%s" target="_blank">%s</a></em>' % (i['source'], i['source_name'])

                    html += u'''
                    <div class="opinion_bl" style="background: #F2F2F2;">
                    <b style="color: #333;">%s</b>
                    %s
                    <p style="color: #888;">%s</p>
                    %s
                    %s<br /><br />%s</div>
                    ''' % (i['nick'], spam_block, tmp_date(i['date'], "H:i, d E Y года"), orate, i['full_txt'], ourl)
            else:
                html += u'<p id="opinions_empty">Отзывов нет</p>'
                if exist:
                    exist_op = False
             
            title = u'Изменить отзыв:' if oid else u'Новый  отзыв:'

            html_new_opinion = u'''
               <!-- <input type="button" value="Оставить отзыв" class="opinions_text" /> -->
                {{placeholder}}
                <div class="opinions_text_fields org_fields">
                <b>%s</b><br />''' % title


            try:
                author_name = request.fio if request.fio else request.acc_list['short_name']
            except:
                author_name = 'Anonymous'



            if request.user.first_name:
                nick = u' - %s' % request.user.first_name
                nick_txt = u'Изменить'
                disabled = ''
            else:
                nick = ''
                nick_txt = u'Добавить'
                disabled = u'disabled'

            if oid:
                filmsnews = NewsFilms.objects.select_related('message').get(pk=oid)
                op_text = filmsnews.message.text
            else:
                op_text = ''
            html_new_opinion += u'<textarea class="otext" >%s</textarea>' % op_text



        if not exist:
            html_new_opinion += u'''
                <div id="author_names">
                    <table style="text-align: left;">
                        <th style="width: 150px;">Для глаз и ушей:</th>
                        <th style="width: 150px;">Для ума:</th>
                        <th style="width: 150px;">Для сердца:</th>
                        <tr>
                            <td><input type="radio" name="eye" id="eye_3" value="3"  /> Супер</td>
                            <td><input type="radio" name="mind" id="mind_3" value="3"  /> Сильно</td>
                            <td><input type="radio" name="heart" id="heart_3" value="3"  /> Трогает</td>
                        </tr>
                        <tr>
                            <td><input type="radio" name="eye" id="eye_2" value="2" checked /> Хорошо</td>
                            <td><input type="radio" name="mind" id="mind_2" value="2" checked /> Занятно</td>
                            <td><input type="radio" name="heart" id="heart_2" value="2" checked /> Так себе</td>
                        </tr>
                        <tr>
                            <td><input type="radio" name="eye" id="eye_1" value="1" /> Скучно</td>
                            <td><input type="radio" name="mind"  id="mind_1" value="1" /> Глупо</td>
                            <td><input type="radio" name="heart" id="heart_1" value="1" /> Раздражает</td>
                        </tr>
                    </table>
                '''


        # оценить фильм
        if show == 2: 
            if exist:
                html_new_opinion = u'Вы уже оценили этот фильм'
            else:
                html_new_opinion += u'''
                </div>
                <br />
                <input type="hidden" value="%s" class="ofilm_id" />
                <input type="hidden" value="%s" class="opinion_id" />
                <input type="button" value="Сохранить" class="opinions_rate_accept_btn" />
                <input type="button" value="Отмена" onclick="$.fancybox.close();" />
                <span class="opinion_msg"></span>
                ''' % (id, oid)
                
        # добавить отзыв
        else:
            
            if exist:
                html_new_opinion += u'<div id="author_names">'

            author_visible = 'hidden' if oid else 'visible' 
                
            author_bl = u'''
                <div class="nick_bl" style = "visibility: %s;">
                Подпись автора:<br />
                <input type="radio" name="author_nick" value="0" checked /> %s
                <br />
                <input type="radio" name="author_nick" value="1" %s/> Псевдоним%s (<a href="/user/profile/" target="_blank">%s</a>)
                <br />
                </div>''' % (author_visible, author_name, disabled, nick, nick_txt)


            html_new_opinion += u'''
                <br /> %s
            </div>
            <br />
            <input type="hidden" value="%s" class="ofilm_id" />
            <input type="hidden" value="%s" class="opinion_id" />
            <input type="button" value="Сохранить" class="opinions_text_accept_btn" />
            <input type="button" value="Отмена (посмотреть отзывы)" class="opinions_text_cancel_btn" />
            <span class="opinion_msg"></span>
            ''' %  (author_bl, id, oid)

            if request.subdomain == 'm':
                html_new_opinion = html_new_opinion.replace(u'Отмена (посмотреть отзывы)', u'Отмена (увидеть отзывы)')

        html_new_opinion += u'</div>'

        if exist_op:
            if request.subdomain == 'm':
                op_button_text = u'Добавить еще отзыв'
            else:
                op_button_text = u'Если Ваше мнение изменилось - оставьте новый отзыв'
            op_button_style = u' style="width: 80%;margin-left: 10%;margin-right: 10%; color:blue;  font-weight: bold;" '
        else:
            if request.subdomain == 'm':
                op_button_text = u'Оставить отзыв о фильме'
            else:
                op_button_text = u'Оставить свой отзыв об этом фильме'
            op_button_style = u' style="width: 80%;margin-left: 10%;margin-right: 10%;  background: #ffb366;  font-weight: bold;" '
        op_button = u'<input type="button" value="%s" class="opinions_text" %s />' % (op_button_text, op_button_style)

        html = u'<div class="opinions_window">%s<div class="opinions_list">%s</div></div>%s' % (html_new_opinion, html, op_button )

        if len(opinions_list) > 5:
            html = html.replace(u'{{placeholder}}', op_button)
        else:
            html = html.replace(u'{{placeholder}}', '')

        return simplejson.dumps({'content': html, 'show': show})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def send_film_opinion(request, id, txt, eye, heart, mind, nick, oid=False):
    try:
        profile = request.profile

        txt = BeautifulSoup(txt.strip(), from_encoding="utf-8").text
        txt = escape(txt)

        oid = False if oid == 'False' else oid
        if oid:
            nf = NewsFilms.objects.select_related('message').get(id=oid)
            if request.user.is_superuser or nf.message.autor == profile:
                nf.message.text = txt
                nf.message.save()

 #           html = get_film_opinions(request, id, 1)
 #           return html

 #           return simplejson.dumps({'content': txt, 'status': True, 'edt': True, 'oid': oid})

            txt = u'<div style="color:red;text-align: center;">Закройте и снова откройте это окно чтобы увидеть измененный отзыв</div>'

            return simplejson.dumps({
                'content': txt, 'status': True, 'edt': True, 'oid': oid})

        values = ['1', '2', '3']

        if nick not in ['0', '1']:
            nick = 0

        try:
            exist = NewsFilms.objects.select_related('message').get(kid=id, message__visible=True, message__autor=profile, rate_1__gt=0)
        except NewsFilms.DoesNotExist:
            exist = False

        next = False
        if exist:
            if txt and eye == 0 and heart == 0 and mind == 0:
                next = True
        else:
            if txt and eye in values and heart in values and mind in values:
                next = True

        if next:
            city_id = request.current_user_city_id
            cache.delete_many([
                'get_film__%s' % id,
                'film__%s__fdata' % id,
                'ka_kinoinfo_dict_%s' % city_id,
                'ka_kinoinfo_dict_%sfuture' % city_id,
                'ka__soon__releasedata',
            ])

            # если нет оценки
            if not exist:
                rate = int(eye) + int(heart) + int(mind)
                if rate >= 7:
                    rate = 5
                elif rate == 6:
                    rate = 4
                elif rate == 5:
                    rate = 3
                elif rate < 5:
                    rate = 2

                news = create_news(
                    request, [], 'отзыв', txt, '8', nick, id, visible=True)

                NewsFilms.objects.get_or_create(
                    kid=id, message=news,
                    defaults={
                        'kid': id, 'message': news,
                        'rate': rate, 'rate_1': eye,
                        'rate_2': mind, 'rate_3': heart,
                    })
                act = 1
                # отзыв-мнение о фильме
                actions_logger(40, id, profile, act, '')

                if rate >= 4:
                    # "рекомендую"
                    eval_film = 3
                else:
                    # "не рекомендую"
                    eval_film = 5

                interface = profile.personinterface

                try:
                    like = Likes.objects.get(
                        personinterface=interface, film=id)
                    if like.evaluation != eval_film:
                        like.evaluation = eval_film
                        like.save()
                except (Likes.DoesNotExist, Likes.MultipleObjectsReturned):
                    Likes.objects.filter(
                        personinterface=interface, film=id).delete()
                    like = Likes.objects.create(
                        evaluation=eval_film, film=id)
                    interface.likes.add(like)
            else:
                # если есть оценка и есть отзыв, то создаем
                # еще один отзыв (без оценки)
                if exist.message.text:
                    rate = 0
                    news = create_news(
                        request, [], 'отзыв', txt, '8', nick, id, visible=True)

                    NewsFilms.objects.get_or_create(
                        kid=id, message=news,
                        defaults={'kid': id, 'message': news})
                    act = 1
                    # отзыв-мнение о фильме
                    actions_logger(40, news.id, profile, act, '')
                # если есть оценка и нет отзыва, то создаем
                # новый отзыв (редактируем пустой)
                else:
                    rate = exist.rate
                    news = exist.message
                    news.title = 'отзыв'
                    news.text = txt
                    news.autor_nick = nick
                    news.save()

            author = org_peoples([profile])[0]
            nick = author['name']
            if int(news.autor_nick) == 1 and author['nickname']:
                nick = author['nickname']

            rate_html = u'<div class="opinion_rate" title="Оценка">%s</div>' % rate if rate else ''

            html = u'''
            <div class="opinion_bl" style="background: #F2F2F2;">
            <b style="color: #333;">%s</b>
            <p style="color: #888;">%s</p>
            %s
            %s<br /><br />
            ''' % (nick, tmp_date(
                news.dtime, "H:i, d E Y года"), rate_html, news.text)

            return simplejson.dumps({'content': html, 'status': True, 'edt': False})

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def send_film_rate(request, id, eye, heart, mind):
    try:

        profile = request.profile

        values = ['1', '2', '3']

        nick = '0'

        if eye in values and heart in values and mind in values:

            exist = News.objects.filter(extra=id, autor=profile, reader_type='8', visible=True).exists()

            if exist:
                return simplejson.dumps({'content': '', 'status': True})
            else:
                rate = int(eye) + int(heart) + int(mind)
                if rate >= 7:
                    rate = 5
                elif rate == 6:
                    rate = 4
                elif rate == 5:
                    rate = 3
                elif rate < 5:
                    rate = 2

                news = create_news(request, [], 'оценка фильма', '', '8', nick, id, visible=True)

                NewsFilms.objects.get_or_create(
                    kid = id,
                    message = news,
                    defaults = {
                        'kid': id,
                        'message': news,
                        'rate': rate,
                        'rate_1': eye,
                        'rate_2': mind,
                        'rate_3': heart,
                    })

                if rate >= 4:
                    # "рекомендую"
                    eval_film = 3
                else:
                    # "не рекомендую"
                    eval_film = 5
                
                interface = profile.personinterface
                
                act = None
                try:
                    like = Likes.objects.get(personinterface=interface, film=id)
                    if like.evaluation != eval_film:
                        like.evaluation = eval_film
                        like.save()
                        act = '2'
                except (Likes.DoesNotExist, Likes.MultipleObjectsReturned):
                    Likes.objects.filter(personinterface=interface, film=id).delete()
                    like = Likes.objects.create(evaluation=eval_film, film=id)
                    interface.likes.add(like)
                    act = '1'

                if act:
                    action_id = 17 if eval_film == 5 else 1
                    actions_logger(action_id, id, profile, act) # Лайк "Рекомендую" / Лайк "Не рекомендую"

                city_id = request.current_user_city_id

                cache.delete_many([
                    'get_film__%s' % id,
                    'film__%s__fdata' % id,
                    'ka_kinoinfo_dict_%s' % (city_id),
                    'ka_kinoinfo_dict_%sfuture' % (city_id),
                    'ka__soon__releasedata',
                ])

                return simplejson.dumps({})

        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def opinion_remove(request, id):
    try:
        if request.user.is_superuser:
            try:
                filmsnews = NewsFilms.objects.select_related('message').get(pk=id)
                filmsnews.message.delete()
                filmsnews.delete()
            except NewsFilms.DoesNotExist:
                pass
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


#not in use!!!
@dajaxice_register
def opinion_edit(request, id):
    try:
        if request.user.is_superuser:
            try:
                pass
            except NewsFilms.DoesNotExist:
                pass
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)\n' % (dir(e), e.args))


@dajaxice_register
def get_torrent_file(request, id, pay=False):
    try:

        try:
            torrent = Torrents.objects.exclude(path=None).get(pk=id)
        except Torrents.DoesNotExist:
            html = u'''
                <div style="width: 300px; font-size: 14px; text-align: center;">
                <p style="text-align: center;">Извините, но файл не найден</p>
                </div>'''
            return simplejson.dumps({'content': html})

        try:
            access = TorrentsUsers.objects.get(torrent=torrent, profile=request.profile)
        except TorrentsUsers.DoesNotExist:
            access = False

        if access:
            return simplejson.dumps({'id': torrent.id, 'paid': True})

        html = u'''
            <div style="width: 300px; font-size: 14px; text-align: center;">
            <p style="text-align: center;">У Вас нет прав для скачивания файла</p>
            </div>'''
        return simplejson.dumps({'content': html})
    except Exception as e:
        open('errors.txt', 'a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_torrent_file_OLD(request, id, pay=False):
    try:
        price = 1
        paid = False

        try:
            torrent = Torrents.objects.exclude(path=None).get(pk=id)
        except Torrents.DoesNotExist:
            html = u'<div style="width: 300px; font-size: 14px; text-align: center;"><p style="text-align: center;">Извините, но файл не найден</p></div>'
            return simplejson.dumps({'content': html})

        try:
            access = TorrentsUsers.objects.get(torrent=torrent, profile=request.profile)
        except TorrentsUsers.DoesNotExist:
            access = False


        interface = request.profile.personinterface

        if not access and interface.money < price:
            html = u'''
            <div class="adv_conditions_txt">
            У Вас не достаточно средств для скачивания файла!<br />
            <b>Стоимость файла %s руб.</b><br />
            Пополнить свой счёт можно двумя способами: <br />
            1 - активностью на наших сайтах <a href="http://www.kinoafisha.ru/" target="_blank">Киноафиша</a> и <a href="http://kinoinfo.ru/" target="_blank">Киноинфо</a> (отзывы, голосования, лайки, рецензии)<br />
            2 - перечислением любой суммы на любой из наших счетов ниже:
            </div>
            <br />
            <div class="paypal_logo" title="PayPal">kinoafisharu@gmail.com</div>
            <div class="sberbank_logo" title="СберКарта">4276 4600 1280 4881</div><br />
            <div class="vtb24_logo" title="ВТБ24">4272 2904 4769 4951</div>
            <div class="webmoney_logo" title="WebMoney">R164037944803</div><br />
            В назначении платежа укажите <b>"KINOAFISHA_ID: %s"</b><br />''' % (price, request.user.id)
            if not request.acc_list['acc']:
                html += u'<br />Рекомендуем Вам <a href="/user/login/">авторизоваться</a> перед пополнением счета<br />'
            html = u'<div style="width: 700px; font-size: 14px; line-height: 25px;">%s</div>' % html
            return simplejson.dumps({'content': html, 'paid': paid})

        if pay or access:
            return simplejson.dumps({'id': torrent.id, 'paid': True})
        else:
            html = u'''
                <div style="width: 300px; font-size: 14px; text-align: center;">
                <p>С Вашего счета будет списан %s руб.</p>
                <input type="button" value="Скачать" onclick="get_torrent_file(%s, true);" style="margin-top: 10px; padding: 15px;" />
                </div>
            ''' % (price, torrent.id)

        return simplejson.dumps({'content': html, 'paid': paid})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

#def fake_function_is_no_func():
#    from settings_kinoafisha import KINOAFISHA_EXT
#    fileName = '{0}/{1}.json'.format(KINOAFISHA_EXT, 'test_settings')
#    with open(fileName, 'a') as outfile:
#        outfile.write("step-by-step!\n")