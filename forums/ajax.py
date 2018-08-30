# -*- coding: utf-8 -*- 
import os
import operator
import datetime
import time
from collections import defaultdict

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.views.decorators.gzip import gzip_page
from django.db.models import Q, F
from django.template.defaultfilters import date as tmp_date
from django.conf import settings

from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup

from base.models import *
from news.views import cut_description
from forums.views import FORUM_SMILES


def html_entities_to_tags(txt):
    data = {
        u'&#160;': u'',
        u'&#60;': u'<',
        u'&#62;': u'>',
        u'&#38;': u'&',
        u'&nbsp;': u'',
        u'&lt;': u'<',
        u'&gt;': u'>',
        u'&amp;': u'&',
    }
    for k, v in data.iteritems():
        txt = txt.replace(k, v)
    return txt
        
def wf_msg_files():
    files = {}
    path = '%s/%s' % (settings.WF_PATH, 'women')
    try:
        for f in os.listdir(path):
            if os.path.isfile('%s/%s' % (path, f)):
                files[f.split('.')[0]] = f
    except OSError: pass
    return files
        
def wf_ignored_msgs(user_kid):
    ignored = {'msg': [], 'author': []}
    if user_kid:
        for i in WomenForumIgnored.objects.filter(user=user_kid):
            if i.type in (1, 2):
                ignored['msg'].append(i.msg)
            elif i.type == 3:
                ignored['author'].append(i.author)
    return ignored


def wf_count_ignored_msgs(msgs, authors):
    ignored_m = {}
    ignored_t = {}
    ignored_a = {}
    
    for i in WomenForumIgnored.objects.filter(Q(msg__in=msgs) | Q(author__in=authors)):
        if i.msg:
            if i.type == 1:
                if not ignored_m.get(i.msg):
                    ignored_m[i.msg] = {'count': 0, 'users': []}
                ignored_m[i.msg]['count'] += 1
                ignored_m[i.msg]['users'].append(i.user)
            elif i.type == 2:
                if not ignored_t.get(i.msg):
                    ignored_t[i.msg] = {'count': 0, 'users': []}
                ignored_t[i.msg]['count'] += 1
                ignored_t[i.msg]['users'].append(i.user)
        else:
            if i.author:
                if not ignored_a.get(i.author):
                    ignored_a[i.author] = {'count': 0, 'users': []}
                ignored_a[i.author]['count'] += 1
            if i.msg:
                ignored_a[i.msg]['users'].append(i.user)
                
    return {'msg': ignored_m, 'topic': ignored_t, 'author': ignored_a}


def msg_html_wrapper(user_kid, obj, files, wfstat, statistic, likes, is_mobile):
    html = ''
    if obj:
        text = obj.text
        subject = obj.subject
        for key, val in FORUM_SMILES.iteritems():
            text = text.replace(key, u'<img src="%sbase/images/forums/smiles/sk_%s.gif" alt="%s"/>' % (settings.STATIC_URL, val['id'], key))
            subject = subject.replace(key, u'<img src="%sbase/images/forums/smiles/sk_%s.gif" alt="%s"/>' % (settings.STATIC_URL, val['id'], key))
        
        date_msg = tmp_date(obj.date, "d b Y")
        
        try:
            nick = obj.nick if obj.nick else obj.user.nickname
        except AttributeError:
            nick = ''
        
        img = files.get(str(obj.id))
        if img:
        
            filesize = ''
            try:
                filepath = '%s/forums/women/%s' % (settings.MEDIA_ROOT, img)
                filesize = os.path.getsize(filepath)
                if filesize < 1048576:
                    filesize = '%.2f KB' % (float(filesize)/1024)
                else:
                    filesize = '%.2f MB' % (float(filesize)/(1024*1024))
            except (OSError, IOError): pass

            url = '%sforums/women/%s' % (settings.MEDIA_URL, img)
            img = '<a class="fancybox wf_img" href="%s"><div> IMG<br />%s</div></a>' % (url, filesize)
        else:
            img = ''
        
        like_data = likes.get(obj.id)
        
        disl = 0
        like = 0
        if like_data:
            disl = like_data['d']
            like = like_data['l']
        
        edit_btn = ''
        if user_kid == obj.user_id:
            edit_btn = u'<input type="button" class="wf_edit" title="Редактировать" />'
            if not is_mobile:
                edit_btn += '''<input type="button" class="wf_xlike" value="%s" disabled />
                    <input type="button" class="wf_xdlike" value="%s" disabled />
                    ''' % (like, disl)
        elif user_kid and not is_mobile:
            edit_btn = u'''
                <input type="button" class="wf_ignore" title="Игнорировать"/>
                <input type="button" class="wf_like like" id="t1" title="Нравится" value="%s" />
                <input type="button" class="wf_like dislike" id="t0" title="Не нравится" value="%s" />
                <p id="wfi"></p>
                ''' % (like, disl)

        count = wfstat.get(obj.id, 0)
        
        msg_ignored = statistic['msg'].get(obj.id, {'count': 0})['count']
        topic_ignored = statistic['topic'].get(obj.id, {'count': 0})['count']
        author_ignored = statistic['author'].get(obj.id, {'count': 0}) if obj.user_id else {'count': 0}
        author_ignored = author_ignored['count']
        
        ignored_txt = u''
        if msg_ignored:
            ignored_txt += u'%sх' % msg_ignored
        if topic_ignored:
            if msg_ignored:
                ignored_txt += u'+'
            ignored_txt += u'%sхх' % topic_ignored
        if author_ignored:
            if msg_ignored or topic_ignored:
                ignored_txt += u'+'
            ignored_txt += u'%sххх' % author_ignored
        if ignored_txt:
            ignored_txt = ' <p id="igc"></p><a href="#" id="igi">%s</a> -' % ignored_txt
        
        
        html += u'''
            <tr class="fmsg" id="%s" >
            <td colspan="3">
            <div class="fmsg_h"><b>%s</b><span>%s</span>, %s</div>
            <div class="fmsg_b"><b>%s</b>%s <span>%s</span></div>
            <div class="fmsg_f">
                <input type="button" value="Ответить" id="answ" onclick="wf_msg(3, %s)"/> 
                <div class="wf_eye" title="Просмотров"><i>%s</i></div> 
                <div id="fmsg_fr">%s %s </div>
            </div>
            </td>
            </tr>
            ''' % (obj.id, nick, obj.date.strftime('%H:%M'), date_msg, obj.subject, img, text, obj.id, count, ignored_txt, edit_btn)
    return html
        

@dajaxice_register
def get_forum_topic(request, id, val):
    try:
        ref = request.META.get('HTTP_REFERER','').split('?')[0]
        is_mobile = True if '/m/' in ref else False


        step_for_admin = 0
        vars_for_admin = []
        
        now_dtime = datetime.datetime.now()
        now = now_dtime.date()
        
        user_kid = request.profile.kid
        
        step_for_admin = 2
        
        ignored = wf_ignored_msgs(user_kid)

        step_for_admin = 3

        files = wf_msg_files()

        step_for_admin = 4
        
        tmp_dict = {}

        profiles = {}

        def printTree(L, new, readed_msg, data, margin=0):
            for i in L:
                if isinstance(i, list):
                    data = printTree(i, new, readed_msg, data, margin)
                else:
                    if int(i.parent) == new:
                        margin = 0
                    else:
                        idnt = tmp_dict.get(i.parent)
                        if not is_mobile:
                            if not idnt:
                                margin = 15
                            else:
                                margin = idnt + 15
                            
                    tmp_dict[i.id] = margin
                    
                    idn = '<div class="nxt" style="margin-left: %spx;"></div>' % margin

                    msg_date = i.date.date()
                    time_nav = ''
                    time_txt = ''
                    if msg_date == now:
                        time_nav = u'mt1'
                        time_txt = u'Добавлено сегодня'
                    elif msg_date == (now - datetime.timedelta(days=1)):
                        time_nav = u'mt2'
                        time_txt = u'Добавлено вчера'
                    elif msg_date == (now - datetime.timedelta(days=2)):
                        time_nav = u'mt3'
                        time_txt = u'Добавлено позавчера'
                    elif msg_date < (now - datetime.timedelta(days=2)) and msg_date >= (now - datetime.timedelta(days=6)):
                        time_nav = u'mt4'
                        time_txt = u'Добавлено в течении недели'
                    elif msg_date < (now - datetime.timedelta(days=6)):
                        time_nav = u'mt5'
                        time_txt = u'Добавлено давно'
                    
                    if i.id != int(val) and i.id not in readed_msg:
                        time_nav = u'mt6'
                        data['2'] = True
                    
                    
                    
                    if time_txt:
                        time_nav = u'<div id="%s" title="%s"></div>' % (time_nav, time_txt)
                    
                    try:
                        nick = i.nick if i.nick else i.user.nickname
                    except AttributeError:
                        nick = ''
                        
                    kinoinfo_user_id = None
                    if i.user:
                        kinoinfo_user_id = profiles.get(i.user.id)

                    subject = cut_description(i.subject, True, 48) if len(i.subject) > 58 else i.subject
                    short_txt = cut_description(i.text, False, 80)
                    
                    minus_txt = ''
                    if short_txt:
                        if not is_mobile:
                            if len(short_txt) >= 80:
                                short_txt = ' title="%s..."' % short_txt 
                            else:
                                short_txt = ' title="%s"' % short_txt 
                    else:
                        short_txt = ''
                        minus_txt = ' (-)'

                    subject = '%s%s' % (subject, minus_txt)

                    data['1'] += u'<tr href="#%s" class="branch"><td>' % i.id
                    if request.user.is_superuser and not is_mobile:
                        if i.deleted:
                            data['1'] += u'<div class="wf_reuse wfr item_ho" id="wfr_%s" title="Восстановить"></div>' % i.id
                        else:
                            data['1'] += u'<div class="wf_del wfd item_ho" id="wfd_%s" title="Удалить"></div>' % i.id

                    if kinoinfo_user_id and request.user.is_superuser:
                        nick_html = u'<a href="http://ya.vsetiinter.net/user/profile/%s/" target="_blank">%s</a>' % (kinoinfo_user_id, nick)
                    else:
                        nick_html = nick

                    data['1'] += u'''
                        <div class="tlink item_ho"%s>%s%s%s</div>
                        </td>
                        <td><div>%s<span>%s</span></div></td>
                        <td><div>%s</div></td>
                        </tr>
                        ''' % (short_txt, idn, time_nav, subject, i.date.strftime('%d.%m'), i.date.strftime('%H:%M'), nick_html)
            return data
        
        
        def printMsgList(L, ldata, wfstat_dict, ignored_statistic, likes):
            for i in L:
                if isinstance(i, list):
                    ldata = printMsgList(i, ldata, wfstat_dict, ignored_statistic, likes)
                else:
                    ldata += msg_html_wrapper(user_kid, i, files, wfstat_dict, ignored_statistic, likes, is_mobile)
            return ldata
        
        
        def tree_level(parent):
            for item in sorted(parent_map[parent]):
                yield q[item]
                sub_items = list(tree_level(item))
                if sub_items:
                    yield sub_items
        
        data = u''
        msg_list = u''
        
        step_for_admin = 5
        
        try:
            main = WFOpinion.objects.using('afisha').only('parent', 'deleted').get(id=id)
        except WFOpinion.DoesNotExist:
            return simplejson.dumps({'status': True, 'error': 'Error: Topic does not exist'})
        
        step_for_admin = 6
        
        filter = {'deleted': False}
        if request.user.is_superuser:
            filter = {}
        
        next = False if main.deleted and filter else True
        if next:
            next = False if main.id in ignored['msg'] else True
            if next:
                defer = ['type_obj', 'type', 'first', 'locked', 'other']

                step_for_admin = 7

                q = list(WFOpinion.objects.using('afisha').select_related('user').defer(*defer).filter(Q(branch=id) | Q(pk=id), **filter).exclude(Q(user__id__in=ignored['author']) | Q(pk__in=ignored['msg'])))

                step_for_admin = 8

                q = dict(zip([i.id for i in q], q))
                
                step_for_admin = 9
                
                readed_msg = q.keys()
                wfstat_dict = {}
                ignored_statistic = {}
                
                step_for_admin = 10
                
                wfstat = WFStat.objects.using('afisha').filter(opinion__in=q.keys())
                
                step_for_admin = 11
                
                #wfstat.update(count=F('count')+1, date=now_dtime)
                for i in wfstat:
                    
                    if user_kid and int(val) == int(id) and i.opinion == int(val):
                        i.count += 1
                        i.save()

                    wfstat_dict[i.opinion] = i.count

                step_for_admin = 12

                authors = set([i.user_id for i in q.values() if i.user_id])
                
                #vars_for_admin = [q.keys(), authors]
                step_for_admin = 13
                
                
                ignored_statistic = wf_count_ignored_msgs(q.keys(), authors)
            
                
                for i in list(Profile.objects.filter(kid__in=authors, auth_status=True).values('user', 'kid')):
                    profiles[i['kid']] = i['user']

                step_for_admin = 14
            
                if user_kid:
                    readed_msg = list(WFUser.objects.using('afisha').filter(user=user_kid, opinion__in=q.keys()).values_list('opinion', flat=True))
                
                step_for_admin = 15
                
                likes = {}
                for i in WomenForumLikes.objects.filter(msg__in=q.keys()):
                    if not likes.get(i.msg):
                        likes[i.msg] = {'l': 0, 'd': 0}
                    if i.like_type:
                        likes[i.msg]['l'] += 1
                    else:
                        likes[i.msg]['d'] += 1
                
                step_for_admin = 16
                
                parent_map = defaultdict(list)
                
                step_for_admin = 17
                
                for item in q.itervalues():
                    parent_map[item.parent].append(item.id)

                step_for_admin = 18
                
                data = ''
                msg_list = ''
                not_readed = False
                for j in (main.parent, 0):
                    tmp = list(tree_level(j))
                    xdata = printTree(tmp, j, readed_msg, {'1': '', '2': not_readed})
                    
                    data += xdata['1']
                    if not not_readed:
                        not_readed = xdata['2']
                        
                    msg_list += printMsgList(tmp, '', wfstat_dict, ignored_statistic, likes)

                step_for_admin = 19

                new_msg_btn = u'<tr><td colspan="3"><div class="tlink" style="padding: 20px 0 20px 0;"><input type="button" value="Новое сообщение" onclick="wf_msg(2, %s)"/></div></td></tr>' % id

                if is_mobile:
                    data = u'%s%s%s' % (new_msg_btn, data, new_msg_btn)
                else:
                    data = u'%s%s' % (data, new_msg_btn)

                return simplejson.dumps({'status': True, 'title': main.subject, 'content': data, 'msgs': msg_list, 'not_readed': not_readed, 'id': id})
            else:
                return simplejson.dumps({'status': True, 'error': 'Error: Топик игнорируется'})
        else:
            return simplejson.dumps({'status': True, 'error': 'Error: Топик был удален'})
    except Exception as e:
        if request.user.is_superuser:
            return simplejson.dumps({'status': True, 'error': '%s * (%s), STEP %s, VARS %s' % (dir(e), e.args, step_for_admin, str(vars_for_admin))})



def create_forum_msg(parent, topic, mtype, kid, anonim, subject, text, name, email):
    # новая тема
    if mtype == 1: 
        categories = list(WFOpinion.objects.using('afisha').filter(type_obj=1, type=5).values_list('id', flat=True))
        if long(parent) in categories:
            topic = 0
            type = 3
            next = True
        else:
            next = False
    # новое сообщение
    elif mtype == 2:
        next = True
        parent = 0
        type = 0
    # ответ
    elif mtype == 3:
        next = True
        type = 0
        
    newmsg = ''
    if next:
        newmsg = WFOpinion.objects.using('afisha').create(
            parent = parent,
            branch = topic,
            user_id = kid,
            text= text,
            subject = subject,
            email = email,
            nick = name,
            type = type,
            anonim = anonim,
        )
    return newmsg


@dajaxice_register
def forum_send_msg(request, topic, parent, name, email, subject, text, anonim, mtype, preview=False, edit=['0','0']):
    try:
        from news.views import cut_description
        
        mtypes = {
            u'1': 1, # Новая тема
            u'2': 2, # Новое сообщение
            u'3': 3, # Ответ на сообщение
        }
        
        name_error = ''
        text_error = ''
        name = name.strip()[:25]
        email = email.strip()[:50]
        text = text.strip()
        subject = subject.strip()[:128]
        
        if not name:
            name_error = u'Слишком короткое имя (не менее 1 символа)'
        if not text and not subject:
            text_error = u'Слишком короткая тема или сообщение'
        
        subj_end = ''
        if subject:
            subject, subj_end = cut_description(subject, False, 47, True)
        else:
            subject = text[:128]
            subject = cut_description(subject, False, 47)
            
        if subj_end:
            text = '%s %s' % (subj_end, text)
        
        
        mtype = mtypes.get(mtype)
        
        
        subject = html_entities_to_tags(subject)
        text = html_entities_to_tags(text)

        text = BeautifulSoup(text, from_encoding="utf-8").text
        subject = BeautifulSoup(subject, from_encoding="utf-8").text
        name = BeautifulSoup(name, from_encoding="utf-8").text
        email = BeautifulSoup(email, from_encoding="utf-8").text

        if mtype:
        
            if not name_error and not text_error:
                
                tmp_txt = text[:len(subject)]
                if tmp_txt == subject:
                    text = text[len(subject):]

                text = text.replace('\n', '<br />')

                if edit[0] == '0':
                    check_user = True if anonim or not request.profile.kid else False
                    
                    error = False
                    if check_user:
                        try:
                            RegisteredUsers.objects.using('afisha').get(nickname=name)
                            error = True
                        except RegisteredUsers.DoesNotExist:
                            error = False
                        except RegisteredUsers.MultipleObjectsReturned:
                            error = True

                        if not error:
                            try:
                                user = User.objects.get(first_name=name, profile__auth_status=True)
                                error = True
                            except User.DoesNotExist:
                                error = False

                else:
                    error = False
                
                if error:
                    name_error = u'В базе есть такой пользователь, <a class="kinoafisha_button">авторизуйтесь</a> или укажите другое имя!'
                    return simplejson.dumps({'status': True, 'nerr': name_error, 'terr': ''})
                else:
                    # если новое сообщение
                    if edit[0] == '0':
                        if request.profile.kid:
                            # зарегистрированный юзер
                            kid = request.profile.kid
                            if not anonim:
                                name = ''
                        else:
                            # новый/неавторизованный юзер с уникальным никнэймом
                            anonim = False
                            
                            null_date = datetime.date(1900, 1, 1)
                            reg_obj = RegisteredUsers.objects.using('afisha').create(
                                nickname='Bk276lPLIO83hjsdfJsdjj23',
                                date_of_birth = null_date,
                            )
                            
                            kid = reg_obj.id

                            reg_obj.nickname = name
                            reg_obj.save()

                            name = ''

                            request.profile.kid = kid
                            request.profile.save()

                    # редактирование
                    else:
                        try:
                            t = WFOpinion.objects.using('afisha').select_related('user').get(pk=edit[1])
                        except WFOpinion.DoesNotExist:
                            return simplejson.dumps({'status': False})
                        else:
                            if t.user_id == request.profile.kid:
                                kid = request.profile.kid
                                name = t.nick if t.nick else t.user.nickname
                    
                    if preview:
                        
                        html = ''
                        for key, val in FORUM_SMILES.iteritems():
                            text = text.replace(key, '<img src="%sbase/images/forums/smiles/sk_%s.gif"/>' % (settings.STATIC_URL, val['id']))
                            subject = subject.replace(key, '<img src="%sbase/images/forums/smiles/sk_%s.gif"/>' % (settings.STATIC_URL, val['id']))
                        
                        date_now = datetime.datetime.now()
                        date_msg = tmp_date(date_now, "d E Y")
                        
                        if name:
                            nick = name
                        else:
                            nick = ''
                            if kid:
                                try:
                                    nick = RegisteredUsers.objects.using('afisha').get(pk=kid).nickname
                                except RegisteredUsers.DoesNotExist: pass
                                    
                        html += u'''
                            <div>
                            <div class="fmsg_h"><b>%s</b><p style="color: #FF5C33;">ПРЕДПРОСМОТР СООБЩЕНИЯ</p></div>
                            <div class="fmsg_b"><b>%s</b> <span>%s</span></div>
                            <div class="fmsg_f"></div>
                            </div>
                            ''' % (nick, subject, text)

                        return simplejson.dumps({'status': True, 'content': html})
                    else:
                        
                        if edit[0] == '0':
                            newmsg = create_forum_msg(parent, topic, mtype, kid, anonim, subject, text, name, email)
                            vcount = 0 if mtype == 1 else 1
                            WFStat.objects.using('afisha').create(opinion=newmsg.id, count=vcount)
                            WFUser.objects.using('afisha').create(user=kid, opinion=newmsg.id)
                            request.session['wf_new_msg'] = newmsg.id
                        elif edit[0] == '1' and t.user_id == kid:
                            t.subject = subject
                            t.text = text
                            t.save()
                            newmsg = t
                        

                        ref = request.META.get('HTTP_REFERER','').split('?')[0]
                        mobile = 'm/' if '/m/' in ref else ''

                            
                        redirect_to = '/women/%s' % mobile
                        next = ''
                        if topic:
                            redirect_to = '/women/%stopic/%s/' % (mobile, topic)
                            next = topic
                        if mtype == 1 and newmsg:
                            redirect_to = '/women/%stopic/%s/' % (mobile, newmsg.id)
                            next = newmsg.id
                            
                        new_id = ''
                        if mtype in (2, 3) and newmsg:
                            new_id = newmsg.id
                        
                        return simplejson.dumps({'status': True, 'redirect_to': redirect_to, 'mid': new_id, 'next': next})
            else:
                return simplejson.dumps({'status': True, 'nerr': name_error, 'terr': text_error})
    
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def forum_msg_del(request, id, topic):
    #try:
        if request.user.is_superuser:
            try:
                obj = WFOpinion.objects.using('afisha').get(pk=id)
            except WFOpinion.DoesNotExist: 
                pass
            else:
                if obj.branch:
                    ids = [id,]
                    while 1:
                        wfo = WFOpinion.objects.using('afisha').filter(Q(branch__in=ids) | Q(parent__in=ids), deleted=False)
                        if wfo:
                            ids = [i.pk for i in wfo]
                            wfo.update(deleted=True)
                        else:
                            break
                else:
                    WFOpinion.objects.using('afisha').filter(branch=id).update(deleted=True)
                obj.deleted = True
                obj.save()
                
                if obj.id == int(topic):
                    redirect_to = '/women/'
                else:
                    redirect_to = '/women/topic/%s/' % topic

                return simplejson.dumps({'status': True, 'redirect_to': redirect_to})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def forum_msg_restore(request, id, topic):
    #try:
        if request.user.is_superuser:
            id = id.replace('wfd_','')
            try:
                obj = WFOpinion.objects.using('afisha').get(pk=id)
            except WFOpinion.DoesNotExist: 
                pass
            else:
                
                ids = [id,]
                while 1:
                    wfo = WFOpinion.objects.using('afisha').filter(Q(branch__in=ids) | Q(parent__in=ids), deleted=True)
                    if wfo:
                        ids = [i.pk for i in wfo]
                        wfo.update(deleted=False)
                    else:
                        break
                        
                obj.deleted = False
                obj.save()
                
                redirect_to = '/women/topic/%s/' % topic
                
                return simplejson.dumps({'status': True, 'redirect_to': redirect_to})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def forum_topic_ignore(request, id, val, author=None):
    #try:
        def set_ignore(msg_id, kid, itype):
            ignore_obj, created = WomenForumIgnored.objects.get_or_create(
                msg = msg_id,
                user = kid,
                author = author,
                defaults = {
                    'msg': msg_id,
                    'type': itype,
                    'user': kid,
                    'author': author,
                })
            if not created:
                ignore_obj.type = itype
                ignore_obj.author = author
                ignore_obj.save()
    
    
        kid = request.profile.kid
        if kid:
            try:
                obj = WFOpinion.objects.using('afisha').get(pk=id)
            except WFOpinion.DoesNotExist:
                pass
            else:
                if obj.user_id != kid:
                    now = datetime.datetime.now()
                    level, lcreated = WomenForumIgnoreLevel.objects.get_or_create(
                        user = kid,
                        defaults = {
                            'user': kid,
                            'dtime': now,
                            'type': 1,
                        })
                    
                    if not lcreated and level.type < 3:
                        future = level.dtime + datetime.timedelta(days=7)
                        if future < now:
                            level.type += 1
                            level.dtime = now
                            level.save()
                
                
                    itype = int(val.replace('im',''))
                    if itype == 1:
                        set_ignore(obj.id, kid, itype)
                    elif itype == 2 and level.type > 1:
                        if obj.user_id:
                            
                            if obj.branch:
                                for i in WFOpinion.objects.using('afisha').filter(branch=obj.branch, user__id=obj.user_id):
                                    set_ignore(i.id, kid, itype)
                            else:
                                for i in WFOpinion.objects.using('afisha').filter(branch=obj.id, user__id=obj.user_id):
                                    set_ignore(i.id, kid, itype)

                        else:
                            set_ignore(obj.id, kid, 1)
                    elif itype == 3 and level.type == 3:
                        if obj.user_id:
                            ignore_obj, created = WomenForumIgnored.objects.get_or_create(
                                author = obj.user_id,
                                user = kid,
                                defaults = {
                                    'author': obj.user_id,
                                    'type': itype,
                                    'user': kid,
                                })
                        else:
                            set_ignore(obj.id, kid, 1)
                    
                    if obj.branch:
                        redirect_to = '/women/topic/%s/' % obj.branch
                    else:
                        redirect_to = '/women/'

                    return simplejson.dumps({'status': True, 'redirect_to': redirect_to})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@dajaxice_register
def get_forum_msg_ignores(request, id):
    
    #try:
        try:
            msg = WFOpinion.objects.using('afisha').select_related('user').get(pk=id)
        except WFOpinion.DoesNotExist:
            pass
        else:
            authors = [msg.user_id] if msg.user_id else []
            data = wf_count_ignored_msgs([msg.id], authors)
            
            igm = data['msg'].get(msg.id)
            igt = data['topic'].get(msg.id)
            iga = data['author'].get(msg.id)
            
            users = []
            if igm:
                users += igm['users']
            if igt:
                users += igt['users']
            if iga:
                users += iga['users']
            
            nicknames = {}
            for i in RegisteredUsers.objects.using('afisha').only('id', 'nickname').filter(pk__in=users):
                nicknames[i.id] = i.nickname

            html = u''
            
            if igm:
                html += u'<b>Игнорируют сообщение %s:</b>' % igm['count']
                for i in igm['users']:
                    html += '<p>%s</p>' % nicknames.get(i, '')
            if igt:
                html += u'<b>Игнорируют сообщения автора в теме %s:</b>' % igt['count']
                for i in igt['users']:
                    html += '<p>%s</p>' % nicknames.get(i, '')
            if iga:
                html += u'<b>Игнорируют автора на форуме %s:</b>' % iga['count']
                for i in iga['users']:
                    html += '<p>%s</p>' % nicknames.get(i, '')

            return simplejson.dumps({'status': True, 'content': html, 'id': id})
            
    
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    
    
@dajaxice_register
def forum_msglike(request, id, ltype):
    #try:
        user_kid = request.profile.kid
        
        if user_kid:
        
            try:
                msg = WFOpinion.objects.using('afisha').get(pk=id)
            except WFOpinion.DoesNotExist:
                pass
            else:
                if msg.user_id != user_kid:
                    ltype = True if int(ltype.replace('t','')) else False
                    
                    obj, created = WomenForumLikes.objects.get_or_create(
                        msg = msg.id,
                        profile = request.profile,
                        defaults = {
                            'msg': msg.id,
                            'profile': request.profile,
                            'like_type': ltype,
                        })
                        
                    if not created and obj.like_type != ltype:
                        obj.like_type = ltype
                        obj.save()
                    
                    like = 0
                    disl = 0
                    for i in WomenForumLikes.objects.filter(msg=msg.id):
                        if i.like_type:
                            like += 1
                        else:
                            disl += 1

                    return simplejson.dumps({'status': True, 'id': id, 'like': like, 'disl': disl})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@dajaxice_register
def forum_topic_counter(request, id):
    #try:
        user_kid = request.profile.kid

        filter = {'deleted': False}
        if request.user.is_superuser:
            filter = {}

        if user_kid:
            filter['pk__in'] = id

            objs = {}
            for i in WFOpinion.objects.using('afisha').only('id', 'date').filter(**filter):
                objs[i.id] = {'d': i.date.date(), 'id': i.id, 'c': 0, 'n': []}
            
            
            wfstat = WFStat.objects.using('afisha').filter(opinion__in=objs.keys())
            wfstat.update(count=F('count')+1, date=datetime.datetime.now())
            
            now = datetime.datetime.now().date()
            for i in wfstat:
                if objs.get(i.opinion):
                    msg_date = objs[i.opinion]['d']
                    
                    time_nav = ''
                    if msg_date:
                        if msg_date == now:
                            time_nav = u'mt1'
                        elif msg_date == (now - datetime.timedelta(days=1)):
                            time_nav = u'mt2'
                        elif msg_date == (now - datetime.timedelta(days=2)):
                            time_nav = u'mt3'
                        elif msg_date < (now - datetime.timedelta(days=2)) and msg_date >= (now - datetime.timedelta(days=6)):
                            time_nav = u'mt4'
                        elif msg_date < (now - datetime.timedelta(days=6)):
                            time_nav = u'mt5'
                        
                    objs[i.opinion]['n'] = time_nav
                    objs[i.opinion]['c'] = i.count
                    
                    
            readed = list(WFUser.objects.using('afisha').filter(user=user_kid, opinion__in=objs.keys()).values_list('opinion', flat=True))
            new_msgs = set(objs.keys()).difference(set(readed))

            for i in new_msgs:
                WFUser.objects.using('afisha').create(user=user_kid, opinion=i)

            
            for k, v in objs.iteritems():
                v['d'] = ''

            return simplejson.dumps({'status': True, 'content': objs.values()})
        return simplejson.dumps({})
    #except Exception as e:
    #    open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write('%s * (%s)' % (dir(e), e.args))


    
