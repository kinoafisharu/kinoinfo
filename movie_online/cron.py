#-*- coding: utf-8 -*- 
from base.models import *
from api.models import *
from movie_online.views import *
from movie_online.parser import *


# запрос к апи мегого
megogo_request()

# сохраняем полученные данные из дампа мегого
save_data()

# идентифицируем фильмы мегого с киноафишей
megogo_ident()

# вычисление интегральной оценки
integral_rate()
