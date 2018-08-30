# -*- coding: utf-8 -*- 
import operator
import datetime


from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _, get_language
from django.template.defaultfilters import date as tmp_date

from dajaxice.decorators import dajaxice_register
from bs4 import BeautifulSoup

from base.models import *
from letsgetrhythm.views import send_invite_invoice, getfiles_func
from kinoinfo_folder.func import get_month_en
from user_registration.func import *
from news.views import cut_description


ACCESS_EMAIL = 'kinoafisharu@gmail.com' #'twohothearts@gmail.com' 

@never_cache
@dajaxice_register
def budget_open(request, id, member):
    try:
        access = False
        if request.user.is_superuser:
            access = True
            filter = {'projects__is_public': True, 'pk': id}
        else:
            if request.user.groups.filter(name='Директор проекта').exists():
                access = True
                filter = {'projects__is_public': True, 'pk': id, 'projects__directors': request.profile}


        if access:
            obj = list(ProjectStages.objects.filter(**filter).values('pk', 'start_date', 'end_date', 'projects', 'projects__currency'))[0]
    
            html = ''
            main_sum = 0
            member = int(member)
            current_group = None
            
            profile = Profile.objects.get(user__pk=member)
            card = org_peoples([profile])[0]

            in_groups = profile.user.groups.filter(actionspricelist__group='8').distinct('pk')
            
            # курс валют
            # {за_1_ед.валюты: кол-во_рублей}
            currency_rate = {}
            for i in CurrencyRate.objects.filter(currency='4'):
                currency_rate[i.by_currency] = {'val': i.value, 'name': i.get_by_currency_display()}
            cur = currency_rate.get(obj['projects__currency'], {'val': 1, 'name': 'RUB'}) # кол-во рублей за 1 ...
            currencyrate = '1 %s = %s RUB' % (cur['name'], cur['val'])
            
            actions = []
            if in_groups:
                current_group = in_groups[0]

                actions = PaidActions.objects.select_related('action').filter(profile=profile, action__user_group=current_group, stage__id=id, ignore=False).order_by('-dtime')
                    
            TR_title = _(u'Ред.')
            TR_comp_tasks = _(u'Выполненные задания')# Completed Tasks
            TR_description = _(u'Описание')# Description
            TR_date = _(u'Дата')
            TR_sum = _(u'Сумма')
            TR_hours = _(u'Часы')
            TR_no_data = _(u'Нет данных')
            TR_future_tasks = _(u'Будущие задания') # Future Tasks
            TR_acc_t_sel = _(u'Одобрить выбранные задания') # Accept Selected Tasks
            TR_add_new = _(u'Добавить новое') # Add New
            TR_del_sel = _(u'Удалить выбранные') # Delete Selected
            TR_save = _(u'Сохранить')
            TR_cancel = _(u'Отмена')
            TR_remaining = _(u'осталось символов') #remaining characters
            TR_txt = _(u'Текст')
            TR_discussion = _(u'Обсуждение')

            html_completed = ''
            html_future = ''
            for i in actions:
                if i.future:
                    if i.is_accepted:
                        html_future += u'<tr id="tr_%s" style="background: #C7E0C7;">' % i.id
                    else:
                        html_future += u'<tr id="tr_%s">' % i.id
                    
                    html_future += u'<td><input type="checkbox" value="%s" name="accept_task"/></td>' % i.id
                    html_future += u'<td><div><span class="task_txt_edit org_hover" title="%s">%s</span></div></td>' % (TR_title, i.extra)
                    html_future += u'<td><div id="tsk_date">%s</div></td>' % i.dtime.strftime('%d.%m.%Y')
                    html_future += u'<td><a href="discussion/%s/" target="_blank">%s</a></td>' % (i.id, TR_discussion)
                    itext = i.text if i.text else ''
                    html_future += u'<td style="display: none;"><div id="tsk_text">%s</div></td>' % itext
                    html_future += u'</tr>'
                else:
                    summa = int(i.action.price * i.number)
                    main_sum += summa
                    html_completed += u'<tr>'
                    html_completed += u'<td><div>%s</div></td>' % i.extra
                    html_completed += u'<td><div>%s</div></td>' % i.dtime.strftime('%d.%m.%Y')
                    html_completed += u'<td><div>%s</div></td>' % summa
                    html_completed += u'<td><div>%s</div></td>' % i.number
                    html_completed += u'</tr>'
            
            group = current_group.name if current_group else ''
            
            html += u'<a href="/user/profile/%s/job/?project=%s" target="_blank">%s</a> (%s)<br />' % (card['id'], obj['projects'], card['name'], group)

            # Completed Tasks
            html += u'<br /><a id="t_completed" class="tasks_link" style="font-size: 16px; font-weight: bold;">%s</a>' % TR_comp_tasks
            if html_completed:
                html += u'<div id="completed_tasks" style="background: #EBD6CC; padding: 5px;"><br />'
                html += u'<table class="modern_tbl">'
                html += u'<th>%s</th><th>%s</th><th>%s</th><th>%s</th>' % (TR_description, TR_date, TR_sum, TR_hours)
                html += u'%s</table><br /></div>' % html_completed
            else:
                html += u'<div id="completed_tasks" style="background: #EBD6CC; padding: 5px;"><br />%s<br /></div>' % TR_no_data
                
            # Future Tasks
            html += u'<br /><a id="t_future" class="tasks_link" style="font-size: 16px; font-weight: bold;">%s</a>' % TR_future_tasks
            accept_btn = ''
            if request.user.is_superuser:
                accept_btn = u' | <input type="button" value="%s" class="accept_tasks_btn"/>' % TR_acc_t_sel
                
            if html_future:
                html += u'<div id="future_tasks" style="background: #EBD6CC; padding: 5px;"><br />'
                html += u'<table class="modern_tbl" id="future_tasks_tbl">'
                html += u'<th></th>'
                html += u'<th>%s</th><th>%s</th><th></th><th style="display: none;"></th>' % (TR_description, TR_date)
                html += u'%s</table><br /><br /><input type="button" value="%s" class="add_new_task" /> %s <input type="button" value="%s" class="del_task" style="float: right;" /></div>' % (html_future, TR_add_new, accept_btn, TR_del_sel)
            else:
                html += u'<div id="future_tasks" style="background: #EBD6CC; padding: 5px;"><br />'
                html += u'<table class="modern_tbl" id="future_tasks_tbl" style="display: none;">'
                html += u'<th></th>'
                html += u'<th>%s</th><th>%s</th><th style="display: none;"></th>' % (TR_description, TR_date)
                html += u'</table>'
                html += u'<span>%s</span><br /><br /><input type="button" value="%s" class="add_new_task"/> %s <input type="button" value="%s" class="del_task" style="float: right;" /></div>' % (TR_no_data, TR_add_new, accept_btn, TR_del_sel)
            
            # New Future Task
            html_new_task = u'<div class="new_task_form" style="display: none; background: #EBD6CC; padding: 5px;"><b>%s:</b> <span id="char_count"></span><br />' % TR_description
            html_new_task += u'<input name="details" maxlength="256" style="width: 95%;" /><br />'
            html_new_task += u'<b>%s:</b><br />' % TR_txt
            html_new_task += u'<textarea name="text" style="width: 95%; min-height: 100px;" /><br />'
            html_new_task += u'<b>%s:</b><br />' % TR_date
            html_new_task += u'<input type="text" name="date" value="" /><br /><br />'
            html_new_task += u'<input type="hidden" name="project" value="%s" />' % obj['projects']
            html_new_task += u'<input type="hidden" name="stage" value="%s" />' % id
            html_new_task += u'<input type="hidden" name="mmbr" value="%s" />' % member
            html_new_task += u'<input type="hidden" name="edt" value="0" />'
            html_new_task += u'<input type="button" value="%s" class="new_task_save" /> <input type="button" value="%s" onclick="$(\'.new_task_form\').hide(); $(\'#future_tasks\').show();"/></div>' % (TR_save, TR_cancel)
            
            
            script = u'<script type="text/javascript">var scroll_h = ($(window).height() / 100) * 45; $(\'.scroll_list\').css(\'height\', scroll_h + \'px\'); $(\'input[name="date"]\').datepicker({ altFormat: "yy-mm-dd", dateFormat: "yy-mm-dd", changeMonth: true, changeYear: true, firstDay: 1, minDate: "%s", maxDate: "%s" });' % (obj['start_date'], obj['end_date'])
            
            script += u'var maxLength = $(\'input[name="details"]\').attr(\'maxlength\'); $(\'input[name="details"]\').keyup(function(){ var curLength = $(\'input[name="details"]\').val().length; if($(this).val().length >= maxLength){ $(this).val($(this).val().substr(0, maxLength)) } var remaning = maxLength - curLength; if(remaning < 0){ remaning = 0 } $(\'#char_count\').html(\'(%s: \' + remaning + \')\') });' % TR_remaining
            
            script += u'</script>'

            aud_sum = int(main_sum / cur['val'])
            # wrapper
            html = u'<div style="min-width: 500px;">%s<h2>%s RUB | %s | %s %s</h2><hr /><br />%s%s</div>' % (script, main_sum, currencyrate, aud_sum, cur['name'], html, html_new_task)

            return simplejson.dumps({'status': True, 'content': html})

        return simplejson.dumps({})
        
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@never_cache
@dajaxice_register
def new_task(request, id, mmbr, txt, text, date, stage, edt):
    try:
        access = False
        if request.user.is_superuser:
            access = True
            filter = {'projects__is_public': True, 'pk': stage}
        else:
            if request.user.groups.filter(name='Директор проекта').exists():
                access = True
                filter = {'projects__is_public': True, 'pk': stage, 'projects__directors': request.profile}

        TR_discussion = _(u'Обсуждение')

        if access:

            obj = list(ProjectStages.objects.filter(**filter).values('pk', 'start_date', 'end_date'))[0]

            set_date = date.split('-')
            set_date = datetime.date(int(set_date[0]), int(set_date[1]), int(set_date[2]))
            
            if set_date <= obj['end_date'] and set_date >= obj['start_date']:
                xdate = set_date
            else:
                xdate = obj['end_date']

            profile = Profile.objects.select_related('user').get(user__pk=mmbr)
            
            in_groups = profile.user.groups.filter(actionspricelist__group='8').distinct('pk')

            if in_groups:
                current_group = in_groups[0]

                if date and txt.strip():
                    if int(edt):
                        paid = PaidActions.objects.get(pk=edt)
                        paid.extra = txt.strip()
                        paid.text = text.strip()
                        paid.dtime = xdate
                        paid.save()
                        
                        return simplejson.dumps({'status': True, 'date': xdate.strftime('%d.%m.%Y'), 'txt': txt.strip(), 'edt': int(edt), 'text': text.strip()})
                    else:
                        try:
                            action = ActionsPriceList.objects.select_related('action').get(user_group=current_group, project=id, allow=True)
                        except ActionsPriceList.DoesNotExist:
                            html = u'Для этого проекта не создано "Оплачиваемое действие" для группы пользователей "%s"' % current_group
                            return simplejson.dumps({'status': False, 'html': html, 'edt': 0, })

                        paid = PaidActions.objects.create(
                            action = action, 
                            profile = profile,
                            object = None,
                            act = '1',
                            extra = txt.strip(),
                            text = text.strip(),
                            number = 1,
                            director = request.profile,
                            future = True,
                            stage_id = stage,
                        )

                        paid.dtime = xdate
                        paid.save()
                        
                        #accept_checker = ''
                        #if access:
                        accept_checker = u'<td><input type="checkbox" value="%s" name="accept_task"/></td>' % paid.id
                        
                        date = xdate.strftime('%d.%m.%Y')
                        
                        html = u'''
                            <tr id="tr_%s">
                                %s
                                <td><div><span class="task_txt_edit org_hover" >%s</span></div></td>
                                <td><div>%s</div></td>
                                <td><a href="discussion/%s/" target="_blank">%s</a></td>
                                <td style="display: none;"><div id="tsk_text">%s</div></td>
                            </tr>''' % (paid.id, accept_checker, txt.strip(), date, paid.id, TR_discussion, text.strip())
                        
                        return simplejson.dumps({'status': True, 'html': html, 'edt': 0})
    
        return simplejson.dumps({})
        
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
        


@never_cache
@dajaxice_register
def accept_tasks(request, arr):
    #try:
        if request.user.is_superuser:
            PaidActions.objects.filter(pk__in=arr, future=True).update(is_accepted=True)

        return simplejson.dumps({})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))

@never_cache
@dajaxice_register
def del_tasks(request, arr):
    #try:
        access = False
        if request.user.is_superuser:
            access = True
            filter = {'future': True, 'pk__in': arr}
        else:
            if request.user.groups.filter(name='Директор проекта').exists():
                access = True
                filter = {'future': True, 'pk__in': arr, 'director': request.profile}

        if access:
            PaidActions.objects.filter(**filter).delete()

        return simplejson.dumps({})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def create_question(request):
    try:
        auth = _(u'Что бы оставить вопрос, <a href="/user/login/">авторизуйтесь</a>, пожалуйста.')

        if request.acc_list['acc']:

            subject_txt = _(u'Вопрос')
            question_txt = _(u'Описание')
            tags_txt = _(u'Теги')
            enter_txt = _(u'перечисление через "Enter"')
            enter_tags_txt = _(u'Введите теги')
            send = _(u'Отправить')

            html = u'<div class="add_question_bl">'
            html += u'<div><b>%s:</b></div>' % subject_txt
            html += u'<div><input type="text" class="question_subject" /></div>'
            html += u'<div><b>%s:</b></div>' % question_txt
            html += u'<div><textarea class="question_txt"></textarea></div>'
            html += u'<div style="clear: both; padding-top: 15px;"><b>%s (%s):</b></div>' % (tags_txt, enter_txt)
            html += u'<div class="tagsinput" id="tagsinput"><input type="text" value="" placeholder="%s" onkeyup="get_tags_auto(this);" style="width: 206px;"/></div>' % enter_tags_txt
            html += u'<div class="clear"></div>'
            html += u'<div><input type="button" class="add_question" value="%s" /></div>' % send
            html += u'</div>'
        else:
            html = u'<div>%s</div>' % auth

        return simplejson.dumps({'content': html})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def add_question(request, subject, text, tags):
    try:

        if request.acc_list['acc']:
            subject = BeautifulSoup(subject.strip(), from_encoding='utf-8').text.strip()
            text = BeautifulSoup(text.strip(), from_encoding='utf-8').text.strip()
            lang = get_language()

            try:
                language = Language.objects.get(code=lang)
            except Language.DoesNotExist:
                language = Language.objects.get(code='en')

            if len(subject) > 1 and len(text) > 1:

                question, created = News.objects.get_or_create(
                    title = subject,
                    text = text,
                    visible = True,
                    autor = request.profile,
                    site = request.current_site,
                    subdomain = 0,
                    reader_type = '22',
                    language = language,
                    defaults = {
                        'title': subject,
                        'text': text,
                        'visible': True,
                        'autor': request.profile,
                        'site': request.current_site,
                        'subdomain': 0,
                        'reader_type': '22',
                        'language': language,
                    })

                
                html = u''
                if created:
                    qa = QuestionAnswer.objects.create()
                    qa.item.add(question)

                    vid = request.META.get('HTTP_REFERER').split('/view/')[1].split('/')[0]

                    html_tags = u''
                    for tag in set(tags):
                        tag = tag.strip()
                        if tag:
                            obj, created = NewsTags.objects.get_or_create(name=tag, defaults={'name': tag})
                            question.tags.add(obj)

                            html_tags += u'<a href="/view/%s/tag/%s/"><div class="item-tag">%s</div></a> ' % (vid, tag, tag)


                    author = org_peoples([question.autor])[0]
                    #text = cut_description(question.text, True, 60)

                    answer_txt = _(u'спрашивает')

                    if lang == 'ru':
                        dtime = tmp_date(question.dtime, 'd M Y г. H:i')
                    else:
                        dtime = tmp_date(question.dtime, 'M d, Y, g:i a')

                    html += u'<div class="question-item">'
                    html += u'<div class="question-item-head">'
                    html += u'<div class="question-item-author"><a href="/user/profile/%s/">%s</a> %s:</div>' % (author['id'], author['name'], answer_txt)
                    html += u'<div class="question-item-datetime">%s</div>' % dtime
                    html += u'</div>'
                    html += u'<div class="question-item-body">'
                    html += u'<div class="question-item-subject"><h2><a href="/view/%s/question/%s/">%s</a></h2></div>' % (vid, qa.id, question.title)
                    #html += u'<div class="question-item-text">%s</div>' % text
                    html += u'<div class="question-item-tags">%s</div>' % html_tags
                    html += u'</div></div>'

                return simplejson.dumps({'status': True, 'content': html})
            
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def create_answer(request):
    try:
        auth = _(u'Что бы дать ответ, <a href="/user/login/">авторизуйтесь</a>, пожалуйста.')

        if request.acc_list['acc']:
            answer_txt = _(u'Ваш ответ')
            send = _(u'Отправить')
            
            html = u'<div class="add_question_bl">'
            html += u'<div><b>%s:</b></div>' % answer_txt
            html += u'<div><textarea class="answer_txt"></textarea></div>'
            html += u'<div class="clear"></div>'
            html += u'<div><input type="button" class="add_answer" value="%s" /></div>' % send
            html += u'</div>'
        else:
            html = u'<div>%s</div>' % auth

        return simplejson.dumps({'content': html})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def add_answer(request, text):
    try:

        if request.acc_list['acc']:
            text = BeautifulSoup(text.strip(), from_encoding='utf-8').text.strip()
            lang = get_language()

            try:
                language = Language.objects.get(code=lang)
            except Language.DoesNotExist:
                language = Language.objects.get(code='en')

            if len(text) > 2:
                question_id = request.META.get('HTTP_REFERER').split('/question/')[1].split('/')[0]
                
                filter = {'reader_type': '22', 'questionanswer__id': question_id, 'translation_for': None}
                question_obj = News.objects.get(**filter)

                answer, created = News.objects.get_or_create(
                    title = '',
                    text = text,
                    visible = True,
                    autor = request.profile,
                    site = request.current_site,
                    subdomain = 0,
                    reader_type = '23',
                    language = language,
                    parent = question_obj,
                    defaults = {
                        'title': '',
                        'text': text,
                        'visible': True,
                        'autor': request.profile,
                        'site': request.current_site,
                        'subdomain': 0,
                        'reader_type': '23',
                        'language': language,
                        'parent': question_obj,
                    })


                html = u''
                if created:
                    qa = QAnswers.objects.create()
                    qa.item.add(answer)

                    author = org_peoples([answer.autor])[0]
                    text = answer.text

                    answer_txt = _(u'отвечает')
                    
                    if lang == 'ru':
                        dtime = tmp_date(answer.dtime, 'd M Y г. H:i')
                    else:
                        dtime = tmp_date(answer.dtime, 'M d, Y, g:i a')

                    html += u'<div class="answer-item">'
                    html += u'<div class="answer-item-head">'
                    html += u'<div class="answer-item-author"><a href="/user/profile/%s/">%s</a> %s:</div>' % (author['id'], author['name'], answer_txt)
                    html += u'<div class="answer-item-datetime">%s</div>' % dtime
                    html += u'</div>'
                    html += u'<div class="answer-item-body">'
                    html += u'<div class="answer-item-text">%s</div>' % text
                    html += u'</div></div>'

                return simplejson.dumps({'status': True, 'content': html})
            
        return simplejson.dumps({})
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))