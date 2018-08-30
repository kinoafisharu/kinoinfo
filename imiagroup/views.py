#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
from random import randrange

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext
from django.core.mail import get_connection, EmailMultiAlternatives
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _, get_language
from django.db.models import Q

from bs4 import BeautifulSoup
from unidecode import unidecode

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits
from user_registration.views import get_usercard
from user_registration.func import *
from user_registration.ajax import bpost_comments_gen
from news.views import cut_description, create_news
from vladaalfimov.forms import *
from organizations.func import is_editor_func
from organizations.ajax import xss_strip2
from kinoinfo_folder.func import low, del_separator, uppercase
from articles.views import pagination as pagi



@only_superuser
@never_cache
def imiagroup_projects_delete(request):
    if request.POST:
        checker = request.POST.getlist('checker')
        if checker:
            Projects.objects.filter(pk__in=checker).delete()
            
    return HttpResponseRedirect(reverse('imiagroup_projects'))


@only_superuser
@never_cache
def imiagroup_projects_edit(request):
    if request.POST:
        name = request.POST.get('project_name','').strip()
        url = request.POST.get('project_url','').strip()
        sdate = request.POST.get('start_date')
        rdate = request.POST.get('release_date')
        budget = request.POST.get('project_budget')
        currency = request.POST.get('project_currency')
        email = request.POST.get('project_email')
        sms = request.POST.get('project_sms')
        
        alldirectors = set([i for i in request.POST.get('alldirectors','').split(',') if i])
        allmembers = set([i for i in request.POST.get('allmembers','').split(',') if i])

        budget = int(budget)
        email = True if email else False
        sms = True if sms else False
        
        edit = int(request.POST.get('edit'))
        
        if name and sdate and rdate:
            if edit:
                obj = Projects.objects.get(pk=edit)
                obj.name = name
                obj.url = url
                obj.start_date = sdate
                obj.release_date = rdate
                obj.email = email
                obj.sms = sms
                obj.budget = budget
                obj.currency = currency
                obj.save()
            else:
                obj = Projects.objects.create(
                    name = name,
                    url = url,
                    start_date = sdate,
                    release_date = rdate,
                    email = email,
                    sms = sms,
                    budget = budget,
                    currency = currency
                )
                
            obj.members.clear()
            for i in Profile.objects.filter(user__id__in=allmembers):
                obj.members.add(i)
                
            obj.directors.clear()
            for i in Profile.objects.filter(user__id__in=alldirectors):
                obj.directors.add(i)

    return HttpResponseRedirect(reverse('imiagroup_projects'))

    


@never_cache
def imiagroup_projects(request):
    filter = {'is_public': True}
    access = False
    if request.user.is_superuser:
        access = True
    else:
        if request.user.groups.filter(name='Директор проекта').exists():
            access = True
            #filter = {'is_public': True, 'directors': request.profile}

    # курс валют
    # {за_1_ед.валюты: кол-во_рублей}
    currency_rate = {}
    for i in CurrencyRate.objects.filter(currency='4'):
        currency_rate[i.by_currency] = i.value
    
    admins = Profile.objects.filter(Q(user__is_superuser=True) | Q(user__groups__name='Директор проекта'))
    admins = org_peoples(admins)
    admins = sorted(admins, key=operator.itemgetter('name'))
    
    members = Profile.objects.filter(auth_status=True)
    members = org_peoples(members, True)

    data = []
    for i in Projects.objects.filter(**filter):
        main_sum = 0
        project_members = []
        for m in i.members.all():
            member = members.get(m.user_id)
            member_id, member_name = (member['id'], member['name']) if member else (m.user_id, None)
            project_members.append({'name': member_name, 'id': member_id})
            
            in_groups = Group.objects.filter(user__pk=m.user_id, actionspricelist__group='8').distinct('pk')
            actions = []

            if in_groups:
                current_group = in_groups[0]

                actions = PaidActions.objects.select_related('action').filter(profile=m, action__user_group=current_group, action__project=i, future=False, allow=True)
            
                summa = sum([int(a.action.price * a.number) for a in actions])
                
                main_sum += summa

        im_director = False
        project_directors = []
        for d in i.directors.all():
            if request.profile == d:
                im_director = False
            director = members.get(d.user_id)
            director_id, director_name = (director['id'], director['name']) if director else (d.user_id, None)
            project_directors.append({'name': director_name, 'id': director_id})
        
        
        cur = currency_rate.get(i.currency, 1) # кол-во рублей за 1 ...
                            
        budget = 0
        if i.budget:
            budget = i.budget

        fact_percent = 0
        if main_sum and budget:
            fact_percent = (int(main_sum / cur) * 100) / budget

        data.append({'obj': i, 'directors': project_directors, 'members': project_members, 'budget': budget, 'fact': fact_percent, 'im_director': im_director})

    members = sorted(members.values(), key=operator.itemgetter('name'))

    vid = 60 if request.domain == '0.0.1:8000' else 60
    return render_to_response('imiagroup/projects.html', {'data': data, 'access': access, 'admins': admins, 'members': members, 'vid': vid}, context_instance=RequestContext(request))



@never_cache
def imiagroup_project_discussion(request, id, dis):
    filter = {'is_public': True, 'pk': id}

    if request.user.groups.filter(name='Директор проекта').exists():
        filter['directors'] = request.profile
    else:
        filter['members'] = request.profile

    
    try:
        project = Projects.objects.get(**filter)
    except Projects.DoesNotExist:
        raise Http404
    
    stages = [i.id for i in project.stages.all()]

    try:
        pa = PaidActions.objects.get(pk=dis, stage__id__in=stages, ignore=False)
    except Projects.DoesNotExist:
        raise Http404


    current_site = request.current_site
    subdomain = request.subdomain if request.subdomain else 0

    news, news_created = News.objects.get_or_create(
        autor = pa.profile,
        reader_type = '24',
        extra = pa.id,
        site = current_site,
        subdomain = subdomain,
        defaults = {
            'title': pa.extra, 
            'autor': pa.profile,
            'site': current_site,
            'subdomain': subdomain,
            'text': pa.text,
            'visible': True,
            'reader_type': '24',
            'autor_nick': 0,
            'extra': pa.id,
        })

    data = bpost_comments_gen(news.id, current_site, request.user.is_superuser)


    email_exist = False
    main_email = request.user.email
    if main_email:
        email_exist = True
    else:
        emails = [i.email.strip() for i in request.profile.accounts.all() if i.email and i.email.strip()]
        if emails:
            email_exist = True


    comments_subscribed = False
    if id:
        try:
            comments_subscribed = SubscriberUser.objects.get(profile=request.profile, type='2', obj=news.id).id
        except SubscriberUser.DoesNotExist: pass
        
    vid = 60 if request.domain == '0.0.1:8000' else 60
    return render_to_response('imiagroup/project_discussion.html', {'data': data, 'news': news, 'vid': vid, 'email_exist': email_exist, 'comments_subscribed': comments_subscribed, 'project': project}, context_instance=RequestContext(request))
    


@only_superuser
@never_cache
def imiagroup_stage_del(request):
    if request.POST:
        proj_id = int(request.POST.get('proj_id'))
    
        checker = request.POST.getlist('checker')
        if checker:
            PaidActions.objects.filter(stage__pk__in=checker).update(stage=None)
            ProjectStages.objects.filter(pk__in=checker).delete()
            
        return HttpResponseRedirect(reverse('imiagroup_project_budget', kwargs={'id': proj_id}))
    return HttpResponseRedirect(reverse('imiagroup_projects'))


@only_superuser
@never_cache
def imiagroup_stage_edit(request):
    if request.POST:
        proj_id = int(request.POST.get('proj_id'))
        edit = int(request.POST.get('edit'))
        name = request.POST.get('stage_name','').strip()
        sdate = request.POST.get('start_date')
        rdate = request.POST.get('end_date')
        budget = int(request.POST.get('stage_budget'))

        project = Projects.objects.get(pk=proj_id, is_public=True)

        if name and sdate and rdate and budget:
            if edit:
                obj = ProjectStages.objects.get(pk=edit)
                obj.name = name
                obj.start_date = sdate
                obj.end_date = rdate
                obj.budget = budget
                obj.save()
            else:
                obj = ProjectStages.objects.create(
                    name = name,
                    start_date = sdate,
                    end_date = rdate,
                    budget = budget,
                )
                project.stages.add(obj)
        
        return HttpResponseRedirect(reverse('imiagroup_project_budget', kwargs={'id': proj_id}))
    return HttpResponseRedirect(reverse('imiagroup_projects'))





@never_cache
def imiagroup_project_budget(request, id):
    
    access = False
    if request.user.is_superuser:
        access = True
        filter = {'is_public': True, 'pk': id}
    else:
        if request.user.groups.filter(name='Директор проекта').exists():
            access = True
            filter = {'is_public': True, 'directors': request.profile, 'pk': id}

    if access:
        # курс валют
        # {за_1_ед.валюты: кол-во_рублей}
        currency_rate = {}
        for i in CurrencyRate.objects.filter(currency='4'):
            currency_rate[i.by_currency] = i.value
            
        try:
            obj = Projects.objects.get(pk=id, is_public=True)
        except Projects.DoesNotExist:
            raise Http404

        html = ''
        main_sum = 0
        
        admins = list(Profile.objects.filter(user__is_superuser=True))
        members = obj.members.all()
        all_members = org_peoples(set(list(members) + admins), True)

        cur = currency_rate.get(obj.currency, 1) # кол-во рублей за 1 ...
        
        stages = {}
        project_members = []
        for m in members:
            member = all_members.get(m.user_id)
            member_id, member_name = (member['id'], member['name']) if member else (m.user_id, None)
            project_members.append({'name': member_name, 'id': member_id})
            
            in_groups = Group.objects.filter(user__pk=m.user_id, actionspricelist__group='8').distinct('pk')
            
            actions = []
            if in_groups:
                current_group = in_groups[0]

                actions = PaidActions.objects.select_related('stage', 'action').filter(profile=m, action__user_group=current_group, action__project=obj, future=False, ignore=False, allow=True)
            
                summa = []
                paid = 0
                for a in actions:
                    if a.stage_id:
                        act_sum = a.action.price * a.number
                        summa.append(act_sum)

                        if not stages.get(a.stage_id):
                            stages[a.stage_id] = {'id': a.stage_id, 'obj': a.stage, 'main_sum': 0, 'member': member_name, 'paid': 0, 'unpaid': 0}
                        stages[a.stage_id]['main_sum'] += act_sum
                        if a.allow:
                            stages[a.stage_id]['paid'] += act_sum
                        else:
                            stages[a.stage_id]['unpaid'] += act_sum
                        
                main_sum += sum(summa)

        project_directors = []
        for d in obj.directors.all():
            director = all_members.get(d.user_id)
            director_id, director_name = (director['id'], director['name']) if director else (d.user_id, None)
            if director_name:
                director_name = unidecode(director_name)
            project_directors.append({'name': director_name, 'id': director_id})

        
        stages_data = []
        for i in obj.stages.all():
            st = stages.get(i.id, {'id': i.id, 'obj': i, 'main_sum': 0, 'member': [], 'paid': 0, 'unpaid': 0})

            paid_percent = 0
            if st['main_sum']:
                paid_percent = int((st['paid'] * 100) / st['main_sum'])
            
            if st['unpaid']:
                st['unpaid'] = int(st['unpaid'] / cur)
            
            st['paid'] = paid_percent

            stages_data.append(st)
            
        
        stages = sorted(stages_data, key=operator.itemgetter('id'))

        for i in stages:
            i['main_sum'] = int(i['main_sum'] / cur)

        # БЮДЖЕТ
        budget = 0
        fact_budget = 0
        fact_budget_percent = 0
        if obj.budget:
            budget = obj.budget

        if main_sum:
            fact_budget = int(main_sum / cur)
            fact_budget_percent = (fact_budget * 100) / budget


        # ДНИ
        def daterange(start_date, end_date):
            for n in range(int ((end_date - start_date).days)):
                yield start_date + datetime.timedelta(n)
            
        days = len([i for i in daterange(obj.start_date, obj.release_date)])
        if datetime.datetime.now().date() > obj.release_date:
            fact_days_to = obj.release_date
        else:
            fact_days_to = datetime.datetime.now().date()
            
        fact_days = len([i for i in daterange(obj.start_date, fact_days_to)])
        fact_days_percent = (fact_days * 100) / days
        

        vid = 60 if request.domain == '0.0.1:8000' else 60
        return render_to_response('imiagroup/budget.html', {'obj': obj, 'stages': stages, 'budget': budget, 'fact_budget': fact_budget, 'fact_budget_percent': fact_budget_percent, 'proj_id': id, 'vid': vid, 'days': days, 'fact_days': fact_days, 'fact_days_percent': fact_days_percent, 'project_members': project_members, 'project_directors': project_directors}, context_instance=RequestContext(request))
    else:
        raise Http404


@only_superuser
@never_cache
def invoice_gen(request):
    from letsgetrhythm.views import create_pdf
    if request.POST:
        proj_id = request.POST.get('proj_id')
        stage_id = request.POST.get('stage_id')
        unpaid = request.POST.get('out_amount', 0)
        note = request.POST.get('proj_invoice_note','')
        invoice_num = request.POST.get('invoice_num', '')
        director = request.POST.get('director')
        director_name = request.POST.get('director_name').strip()
        
        stage = ProjectStages.objects.get(pk=stage_id)
        
        
        profile = Profile.objects.get(user__pk=director)
        card = org_peoples([profile])[0]
        
        if not director_name:
            director_name = unidecode(card['name'])
        
        if len(invoice_num) == 1:
            invoice_num = '0%s' % invoice_num
        
        current_site = request.current_site
        to = {'name': director_name, 'address': ''}
        event = stage.name
        today = datetime.datetime.now().date()
        general_price = int(unpaid)
        offer = int(unpaid)
        domain = current_site.domain
        
        bank = LetsGetBank.objects.get(site=current_site)
        
        numsess = 1
        bcr = invoice_num
        bcr_code = proj_id
        
        file_name = create_pdf(to=to, event=event, today=today, general_price=general_price, offer=offer, domain=domain, bank=bank, note=note, bcr=bcr, bcr_code=bcr_code, numsess=numsess, forwhat='', times=False, subtotal=False)

        with open('%s/%s' % (settings.INVOICES_TMP, file_name), 'r') as f:
            file_obj = f.read()
        
        response = HttpResponse(file_obj, mimetype='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
        
        '''
        mail = EmailMultiAlternatives('IMIAGroup Invoice', 'Invoice PDF file has been attached to this e-mail message', ['kinoafisharu@gmail.com'])
        mail.attach_file('%s/%s' % (settings.INVOICES_TMP, file_name), mimetype='application/pdf')
        mail.send()
        '''
        
        try:
            os.remove('%s/%s' % (settings.INVOICES_TMP, file_name))
        except OSError: pass
        
        return response

    raise Http404
    


# ВОПРОС - ОТВЕТ
@never_cache
def question_answer_type(request, qtype):
    return question_answer(request, None, qtype)

@never_cache
def question_answer(request, tag=None, qtype=None):

    lang = get_language()

    do_query = True
    filter = {'reader_type': '22', 'language__code': lang}
    if tag:
        tag = tag.encode('utf-8')
        filter['tags__name'] = tag
        del filter['language__code']
    elif qtype:
        if qtype in ('with', 'without'):
            if qtype == 'with':
                #query_result = list(News.objects.filter(Q(parent_rel__language__code=lang) | Q( translation_for__parent_rel__language__code=lang), language__code=lang, reader_type='22').distinct('pk').values('questionanswer', 'pk'))
                
                query_result_1 = list(News.objects.filter(parent_rel__language__code=lang, language__code=lang, reader_type='22').distinct('pk').values('questionanswer', 'pk'))
                query_result_2 = list(News.objects.filter(translation_for__parent_rel__language__code=lang, language__code=lang, reader_type='22').distinct('pk').values('questionanswer', 'pk'))

                query_result = query_result_1 + query_result_2
                
                do_query = False
            elif qtype == 'without':
                query_result_tmp = list(News.objects.filter(language__code=lang, reader_type='22').exclude(translation_for__parent_rel__language__code=lang).distinct('pk').values_list('pk', flat=True))
                query_result = list(News.objects.filter(pk__in=query_result_tmp).exclude(parent_rel__language__code=lang).distinct('pk').values('questionanswer', 'pk'))
                do_query = False
                
        else:
            raise Http404



    if do_query:
        query_result = list(News.objects.filter(**filter).distinct('pk').values('questionanswer', 'pk'))


    q_ids = {}
    for i in query_result:
        if i['questionanswer']:
            q_ids[i['pk']] = i['questionanswer']


    questions = News.objects.select_related('autor', 'language').filter(pk__in=q_ids.keys()).order_by('-dtime')

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, questions, 8)

    profiles = []
    ids = []
    questionanswers = []
    for i in p.object_list:
        profiles.append(i.autor)
        ids.append(i.id)
        qas = q_ids.get(i.id)
        if qas:
            questionanswers.append(qas)


    answers = {}
    for i in list(News.objects.filter(parent__questionanswer__id__in=questionanswers, reader_type='23', language__code=lang).values('pk', 'parent__questionanswer')):
        if not answers.get(i['parent__questionanswer']):
            answers[i['parent__questionanswer']] = 0
        answers[i['parent__questionanswer']] += 1

    peoples = org_peoples(set(profiles), True)

    tags_list = set(list(NewsTags.objects.filter(news__reader_type='22').values_list('name', flat=True)))

    tags_all = {}
    for i in list(NewsTags.objects.filter(news__pk__in=ids).values('name', 'news__pk')):
        if not tags_all.get(i['news__pk']):
            tags_all[i['news__pk']] = []
        tags_all[i['news__pk']].append(i['name'])

    data = []
    for i in p.object_list:
        author = peoples.get(i.autor.user_id)
        tags = tags_all.get(i.id)

        text = cut_description(i.text, True, 60)

        qid = q_ids.get(i.id)

        answers_count = answers.get(qid, 0)

        data.append({
            'id': qid,
            'dtime': i.dtime,
            'subject': i.title,
            'text': text,
            'author': author,
            'tags': tags,
            'lang': i.language.code,
            'answers': answers_count,
            'views': i.views,
        })

    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/question_answer.html', {'vid': vid, 'data': data, 'p': p, 'page': page, 'tags_list': tags_list, 'lang': lang, 'qtype': qtype, 'qa_list_type': 'questions'}, context_instance=RequestContext(request))


@never_cache
def question(request, id):

    lang = get_language()

    try:
        qa = QuestionAnswer.objects.get(pk=id)
    except News.DoesNotExist:
        raise Http404

    filter = {'reader_type': '22', 'questionanswer__id': qa.id}


    question = None
    eng = None
    for i in News.objects.select_related('autor', 'language').filter(**filter):
        question = i
        if i.language.code == lang:
            question = i
            break
        if i.language.code == 'en':
            eng = i
    
    if question.language.code != lang and eng:
        question = eng

    question.views += 1
    question.save()

    tags_list = set(list(NewsTags.objects.filter(news__reader_type='22').values_list('name', flat=True)))

    answers = News.objects.select_related('autor').filter(parent__questionanswer__id=qa.id, reader_type='23', language=question.language)

    profiles = set([i.autor for i in answers])

    if question.autor not in profiles:
        profiles = list(profiles)
        profiles.append(question.autor)
        
    peoples = org_peoples(profiles, True)

    question_tags = set([i.name for i in question.tags.all()])
    question_author = peoples.get(question.autor.user_id)

    answers_data = []
    for i in answers:
        author = peoples.get(i.autor.user_id)
        answers_data.append({
            'id': i.id,
            'dtime': i.dtime,
            'text': i.text,
            'author': author,
        })


    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/question.html', {'vid': vid, 'question': question, 'question_tags': question_tags, 'question_author': question_author, 'answers': answers_data, 'tags_list': tags_list, 'lang': lang, 'qa_id': qa.id}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def question_answer_admin(request):

    lang = get_language()

    q_ids = {}
    for i in list(News.objects.filter(reader_type='22', translation_for=None).distinct('pk').order_by('-dtime').values('questionanswer', 'pk')):
        if i['questionanswer']:
            q_ids[i['pk']] = i['questionanswer']

    questions = News.objects.select_related('autor', 'language').filter(pk__in=q_ids.keys()).order_by('-dtime')

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, questions, 8)

    langs = [l[0] for l in settings.LANGUAGES]

    profiles = []
    ids = []
    translation = {}
    for i in p.object_list:
        profiles.append(i.autor)
        ids.append(i.id)
        default_langs = {}
        for lg in langs:
            default_langs[lg] = False
        translation[i.id] = default_langs
        translation[i.id][i.language.code] = True
            
    
    for i in list(News.objects.filter(translation_for__in=ids).values('translation_for', 'language__code')):
        translation[i['translation_for']][i['language__code']] = True

    peoples = org_peoples(set(profiles), True)

    tags_list = set(list(NewsTags.objects.filter(news__reader_type='22').values_list('name', flat=True)))

    tags_all = {}
    for i in list(NewsTags.objects.filter(news__pk__in=ids).values('name', 'news__pk')):
        if not tags_all.get(i['news__pk']):
            tags_all[i['news__pk']] = []
        tags_all[i['news__pk']].append(i['name'])

    data = []
    for i in p.object_list:
        author = peoples.get(i.autor.user_id)
        tags = tags_all.get(i.id)

        text = cut_description(i.text, True, 60)

        qid = q_ids.get(i.id)

        translation_languages = translation.get(i.id, [])

        data.append({
            'id': qid,
            'dtime': i.dtime,
            'subject': i.title,
            'text': text,
            'author': author,
            'tags': tags,
            'lang': i.language.code,
            'translation': translation_languages,
        })

    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/question_answer.html', {'vid': vid, 'data': data, 'p': p, 'page': page, 'tags_list': tags_list, 'lang': lang, 'qtype': 'admin', 'qa_list_type': 'questions'}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def answers_admin(request):

    lang = get_language()

    all_answers_ids = {}
    for i in list(News.objects.filter(reader_type='23', translation_for=None).order_by('-dtime').values('pk', 'qanswers')):
        all_answers_ids[i['pk']] = i['qanswers']
    

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    p, page = pagi(page, all_answers_ids.keys(), 8)


    answers_ids = {}
    for i in list(News.objects.filter(pk__in=p.object_list, reader_type='23').order_by('-dtime').values('pk', 'parent')):
        answers_ids[i['pk']] = i['parent']
    

    q_ids = {}
    for i in list(News.objects.filter(pk__in=answers_ids.values(), reader_type='22', translation_for=None).distinct('pk').order_by('-dtime').values('questionanswer', 'pk')):
        if i['questionanswer']:
            q_ids[i['pk']] = i['questionanswer']

    answers = News.objects.select_related('autor', 'language').filter(pk__in=answers_ids.keys()).order_by('-dtime')

    langs = [l[0] for l in settings.LANGUAGES]

    profiles = []
    ids = []
    translation = {}
    for i in answers:
        profiles.append(i.autor)
        ids.append(i.id)
        default_langs = {}
        for lg in langs:
            default_langs[lg] = False
        translation[i.id] = default_langs
        translation[i.id][i.language.code] = True
            
    for i in list(News.objects.filter(translation_for__in=ids, reader_type='23').values('translation_for', 'language__code')):
        translation[i['translation_for']][i['language__code']] = True

    peoples = org_peoples(set(profiles), True)


    data = []
    for i in answers:
        author = peoples.get(i.autor.user_id)

        text = cut_description(i.text, True, 60)

        qid = q_ids.get(i.parent_id)
        aid = all_answers_ids.get(i.id)

        translation_languages = translation.get(i.id, [])

        data.append({
            'id': aid,
            'qid': qid,
            'dtime': i.dtime,
            'text': text,
            'author': author,
            'lang': i.language.code,
            'translation': translation_languages,
            'parent': i.parent_id
        })
    
    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/question_answer.html', {'vid': vid, 'data': data, 'p': p, 'page': page, 'lang': lang, 'qtype': 'admin', 'qa_list_type': 'answers'}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def questions_translate_admin(request, id, code):

    lang = get_language()

    try:
        qa = QuestionAnswer.objects.get(pk=id)
    except QuestionAnswer.DoesNotExist:
        raise Http404

    filter = {'reader_type': '22', 'questionanswer__id': qa.id, 'translation_for': None}
    try:
        question = News.objects.select_related('autor', 'language').get(**filter)
    except News.DoesNotExist:
        raise Http404

    if request.POST:
        original_edit = request.POST.get('original_edit')
        original_id = request.POST.get('original_id')
        translation_id = request.POST.get('translation_id')
        translate_to_lang = request.POST.get('translate_to_lang')
        subject = BeautifulSoup(request.POST.get('translation_subject', '').strip(), from_encoding='utf-8').text.strip()
        text = BeautifulSoup(request.POST.get('translation_txt', '').strip(), from_encoding='utf-8').text.strip()
        tags_txt = request.POST.get('translation_tags')

        if len(subject) > 1 and len(text) > 1:
            if original_edit and original_id:
                translation_id = original_id

            if translation_id:
                
                translated_question = News.objects.get(pk=int(translation_id), reader_type = '22')
                translated_question.title = subject
                translated_question.text = text
                translated_question.save()
                translated_question.tags.clear()
                for tag in set(tags_txt.split(';')):
                    tag = tag.strip()
                    if tag:
                        obj, created = NewsTags.objects.get_or_create(name=tag, defaults={'name': tag})
                        translated_question.tags.add(obj)

            else:
                language = Language.objects.get(code=translate_to_lang)

                translated_question = News.objects.create(
                    title = subject,
                    text = text,
                    visible = True,
                    autor = question.autor,
                    site = question.site,
                    subdomain = 0,
                    reader_type = '22',
                    language = language,
                    translation_for = question,
                )
                translated_question.dtime = question.dtime
                translated_question.save()

                qa.item.add(translated_question)

                for tag in set(tags_txt.split(';')):
                    tag = tag.strip()
                    if tag:
                        obj, created = NewsTags.objects.get_or_create(name=tag, defaults={'name': tag})
                        translated_question.tags.add(obj)

        return HttpResponseRedirect(reverse('imiagroup_questions_translate_admin', kwargs={'id': id, 'code': code}))

    filter['translation_for'] = question
    filter['language__code'] = code
    try:
        translation = News.objects.select_related('autor', 'language').get(**filter)
    except News.DoesNotExist:
        translation = None

    tags_list = set(list(NewsTags.objects.filter(news__reader_type='22').values_list('name', flat=True)))

    question_tags = set([i.name for i in question.tags.all()])
    translation_tags = set([i.name for i in translation.tags.all()]) if translation else []

    question_author = org_peoples([question.autor])[0]

    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/questions_translate_admin.html', {'vid': vid, 'question': question, 'question_tags': question_tags, 'question_author': question_author, 'translation_tags': translation_tags, 'tags_list': tags_list, 'lang': lang, 'translation': translation, 'code': code}, context_instance=RequestContext(request))


@only_superuser
@never_cache
def answers_translate_admin(request, id, parent, code):

    lang = get_language()

    try:
        qa = QAnswers.objects.get(pk=id)
    except QAnswers.DoesNotExist:
        raise Http404

    filter = {'reader_type': '23', 'qanswers__id': qa.id, 'parent__id': parent, 'translation_for': None}
    try:
        answer = News.objects.select_related('autor', 'language', 'parent').get(**filter)
    except News.DoesNotExist:
        raise Http404


    filter = {'reader_type': '22', 'pk': parent, 'translation_for': None}
    question = News.objects.filter(**filter).values_list('questionanswer', flat=True)[0]

    
    if request.POST:
        original_edit = request.POST.get('original_edit')
        original_id = request.POST.get('original_id')
        translation_id = request.POST.get('translation_id')
        translate_to_lang = request.POST.get('translate_to_lang')
        text = BeautifulSoup(request.POST.get('translation_txt', '').strip(), from_encoding='utf-8').text.strip()

        if len(text) > 1:
            if original_edit and original_id:
                translation_id = original_id

            if translation_id:
                translated_answer = News.objects.get(pk=int(translation_id), reader_type='23')
                translated_answer.text = text
                translated_answer.save()
            else:
                language = Language.objects.get(code=translate_to_lang)

                translated_answer = News.objects.create(
                    title = '',
                    text = text,
                    visible = True,
                    autor = answer.autor,
                    site = answer.site,
                    subdomain = 0,
                    reader_type = '23',
                    language = language,
                    translation_for = answer,
                    parent = answer.parent,
                )
                translated_answer.dtime = answer.dtime
                translated_answer.save()

                qa.item.add(translated_answer)

        return HttpResponseRedirect(reverse('imiagroup_answers_translate_admin', kwargs={'id': id, 'parent': parent, 'code': code}))
    
    filter = {'reader_type': '23', 'qanswers__id': qa.id, 'parent__id': parent, 'translation_for': answer, 'language__code': code}

    try:
        translation = News.objects.select_related('autor', 'language').get(**filter)
    except News.DoesNotExist:
        translation = None

    answer_author = org_peoples([answer.autor])[0]

    vid = 99 if request.domain == '0.0.1:8000' else 95

    return render_to_response('imiagroup/answers_translate_admin.html', {'vid': vid, 'answer': answer, 'answer_author': answer_author, 'lang': lang, 'translation': translation, 'code': code, 'question': question}, context_instance=RequestContext(request))

