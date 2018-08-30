# -*- coding: utf-8 -*-
import re
import sys
import tempfile
import hotshot
import hotshot.stats
import json
import random
import datetime

from cStringIO import StringIO

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import auth
from django.utils import translation
from django.db import connection
from django.utils.log import getLogger
from django.http import HttpResponse, HttpResponseRedirect

from base.models import *
from user_registration.views import auth_user
from user_registration.func import org_peoples, login_counter
from kinoinfo_folder.func import low
from api.func import get_client_ip, get_country_by_ip
from base.views import get_bg


logger = getLogger(__name__)


class QueryCountDebugMiddleware(object):
    """
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """
    def process_response(self, request, response):
        if response.status_code == 200:
            total_time = 0

            for query in connection.queries:
                query_time = query.get('time')
                if query_time is None:
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)

            print '***** %s queries, total %s seconds' % (len(connection.queries), total_time)
        return response


class ProfileMiddleware(object):
    """
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode,
    but you really shouldn't add this middleware to any production configuration.
    * Only tested on Linux
    """
    def process_request(self, request):
        if settings.DEBUG and 'prof' in request.GET:
            self.tmpfile = tempfile.NamedTemporaryFile()
            self.prof = hotshot.Profile(self.tmpfile.name)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if settings.DEBUG and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def process_response(self, request, response):
        if settings.DEBUG and 'prof' in request.GET:
            self.prof.close()

            out = StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile.name)
            # stats.strip_dirs()
            stats.sort_stats('time', 'calls')
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if response and response.content and stats_str:
                response.content = "<pre>" + stats_str + "</pre>"

        return response


class XsSharing(object):
    """
    This middleware allows cross-domain XHR using the html5 postMessage API.
    Based off https://gist.github.com/426829
    """
    def process_request(self, request):
        if 'HTTP_ACCESS_CONTROL_REQUEST_METHOD' in request.META:
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = settings.XS_SHARING_ALLOWED_ORIGINS
            response['Access-Control-Allow-Methods'] = ",".join(settings.XS_SHARING_ALLOWED_METHODS)
            response['Access-Control-Allow-Headers'] = ",".join(settings.XS_SHARING_ALLOWED_HEADERS)
            response['Access-Control-Allow-Credentials'] = settings.XS_SHARING_ALLOWED_CREDENTIALS
            return response
        return None

    def process_response(self, request, response):
        response['Access-Control-Allow-Origin'] = settings.XS_SHARING_ALLOWED_ORIGINS
        response['Access-Control-Allow-Methods'] = ",".join(settings.XS_SHARING_ALLOWED_METHODS)
        response['Access-Control-Allow-Headers'] = ",".join(settings.XS_SHARING_ALLOWED_HEADERS)
        response['Access-Control-Allow-Credentials'] = settings.XS_SHARING_ALLOWED_CREDENTIALS
        return response


class SubdomainMiddleware:
    """ Make the subdomain publicly available to classes """

    def process_request(self, request):
        reg_b = re.compile(r"(android|bb\\d+|meego).+mobile|avantgo|bada\\/|blackberry|blazer|compal|elaine|fennec|hiptop|iemobile|ip(hone|od)|iris|kindle|lge |maemo|midp|mmp|mobile.+firefox|netfront|opera m(ob|in)i|palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|series(4|6)0|symbian|treo|up\\.(browser|link)|vodafone|wap|windows ce|xda|xiino", re.I|re.M)
        reg_v = re.compile(r"1207|6310|6590|3gso|4thp|50[1-6]i|770s|802s|a wa|abac|ac(er|oo|s\\-)|ai(ko|rn)|al(av|ca|co)|amoi|an(ex|ny|yw)|aptu|ar(ch|go)|as(te|us)|attw|au(di|\\-m|r |s )|avan|be(ck|ll|nq)|bi(lb|rd)|bl(ac|az)|br(e|v)w|bumb|bw\\-(n|u)|c55\\/|capi|ccwa|cdm\\-|cell|chtm|cldc|cmd\\-|co(mp|nd)|craw|da(it|ll|ng)|dbte|dc\\-s|devi|dica|dmob|do(c|p)o|ds(12|\\-d)|el(49|ai)|em(l2|ul)|er(ic|k0)|esl8|ez([4-7]0|os|wa|ze)|fetc|fly(\\-|_)|g1 u|g560|gene|gf\\-5|g\\-mo|go(\\.w|od)|gr(ad|un)|haie|hcit|hd\\-(m|p|t)|hei\\-|hi(pt|ta)|hp( i|ip)|hs\\-c|ht(c(\\-| |_|a|g|p|s|t)|tp)|hu(aw|tc)|i\\-(20|go|ma)|i230|iac( |\\-|\\/)|ibro|idea|ig01|ikom|im1k|inno|ipaq|iris|ja(t|v)a|jbro|jemu|jigs|kddi|keji|kgt( |\\/)|klon|kpt |kwc\\-|kyo(c|k)|le(no|xi)|lg( g|\\/(k|l|u)|50|54|\\-[a-w])|libw|lynx|m1\\-w|m3ga|m50\\/|ma(te|ui|xo)|mc(01|21|ca)|m\\-cr|me(rc|ri)|mi(o8|oa|ts)|mmef|mo(01|02|bi|de|do|t(\\-| |o|v)|zz)|mt(50|p1|v )|mwbp|mywa|n10[0-2]|n20[2-3]|n30(0|2)|n50(0|2|5)|n7(0(0|1)|10)|ne((c|m)\\-|on|tf|wf|wg|wt)|nok(6|i)|nzph|o2im|op(ti|wv)|oran|owg1|p800|pan(a|d|t)|pdxg|pg(13|\\-([1-8]|c))|phil|pire|pl(ay|uc)|pn\\-2|po(ck|rt|se)|prox|psio|pt\\-g|qa\\-a|qc(07|12|21|32|60|\\-[2-7]|i\\-)|qtek|r380|r600|raks|rim9|ro(ve|zo)|s55\\/|sa(ge|ma|mm|ms|ny|va)|sc(01|h\\-|oo|p\\-)|sdk\\/|se(c(\\-|0|1)|47|mc|nd|ri)|sgh\\-|shar|sie(\\-|m)|sk\\-0|sl(45|id)|sm(al|ar|b3|it|t5)|so(ft|ny)|sp(01|h\\-|v\\-|v )|sy(01|mb)|t2(18|50)|t6(00|10|18)|ta(gt|lk)|tcl\\-|tdg\\-|tel(i|m)|tim\\-|t\\-mo|to(pl|sh)|ts(70|m\\-|m3|m5)|tx\\-9|up(\\.b|g1|si)|utst|v400|v750|veri|vi(rg|te)|vk(40|5[0-3]|\\-v)|vm40|voda|vulc|vx(52|53|60|61|70|80|81|83|85|98)|w3c(\\-| )|webc|whit|wi(g |nc|nw)|wmlb|wonu|x700|yas\\-|your|zeto|zte\\-", re.I|re.M)

        domain_parts = request.get_host().split('.')
        if (len(domain_parts) > 2):
            if domain_parts[1] in ('com', 'net', 'biz', 'org', 'in'):
                subdomain = None
                domain = '.'.join(domain_parts)
            else:
                subdomain = domain_parts[0]
                if (subdomain.lower() == 'www'):
                    subdomain = None
                if subdomain == '127':
                    subdomain = None
                domain = '.'.join(domain_parts[1:])
            # для локального
            if domain == 'vseti.net:8000':
                domain = 'vsetiinter.net'
        else:
            subdomain = None
            domain = request.get_host()

        request.subdomain = subdomain
        request.domain = domain

        current_site = DjangoSite.objects.get_current()

        get_full_path = request.get_full_path().replace(u'/myapp.wsgi', '')

        if 'HTTP_USER_AGENT' in request.META:
            user_agent = request.META['HTTP_USER_AGENT']
            rb = reg_b.search(user_agent)
            rv = reg_v.search(user_agent[0:4])

            if rb or rv:
                mobile_cookie = request.COOKIES.get('mobile', '1')
                if mobile_cookie == '1':
                    if not subdomain and current_site.domain == 'kinoinfo.ru':
                        return HttpResponseRedirect("http://m.kinoinfo.ru/")
                    elif not subdomain and current_site.domain == 'kinoafisha.ru':
                        return HttpResponseRedirect("http://m.kinoafisha.ru/")
                    elif current_site.domain == 'vsetiinter.net' and subdomain == 'forums':
                        if '/women/' in get_full_path and '/m/' not in get_full_path:
                            if '/topic/' in get_full_path:
                                topic = get_full_path.split('topic/')[-1].replace('/', '')
                                return HttpResponseRedirect(reverse('women_forum', kwargs={'m': 'm', 'topic': topic}))
                            else:
                                return HttpResponseRedirect(reverse('women_forum', kwargs={'m': 'm'}))

        noob = False

        current_url = get_full_path.split(u'/api/')

        rating_img = False
        if '/ratingi' in get_full_path and '.png' in get_full_path:
            rating_img = True

        noindex = True if '/inform/' in get_full_path else False

        profile = None

        agent = False
        api = False
        if request.user.is_authenticated():
            try:
                profile = Profile.objects.select_related('person', 'user', 'personinterface').get(user=request.user)
            except Profile.DoesNotExist:
                auth.logout(request)

        if not rating_img and not request.user.is_authenticated():
            try:
                user_agent = low(request.META.get('HTTP_USER_AGENT', ''))
            except UnicodeDecodeError:
                open('LOGGING.TXT', 'a').write(str(request.META.get('HTTP_USER_AGENT')))
                raise UnicodeDecodeError

            agent = re.findall('(yandexbot|yandexdirect|googlebot|yahoo|bingbot|mj12bot|spider|dotbot|siteexplorer|ahrefsbot|org_bot|hosttracker|smtbot|xovibot|ccbot|semrushbot|crawl|slurp|typhoeus|sputnikbot|blexbot|exabot|ru_bot|crawler)', user_agent)

            # не авторегистрируем юзера если это запрос к API
            if len(current_url) == 1 or u'/details/' in request.get_full_path():
                if agent:
                    agent_name = '%s__(BOT)' % agent[0]
                    profile = Profile.objects.filter(accounts__login=agent_name).order_by('-id')

                    if len(profile) > 0:
                        profile = profile[0]

                    if profile:
                        # u = auth.authenticate(pk=profile.user_id, password='pswd')
                        # auth.login(request, u)

                        u = profile.user
                        u = auth.authenticate(username=u.username, password='pswd')
                        auth.login(request, u)
                    else:
                        auth_user(request)
                        profile = Profile.objects.select_related('person', 'user', 'personinterface').\
                            get(user=request.user)
                        acc = Accounts.objects.create(login=agent_name, validation_code=None, email=None)
                        profile.accounts.add(acc)
                else:
                    auth_user(request)
                    profile = Profile.objects.select_related('person', 'user', 'personinterface').get(user=request.user)
                    noob = True
                    # open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write(str(user_agent) + '\n')
                    # pr = request.user.get_profile() # !
                    # pr.path = user_agent # !
                    # pr.save() # !
            else:
                api = True

        request.noob = noob

        current_user_city = None
        current_user_city_id = None
        country = None
        accounts = None
        fio = None
        money = '0.00'
        money_int = '0'
        my_sites = []

        now = datetime.datetime.now()

        bg_disable = False
        if profile:
            bg_disable = SiteBanners.objects.filter(btype='0', user=profile, bg_disable_dtime_to__gte=now).exists()

        bg_filter = {'site': current_site, 'country__id': 2, 'subdomain': subdomain}
        is_admin = False

        capitals = {
            2: {'id': 1, 'name': 'Москва'},
            4: {'id': 48, 'name': 'Минск'},
            43: {'id': 42, 'name': 'Киев'},
            49: {'id': 105, 'name': 'Астана'}
        }

        if request.user.is_authenticated() and not rating_img:
            accounts = org_peoples([profile])
            accounts = accounts[0] if accounts else {}

            if accounts and u'__(BOT)' in accounts['acc']:
                agent = True
            else:
                fio = accounts.get('fio')

                country = accounts.get('country_id')
                if country:
                    person_city = accounts['city_id']
                    bg_filter['country__id'] = accounts['country_id']
                    bg_filter['city__id'] = person_city

                    if person_city:
                        current_user_city_id = person_city
                        current_user_city = accounts['city']

                if not current_user_city_id:
                    # Определяем страну и город юзера
                    if not country:
                        ip = get_client_ip(request)
                        # для локальной машины
                        if ip == '127.0.0.1':
                            ip = '91.224.86.255'
                        country = get_country_by_ip(ip)
                        country = country.id if country else 2
                        if not capitals.get(country):
                            country = 2

                if not api and not agent:
                    my_sites = list(profile.site_admin.all().values_list('id', flat=True))
                    is_admin = True if long(current_site.id) in my_sites else False

                    money = "%.2f" % profile.personinterface.money
                    money_int = int(profile.personinterface.money)

        if not country:
            country = 2

        if not current_user_city_id and not api and not rating_img:
            city = capitals.get(country)
            current_user_city_id = city['id']
            current_user_city = city['name']
            if profile:
                profile.person.city_id = current_user_city_id
                profile.person.country_id = country
                profile.person.save()

        new_messages = 0
        if not agent and not api and not rating_img and subdomain != 'forums':
            if profile:
                new_messages = NewsReaders.objects.filter(user=profile, status='0').count()

        current_language = translation.get_language()
        if current_site.domain == 'imiagroup.com.au' and not translation.get_language():
            translation.activate('en')
            current_language = 'en'
        elif current_site.domain == 'vsetiinter.net':
            if subdomain in ('ivanov',):
                translation.activate('en')
                current_language = 'en'

        if not agent and not api and not rating_img:
            login_counter(request)

        site_file = '%s/%s__mainpage.json' % (settings.SEO_PATH, current_site.domain)
        try:
            with open(site_file, 'r') as f:
                seo_data = json.loads(f.read())
            if seo_data.get('tags'):
                random.shuffle(seo_data['tags'])
        except IOError:
            seo_data = {}

        request.acc_list = accounts
        request.current_user_city = current_user_city
        request.current_user_city_id = current_user_city_id
        request.current_user_country_id = country
        request.profile = profile
        request.new_messages = new_messages
        request.fio = fio
        request.mymoney = money
        request.mymoney_int = money_int
        request.current_site = current_site
        request.is_admin = is_admin
        request.current_language = current_language
        request.noindex = noindex
        request.seo_data = seo_data
        request.bot = agent

        # Бэкграунд и рекламная ссылка
        adv = {'img': '', 'url': '', 'id': ''}
        if subdomain == 'forums':
            try:
                with open('%s/wf_top_banner.swf' % settings.BACKGROUND_PATH, 'r') as b:
                    b.read()
                adv['img'] = '%sbg/wf_top_banner.swf' % settings.MEDIA_URL
            except IOError:
                pass

            with open('%s/wf_ticker.txt' % settings.API_EX_PATH, 'r') as f:
                adv['url'] = f.read()
        else:
            if not agent and not api and not rating_img and not bg_disable:
                adv = get_bg(request)

        request.bg_img = adv['img']
        request.advert_url = adv['url']
        request.advert_id = adv['id']
