# -*- coding: utf-8 -*- 
import datetime
import re

from django.http import HttpResponse
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.decorators.cache import never_cache
from django.utils.translation import ugettext_lazy as _
from django.template.context import RequestContext

from bs4 import BeautifulSoup
from release_parser.views import schedules_feed, releases_feed
from base.models_dic import NameCity
from base.models import SubscriptionFeeds, Articles, DjangoSite, News


class FilmsFeed(Feed):
    link = "/schedule/"
    description = ""
    films_dict = {}
    city_id = None
    
    current_site = DjangoSite.objects.get_current()
    
    title = current_site.domain
    
    def get_object(self, request, city):
        try:
            name_city = NameCity.objects.get(city__pk=city, status=1)
            self.description = 'Лучшие сеансы на сегодня в городе %s' % name_city

            if request.user.is_authenticated():
                profile = request.user.get_profile()
                SubscriptionFeeds.objects.get_or_create(
                    profile = profile,
                    type = '1',
                    defaults = {
                        'profile': profile,
                        'type': '1',
                    })
        except (NameCity.DoesNotExist, ValueError): 
            self.description = ''
            city = None
        self.city_id = city
        return city
    
    def items(self, obj):
        schedules, self.films_dict = schedules_feed(obj)
        return schedules
    
    def item_title(self, item):
        name = self.films_dict.get(item['obj'].film.kid)
        name = BeautifulSoup(name.name)
        name = str(name).replace('<html><head></head><body>','').replace('</body></html>','')
        return name
        
    def item_description(self, item):
        times = ''
        for i in sorted(list(set(item['times']))):
            if times:
                times += ', '
            times += '%s' % i
        return times
        
    def item_link(self, item):
        return reverse('schedule_ajax', args=[self.city_id])



class ArticlesFeed(Feed):
    link = "/articles/"
    description = "Рецензии, обзоры, статьи"
    current_site = DjangoSite.objects.get_current()
    
    title = current_site.domain
    
    def get_object(self, request):
        if request.user.is_authenticated():
            profile = request.user.get_profile()
            SubscriptionFeeds.objects.get_or_create(
                profile = profile,
                type = '3',
                defaults = {
                    'profile': profile,
                    'type': '3',
                })
        return True
    
    def items(self):
        articles = Articles.objects.filter(site=self.current_site).order_by('-pub_date')[:5]
        return articles
    
    def item_title(self, item):
        return item.title
        
    def item_description(self, item):
        name = BeautifulSoup(item.text)
        name = name.get_text()
        return '%s ...' % name[:100]

    def item_link(self, item):
        return reverse('articles_main', args=[item.id])
        

class ReleasesFeed(Feed):
    link = "/releases/"
    description = "Скоро в кино"
    current_site = DjangoSite.objects.get_current()
    
    title = current_site.domain

    def get_object(self, request):
        if request.user.is_authenticated():
            profile = request.user.get_profile()
            SubscriptionFeeds.objects.get_or_create(
                profile = profile,
                type = '2',
                defaults = {
                    'profile': profile,
                    'type': '2',
                })
        return True
    
    def items(self):
        releases = releases_feed(self.title)
        return releases
    
    def item_title(self, item):
        return item.get('name', '')
        
    def item_description(self, item):
        return str(item['release'])

    def item_link(self, item):
        return reverse('releases_ajax')


class NewsFeed(Feed):
    link = "/"
    description = ""
    subdomain = None
    title = ""
    
    @never_cache
    def get_object(self, request):
        subdomain = request.subdomain
        current_site = request.current_site
        self.link = '%s.%s' % (subdomain, request.domain)
        self.subdomain = subdomain
        self.title = self.link
        
        city_name = ''
        if current_site.domain != 'letsgetrhythm.com.au':
            if subdomain in ('yalta', 'yalta2'):
                city_name = u'Ялты'
                type = '4'
            elif subdomain == 'orsk':
                city_name = u'Орскa'
                type = '5'
            elif subdomain == 'memoirs':
                city_name = u'- посты'
                type = '7'
        else:
            city_name = ''
            type = '6'
            
        self.description = _(u"Новости" + ' %s' % city_name)
        
        if request.user.is_authenticated():
            profile = request.user.get_profile()
            SubscriptionFeeds.objects.get_or_create(
                profile = profile,
                type = type,
                defaults = {
                    'profile': profile,
                    'type': type,
                })
        return HttpResponse(str())
    
    def items(self):
        news = News.objects.filter(Q(subdomain=self.subdomain) | Q(world_pub=True), reader_type=None).order_by('-id')[:5]
        return news
    
    def item_title(self, item):
        return item.title
        
    def item_description(self, item):
        '''
        description = BeautifulSoup(item.text, from_encoding='utf-8').text.strip().split()[:20]
        description = ' '.join(description)
        return '%s ...' % description
        '''
        description_orig = BeautifulSoup(item.text, from_encoding='utf-8').text.strip()
        description = description_orig[:130]
        try:
            last_word = description_orig[130:]
            if last_word[0] == ' ':
                last_word = ' ' + last_word.split()[0]
            else:
                last_word = last_word.split()[0]
        except IndexError:
            last_word = ''
            
        return '%s%s ...' % (description, last_word)
        
        
    def item_link(self, item):
        return 'http://%s/news/%s' % (self.link, item.id)


