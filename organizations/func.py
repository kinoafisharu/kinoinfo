#-*- coding: utf-8 -*-
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template.context import RequestContext

def is_editor_func(request, org):
    is_editor = False
    if request.user.is_authenticated():
        profile = request.profile
        if profile in org.editors.all():
            is_editor = True
    return is_editor

    

