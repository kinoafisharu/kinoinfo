# -*- coding: utf-8 -*-
from django import forms
from base.models import *
from base.models_choices import OWNERSHIP_CHOICES
from tinymce.widgets import TinyMCE

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        exclude = ('phones', 'tags', 'edited', 'profile')
        
    city_query = NameCity.objects.filter(city__country__name='Украина', status=1).order_by('name')

    name = forms.CharField(widget=forms.TextInput(attrs={'size': 36}), label="Название", required=True)
    city = forms.ModelChoiceField(queryset=city_query, label="Город", required=True, widget=forms.Select(attrs={'style': 'width: 300px;'}))
    ownership = forms.CharField(max_length=1, widget=forms.Select(choices=OWNERSHIP_CHOICES), label="Форма собс.", required=False)
    street = forms.CharField(widget=forms.TextInput(attrs={'size': 30}), label="Название", required=False)
    street_type = forms.CharField(max_length=2, widget=forms.Select(choices=STREET_TYPE_CHOICES), label="Тип")
    room_num = forms.CharField(widget=forms.TextInput(attrs={'size': 6}), label="Номер", required=False)
    room_type = forms.CharField(max_length=1, widget=forms.Select(choices=ROOM_TYPE_CHOICES), label="Помещение")
    buildings = forms.CharField(widget=forms.TextInput(attrs={'size': 6}), label="Дом", required=False)
    note = forms.CharField(widget=TinyMCE(attrs={'cols': 56, 'rows': 10, 'style': 'width: 370px;'}), label="Примечание", required=False)
    site = forms.CharField(widget=forms.TextInput(attrs={'size': 25}), label="Сайт", required=False)
    email = forms.CharField(widget=forms.TextInput(attrs={'size': 25}), label="E-mail", required=False)

    def clean_city(self):
        if self.cleaned_data['city']:
            data = self.cleaned_data['city']
            city_obj = City.objects.get(name__name=data, name__status=1)
            return city_obj
        else:
            return None
    
    def clean_site(self):
        site = self.cleaned_data['site']
        if site:
            if 'http://' not in site:
                site = 'http://%s' % site
            return site
        else:
            return None


class OrganizationImageUploadForm(forms.Form):
    file = forms.ImageField()
    
class OrganizationImageSlideUploadForm(forms.Form):
    slides = forms.ImageField()
    
class OrganizationInviteTextForm(forms.Form):
    text = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 10}), label='Текст')
    
