# -*- coding: utf-8 -*-
from django.utils import translation

def base_processor(request):
    current_site = request.current_site
    
    data = {}
    data['acc_list'] = request.acc_list
    data['current_user_city'] = request.current_user_city
    data['current_user_city_id'] = request.current_user_city_id
    data['current_site'] = request.current_site
    data['profile'] = request.profile
    data['new_messages'] = request.new_messages
    data['fio'] = request.fio
    data['mymoney'] = request.mymoney
    
    if current_site.domain == 'kinoinfo.ru':
        if translation.get_language() != 'ru':
            #translation.activate('ru')
            pass
    elif current_site.domain == 'letsgetrhythm.com.au':
        if translation.get_language() != 'en':
            translation.activate('en')

    return data

