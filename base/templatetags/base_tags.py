# -*- coding: utf-8 -*- 
import json
import datetime
import random

from django import template
from django.template import RequestContext
from django.conf import settings
from django.db.models import Q

from base.models import *
from api.views import get_dump_files, get_dump_films_files, in_group
from release_parser.kinoafisha_admin import admin_identification_status
from articles.views import pagination
from letsgetrhythm.views import get_org_menu, get_org_left_menu
from user_registration.func import *

from api.func import get_method_state
from kinoafisha.func import get_menu_state

register = template.Library()


@register.simple_tag
def base_title_page():
#    return 'Киноафиша России'
    return 'Киноафиша'

@register.inclusion_tag('menu.html', takes_context=True)
def menu(context):
    request = context['request']
    subdomain = request.subdomain
    current_site = request.current_site
    
    # 2 - ссылка, 3 - признак активности, 4 - признак выделенности, 5 - признак открытия в новом окне 
    links = []
    
    if current_site.domain == 'vsetiinter.net':
        if subdomain == 'yalta':
            city = 'Ялты'
            schedule = 'http://kinoinfo.ru/schedule/238/'
        elif subdomain == 'orsk':
            city = 'Орска'
            schedule = 'http://kinoinfo.ru/schedule/280/'
            
        if subdomain in ('yalta', 'orsk'):
            links = (
                 ('Новости %s' % city, '/', 0, 0, 0),
                 ('Организации %s' % city, '/organizations/list/а/', 0, 0, 0),
                 ('Люди %s' % city, '#', 0, 0, 0),
                 ('Афиша %s' % city, schedule, 0, 0, 1),
            )
            
    elif current_site.domain in ('letsgetrhythm.com.au', 'vladaalfimovdesign.com.au'):
        slug = 'lets-get-rhythm' if current_site.domain == 'letsgetrhythm.com.au' else 'vlada-alfimov-design'
        
        menu = list(OrgSubMenu.objects.filter(orgmenu__organization__uni_slug=slug).values('name', 'id', 'orgmenu__name', 'orgmenu', 'page_type'))
        menu_data = {}
        for i in menu:
            key = i['orgmenu']
            if i['orgmenu__name'] != 'About Us':
                if not menu_data.get(key):
                    menu_data[key] = {'key': i['orgmenu'], 'title': i['orgmenu__name'], 'sub': [{'id': i['id'], 'name': i['name'], 'type': i['page_type']}]}
        
        if current_site.domain == 'vladaalfimovdesign.com.au':
            links = [('Home', '/', 0, 0, 0, 'about_section'), ('About Us', '/about/', 0, 0, 0, 'about_section'),]
        else:
            links = [('About Us', '/', 0, 0, 0, 'about_section'), ]
            
        for i in menu_data.values()[:6]:
            sub = i['sub'][0]
            url = '/gallery/%s/' % sub['id'] if sub['type'] == '2' else '/view/%s/' % sub['id']
            menu_id = '%s_section%s' % (slug, i['key'])
            links.append((i['title'], url, 0, 0, 0, menu_id))
    elif current_site.domain == 'kinoafisha.ru':
        menu_state = get_menu_state()
        tmp = []
        if menu_state['kinoafisha_menu_section01_s00']:
            tmp.append(('В кинотеатрах', '/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section02_s00']:
            tmp.append(('Скоро', '/soon/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section03_s00']:
            tmp.append(('Рекомендации', '/best/schedules/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section04_s00']:
            tmp.append(('Бокс-офис', '/boxoffice/russia/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section05_s00']:
            tmp.append(('Кино он-лайн', '/online/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section06_s00']:
            tmp.append(('Обзоры, мнения и комментарии', '/reviews/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section07_s00']:
            tmp.append(('Новости', '/news/', 0, 0, 0))
        if menu_state['kinoafisha_menu_section08_s00']:
            tmp.append(('Мегакритик', 'https://www.megacritic.ru/', 0, 0, 1))
        links = tuple(tmp)


    elif current_site.domain == 'kinoinfo.ru':
        links = (
             ('Cеансы', 'http://kinoafisha.ru/schedules/', 0, 0, 1),
             ('Скоро в кино', '/releases/', 0, 0, 0),
             ('Кино он-лайн', '/online/movie/', 0, 0, 0),
             ('API', '/api/', 0, 0, 0),
        )
            
    return {'links': links, 'request': request}


@register.inclusion_tag('mobile/ki_main_menu.html', takes_context = True)
def ki_main_menu_mobile(context):
    return {'request': context['request']}

@register.inclusion_tag('user/openid.html', takes_context = True)
def base_user_openid(context, message=''):
    return {'message': message, 'request': context['request']}
    
@register.inclusion_tag('user/email.html')
def base_user_email():
    return {'value': 0}

@register.inclusion_tag('user/livejournal.html')
def base_user_lj():
    return {'value': 0}

@register.inclusion_tag('user/kinoafisha.html')
def base_user_kinoafisha():
    return {'value': 0}

@register.inclusion_tag('mobile/user/kinoafisha.html')
def base_user_kinoafisha_mobile():
    return {'value': 0}

@register.inclusion_tag('api/api_description.html')
def api_description():
    return {'value':0}
    
@register.inclusion_tag('release_parser/brand_org_navigate.html')
def brand_org_navigate():
    return {'value':0}
    
@register.inclusion_tag('api/api_menu.html', takes_context = True)
def api_menu(context):
    acc = in_group(context['user'], 'API')
    dump_dict = get_dump_files(settings.API_DUMPS_LIST, settings.API_DUMP_PATH)
    films = get_dump_films_files(settings.API_DUMP_PATH)
    method_state = get_method_state()
    return {'content': dump_dict, 'acc': acc, 'context': context, 'method_state' : method_state, 'films_dumps': films}

@register.inclusion_tag('api/api_menu_en.html', takes_context = True)
def api_menu_en(context):
    acc = in_group(context['user'], 'API')
    dump_dict = get_dump_files(settings.API_DUMPS_LIST, settings.API_DUMP_PATH)
    films = get_dump_films_files(settings.API_DUMP_PATH)
    return {'content': dump_dict, 'acc': acc, 'context': context, 'films_dumps': films}


'''
@register.inclusion_tag('release_parser/release_menu.html')
def release_menu():
    dump_dict = get_dump_files(settings.PARSER_DUMPS_LIST, settings.API_DUMP_PATH)
    return {'content': dump_dict}
'''
@register.inclusion_tag('release_parser/kinoafisha_admin_menu.html', takes_context = True)
def kinoafisha_admin_menu(context):
    objects = ['country', 'city', 'cinema', 'hall', 'film', 'distributor', 'person']
    obj_error = {}
    for i in objects:
        data, error, to, yes = admin_identification_status(i)
        obj_error[i] = error
    return {'obj_error': obj_error, 'request': context['request']}
    
    
@register.inclusion_tag('kinoafisha/menu.html', takes_context = True)
def kinoafisha_main_menu(context):
    menu_state = get_menu_state()
    return {'user': context['user'], 'menu_state':menu_state, 'request': context['request']}

@register.inclusion_tag('kinoafisha/torrents_menu.html', takes_context = True)
def torrents_menu(context):
    return {'request': context['request']}

@register.inclusion_tag('mobile/kinoafisha/menu.html', takes_context = True)
def kinoafisha_main_menu_mobile(context):
    menu_state = get_menu_state()
    return {'user': context['user'], 'menu_state':menu_state, 'request': context['request']}

@register.inclusion_tag('mobile/mobile_header.html', takes_context = True)
def mobile_header(context):
    return {'request': context['request']}

@register.inclusion_tag('mobile/forums/mobile_header.html', takes_context = True)
def wf_mobile_header(context):
    return {'request': context['request']}

@register.inclusion_tag('mobile/user/login_menu_mobile.html', takes_context = True)
def login_menu_mobile(context):
    return {'request': context['request']}

'''
@register.inclusion_tag('release_parser/schedule_menu.html')
def schedule_menu():
    dump_dict = get_dump_files(settings.PARSER_DUMPS_LIST, settings.API_DUMP_PATH)
    return {'content': dump_dict}
'''
@register.inclusion_tag('articles/articles_menu.html', takes_context = True)
def articles_menu(context):
    page = context['request'].GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    articles = Articles.objects.filter(site=settings.SITE_ID).order_by('id')
    p, page = pagination(page, articles, 6)
    return {'p': p, 'page': page, 'user': context['user']}

#Главная страница Movie Online, я не уверен, что она будет использоваться
#@register.inclusion_tag('movie_online/movie_menu.html')
#def movie_menu():
    #return {'value': 0}

#Admin Panel  movie_online_admin
@register.inclusion_tag('movie_online/admin_menu.html')
def admin_menu():
    return {'value': 0}

#admin panel music
@register.inclusion_tag('music/admin_menu.html')
def music_admin_menu():
    return {}

@register.inclusion_tag('footer/liveinternet_counter.html', takes_context = True)
def liveinternet_counter(context):
    current_site = settings.SITE_ID # 1 - kinoinfo.ru; 2 - umru.net; 3 - kinoafisha.ua
    return {'current_site': current_site, 'request': context['request']}
    
@register.inclusion_tag('pagination.html')
def base_pagination(p, page):
    return {'p': p, 'page': page}

@register.inclusion_tag('film/film_menu.html', takes_context = True)
def film_menu(context, id, menu, film_editor):
    return {'film_id': id, 'menu': menu, 'user': context['user'], 'film_editor': film_editor, 'request': context['request']}

@register.inclusion_tag('mobile/film/film_menu.html', takes_context = True)
def film_menu_mobile(context, id, menu, film_editor):
    return {'film_id': id, 'menu': menu, 'user': context['user'], 'film_editor': film_editor, 'request': context['request']}


@register.inclusion_tag('person/person_menu.html', takes_context = True)
def person_menu(context, id):
    return {'person_id': id, 'user': context['user'], 'request': context['request']}

@register.inclusion_tag('mobile/person/person_menu.html', takes_context = True)
def person_menu_mobile(context, id):
    return {'person_id': id, 'user': context['user'], 'request': context['request']}

@register.inclusion_tag('mobile/forums/menu.html', takes_context = True)
def wf_menu_mobile(context, data, search_query):
    return {'data': data, 'search_query': search_query, 'request': context['request']}

@register.inclusion_tag('music/artist_menu.html', takes_context = True)
def artist_menu(context, id):
    return {'artist_id': id, 'user': context['user']}
    
@register.inclusion_tag('distributor/distributor_menu.html', takes_context = True)
def distributor_menu(context, id):
    return {'distributor_id': id, 'user': context['user']}
    
@register.inclusion_tag('user/profile_menu.html', takes_context = True)
def profile_menu(context, card, lb=False):
    org_menu = get_org_menu(card['profile'].user_id, context['request'], profile=True)
    return {'request': context['request'], 'card': card, 'org_menu': org_menu, 'lb': lb}

@register.inclusion_tag('mobile/user/profile_menu.html', takes_context = True)
def profile_menu_mobile(context, is_my_profile, user_id):
    org_menu = get_org_menu(user_id, context['request'], profile=True)
    return {'is_my_profile': is_my_profile, 'request': context['request'], 'user_id': user_id, 'org_menu': org_menu}

@register.inclusion_tag('pmprepare/user/profile_menu.html', takes_context = True)
def pmprepare_profile_menu(context, is_my_profile, user_id):
    org_menu = get_org_menu(user_id, context['request'], profile=True)
    return {'is_my_profile': is_my_profile, 'request': context['request'], 'user_id': user_id, 'org_menu': org_menu}


@register.inclusion_tag('organizations/organization_menu.html', takes_context = True)
def organization_menu(context, id, offers_tags, advert_tags, is_editor, branding, org_ka=False):
    org_menu = get_org_menu(id, context['request'])
    return {'org_id': id, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'request': context['request'], 'branding': branding, 'org_ka': org_ka, 'org_menu': org_menu}

@register.inclusion_tag('mobile/organizations/organization_menu.html', takes_context = True)
def organization_menu_mobile(context, id, offers_tags, advert_tags, is_editor, branding, org_ka=False):
    org_menu = get_org_menu(id, context['request'])
    return {'org_id': id, 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'is_editor': is_editor, 'request': context['request'], 'branding': branding, 'org_ka': org_ka, 'org_menu': org_menu}


@register.simple_tag
def film_left_banner():
    img_path = '%s/film_left_banner.swf' % settings.BACKGROUND_PATH
    try:
        with open(img_path, 'r') as f:
            exist = True
    except IOError:
        exist = False
        
    if exist:
        obj = '<a href="http://www.xn----9sbbiias0cmmbcpes2j0c.xn--p1ai/#!about1/c1o3p" target="_blank" class="flb_link"><div></div><object type="application/x-shockwave-flash" data="/upload/bg/film_left_banner.swf"><param name="movie" value="/upload/bg/film_left_banner.swf" /><param name="wmode" value="transparent" /></object></a>'
    else:
        obj = 'Banner'
    return obj

@register.inclusion_tag('seo_tags.html', takes_context = True)
def seo_tags(context):
    return {'request': context['request']}


@register.inclusion_tag('left_banner_adv.html', takes_context = True)
def left_banner(context, simple=False):
    from user_registration.views import left_banner_func

    request = context['request']
    site = context['request'].current_site
    city = request.current_user_city_id
    country = request.current_user_country_id

    obj = left_banner_func(request, site, city, country)
    obj['simple'] = simple

    return obj


@register.inclusion_tag('left_banner_user.html', takes_context = True)
def left_banner_user(context, user_id, is_my_profile, simple=False, lb=False):
    from user_registration.views import left_banner_user_func

    request = context['request']
    site = context['request'].current_site
    city = request.current_user_city_id
    country = request.current_user_country_id
    if lb is False:
        obj = left_banner_user_func(request, site, city, country, user_id)
    else:
        obj = lb
    obj['simple'] = simple
    obj['is_my_profile'] = is_my_profile
    return obj


@register.inclusion_tag('mobile_adv_bottom.html', takes_context = True)
def mobile_adv_bottom(context, simple=False):
    request = context['request']
    site = context['request'].current_site
    city = request.current_user_city_id
    country = request.current_user_country_id
    style = ''
    banner_city, banner_country, banner_other = ([], [], [])
    banner, banner_id, banner_url = (None, None, None)

    now = datetime.datetime.now()

    # выбрать оплаченную рекламу
    btype = '6'
    price = get_adv_price(btype)

    banners = SiteBanners.objects.filter(Q(country__pk=country) | Q(country=None), user__personinterface__money__gte=price, balance__gte=price, btype=btype, user__user__is_superuser=False, deleted=False, sites=site).values('url', 'id', 'views', 'country', 'cities__pk', 'style', 'name', 'text', 'dtime').order_by('-cities__pk')

    for i in banners:
        future = i['dtime'].date() + datetime.timedelta(days=13)
        if now.date() <= future:
            if i['cities__pk'] == request.current_user_city_id:
                banner_city.append(i)
            elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                banner_country.append(i)
            elif not i['country']:
                banner_other.append(i)
    
    if banner_city:
        banner = random.choice(banner_city)
    elif banner_country:
        banner = random.choice(banner_country)
    elif banner_other:
        banner = random.choice(banner_other)


    adv_type = 'banner'
    if banner:
        adv_type = 'adv'

        style = banner['style']
        swf = u'<span class="adv_anchor">%s</span>' % banner['name']
        swf += u'<div class="adv_text">%s</div>' % banner['text']

        banner_id = banner['id']
        banner_url = banner['url']

        if not request.bot:
            set_adv_view(request, banner['id'])
    else:
        # если нет оплаченной, то получаю установленную админом
        banner_city, banner_country, banner_other = ([], [], [])
        banner = None

        banners = SiteBanners.objects.filter(Q(country__pk=country) | Q(country=None), btype=btype, user__user__is_superuser=True, user__personinterface__money__gte=price, balance__gte=price, deleted=False, sites=site).values('file', 'url', 'id', 'views', 'country', 'cities__pk', 'style', 'name', 'text', 'dtime')
        
        for i in banners:
            future = i['dtime'].date() + datetime.timedelta(days=13)
            if now.date() <= future:
                if i['cities__pk'] == request.current_user_city_id:
                    banner_city.append(i)
                elif i['country'] == request.current_user_country_id and not i['cities__pk']:
                    banner_country.append(i)
                elif not i['country']:
                    banner_other.append(i)
    
        if banner_city:
            banner = random.choice(banner_city)
        elif banner_country:
            banner = random.choice(banner_country)
        elif banner_other:
            banner = random.choice(banner_other)


        if banner:
            if not request.bot:
                set_adv_view(request, banner['id'])

            # swf баннер
            if banner['style'] == None:
                adv_type = 'banner'
                swf = u'<object type="application/x-shockwave-flash" data="%s"><param name="movie" value="%s" /><param name="wmode" value="transparent" /></object>' % (banner['file'], banner['file'])
                if banner['url']:
                    swf = u'<noindex><a class="flb_link" id="flb_id_%s" href="%s" target="_blank" rel="nofollow">%s<div class="flb_layout"></div></a></noindex>' % (banner['id'], banner['url'], swf)
                else:
                    swf = u'<div class="flb_link" id="flb_id_%s">%s</div>' % (banner['id'], swf)
            # рекламный блок из конструктора блоков
            else:
                adv_type = 'adv'
                style = banner['style']
                swf = u'<span class="adv_anchor">%s</span>' % banner['name']
                swf += u'<div class="adv_text">%s</div>' % banner['text']

                banner_id = banner['id']
                banner_url = banner['url']

        else:
            swf = u'Banner'
    
    return {'swf_object': swf, 'request': request, 'adv_style': style, 'adv_type': adv_type, 'banner_id': banner_id, 'banner_url': banner_url, 'simple': simple}


@register.simple_tag
def linkanoid_links():
    from linkanoid.client import Client
    c = Client(
        charset='utf-8',
        TRUSTLINK_USER='e4b4a24eba7a02936a947af7b59866f7c7edba6d',
        host='www.kinoafisha.ru',
        tl_multi_site=True,
    )
    links = c.build_links()
    return links

    
@register.inclusion_tag('messanger.html', takes_context = True)
def messanger(context):
    return {'user': context['user']}
    
    
@register.inclusion_tag('poster_with_likes.html')
def poster_with_likes(id, rate, rate_imdb, rate_rotten, rate_reviews, like_cinema, like_home, like_recom, dis_seen, dis_recom, count_likes, count_dislikes, limit, poster, cl, tickets=''):
    return {'id': id, 'rate': rate, 'rate_imdb': rate_imdb, 'rate_rotten': rate_rotten, 'rate_views': rate_reviews, 'like_cinema': like_cinema, 'like_home': like_home, 'like_recom': like_recom, 'dis_seen': dis_seen, 'dis_recom': dis_recom, 'count_likes': count_likes, 'count_dislikes': count_dislikes, 'limit': limit, 'poster': poster, 'class': cl, 'tickets': tickets}

@register.inclusion_tag('mobile/poster_with_likes.html')
def poster_with_likes_mobile(id, rate, rate_imdb, rate_rotten, rate_reviews, like_cinema, like_home, like_recom, dis_seen, dis_recom, count_likes, count_dislikes, limit, poster, cl, tickets=''):
    return {'id': id, 'rate': rate, 'rate_imdb': rate_imdb, 'rate_rotten': rate_rotten, 'rate_views': rate_reviews, 'like_cinema': like_cinema, 'like_home': like_home, 'like_recom': like_recom, 'dis_seen': dis_seen, 'dis_recom': dis_recom, 'count_likes': count_likes, 'count_dislikes': count_dislikes, 'limit': limit, 'poster': poster, 'class': cl, 'tickets': tickets}


@register.inclusion_tag('film/film_block.html', takes_context = True)
def film_data(context, status):
    return {'page_status': status}

@register.inclusion_tag('mobile/film/film_block.html', takes_context = True)
def film_data_mobile(context, status):
    return {'page_status': status}

@register.inclusion_tag('vladaalfimov/vlada_menu.html', takes_context=True)
def vlada_menu(context, slug):
    org_menu = get_org_menu(slug, context['request'])
    return {'request': context['request'], 'org_id': slug, 'org_menu': org_menu}

@register.inclusion_tag('vladaalfimov/vlada_top_menu.html', takes_context=True)
def vlada_top_menu(context):
    request = context['request']
    current_site = request.current_site
    if current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'

    org_menu = get_org_menu(slug, context['request'])
    return {'request': context['request'], 'org_id': slug, 'org_menu': org_menu, 'LANGUAGES': settings.LANGUAGES}

@register.inclusion_tag('pmprepare/top_menu.html', takes_context=True)
def pmprepare_top_menu(context):
    request = context['request']
    slug = 'pmprepare'
    org_menu = get_org_menu(slug, request)
    return {'request': request, 'org_id': slug, 'org_menu': org_menu, 'LANGUAGES': settings.LANGUAGES}

@register.inclusion_tag('vladaalfimov/vlada_left_menu.html', takes_context=True)
def vlada_left_menu(context, vid):
    request = context['request']
    current_site = request.current_site
    if current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
    orgmenu, left_menu = get_org_left_menu(slug, vid, request)
    return {'request': context['request'], 'slug': slug, 'orgmenu': orgmenu, 'left_menu': left_menu}
    
@register.inclusion_tag('vladaalfimov/vlada_tools_menu.html', takes_context=True)
def vlada_tools_menu(context):
    request = context['request']
    current_site = request.current_site
    if current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
    return {'slug': slug, 'request': context['request']}

@register.inclusion_tag('vladaalfimov/socialblock.html', takes_context=True)
def social_icons(context):
    request = context['request']
    current_site = request.current_site
    data = {}
    if current_site.domain == 'vladaalfimovdesign.com.au':
        with open('%s/%s_social_icons.json' % (settings.API_EX_PATH, current_site.domain), 'r') as f:
            data = json.loads(f.read())
    return {'data': data}

@register.inclusion_tag('letsget/letsget_menu.html', takes_context=True)
def letsget_menu(context, slug):
    org_menu = get_org_menu(slug, context['request'])
    return {'request': context['request'], 'org_id': slug, 'org_menu': org_menu}


@register.inclusion_tag('letsget/org_menu.html', takes_context=True)
def org_menu(context, id, is_editor):
    offers = Organization_Tags.objects.filter(
        organization__uni_slug = id, 
        organizationtags__group_flag__in = ('3', '4')
    ).order_by('id')
    
    offers_tags = []
    advert_tags = []
    for i in offers:
        if i.organizationtags.group_flag == '3':
            offers_tags.append(i)
        elif i.organizationtags.group_flag == '4':
            advert_tags.append(i)
            
    return {'request': context['request'], 'offers_tags': offers_tags, 'advert_tags': advert_tags, 'org_id': id, 'is_editor': is_editor}

@register.inclusion_tag('sys_info.html', takes_context=True)
def sys_info(context, timer, cached_page):
    return {'request': context['request'], 'timer': timer, 'cached_page': cached_page}

'''
@register.inclusion_tag('forums/body_bg.html', takes_context=True)
def wf_bg_color(takes_context=True):
    from forums.views import FORUM_SH_STYLE
    request = context['request']
    wf_settings = request.session.get('fw_settings', {})
    wf_style = wf_settings.get('style', FORUM_SH_STYLE['1']['val'])
    return {'fw_body_bg': wf_style}
'''
    
@register.filter
def get_city_name_3(request):
    id = request.current_user_city_id
    cityName = NameCity.objects.filter(city__id=id, status=3)
    if len(cityName):
        res = cityName[0]
    else:
        res = request.current_user_city
#    res = '*'
#    cityName = NameCity.objects.filter(name = name)
#    res = cityName[0]
#    res = d
    return res

@register.filter
def get_site_name2018(request):
    try:
        id = request.current_user_city_id
        cityName = NameCity.objects.filter(city__id=id, status=3)
        if len(cityName):
            res = 'Киноафиша ' + str(cityName[0])
        else:
            res = 'Киноафиша ' + str(request.current_user_city)
    except:
        res = 'Киноафиша города'
    return res
