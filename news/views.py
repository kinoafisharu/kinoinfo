#-*- coding: utf-8 -*- 
import re
import os
import datetime
import time
import operator

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.utils import simplejson
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from bs4 import BeautifulSoup
#from unidecode import unidecode

from base.models import *
from kinoinfo_folder.func import low, capit
from user_registration.func import only_superuser, only_superuser_or_admin, md5_string_generate, org_peoples, is_film_editor
from articles.views import pagination as pagi
from news.forms import NewsImageUploadForm
from release_parser.func import actions_logger
from organizations.func import *
from organizations.ajax import xss_strip2
from api.func import get_client_ip, resize_image
    
def cut_description(data, ellipsis, limit, end=False):
    description_orig = BeautifulSoup(data.replace('<br />',' '), from_encoding='utf-8').text.strip()
    description = description_orig[:limit]
    last = ''
    
    try:
        last_word = description_orig[limit:]
        if last_word[0] == ' ':
            last = ' '.join(last_word.split())
            last_word = ' ' + last_word.split()[0]
            
            if last.startswith(last_word.strip()):
                last = last[len(last_word.strip()):]

        else:
            last = ' '.join(last_word.split())
            last_word = last_word.split()[0]
            l = ''

            if len(last_word) > 15:
                l = last_word[15:]
                last_word = last_word[:15]
            
            if last.startswith(last_word):
                last = '%s%s' % (l, last[len(last_word):])
            
    except IndexError:
        last_word = ''
    
    ellipsis = ' ...' if ellipsis else ''
    description = '%s%s%s' % (description, last_word, ellipsis)
    if end:
        return description, last
    else:
        return description
    
    
@never_cache
def index(request):
    current_site = request.current_site
    subdomain = request.subdomain
    
    if subdomain not in ('yalta', 'yalta2', 'orsk', 'memoirs'):
        raise Http404
        
    filter = {'site': current_site}
    if not request.user.is_superuser and not request.is_admin:
        filter['visible'] = True
       
    reader_type = (8, 11, 12)
    
    tag = request.GET.get('tag')
    if tag == 'news':
        tag = 'новост'
    elif tag == 'recomm':
        tag = 'рекомендац'
    elif tag == 'review':
        tag = 'отзыв'
        reader_type = (8,)
    elif tag == 'announce':
        tag = 'анонс'
    elif tag == 'offer':
        tag = 'предло'
        reader_type = (11,)
    elif tag == 'advert':
        tag = 'спрос'
        reader_type = (12,)
    else:
        tag = None
        
    if tag:
        filter['tags__name__icontains'] = tag
    
    if subdomain == 'memoirs':
        news = News.objects.select_related('autor').filter(Q(subdomain=subdomain, reader_type=None), **filter).order_by('-dtime')
    else:
        news = News.objects.select_related('autor').filter(Q(subdomain=subdomain) | Q(world_pub=True), Q(reader_type__in=reader_type) | Q(reader_type=None), **filter).order_by('-dtime')
    
    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    p, page = pagi(page, news, 8)
    
    news_data = []
    for ind, i in enumerate(p.object_list):
        '''
        description = BeautifulSoup(i.text, from_encoding='utf-8').text.strip().split()[:20]
        description = ' '.join(description)
        description = '%s ...' % description
        '''
        description_orig = BeautifulSoup(i.text, from_encoding='utf-8').text.strip()
        description = description_orig[:130]
        try:
            last_word = description_orig[130:]
            if last_word[0] == ' ':
                last_word = ' ' + last_word.split()[0]
            else:
                last_word = last_word.split()[0]
        except IndexError:
            last_word = ''
            
        description = '%s%s ...' % (description, last_word)
        
        even = True if ind % 2 == 0 else False
        video = True if i.video else False
        
        if i.autor:
            autor = org_peoples([i.autor])[0]
            
            if i.autor_nick == 1:
                if i.autor.user.first_name:
                    autor['fio'] = i.autor.user.first_name
                    autor['show'] = '2'
            elif i.autor_nick == 2:
                autor['fio'] = ''
                autor['short_name'] = ''
        else:
            autor = {'fio': '','short_name': ''}
        
        news_data.append({'obj': i, 'description': description, 'even': even, 'video': video, 'autor': autor})
    
    city_name = ''
    if subdomain in ('yalta', 'yalta2'):
        city_name = 'Ялта'
    elif subdomain == 'orsk':
        city_name = 'Орск'
    elif subdomain == 'memoirs':
        city_name = 'Мои Истории'
    main_description = '%s в сети интернет: новости, анонсы, рекомендации, отзывы, предложения и спрос' % city_name
    
    if subdomain == 'memoirs':
        main_description = ''
        
    return render_to_response('news/main.html', {'news_data': news_data, 'p': p, 'page': page, 'main_description': main_description, 'city_name': city_name, 'tag': tag}, context_instance=RequestContext(request))


def news_edit(request, is_editor, news, id, offers):

    text = request.POST.get('note')
        
    if request.user.is_superuser or is_editor or request.is_admin:
        if text:
            news.text = text
        elif 'visible_btn' in request.POST:
            visible = True if request.POST.get('visible') else False
            news.visible = visible
        news.save()
        
        if news.reader_type in ('8', '9', '10'):
            try:
                org = OrganizationNews.objects.get(news=news)
            except OrganizationNews.DoesNotExist: 
                pass
            else:
                if news.reader_type == '8':
                    ntype = 'отзыв'
                elif news.reader_type == '9':
                    ntype = 'вопрос'
                elif news.reader_type == '10':
                    ntype = 'комментарий'
                
                ActionsLog.objects.create(
                    profile = request.profile,
                    object = '1',
                    action = '2',
                    object_id = org.organization_id,
                    attributes = ntype,
                    site = request.current_site,
                )
        
        if 'file' in request.FILES:
            date_path = news.dtime.date()
            img_path = '%s/%s' % (settings.NEWS_PATH, date_path)
            try: os.makedirs(img_path)
            except OSError: pass

            if 'file' in request.FILES:
                form = NewsImageUploadForm(request.POST, request.FILES)
                if form.is_valid():
                    file_format = low(request.FILES['file'].name)
                    img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif)$', file_format)[0]
                    if img_format:
                        img_obj = request.FILES['file'].read()
                        img_name = '%s.%s' % (md5_string_generate(news.id), img_format)
                        img_path_tmp = '%s/%s' % (img_path, img_name)

                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)
                            
                        resized = resize_image(1000, None, img_obj, 1500)
                        if resized:
                            resized.save(img_path_tmp)
                            
                        img_name_tmp = '%s/%s/%s' % (settings.NEWS_FOLDER, date_path, img_name)

                        if news.img:
                            img_del = news.img.replace(settings.NEWS_FOLDER, settings.NEWS_PATH)
                            os.remove(img_del)

                        news.img = img_name_tmp
                        news.save()
                        
        if 'video' in request.POST:
            video = request.POST.get('video')

            video_id = ''
            code = None

            if video and 'youtu' in video:
                video = strip_tags(video)

                if 'youtu.be' in video:
                    video_id = video.split('http://youtu.be/')[1]
                elif 'www.youtube.com' in video:
                    if 'www.youtube.com/embed/' in video:
                        video_id = video.split('/embed/')[1]
                    else:
                        try:
                            video_id = video.split('?v=')[1]
                            video_id = video_id.split('&')[0]
                        except IndexError:
                            try:
                                video_id = video.split('/v/')[1]
                                video_id = video_id.split('?')[0]
                            except IndexError:
                                video_id = video.split('&v=')[1]
                                video_id = video_id.split('&')[0]

            if video_id:
                video_id = video_id.replace("'", '').replace('"', '').replace('=', '')
                code = '<iframe width="560" height="315" src="//www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>' % video_id

            news.video = code
            news.save()
        
        domain = request.current_site.domain
        if domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au', 'imiagroup.com.au'):
            ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
            return HttpResponseRedirect(ref)
        else:
            if offers:
                if offers['status'] == 11 and offers.get('org'):
                    return HttpResponseRedirect(reverse('organization_offers_news', kwargs={'id': offers['org'].uni_slug, 'offer_id': offers['offer'].id, 'item_id': news.id}))
                elif offers['status'] == 12 and offers.get('org'):
                    return HttpResponseRedirect(reverse('organization_adverts_news', kwargs={'id': offers['org'].uni_slug, 'advert_id': offers['offer'].id, 'item_id': news.id}))
                elif offers['status'] == 8 and offers.get('org'):
                    return HttpResponseRedirect(reverse('organization_reviews_news', kwargs={'id': offers['org'].uni_slug, 'item_id': news.id}))
                elif offers['status'] == 9 and offers.get('org'):
                    return HttpResponseRedirect(reverse('organization_questions_news', kwargs={'id': offers['org'].uni_slug, 'item_id': news.id}))
                elif offers['status'] == 10 and offers.get('org'):
                    return HttpResponseRedirect(reverse('organization_comments_news', kwargs={'id': offers['org'].uni_slug, 'item_id': news.id}))
                
            return HttpResponseRedirect(reverse('news', kwargs={'id': id}))

@never_cache
def news(request, id, offers={}):
    
    current_site = request.current_site
    subdomain = request.subdomain
    if current_site.domain == 'vsetiinter.net':
        if subdomain not in ('yalta', 'yalta2', 'orsk', 'memoirs'):
            raise Http404
    else:
        if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
            subdomain = None
        if not subdomain:
            subdomain = 0
    
    reader_type = None
    is_editor = False
    reader = (8, 11, 12)
    branding = None
    if offers.get('org'):
        reader_type = offers.get('status')
        is_editor = offers.get('is_editor')
        reader = (8, 9, 10, 11, 12)
        branding = offers.get('branding')

    filter = {'pk': id}
    if not request.user.is_superuser and not is_editor and not request.is_admin:
        filter['visible'] = True
        
    try:
        news = News.objects.select_related('autor').get(Q(subdomain=subdomain) | Q(world_pub=True), Q(reader_type__in=reader) | Q(reader_type= None), **filter)
    except News.DoesNotExist:
        raise Http404

    flag = False
    if not reader_type:
        offers['status'] = int(news.reader_type) if news.reader_type else None
        profile = request.profile
        is_editor = True if news.autor == profile else False
        offers['is_editor'] = is_editor
        flag = True
        
    tags = []
    o_tags_list = []
    form = ''

    if request.POST:
        return news_edit(request, is_editor, news, id, offers)
    
    org_id = None
    
    if request.user.is_superuser or is_editor or request.is_admin:
        form = NewsImageUploadForm()
    
        tags = list(NewsTags.objects.all().values_list('name', flat=True))
        
        o_tags = news.tags.all()
        empty_tags = 6 - o_tags.count()
        o_tags_list = [{'id': i.id, 'name': i.name} for i in o_tags]
        o_tags_list = sorted(o_tags_list, key=operator.itemgetter('name'))
        for i in range(empty_tags):
            o_tags_list.append({'id': 99999999 + i + 1, 'name': ''})
    
        if not offers.get('org'):
            try:
                org_id = OrganizationNews.objects.get(news=news).organization_id
            except OrganizationNews.DoesNotExist: pass
    
    # Видео
    trailer_code = news.video if news.video else ''
    trailer_url = ''

    if trailer_code:
        trailer = BeautifulSoup(trailer_code, from_encoding='utf-8')
        trailer = trailer.find('iframe')
        if trailer:
            trailer_url = 'http:%s' % trailer['src']
            trailer_code = trailer
            trailer_code['width'] = 250
            trailer_code['height'] = 150
        else:
            trailer_code = ''

    trailer = str(trailer_code)

    description = BeautifulSoup(news.text, from_encoding='utf-8').text.strip().split()[:20]
    description = ' '.join(description)

    if news.autor:
        autor = org_peoples([news.autor])[0]
        
        if news.autor_nick == 1:
            if news.autor.user.first_name:
                autor['fio'] = news.autor.user.first_name
                autor['show'] = '2'
        elif news.autor_nick == 2:
            autor['fio'] = ''
            autor['short_name'] = ''
    else:
        autor = {'fio': '', 'short_name': ''}

    data = {'news': news, 'description': description, 'tags': tags, 'o_tags_list': o_tags_list, 'form': form, 'video_url': trailer_url, 'video': trailer, 'autor': autor, 'offers': offers, 'flag': flag, 'branding': branding, 'org_id': org_id}
    
    tmplt = 'news/news.html'
    if request.subdomain == 'm' and request.current_site.domain in ('kinoafisha.ru', 'kinoinfo.ru'):
        tmplt = 'mobile/news/news.html'

    return render_to_response(tmplt, data, context_instance=RequestContext(request))


def is_news_spam(request, type):
    ip = get_client_ip(request)
    
    ips = list(Interface.objects.filter(ip_address=ip, profile=request.profile).values_list('pk', flat=True))
    if not ips:
        interface = Interface.objects.create(ip_address=ip)
        request.profile.interface.add(interface)

    now = datetime.datetime.now()
    past = now - datetime.timedelta(days=1)
    created_news = News.objects.filter(autor__interface__ip_address=ip, reader_type=type, dtime__lte=now, dtime__gte=past).order_by('-dtime')
    
    if created_news:
        if created_news.count() > 99:
            # не более 100 сообщений в сутки
            request.session['news_antispam'] = _(u'Вы уже отправили максимальное число сообщений в сутки (100 штук)')
            return True
        else:
            last_news = created_news[0]
            past_5_minutes = now - datetime.timedelta(minutes=5)
            if last_news.dtime > past_5_minutes:
                # не более 1 сообщения в 5 минут
                request.session['news_antispam'] = _(u'Вы можете отправить не более 1 сообщения в 5 минут')
                return True
    return False

def is_banned_user(request):
    ip = get_client_ip(request)
    result = BannedUsersAndIPs.objects.filter(Q(ip=ip) | Q(profile=request.profile))
    if result:
        request.session['banned'] = True
        return True
    else:
        request.session['banned'] = False
        return False



def create_news(request, tags, name, text, reader_type, nick=0, extra=None, visible=None):

    profile = request.profile
    current_site = request.current_site
    subdomain = request.subdomain if request.subdomain else 0
    
    if current_site.domain in ('kinoinfo.ru', 'kinoafisha.ru'):
        subdomain = 0

    language = None
    if current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    tags_list = []
    for i in tags:
        tag = i.strip()
        t_list = (tag, capit(tag), low(tag))
        tag_obj = None
        for t in t_list:
            try:
                tag_obj = NewsTags.objects.get(name=t)
                break
            except NewsTags.DoesNotExist: pass

        if not tag_obj:
            tag_obj = NewsTags.objects.create(name=t_list[0])
            
        tags_list.append(tag_obj)
    
    if visible is None:
        visible = True if text else False
    
    news = News.objects.create(
        title = name, 
        autor = profile,
        site = current_site,
        subdomain = subdomain,
        language = language,
        text = text,
        visible = visible,
        reader_type = reader_type,
        autor_nick = nick,
        extra = extra,
    )
    
    for i in set(tags_list):
        news.tags.add(i)

    NewsTags.objects.filter(news=None).delete()

    return news


@never_cache
def news_add(request):
    
    profile = request.profile
    current_site = request.current_site

    if request.POST:
        type = request.POST.get('type')          
        # если предложение или спрос
        if type in ('11', '12'):
            id = request.POST.get('org_id')
            offer = request.POST.get('offer')
            org = get_object_or_404(Organization, pk=id)
            tag_rel = get_object_or_404(Organization_Tags, pk=offer)
            is_editor = is_editor_func(request, org)
            if request.user.is_superuser or is_editor or request.is_admin:
                name = request.POST.get('news_title')
                tag = request.POST.get('tag')
                if name and tag:
                    tags = tag.split(',')
                    if type == '11':
                        tags = tags[:6] + ['предложение']
                    elif type == '12':
                        tags = tags[:6] + ['спрос']
                    
                    news = create_news(request, tags, name, '', type)
                    
                    OrganizationNews.objects.create(organization=org, news=news, tag=tag_rel)
                if type == '11':
                    return HttpResponseRedirect(reverse('organization_offers_news', kwargs={'id': org.uni_slug, 'offer_id': offer, 'item_id': news.id}))
                else:
                    return HttpResponseRedirect(reverse('organization_adverts_news', kwargs={'id': org.uni_slug, 'advert_id': offer, 'item_id': news.id}))
        
        else:
            # если вопрос, отзыв, коммент
            if type in ('8', '9', '10'):
                id = request.POST.get('org_id')
                org = get_object_or_404(Organization, pk=id)
                text = request.POST.get('text')
                author_nick = request.POST.get('author_nick', 0)
                if request.user.is_authenticated() and text:
                    if type == '8':
                        name = 'Отзыв на %s' % org.name.encode('utf-8')
                        tag = 'отзыв'
                    elif type == '9':
                        name = 'Вопрос для %s' % org.name.encode('utf-8')
                        tag = 'вопрос'
                    elif type == '10':
                        name = 'Комментарий к %s' % org.name.encode('utf-8')
                        tag = 'комментарий'
                    
                    
                    # антиспам
                    spam = is_news_spam(request, type)
                    banned = is_banned_user(request)
                    if not spam and not banned:
                        text = xss_strip2(text)
                        text = BeautifulSoup(text, from_encoding="utf-8")
                        for t in text.find_all('a'):
                            t.extract()
                        text = str(text).replace('<html><head></head><body>','').replace('</body></html>','')
                        
                        news = create_news(request, [tag], name, text, type, author_nick)
                        OrganizationNews.objects.create(organization=org, news=news)

                        ActionsLog.objects.create(
                            profile = profile,
                            object = '1',
                            action = '1',
                            object_id = org.id,
                            attributes = tag,
                            site = current_site,
                        )
                        
                        
                    if type == '8':
                        return HttpResponseRedirect(reverse('organization_reviews', kwargs={'id': org.uni_slug}))
                    elif type == '9':
                        return HttpResponseRedirect(reverse('organization_questions', kwargs={'id': org.uni_slug}))
                    elif type == '10':
                        return HttpResponseRedirect(reverse('organization_comments', kwargs={'id': org.uni_slug}))
            # если рецензия к фильму
            elif type == '14':
                film_editor = is_film_editor(request)
                
                if film_editor:
                    id = request.POST.get('film_id')
                    rate1 = request.POST.get('eye')
                    rate2 = request.POST.get('mind')
                    rate3 = request.POST.get('heart')
                    
                    if id:
                        text = request.POST.get('note')
                        title = request.POST.get('title', 'Рецензия на фильм')
                        review_id = request.POST.get('review_id')
                        profile_id = request.POST.get('profile_id')
                        
                        act = None
                        
                        if review_id:
                            obj = News.objects.get(id=review_id)
                            obj.title = title
                            obj.text = text
                            obj.save()
                            
                            if rate1 and rate2 and rate3:
                                votes, votes_created = FilmsVotes.objects.get_or_create(
                                    kid = id,
                                    user_id = profile_id,
                                    defaults = {
                                        'kid': id,
                                        'user_id': profile_id,
                                        'rate_1': rate1,
                                        'rate_2': rate2,
                                        'rate_3': rate3,
                                })
                                if not votes_created:
                                    votes.rate_1 = rate1
                                    votes.rate_2 = rate2
                                    votes.rate_3 = rate3
                                    votes.save()
                                    
                                FilmVotes.objects.using('afisha').filter(pk=obj.kid).update(
                                    rate_1 = rate1,
                                    rate_2 = rate2,
                                    rate_3 = rate3,
                                )
                            act = '2'
                        else:
                            author_nick = request.POST.get('author_nick', 0)
                            
                            news = create_news(request, [], title, text, type, author_nick, id)

                            FilmsVotes.objects.get_or_create(
                                kid = id,
                                user = profile,
                                defaults = {
                                    'kid': id,
                                    'user': profile,
                                    'rate_1': rate1,
                                    'rate_2': rate2,
                                    'rate_3': rate3,
                            })
                            
                            act = '1'
                        
                        actions_logger(4, id, profile, act, title) # рецензия

            # коммент к рецензии
            elif type == '010':
                review_id = request.POST.get('review')
                answer = int(request.POST.get('answer', 0))
                text = request.POST.get('text')
                author_nick = request.POST.get('author_nick', 0)
                if review_id and text:
                    # антиспам
                    spam = is_news_spam(request, 10)
                    banned = is_banned_user(request)
                    if not spam and not banned:
                        text = BeautifulSoup(text, from_encoding="utf-8").text.strip()
                        extra = '%s;%s' % (review_id, answer) if answer else '%s;' % review_id
                        news = create_news(request, [], 'Комментарий к рецензии', text, '10', author_nick, extra)
            # если новость
            else:
                if request.user.is_superuser or request.is_admin:
                    name = request.POST.get('news_title')
                    tag = request.POST.get('tag')
                    author_nick = request.POST.get('author_nick', 0)
                    if name and tag:
                        tags = tag.split(',')
                        tags = tags[:6]
                        news = create_news(request, tags, name, '', None, author_nick)
                        if current_site.domain not in ('vladaalfimovdesign.com.au', 'letsgetrhythm.com.au', 'imiagroup.com.au'):
                            return HttpResponseRedirect(reverse('news', kwargs={'id': news.id}))
    
    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
        
    return HttpResponseRedirect(ref)


@never_cache
def news_delete(request, id):
    if request.POST:
        type = request.POST.get('type')
        # если спрос или предложение
        if type in ('11', '12'):
            org_id = request.POST.get('org_id')
            offer = request.POST.get('offer')
            org = get_object_or_404(Organization, pk=org_id)
            is_editor = is_editor_func(request, org)
            if request.user.is_superuser or is_editor or request.is_admin:
                autor = request.profile
                news = get_object_or_404(News, pk=id)
                if request.user.is_superuser or news.autor == autor or request.is_admin:
                    news.delete()
                    NewsTags.objects.filter(news=None).delete()

                    if type == '11' and offer:
                        return HttpResponseRedirect(reverse('organization_offers', kwargs={'id': org.uni_slug, 'offer_id': offer}))
                    elif type == '12' and offer:
                        return HttpResponseRedirect(reverse('organization_adverts', kwargs={'id': org.uni_slug, 'advert_id': offer}))
            return HttpResponseRedirect(reverse('main'))
        # если коммент, вопрос, отзыв
        elif type in ('8', '9', '10'):
            org_id = request.POST.get('org_id')
            autor = request.profile
            news = get_object_or_404(News, pk=id)
            
            if request.user.is_authenticated and news.autor == autor or request.user.is_superuser:
                news.delete()
                NewsTags.objects.filter(news=None).delete()

                if org_id:
                    if type == '8':
                        ntype = 'отзыв'
                    elif type == '9':
                        ntype = 'вопрос'
                    elif type == '10':
                        ntype = 'комментарий'
                        
                    ActionsLog.objects.create(
                        profile = request.profile,
                        object = '1',
                        action = '3',
                        object_id = org_id,
                        attributes = ntype,
                        site = request.current_site,
                    )
                
                    org = get_object_or_404(Organization, pk=org_id)
                    if type == '8':
                        return HttpResponseRedirect(reverse('organization_reviews', kwargs={'id': org.uni_slug}))
                    elif type == '9':
                        return HttpResponseRedirect(reverse('organization_questions', kwargs={'id': org.uni_slug})) 
                    elif type == '10':
                        return HttpResponseRedirect(reverse('organization_comments', kwargs={'id': org.uni_slug}))
            return HttpResponseRedirect(reverse('main'))
        # если рецензия
        elif type == '14':
            film_editor = is_film_editor(request)
            if film_editor:
                n = get_object_or_404(News, pk=id)
                
                actions_logger(4, n.extra, request.profile, '3', n.title) # рецензия
                    
                n.delete()
                News.objects.filter(reader_type='10', extra__istartswith='%s;' % id).delete()
                NewsTags.objects.filter(news=None).delete()
                ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
                return HttpResponseRedirect(ref)
        # если новость
        else:
            if request.user.is_superuser or request.is_admin:
                news = get_object_or_404(News, pk=id)
                news.delete()
                NewsTags.objects.filter(news=None).delete()
            if request.current_site.domain in ('vladaalfimovdesign.com.au', 'letsgetrhythm.com.au', 'imiagroup.com.au'):
                return HttpResponseRedirect(reverse('blog'))
            else:
                return HttpResponseRedirect(reverse('main'))
    else:
        raise Http404
        
    

