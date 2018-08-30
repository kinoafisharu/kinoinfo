# -*- coding: utf-8 -*-
from django.contrib import admin
from base.models import *
'''
# подключаем модели топиков
admin.site.register(Section)
admin.site.register(Topick)
# подключаем модели "простых" справочников
# справочники источника
admin.site.register(Language)
admin.site.register(Country)
admin.site.register(Version)
admin.site.register(Genre)
# справочники персоны
admin.site.register(Action)
admin.site.register(StatusAct)
# справочники носителя
admin.site.register(CarrierType)
admin.site.register(CarrierLayer)
admin.site.register(CarrierRipType)
admin.site.register(CarrierTapeCategorie)
# справочники копии
admin.site.register(CopyFilmType)
admin.site.register(CopyFilmFormat)
admin.site.register(CopyFilmAddValue)
# подключаем модели справочников
admin.site.register(Source)     # источник

admin.site.register(Budget)     # бюджет
admin.site.register(Currency)   # валюта

admin.site.register(Carrier)    # носитель
admin.site.register(CopyFilm)   # копия
admin.site.register(AboutFilm)  # источник

admin.site.register(NameFilm)   # имена фильма
admin.site.register(Note)       # аннотация фильма

admin.site.register(Person)     # персона
# подключаем модели Связи
admin.site.register(RelationFP)

admin.site.register(City)
admin.site.register(Cinema)
admin.site.register(Hall)
admin.site.register(CinemaCircuit)
admin.site.register(Metro)
admin.site.register(StreetType)
admin.site.register(Phone)
admin.site.register(Site)
admin.site.register(Session)

# импорт источников
admin.site.register(ImportSources)
'''
