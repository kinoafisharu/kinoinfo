#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
from random import randrange
from collections import defaultdict

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.core.mail import get_connection, EmailMultiAlternatives
from django.utils.html import escape
from django.db.models import Q
from django.template.defaultfilters import date as tmp_date
from django.core.cache import cache

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits
from user_registration.views import get_usercard
from user_registration.func import *
from news.views import cut_description, create_news
from vladaalfimov.forms import *
from organizations.ajax import xss_strip2
from kinoinfo_folder.func import low, del_separator, uppercase
from articles.views import pagination as pagi



FORUM_SHOW_TOPIC = {
    u"1": {'title': '3 дня', 'val': 3, 'id': '1'},
    u"2": {'title': '7 дней', 'val': 7, 'id': '2'},
    u"3": {'title': '15 дней', 'val': 15, 'id': '3'},
    u"4": {'title': '30 дней', 'val': 30, 'id': '4'},
    u"5": {'title': 'Все', 'val': 0, 'id': '5'},
}

FORUM_SHOW_LAST = {
    u"1": {'title': '50 тем', 'val': 50, 'id': '1'},
    u"2": {'title': '100 тем', 'val': 100, 'id': '2'},
    u"3": {'title': '300 тем', 'val': 300, 'id': '3'},
}

FORUM_SHOW_STYLE = {
    u"1": {'title': 'Милитари', 'id': '1'},
    u"2": {'title': 'Белая', 'id': '2'},
    u"3": {'title': 'Кремовая', 'id': '3'},
}

FORUM_SH_STYLE = {
    u"1": {'val': '#FFFFFF', 'id': '1'}, #белый
    u"2": {'val': '#EBFDFD', 'id': '2'}, #берюзовый
    u"3": {'val': '#E7E7F2', 'id': '3'}, #голубой
    u"4": {'val': '#E2E2E2', 'id': '4'}, #серый
    u"5": {'val': '#DFD2DF', 'id': '5'}, #фиолетовый
    u"6": {'val': '#E8DED5', 'id': '6'}, #каричневый
    u"7": {'val': '#E6E6B8', 'id': '7'}, #зеленый
    u"8": {'val': '#FFFFCC', 'id': '8'}, #желтый
}

FORUM_SMILES = {
    u":-)": {'id': '01', 'val': ':-) '},
    u":-(": {'id': '02', 'val': ':-( '},
    u";-)": {'id': '03', 'val': ';-) '},
    u":-P": {'id': '04', 'val': ':-P '},
    u"8-)": {'id': '05', 'val': '8-) '},
    u":-D": {'id': '06', 'val': ':-D '},
    u":-[": {'id': '07', 'val': ':-[ '},
    u"=-O": {'id': '08', 'val': '=-O '},
    u":`(": {'id': '09', 'val': ':`( '},
    u":-|": {'id': '10', 'val': ':-| '},
    u"[:-}": {'id': '11', 'val': '[:-} '},
    u"%)": {'id': '12', 'val': '%) '},
    u"*HELP*": {'id': '13', 'val': '*HELP* '},
    u"*UMBRELLA*": {'id': '14', 'val': '*UMBRELLA* '},
    u"*ROSE*": {'id': '15', 'val': '*ROSE* '},
    u"!:[": {'id': '16', 'val': '!:[ '},
    u"*KISSED*": {'id': '17', 'val': '*KISSED* '},
    u"*THUMBS_UP*": {'id': '18', 'val': '*THUMBS_UP* '},
    u"*DANCE*": {'id': '19', 'val': '*DANCE* '},
    u"*BLOW*": {'id': '20', 'val': '*BLOW* '},
    u":-*": {'id': '21', 'val': ':-* '},
    u"*JOKINGLY*": {'id': '22', 'val': '*JOKINGLY* '},
    u"*DAEMON*": {'id': '23', 'val': '*DAEMON* '},
    u":-!": {'id': '24', 'val': ':-! '},
}


def index(request):
    return render_to_response('forums/main.html', {}, context_instance=RequestContext(request))


@never_cache
def addfile(request, m=None):
    if m and m != 'm':
        raise Http404
    if request.POST:
        from user_registration.func import md5_string_generate
        from api.func import resize_image
        
        next = request.POST.get('fnext')
        new = request.POST.get('new_msg_id')
        
        f = request.FILES.get('file')
        
        # если есть файл
        if f and f.size < 5000000:
            
            file_format = low(f.name.encode('utf-8'))
            img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif)$', file_format)
            # если подходит формат
            if img_format:

                img_path = '%s/%s' % (settings.WF_PATH, 'women')
                try: os.makedirs(img_path)
                except OSError: pass

                # если существует сообщение для файла
                try:
                    obj = WFOpinion.objects.using('afisha').get(pk=new)
                except WFOpinion.DoesNotExist: 
                    pass
                else:
                    # если юзер загружающий файл является автором сообщения
                    if obj.user_id == request.profile.kid:
                        
                        img_obj = f.read()
                        img_name = '%s.%s' % (new, img_format[0])
                        img_path_tmp = '%s/%s' % (img_path, img_name)
                        
                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)
                            
                        resized = resize_image(1000, None, img_obj, 1500)
                        if resized:
                            resized.save(img_path_tmp)

        if next:
            if m:
                return HttpResponseRedirect(reverse('women_forum', kwargs={'m': m, 'topic': next}))
            else:
                return HttpResponseRedirect(reverse('women_forum', kwargs={'topic': next}))
        
        if m:
            return HttpResponseRedirect(reverse('women_forum', kwargs={'m': m}))
        else:
            return HttpResponseRedirect(reverse('women_forum'))
    else:
        raise Http404

@never_cache
def settings_save(request, m=None):
    if m and m != 'm':
        raise Http404
    if request.POST:
        topic = request.POST.get('show_topic')
        topic = FORUM_SHOW_TOPIC.get(topic)
        topic = topic['val'] if topic else FORUM_SHOW_TOPIC['2']['val']

        last = request.POST.get('show_last')
        last = FORUM_SHOW_LAST.get(last)
        last = last['val'] if last else FORUM_SHOW_LAST['2']['val']
        
        style = request.POST.get('sh_style')
        style = FORUM_SH_STYLE.get(style)
        style = style['val'] if style else FORUM_SH_STYLE['1']['val']
        
        msg_open = request.POST.get('msg_open', 0)
        if msg_open:
            msg_open = 1
        
        next = request.POST.get('next')
        
        theme = request.POST.getlist('checker')
        if not theme:
            theme = ['5',]

        #request.session['fw_settings'] = {'topic': topic, 'last': last, 'style': style, 'theme': theme, 'msg_open': msg_open}
        request.session['fw_theme_settings'] = theme
        request.session['fw_style_settings'] = style

        person_settings = request.profile.personinterface
        person_settings.wf_topic = topic
        person_settings.wf_last = last
        person_settings.wf_style = style
        person_settings.wf_msg_open = msg_open
        person_settings.save()
        
        if next:
            if m:
                return HttpResponseRedirect(reverse('women_forum', kwargs={'m': m, 'topic': next}))
            else:
                return HttpResponseRedirect(reverse('women_forum', kwargs={'topic': next}))
    if m:
        return HttpResponseRedirect(reverse('women_forum', kwargs={'m': m}))
    else:
        return HttpResponseRedirect(reverse('women_forum'))

@never_cache
def women(request, m=None, topic=None):
    if m and m != 'm':
        raise Http404

    from forums.ajax import wf_ignored_msgs
    timer = time.time()
    
    if request.POST and 'refresh' in request.POST:
        if m:
            return HttpResponseRedirect(reverse('women_forum', kwargs={'m': m}))
        else:
            return HttpResponseRedirect(reverse('women_forum'))

    #wf_settings = request.session.get('fw_settings', {})
    
    default_show_topic = FORUM_SHOW_TOPIC['2']['val']
    default_show_last = FORUM_SHOW_LAST['1']['val']
    default_sh_style = FORUM_SH_STYLE['1']['val']

    wf_msg_open = True
    wf_theme = request.session.get('fw_theme_settings', [])
    wf_topic, wf_last, wf_style = (default_show_topic, default_show_last, default_sh_style)
    
    if request.profile:
        interface = request.profile.personinterface
        if interface.wf_topic is not None:
            wf_topic = None if int(interface.wf_topic) == 0 else interface.wf_topic
        if interface.wf_last is not None:
            wf_last = interface.wf_last
        if interface.wf_style is not None:
            wf_style = interface.wf_style
        if interface.wf_msg_open is not None:
            wf_msg_open = interface.wf_msg_open
    
    def tree_level(parent):
        for item in sorted(parent_map[parent]):
            yield q[item]
            sub_items = list(tree_level(item))
            if sub_items:
                yield sub_items
    
    def printTree(L, new, ind, readed_msg, data=0):
        for i in L:
            if isinstance(i, list):
                data = printTree(i, new, ind, readed_msg, data)
            else:
                if i.id not in readed_msg:
                    if ind == 0 and int(i.parent) != new:
                        data += 1
                    elif ind == 1:
                        data += 1
                        
        return data
    

    
    readed_msg = []
    nickname = ''
    ignored = {'msg': [], 'author': []}
    kid = request.profile.kid if request.profile else None
    
    if kid:
        try:
            #nick = request.user.first_name
            reg_user = RegisteredUsers.objects.only('nickname').using('afisha').get(pk=kid)
            nickname = reg_user.nickname
        except RegisteredUsers.DoesNotExist: pass

        ignored = wf_ignored_msgs(kid)

        readed_msg = list(WFUser.objects.using('afisha').filter(user=kid).values_list('opinion', flat=True))

    categories = WFOpinion.objects.using('afisha').only('id', 'subject').filter(type_obj=1, type=5).order_by('id')
    
    
    
    if not wf_theme:
        wf_theme = [str(i.id) for i in categories]

 
    settings_categories = []
    topics = {}
    for i in categories:
        if str(i.id) in wf_theme:
            topics[i.id] = {'id': i.id, 'subject': i.subject, 'topics': []}
            settings_categories.append({'obj': i, 'set': True})
        else:
            settings_categories.append({'obj': i, 'set': False})
    
    first_load = None
    first_title = ''
    first_cat_id = None
    topics_list = []
    
    filter = {}
    if wf_topic:
        now = datetime.datetime.now()
        from_date = now - datetime.timedelta(days=wf_topic)
        filter = {'date__gte': from_date}
    else:
        from_date = datetime.datetime(1990, 1, 1, 0, 0)
    

    topics_left_data = []
    branches = []
    
    themes = WFOpinion.objects.using('afisha').only('id', 'subject').filter(pk__in=wf_theme)
    
    filter = {'deleted': False}
    if request.user.is_superuser:
        filter = {}
    
    search_query = request.GET.get('q','')
    if search_query:
        search_query = BeautifulSoup(search_query, from_encoding="utf-8").text
        if len(search_query.replace(' ','').strip()) > 3:
            search_query = search_query
        else:
            search_query = ''
    
    
    
    themes_ids = {}
    for i in themes:
        themes_ids[i.id] = i.subject
     
    topics_in_category = {}
    topics_deleted = {}
    '''
    for i in WFOpinion.objects.using('afisha').only('id', 'parent', 'deleted').filter(parent__in=themes_ids.keys(), **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg'])).order_by('-date')[:15000]:
        if not topics_in_category.get(i.parent):
            subj = themes_ids.get(i.parent)
            topics_in_category[i.parent] = {'ids': [i.id], 'subj': subj}
        topics_in_category[i.parent]['ids'].append(i.id)
        if not topics_deleted.get(i.id):
            topics_deleted[i.id] = i.deleted
    '''
    # Получаю топики для списка категорий (например: для категории "Доска объявлений" 50 топиков, и т.д.)
    for k in themes_ids.keys():
        for i in WFOpinion.objects.using('afisha').only('id', 'parent', 'deleted').filter(parent=k, **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg'])).order_by('-date')[:wf_last]:
        
            if not topics_in_category.get(k):
                subj = themes_ids.get(k)
                topics_in_category[k] = {'ids': [i.id], 'subj': subj}
            topics_in_category[k]['ids'].append(i.id)
            if not topics_deleted.get(i.id):
                topics_deleted[i.id] = i.deleted
            
    
    for k, v in topics_in_category.iteritems():
        if search_query:
            messages_in_topics = WFOpinion.objects.using('afisha').only('id', 'branch', 'date', 'deleted').filter(Q(branch__in=v['ids']) | Q(pk__in=v['ids']), Q(subject__icontains=search_query) | Q(text__icontains=search_query), **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg'])).order_by('-date')[:2000]
        else:
            # получаю все сообщения для каждого топика
            messages_in_topics = WFOpinion.objects.using('afisha').only('id', 'branch', 'date', 'deleted').filter(Q(branch__in=v['ids']) | Q(pk__in=v['ids']), date__gte=from_date, **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg'])).order_by('-date')[:2000]
        
        
        msg_dict = {}
        for msg in messages_in_topics:
            branch = msg.branch if msg.branch else msg.id
            if not msg_dict.get(branch):
                deleted = topics_deleted.get(branch)
                msg_dict[branch] = {'id': branch, 'date': msg.date, 'count': 0, 'cat': v['subj'], 'cat_id': k, 'del': deleted}
                branches.append(branch)

        
        topics_left_data.append({
            'id': k,
            'subject': v['subj'],
            'topics': sorted(msg_dict.values(), key=operator.itemgetter('date'), reverse=True),
        })
    

    brnch_dict = {}
    for i in WFOpinion.objects.using('afisha').select_related('user__nickname').filter(pk__in=branches, **filter).only('id', 'nick', 'subject', 'user__nickname', 'parent'):
        try:
            nick = i.nick if i.nick else i.user.nickname
        except AttributeError:
            nick = ''
        brnch_dict[i.id] = {'nick': nick, 'count': 0, 'subject': i.subject, 'parent': i.parent, 'msgs': []}
    
    
    counter = {}
    
    for i in WFOpinion.objects.using('afisha').only('id', 'branch').filter(branch__in=brnch_dict.keys(), **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg']) | Q(parent__in=ignored['msg'])):
        
        if counter.get(i.branch):
            counter[i.branch]['count'] += 1
        else:
            counter[i.branch] = {'count': 1}
            


    #if not wf_msg_open:
    if kid:
        msgs_data = WFOpinion.objects.using('afisha').only('id', 'parent', 'branch').filter(Q(branch__in=brnch_dict.keys()) | Q(pk__in=brnch_dict.keys())).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg']))

        for i, val in brnch_dict.iteritems():
            for md in msgs_data:
                if md.id == i or md.branch == i:
                    brnch_dict[i]['msgs'].append(md)

        for i, val in brnch_dict.iteritems():
            
            q = dict(zip([qi.id for qi in val['msgs']], val['msgs']))
            
            parent_map = defaultdict(list)
            
            for item in q.itervalues():
                parent_map[item.parent].append(item.id)

            read_n = 0
            
            for ind, j in enumerate((int(val['parent']), 0)):
                tmp = list(tree_level(j))
                read_n += printTree(tmp, j, ind, readed_msg)
            
            if counter.get(i):
                counter[i]['no_readed'] = read_n


    
    # добавляем к данным Автора темы и дату время последнего сообщение в теме
    for i in topics_left_data:
        for t in i['topics']:
            x = brnch_dict.get(t['id'])
            count = counter.get(t['id'], {'count': 0, 'no_readed': 0})
            if x:
                t['author'] = x['nick']
                t['count'] = count['count']
                t['no_readed'] = count.get('no_readed', 0)
                t['subject'] = x['subject']
    
    data = sorted(topics_left_data, key=operator.itemgetter('id'))
    stopic = sorted(FORUM_SHOW_TOPIC.values(), key=operator.itemgetter('id'))
    slast = sorted(FORUM_SHOW_LAST.values(), key=operator.itemgetter('id'))
    sstyle = sorted(FORUM_SH_STYLE.values(), key=operator.itemgetter('id'))
    smiles = sorted(FORUM_SMILES.values(), key=operator.itemgetter('id'))

    if topic:
        try:
            topic_obj = WFOpinion.objects.using('afisha').only('branch').get(id=topic)
            topic_br = WFOpinion.objects.using('afisha').only('parent').get(id=topic_obj.branch)
            first_load = topic
            for i in categories:
                if i.id == topic_br.parent:
                    first_title = i.subject
                    first_cat_id = i.id
                    break
        except WFOpinion.DoesNotExist: pass
            
    if not first_load:
        for i in data:
            if first_load:
                break
            for t in i['topics']:
                first_load = t['id']
                first_title = t['cat']
                first_cat_id = t['cat_id']
                break

    newmsg = request.session.get('wf_new_msg','')
    if newmsg:
        request.session['wf_new_msg'] = ''
    
    next_level = ''
    try:
        level_obj = WomenForumIgnoreLevel.objects.get(user=kid)
        now = datetime.datetime.now()
        
        future = level_obj.dtime + datetime.timedelta(days=7)
        if future < now and level_obj.type < 3:
            level_obj.type += 1
            level_obj.dtime = now
            level_obj.save()
            
        if level_obj.type < 3:
            next_level = level_obj.dtime + datetime.timedelta(days=7)
            next_level = tmp_date(next_level, "d E в H:i")
        level = level_obj.type
    except WomenForumIgnoreLevel.DoesNotExist:
        level = 1

    timer = '%5.2f' % (time.time()-timer)

    template = 'forums/women_main.html'
    if m:
        template = 'mobile/forums/women_main.html'

    return render_to_response(template, {'data': data, 'FORUM_SHOW_TOPIC': stopic, 'FORUM_SHOW_LAST': slast, 'wf_topic': wf_topic, 'wf_last': wf_last, 'wf_style': wf_style, 'categories': settings_categories, 'topic': topic, 'first_load': first_load, 'first_title': first_title, 'first_cat_id': first_cat_id, 'FORUM_SH_STYLE': sstyle, 'FORUM_SMILES': smiles, 'nickname': nickname, 'search_query': search_query, 'newmsg': newmsg, 'level': level, 'next_level': next_level, 'wf_msg_open': wf_msg_open, 'timer': timer}, context_instance=RequestContext(request))
    

def wf_logout(request, m=None):
    from django.contrib import auth
    if request.POST and 'wf_logout' in request.POST:
        auth.logout(request)
    ref = request.META.get('HTTP_REFERER', '/').split('?')[0]
    return HttpResponseRedirect(ref)


@only_superuser
@never_cache
def wf_banner(request, m=None):
    if m and m != 'm':
        raise Http404
    if request.POST:
        img_path = '%s/wf_top_banner.swf' % settings.BACKGROUND_PATH
        
        if 'save' in request.POST and 'banner' in request.FILES:
            file = request.FILES.get('banner').read()
            with open(img_path, 'wb') as f:
                f.write(file)
                
        elif 'delete' in request.POST:
            try:
                os.remove(img_path)
            except OSError: pass  
        
        
        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404

@only_superuser
@never_cache
def wf_string(request, m=None):
    if m and m != 'm':
        raise Http404

    if request.POST and 'save' in request.POST:
        content = request.POST['text'].encode('utf-8')
        with open('%s/wf_ticker.txt' % settings.API_EX_PATH, 'w') as f:
            f.write(content)

        ref = request.META.get('HTTP_REFERER', '/')
        return HttpResponseRedirect(ref)
    else:
        raise Http404


