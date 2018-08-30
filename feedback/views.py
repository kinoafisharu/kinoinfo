# -*- coding: utf-8 -*- 
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.views.decorators.cache import never_cache

from base.models import Accounts, DjangoSite
from feedback.forms import FeedbackForm
from user_registration.func import only_superuser
from user_registration.views import create_account
    


@never_cache
def main(request):
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        acc = Accounts.objects.filter(profile__id=profile.id).exclude(email=None)
        emails = [i.email for i in acc]
        emails = set(emails)
        current_site = DjangoSite.objects.get_current()
        feedback_msg = request.session.get('feedback_msg', '')
        
        request.session['feedback_msg'] = ''
        if request.POST:
            referer = request.session.get('ref')
            request.session['ref'] = ''
            form = FeedbackForm(request.POST)
            if form.is_valid():
                email = request.POST.get('emails')
                if not email:
                    email = form.cleaned_data['email']
                    create_account(profile, email, None, email=email)
                    
                msg = form.cleaned_data['msg']
                msg = u'%s\n(Пользователь %s [Отправлено со страницы %s])' % (msg, email, referer)
                # kinoafisharu@gmail.com
                # twohothearts@gmail.com
                if current_site.domain == 'kinoinfo.ru':
                    send_mail('Обратная связь kinoinfo.ru', msg, '', ['kinoafisharu@gmail.com'])
                elif current_site.domain == 'kinoafisha.in.ua':
                    send_mail('Обратная связь kinoafisha.in.ua', msg, '', ['kinoafisharu@gmail.com'])
                elif current_site.domain == 'umru.net':
                    send_mail('Обратная связь umru.net', msg, '', ['kinoafisharu@gmail.com'])
                request.session['feedback_msg'] = u'Спасибо за сообщение!'

                return HttpResponseRedirect(reverse("feedback_main"))
        else:
            try:
                request.session['ref'] = request.META['HTTP_REFERER']
            except KeyError: pass
            form = FeedbackForm()

        if current_site.domain == 'kinoinfo.ru':
            template = 'feedback/feedback.html'
        elif current_site.domain == 'umru.net':
            template = 'feedback/umrunet_feedback.html'
        elif current_site.domain == 'kinoafisha.in.ua':
            template = 'feedback/kua_feedback.html'
        return render_to_response(template, {'form': form, 'feedback_msg': feedback_msg, 'feedback': 'feedback', 'emails': emails}, context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect(reverse("main"))


@only_superuser
@never_cache
def feedback_panel(request):
    if request.POST and 'del' in request.POST:
        e = request.POST['email']
        
        
    f = open('%s/feedback_emails.txt' % settings.API_EX_PATH, 'r')
    emails = f.readlines()
    f.close()
    return render_to_response('feedback/feedback_panel.html', {'emails': emails}, context_instance=RequestContext(request))  
