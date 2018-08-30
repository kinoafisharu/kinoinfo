# -*- coding: utf-8 -*- 
from django import forms
from django.utils.translation import ugettext_lazy as _

from base.models import Background
from base.models_dic import NameCity, City, Country
from tinymce.widgets import TinyMCE


class BackgroundForm(forms.ModelForm):
    class Meta:
        model = Background
        
    city_query = NameCity.objects.filter(status=1).exclude(city__country=None).order_by('name')
    names_ids = [i.id for i in city_query]
    
    countries = list(City.objects.filter(name__id__in=names_ids).values_list('country', flat=True).distinct('country'))
    
    city = forms.ModelChoiceField(queryset=city_query, label=_(u"Город"), required=False, widget=forms.Select(attrs={'class': 'city_in_card'}))
    country = forms.ModelChoiceField(queryset=Country.objects.filter(pk__in=countries).order_by('name'), required=True, label=_(u"Страна"), widget=forms.Select(attrs={'class': 'country_in_card'}))
    
    url = forms.CharField(max_length=200, widget=forms.TextInput(attrs={'size': 50}))
    image  = forms.FileField(widget=forms.FileInput(attrs={'size': 40}))

    
    def clean_city(self):
        if self.cleaned_data['city']:
            data = self.cleaned_data['city']
            city_obj = City.objects.get(name__name=data, name__status=1)
            return city_obj
        else:
            return None
    
    def __init__(self, user_country=None, *args, **kwargs):
        super(BackgroundForm, self).__init__(*args, **kwargs)
        if user_country:
            self.fields['city'] = forms.ModelChoiceField(
                NameCity.objects.filter(status=1, city__country__id=user_country).order_by('name'), 
                label=_(u"Город"), 
                widget=forms.Select(attrs={'class': 'city_in_card'}))
        else:
            self.fields['city'] = forms.ModelChoiceField(
                queryset=NameCity.objects.filter(status=1).exclude(city__country=None).order_by('name'), 
                label=_(u"Город"), 
                widget=forms.Select(attrs={'class': 'city_in_card', 'disabled': 'disabled'}))
        self.fields['city'].empty_label = _(u'ДЛЯ ВСЕХ')
        self.fields['city'].required = False
        self.fields['city'].widget.attrs['title'] = 'city'
        self.fields['country'].empty_label = None 
    
    
class ApiDescriptionForm(forms.Form):
    text = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 16}), label='Текст')
    
class ApiDevForm(forms.Form):
    text = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 16}), label='Текст')
