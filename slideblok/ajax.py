# -*- coding: utf-8 -*-

from django.utils import simplejson
from django.conf import settings
from django.template.context import RequestContext

from dajaxice.decorators import dajaxice_register

from base.models import PersonInterface
from movie_online.debug import debug_logs


@dajaxice_register
def interface_select(request, interface_type, block_type):
    debug_logs(1)
    if request.user.is_superuser:

        profile = RequestContext(request).get('profile')
        interface = profile.personinterface
        if int(block_type) == 1:
            interface.option1 = int(interface_type)
        if int(block_type) == 2:
            interface.option2 = int(interface_type)
        if int(block_type) == 3:
            interface.option3 = int(interface_type)
        if int(block_type) == 4:
            interface.option4 = int(interface_type)

        interface.save()
    return simplejson.dumps({'status': True})







