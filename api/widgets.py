#-*- coding: utf-8 -*- 
import datetime
import operator

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect
from django.views.decorators.cache import never_cache

from api.models import *
from base.models import SourceSchedules
from base.models_dic import City
from api.views import film_poster2
from kinoinfo_folder.func import del_separator, low

@never_cache
def schedule_widget(request):
    now = datetime.datetime.now()
    today = now.date()
    today = datetime.datetime(today.year, today.month, today.day, 0, 0)
    tomorrow = today + datetime.timedelta(days=1)
    
    now_time = now.time()

    city = request.GET.get('city')
    if city:
        if u'�' in city:
            request.encoding = 'windows-1251'
            city = request.GET.get('city')
        city = low(del_separator(city.encode('utf-8')))
    else:
        city = 'москва'
    
    style = request.GET.get('style')
    if style and style == 'small':
        style = 'small'
        height = 98
    else:
        style = 'normal'
        height = 143
    
    
    #schedule = AfishaSession.objects.using('afisha').select_related('schedule_id', 'session_list_id', 'schedule_id__movie_id', 'schedule_id__film_id').filter(schedule_id__date_from__lte=today, schedule_id__date_to__gte=today, schedule_id__movie_id__city__name=city).order_by('session_list_id__time')
    
    #films_id = set([i.schedule_id.film_id_id for i in schedule])
    

    schedule = SourceSchedules.objects.select_related('film', 'cinema', 'cinema__cinema', 'cinema__cinema__city').filter(dtime__gte=today, dtime__lt=tomorrow, cinema__cinema__city__name__name=city).exclude(film__source_id=0).order_by('dtime')

    films_id = set([i.film.kid for i in schedule])
    
    
    film_name = FilmsName.objects.using('afisha').filter(film_id__in=films_id, type=2, status=1)
    film_names = {}
    for i in film_name:
        film_names[i.film_id_id] = i.name.strip()
        

    '''
    movies_id = [i.schedule_id.movie_id_id for i in schedule]

    cinema = Movie.objects.using('afisha').filter(pk__in=movies_id)
    cinemas = {}
    for i in cinema:
        cinemas[str(i.id)] = i
    '''

    poster_obj = Objxres.objects.using('afisha').select_related('extresid').filter(objtypeid=301, objpkvalue__in=films_id)
    posters = {}
    for p in poster_obj:
        if posters.get(p.objpkvalue):
            posters[p.objpkvalue].append(p)
        else:
            posters[p.objpkvalue] = [p]
            
    films = {}
    city_name = ''
    
    for i in schedule:
        #past = True if now_time > i.session_list_id.time else False
        #showtime = str(i.session_list_id.time).split(':')
        #showtime = {'time': '%s:%s' % (showtime[0], showtime[1]), 'past': past}
        #film_id = i.schedule_id.film_id_id
        
        if not city_name:
            for c in i.cinema.cinema.city.name.all():
                if c.status == 1:
                    city_name = c.name
                
        past = True if now_time > i.dtime.time() else False
        showtime = {'time': i.dtime.time().strftime('%H:%M'), 'past': past}
        film_id = i.film.kid

        if films.get(film_id):
            if showtime not in films[film_id]['sessions']:
                films[film_id]['sessions'].append(showtime)
        else:
            poster_path = ''
            poster = posters.get(film_id)
            if poster:                                 
                poster_path = film_poster2(poster)
            
            film_name = film_names.get(film_id)
            
            films[film_id] = {'id': film_id, 'poster': poster_path, 'name': film_name, 'sessions': [showtime]}
    
    if not schedule:
        try:
            ncity = City.objects.get(name__status=2, name__name=city)
            for c in ncity.name.all():
                if c.status == 1:
                    city_name = c.name
        except City.DoesNotExist: pass
    
    films = sorted(films.values(), key=operator.itemgetter('name'))
    
    return render_to_response('api/widgets/schedule.html', {'films': films, 'city_name': city_name, 'style': style, 'height': height}, context_instance=RequestContext(request))



@never_cache
def widget_test(request):
    return render_to_response('api/widgets/test.html', {}, context_instance=RequestContext(request))



