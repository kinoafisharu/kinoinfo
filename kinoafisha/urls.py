# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('kinoafisha.views',
    # получение и сохраниение источников из файла sms.txt
    url(r'^save_sms_sources/$', 'save_sms_sources', name='save_sms_sources'),
    # получение данных из источников (sms, yandex, rambler)
    url(r'^get_source_data/(?P<source_id>\d+)/$', 'get_source_data', name='get_source_data'),
    # сохранение сеансов в БД из sms
    url(r'^save_sms_schedule/$', 'save_sms_schedule', name='save_sms_schedule'),
    # редактор лога
    url(r'^editor/(?P<event>\d+)/(?P<code>\d+)/(?P<id>\d+)/$', 'editor', name='editor'),
    # вывод списка временных файлов в шаблон
    url(r'^get_files_list_sms_schedule/$', 'get_files_list_sms_schedule', name='get_files_list_sms_schedule'),
    # удаление всех временных файлов
    url(r'^delete_sms_files/$', 'delete_sms_files', name='delete_sms_files'),


)



