# -*- coding: utf-8 -*- 
import operator
import datetime
import time

from django.http import HttpResponse
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives

from bs4 import BeautifulSoup
from dajaxice.decorators import dajaxice_register

from base.models import *
from letsgetrhythm.views import send_invite_invoice, getfiles_func
from kinoinfo_folder.func import get_month_en
from user_registration.views import get_usercard

@never_cache
@dajaxice_register
def letsget_edit_tag(request, id, val):
    #try:
    if request.user.is_superuser or request.is_admin:
        current_site = request.current_site
        subdomain = request.subdomain
        
        pk = id.split(';')
        client = LetsGetClients.objects.filter(pk=pk[1], site=current_site, subdomain=subdomain).update(tag=val)
        
        color = ''
        if val == 'OK':
            color = '#B2E0B2'
        elif val == 'NO':
            color = '#FFCCCC'
            
        return simplejson.dumps({'status': True, 'id': id.replace(';', '__'), 'val': val, 'color': color})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

@never_cache
@dajaxice_register
def letsget_edit_note(request, id, val):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
        
            pk = id.split(';')
            client = LetsGetClients.objects.select_related('organization').get(pk=pk[1], site=current_site, subdomain=subdomain)
            extra = ['', '', '', '']
            if client.organization.extra:
                extra = client.organization.extra.replace(' 00:00:00','').split(';')
            
            if pk[0] == 'note0':
                year, month, day = val.split('-')
                try:
                    val = datetime.datetime(int(year), int(month), int(day))
                except ValueError:
                    month = get_month_en(month)
                    val = datetime.datetime(int(day), int(month), int(year))

            extra[int(pk[0].replace('note',''))] = str(val)
            client.organization.extra = ';'.join(extra)
            client.organization.save()
            
            if pk[0] == 'note0':
                val = val.strftime('%d-%b-%Y').lower()
                
            return simplejson.dumps({'status': True, 'id': id.replace(';', '__'), 'val': val})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))
    

def get_inv_tmplt(itype, site, subdomain):
    inv_t = {'invite': '15', 'invoice': '16',}
    type_obj = inv_t.get(itype)
    if not subdomain:
        subdomain = 0
    objs = []
    for ind, i in enumerate(News.objects.filter(site=site, subdomain=subdomain, reader_type=type_obj)):
        check = 'checked' if ind == 0 else ''
        objs.append({'id': i.id, 'title': i.title, 'check': check, 'txt': i.text})
        
    return objs

@never_cache
@dajaxice_register
def invoice_gen(request, arr, name, validate, cl, files, tmpl, txt):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            
            invites_relations = {u'SCH': 5611, u'NH': 5610}
            if request.domain == '0.0.1:8000':
                invites_relations = {u'SCH': 44458, u'NH': 44457}
    

            if name == 'invite':
                invite = True
                invoice = False
            elif name == 'invoice':
                invite = False
                invoice = True
                cl = False
                files = []
                
            objs = []
            
            if invite or invoice:
                log = send_invite_invoice(current_site, arr, invite, invoice, validate, cl, files, tmpl, txt, invites_relations)
                
                if name == 'invoice' and validate:
                    #objs = get_inv_tmplt(name, current_site)
                    objs = []
                
                return simplejson.dumps({'status': True, 'type': '', 'log': log, 'validate': validate, 'objs': objs})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def invite_files(request, itype, cl, arr):
    #try:
        current_site = request.current_site
        subdomain = request.subdomain
        
        files, path = getfiles_func(current_site.domain, subdomain, 'private')
        
        objs = get_inv_tmplt(itype, current_site, subdomain)


        if current_site.domain == 'letsgetrhythm.com.au':
            invrel = {u'SCH': 5611, u'NH': 5610}
            if request.domain == '0.0.1:8000':
                invrel = {u'SCH': 44458, u'NH': 44457}
        
            if cl:
                data = LetsGetClients.objects.select_related('organization').filter(pk__in=arr)
            else:
                data = LetsGetCalendar.objects.select_related('client', 'client__organization', 'bank').filter(pk__in=arr)
            
            text = ''
            title = ''
            tmpl = 0
            for i in data:
                client_tag = i.tag if cl else i.client.tag
                if client_tag in (u'SCH', u'NH'):
                    tmpl = invrel.get(client_tag, 0)
                    try:
                        text = News.objects.get(pk=tmpl, site=current_site)
                        title = text.title
                        text = text.text
                    except News.DoesNotExist: pass
                    

        return simplejson.dumps({'status': True, 'files': files, 'cl': cl, 'objs': objs, 'tmpl': tmpl, 'text': text, 'title': title})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 


@never_cache
@dajaxice_register
def letsget_bank(request, id, name, acc):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            
            if name and acc:
                if not id:
                    id = None
                bank, created = LetsGetBank.objects.get_or_create(
                    id = id,
                    site = current_site,
                    subdomain = subdomain,
                    defaults = {
                        'name': name,
                        'account': acc,
                        'site': current_site,
                        'subdomain': subdomain,
                    })
                if not created:
                    bank.name = name
                    bank.account = acc
                    bank.save()
                
            banks = list(LetsGetBank.objects.filter(site=current_site, subdomain=subdomain).values('id', 'name', 'account'))
            
            return simplejson.dumps({'status': True, 'content': banks})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 



def get_bcr_and_bcr_code(client_id, event):
    ev = LetsGetCalendar.objects.filter(client__id=client_id).exclude(Q(pdf='') | Q(pdf=None)).order_by('-bcr')

    # если редактируется инвойс, то беру текущее значение
    current_bcr, current_bcr_code, next, warning = (event.bcr, event.bcr_code, False, True) if event else (1, 'BCR', True, False)
    
    if ev:
        ev = ev[0]
        bcr = ev.bcr + 1 if ev.bcr else 1
        bcr_code = ev.bcr_code
        next = True
    else:
        bcr, bcr_code = (current_bcr, current_bcr_code)
        next = False

    return {
        'curr_bcr': str(current_bcr),
        'curr_code': current_bcr_code,
        'next_bcr': str(bcr),
        'next_code': bcr_code,
        'next': next,
        'warning': warning,
    }


@never_cache
@dajaxice_register
def bcr(request, id, next, event):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            filter = {'site': current_site, 'subdomain': subdomain}
            ev_obj = None
            
            curr_code = 'BCR'
            curr_num = 1
            
            if event and int(event):
                filter['pk'] = event
                ev_obj = LetsGetCalendar.objects.get(**filter)
                curr_code = ev_obj.bcr_code
                curr_num = ev_obj.bcr

            bcr = get_bcr_and_bcr_code(id, ev_obj)

            #bcr['curr_code'] = curr_code
            #bcr['curr_num'] = curr_num

            return simplejson.dumps({'status': True, 'content': bcr})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 
    



def get_bcr_and_bcr_code_nxt(client_id):

    ev = LetsGetCalendar.objects.filter(client__id=client_id).order_by('-dtime')
    if ev:
        event = ev[0]
        
        # текущее значение
        curr_bcr_num = event.bcr + 1 if event.bcr else 1
        curr_bcr_code = event.bcr_code if event.bcr_code else 'BCR'
        
        # предыдущее значение
        prev_bcr_num = event.bcr if event.bcr else 0
        prev_bcr_code = curr_bcr_code

        # следующее значение
        next_bcr_num = curr_bcr_num + 1
        next_bcr_code = curr_bcr_code
    else:
        curr_bcr_num, curr_bcr_code = (1, 'BCR')
        prev_bcr_num, prev_bcr_code = (0, 'BCR')
        next_bcr_num, next_bcr_code = (2, 'BCR')
        
    return {
        'curr_bcr': str(curr_bcr_num),
        'curr_code': curr_bcr_code,
        'next_bcr': str(next_bcr_num),
        'next_code': next_bcr_code,
        'prev_bcr': str(prev_bcr_num),
        'prev_code': prev_bcr_code,
        'next': next,
    }



def get_bcr_and_bcr_code2(client_id, event):

    # текущее значение
    curr_bcr_num, curr_bcr_code = (event.bcr, event.bcr_code) if event and event.bcr else (1, 'BCR')
        
    # предыдущее значение
    prev_ev = None
    if event:
        prev_ev = LetsGetCalendar.objects.filter(client__id=client_id, bcr_code=curr_bcr_code, dtime__lt=event.dtime).exclude(pk=event.id).order_by('-dtime')
        
    if prev_ev:
        prev_bcr_num = prev_ev[0].bcr if prev_ev[0].bcr else 0
        prev_bcr_code = prev_ev[0].bcr_code if prev_ev[0].bcr_code else curr_bcr_code
    else:
        prev_bcr_num = 0
        prev_bcr_code = None

    # следующее значение
    next_ev = None
    if event:
        next_ev = LetsGetCalendar.objects.filter(client__id=client_id, bcr_code=curr_bcr_code, dtime__gt=event.dtime).exclude(pk=event.id).order_by('dtime')
    if next_ev:
        next_bcr_num = next_ev[0].bcr if next_ev[0].bcr else 1
        next_bcr_code = next_ev[0].bcr_code if next_ev[0].bcr_code else curr_bcr_code
    else:
        next_bcr_num = curr_bcr_num + 1 
        next_bcr_code = curr_bcr_code
    
    return {
        'curr_bcr': str(curr_bcr_num),
        'curr_code': curr_bcr_code,
        'next_bcr': str(next_bcr_num),
        'next_code': next_bcr_code,
        'prev_bcr': str(prev_bcr_num),
        'prev_code': prev_bcr_code,
    }

@never_cache
@dajaxice_register
def bcr2(request, id, next, event):
    #try:
        if request.user.is_superuser or request.is_admin:
            current_site = request.current_site
            subdomain = request.subdomain
            
            filter = {'site': current_site, 'subdomain': subdomain}
            ev_obj = None
            
            if event and int(event):
                filter['pk'] = event
                try:
                    ev_obj = LetsGetCalendar.objects.get(**filter)
                except LetsGetCalendar.DoesNotExist:
                    pass

            if next:
                bcr = get_bcr_and_bcr_code_nxt(id)
            else:
                bcr = get_bcr_and_bcr_code2(id, ev_obj)
            
            bcr['next'] = next
            bcr['status'] = True

            return simplejson.dumps(bcr)
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 



@never_cache
@dajaxice_register
def send_reminder_email(request, arr):
    #try:
        if request.user.is_superuser or request.is_admin:
            count = 0
            
            current_site = request.current_site
            subdomain = request.subdomain
            
            if current_site.domain == 'letsgetrhythm.com.au':
                froms = {
                    'letsgetrhythm.com.au': 'letsgetrhythm@gmail.com',
                    'vladaalfimovdesign.com.au': 'vladaalfimov@gmail.com',
                    'imiagroup.com.au': 'info@imiagroup.com.au',
                }
                
                efrom = froms.get(current_site.domain, '')
                
                filter = {'pk__in': arr, 'site': current_site}

                data = LetsGetCalendar.objects.select_related('client', 'client__organization', 'bank').filter(**filter)
        
                for i in data:
                    org = i.client.organization

                    if org:
                        profile = org.staff.all()
                        if profile:
                            profile = profile[0]
                    else:
                        profile = i.profile if clients else i.client.profile

                    
                    if profile:
                        card = get_usercard(profile.user_id, ucity=False)
                        email = None
                        if card['email']:
                            email = card['email']
                        elif not card['email'] and card['emails']:
                            profile.user.email = card['emails'][0]
                            profile.user.save()
                            card['email'] = card['emails'][0]
                            email = card['email']
                        if not card['email'] and card['emails_not_auth']:
                            email = card['emails_not_auth'][0]


                        if email and '@' in email:
                            
                            bcr = str(i.bcr)
                            if len(bcr) == 1:
                                bcr = u'0%s' % bcr
                            bcr_code = i.bcr_code
                            
                            invoice_num = u'%s-%s' % (bcr_code, bcr)
                            
                            subject = u'"%s" Reminder' % current_site.name
                            
                            msg = u"Dear customer! My records shows that invoice No %s wasn't paid yet. Please check. If this invoice been paid, please send to me date when it been done. Thank you.<br /><br />\
                                Kind regards<br />\
                                Administration of %s." % (invoice_num, current_site.name)

                            msg_clear = BeautifulSoup(msg, from_encoding='utf-8').text.strip()

                            msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                                %s <br /><br /></div>' % msg
                            
                            # отправка письма клиенту
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, [email.strip()])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.send()
                            
                            count += 1
                
                msg_msg = 'Messages' if count > 1 else 'Message'
                return_msg = '<b>%s</b> %s Has Been Sent Successfully' % (count, msg_msg)
                
                return simplejson.dumps({'status': True, 'msg': return_msg})
            
        return simplejson.dumps({})
        
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


@never_cache
@dajaxice_register
def send_report_client(request, id):
    #try:
        if request.user.is_superuser or request.is_admin:
            froms = {
                'letsgetrhythm.com.au': 'letsgetrhythm@gmail.com',
                'vladaalfimovdesign.com.au': 'vladaalfimov@gmail.com',
                'imiagroup.com.au': 'info@imiagroup.com.au',
            }
            
            orgs_dict = {}
            orgs = Organization.objects.select_related('domain').filter(uni_slug__in=('vlada-alfimov-design', 'lets-get-rhythm', 'imia-group'))
            for i in orgs:
                orgs_dict[i.domain.domain] = i.email
            
            vid, post_id, id = id.split(';')
        
            current_site = request.current_site
            subdomain = request.subdomain

            filter = {'site': current_site, 'subdomain': subdomain, 'pk': id}
           
            try:
                obj = LetsGetCalendar.objects.select_related('report').get(**filter)
            except LetsGetCalendar.DoesNotExist: 
                obj = None
                
            if obj:
                profile = None
                org = obj.client.organization
                if org:
                    profile = org.staff.all()
                    if profile:
                        profile = profile[0]
                else:
                    profile = obj.client.profile
                
                if profile:
                    card = get_usercard(profile.user)
                    
                    email = None
                    
                    if card['email']:
                        email = card['email']
                    elif not card['email'] and card['emails']:
                        profile.user.email = card['emails'][0]
                        profile.user.save()
                        card['email'] = card['emails'][0]
                        email = card['email']
                    
                    if not card['email'] and card['emails_not_auth']:
                        email = card['emails_not_auth'][0]

                        
                if (org and not profile) or (org and profile and not email):
                    email = org.email if org.email else None
                
                
                if current_site.domain == 'letsgetrhythm.com.au':
                    if email:
                        if '@' in email:
                            efrom = froms.get(current_site.domain, '')
                            
                            if subdomain:
                                site = u'%s.%s' % (subdomain, current_site.domain)
                            else:
                                site = current_site.domain
                            url = u'http://%s/view/%s/post/%s/' % (site, vid, post_id)

                            add_to_msgh = u'<b>Original Post Here: <a href="%s">%s</a></b>' % (url, url)
                            
                            msg = obj.report.text
                            msg_clear = BeautifulSoup(msg, from_encoding='utf-8').text.strip()
                            msg_html = u'<div style="background: #FFF; padding: 5px; font-size: 14px; color: #333;">\
                                %s <br /><br />%s</div>' % (msg, add_to_msgh)
                            
                            subject = u'"%s" Report' % current_site.name
                            
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, [email.strip()])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.send()
                            
                            obj.report_send = True
                            obj.save()

                            # ------------------------------
                            # копия для Алфимова
                            subject = u'%s [COPY]' % subject
                            admin_email = orgs_dict.get(current_site.domain)
                            if admin_email:
                                mail = EmailMultiAlternatives(subject, msg_clear, efrom, [admin_email])
                                mail.attach_alternative(msg_html, "text/html")
                                mail.send()
                            
                            # копия для Иванова
                            mail = EmailMultiAlternatives(subject, msg_clear, efrom, ['kinoafisharu@gmail.com'])
                            mail.attach_alternative(msg_html, "text/html")
                            mail.send()

                            return simplejson.dumps({'status': True, 'msg': "<span style='color: green;'>Report Message Has Been Sent Successfully</span>", 'send': True})
                        else:
                            return simplejson.dumps({'status': True, 'msg': "<span style='color: red;'>Client Had An Incorrect E-mail Address</span>", 'send': False})
                    else:
                        return simplejson.dumps({'status': True, 'msg': "<span style='color: red;'>Client Didn't Have E-mail Address</span>", 'send': False})
                else:
                    return simplejson.dumps({'status': True, 'msg': "<span style='color: red;'>Function Is Not Available</span>", 'send': False})
            else:
                return simplejson.dumps({'status': True, 'msg': "<span style='color: red;'>Object Does Not Exist</span>", 'send': False})

        return simplejson.dumps({'status': False})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 
    


@never_cache
@dajaxice_register
def blog_cmmnt(request, pst, answ, stype, text, rev):
    try:
        from news.views import is_news_spam, is_banned_user, create_news
        
        current_site = request.current_site
        subdomain = request.subdomain
        if not subdomain:
            subdomain = 0
        
        msg_type = '10'
        
        author_nick = 0 
        if stype in ('0', '1', '2'):
            if request.user.is_superuser or request.is_admin:
                author_nick = stype

        # антиспам
        spam = is_news_spam(request, msg_type)
        banned = is_banned_user(request)

        if not spam and not banned:
            try:
                pst_exsit = News.objects.get(pk=pst, site=current_site, subdomain=subdomain)
            except News.DoesNotExist:
                pst_exsit = None
                
            if pst_exsit:
                answer = answ if int(answ) else answ
                text = BeautifulSoup(text, from_encoding="utf-8").text.strip()
                    
                if text:
                    extra = '%s;%s' % (pst, answer) if answer else '%s;' % pst
                    news = create_news(request, [], 'Comment', text, msg_type, author_nick, extra)
                    
                    return simplejson.dumps({'status': True, 'msg': ''})
                    
                else:
                    return simplejson.dumps({'status': True, 'msg': "Comment Must Be Longer"})
            else:
                return simplejson.dumps({'status': True, 'msg': "Post Does Not Exist"})
        else:
            txt = ''
            if spam:
                txt = request.session.get('news_antispam','')
                if txt:
                    txt = unicode(txt)
            if banned:
                if txt:
                    txt += u'<br /><br />'
                txt += u'<b>You Have Been Banned!<br /><br />You Can Not Send Messages.<br /><br />All Questions To Submit To The <a href="#in_modal" id="modal">Feedback</a></b>'

            return simplejson.dumps({'status': True, 'msg': txt})
                        
        return simplejson.dumps({'status': False})
        
    except Exception as e:
        open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args)) 



