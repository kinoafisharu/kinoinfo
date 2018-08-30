# -*- coding: utf-8 -*- 
import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from base.models import Person, NamePerson
from base.models_dic import NameCity, City, Country
from base.models_choices import SHOW_PROFILE_CHOICES




class UserCardForm(forms.Form):
    city_query = NameCity.objects.filter(status=1).exclude(city__country=None).order_by('name')
    names_ids = [i.id for i in city_query]
    
    countries = list(City.objects.filter(name__id__in=names_ids).values_list('country', flat=True).distinct('country'))
    
    year_now = datetime.datetime.now().year
    year_now = year_now - 3
    years = [i for i in range(1930, year_now)]
    years.reverse()
    sex_choices = ((0, '---------',), (1, _(u'Мужской'),), (2, _(u'Женский'),))
    male = forms.ChoiceField(choices=sex_choices, label=_(u"Пол"))
    name = forms.CharField(required=False, label=_(u"ФИО"), validators=[validators.MinLengthValidator(2)])
    born = forms.DateField(widget=SelectDateWidget(years=years), required=False, label=_(u"Дата рождения"))
    email = forms.CharField(required=False)
    city = forms.ModelChoiceField(queryset=city_query, label=_(u"Город"), widget=forms.Select(attrs={'class': 'city_in_card'}))
    country = forms.ModelChoiceField(queryset=Country.objects.filter(pk__in=countries).order_by('name'), required=True, label=_(u"Страна"), widget=forms.Select(attrs={'class': 'country_in_card'}))
    show_profile = forms.CharField(max_length=1, widget=forms.Select(choices=SHOW_PROFILE_CHOICES), label=_(u"Страница видна"))
    nickname = forms.CharField(required=False, label=_(u"Псевдоним"))
    
    def clean_city(self):
        if self.cleaned_data['city']:
            data = self.cleaned_data['city']
            city_obj = City.objects.get(name__name=data, name__status=1)
            return city_obj
            
    def __init__(self, user_country=None, *args, **kwargs):
        super(UserCardForm, self).__init__(*args, **kwargs)
        if user_country:
            self.fields['city'] = forms.ModelChoiceField(
                NameCity.objects.filter(status=1, city__country__id=user_country).order_by('name'), 
                label="Город", 
                widget=forms.Select(attrs={'class': 'city_in_card'}))
        else:
            self.fields['city'] = forms.ModelChoiceField(
                queryset=NameCity.objects.filter(status=1).exclude(city__country=None).order_by('name'), 
                label="Город", 
                widget=forms.Select(attrs={'class': 'city_in_card', 'disabled': 'disabled'}))
        self.fields['city'].empty_label = None 
        self.fields['country'].empty_label = None 
        
