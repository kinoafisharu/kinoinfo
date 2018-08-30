# -*- coding: utf-8 -*- 
import operator
import datetime

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.db.models import Q, Max, Min
from django import db
from django.conf import settings

from user_registration.func import *
from kinoinfo_folder.func import low, capit, del_separator
from api.models import FilmsName
from base.models import *
from base.func import create_kinoafisha_button
from articles.views import pagination as pagi



@never_cache
def get_spec(request, url, id=None):
    from letsgetrhythm.views import view_func

    access = False
    if request.user.is_superuser or url == 'booking':
        access = True

    if access:

        try:
            spec = OrgSubMenu.objects.get(name='SPEC', url=url, page_type='1')
        except OrgSubMenu.DoesNotExist:
            create = request.GET.get('create')
            if create:
                spec = OrgSubMenu.objects.create(name='SPEC', url=url, page_type='1')
                return HttpResponseRedirect(reverse('get_spec', kwargs={'url': url}))
            else:
                ref = request.META.get('HTTP_REFERER', '/')
                html = u'''
                    <div style="text-align: center; width: 300px; height: 100px; border: 1px solid #CCC; border-radius: 10px; margin: 100px auto; padding: 20px; ">
                    <b>Для этого URL не создан блог</b>
                    <br /><br />
                    <a href="?create=yes">Создать</a> | <a href="%s">Отмена</a>
                    </div>
                    ''' % ref
                return HttpResponse(str(html.encode('utf-8')))

        data = view_func(request, spec.id, id, 'spec', True)
        
        if data == 'redirect':
            return HttpResponseRedirect(reverse('get_spec', kwargs={'url': url}))

        if not id and data['count'] == 1:
            return HttpResponseRedirect(reverse('get_spec', kwargs={'url': url, 'id': data['news_data'][0]['obj'].id}))


        main_email = request.user.email
        emails = []
        for i in request.profile.accounts.all():
            if i.email and i.email.strip():
                emails.append(i.email.strip())
        emails = set(emails)
        email_exist = True if main_email or emails else False

        comments_subscribed = False
        if id:
            try:
                comments_subscribed = SubscriberUser.objects.get(profile=request.profile, type='2', obj=id).id
            except SubscriberUser.DoesNotExist: pass

        data['url'] = url
        data['title'] = u'Спек для %s' % url
        data['email_exist'] = email_exist
        data['comments_subscribed'] = comments_subscribed

        return render_to_response('release_parser/get_spec.html', data,  context_instance=RequestContext(request))
    else:
        raise Http404

