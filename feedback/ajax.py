# -*- coding: utf-8 -*- 
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail

from dajaxice.decorators import dajaxice_register

from base.models import Accounts, DjangoSite


# функция создает форму обратной связи
@never_cache
@dajaxice_register
def feedback_user_request(request):
    
    profile = request.profile
    acc = Accounts.objects.filter(profile=profile).exclude(email=None)
    emails = list(set([i.email for i in acc]))
    is_email = True if emails else False
 
    return simplejson.dumps({
        'is_email': is_email, 
        'emails': emails,
    })
        


# функция обрабатывает полученные от пользователя данные 
@never_cache
@dajaxice_register
def send_user_message(request, msg, emailval, get_url, resend):
#OFC076
 #       fileNameTest = '/var/www/kinoinfo/data/www/kinoinfo/api/clients/testFeedback.txt.f'
 #       with open(fileNameTest , 'a') as outfile:
 #           outfile.write(str(msg)+'\n')
    #try: 
        current_site = request.current_site
        subdomain = request.subdomain
        
        if request.user.is_authenticated():
            profile = request.user.id
            user_profile = u'http://%s/user/profile/%s/' % (current_site.domain, profile)

        msg_add = '' if resend else _(u'отказался получить ответ')
            
        msg += _(u'\nПользователь: %s') % msg_add
        msg += emailval
        msg += _(u'\nОтправлено со страницы: %s') % get_url
        msg += _(u'\nПрофиль: %s') % user_profile
        
        if subdomain:
            msg += _(u'\nСубдомен: %s') % subdomain

        subj = _(u'Обратная связь %s') % current_site.domain

        subdomain = request.subdomain

        emails = ['kinoafisharu@gmail.com']
        if current_site.domain == 'vsetiinter.net':
            if subdomain == 'orsk':
                emails = ['al.duma@rambler.ru']
        elif current_site.domain == 'letsgetrhythm.com.au':
            emails = ['ialfimov@gmail.com']
        elif current_site.domain == 'vladaalfimovdesign.com.au':
            emails = ['vladaalfimov@gmail.com']

  #      with open(fileNameTest , 'a') as outfile:
  #          outfile.write('send mail... \n')
#        send_mail(subj, msg, '', emails,fail_silently=True)
        send_mail(subj, msg, '', emails)

   #     with open(fileNameTest , 'a') as outfile:
   #         outfile.write('send mail is ok \n')
        return simplejson.dumps({})
    #except Exception as e:
    #    open('errors.txt','a').write('%s * (%s)' % (dir(e), e.args))


