# -*- coding: utf-8 -*-
import operator
from django import forms
from base.models import *
from base.models_choices import OWNERSHIP_CHOICES
from tinymce.widgets import TinyMCE

class DistributorsForm(forms.ModelForm):
    class Meta:
        model = Distributors
    iid = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), required=False)
    kid = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), required=False)
    name = forms.ModelMultipleChoiceField(queryset=NameDistributors.objects.all().order_by('name'), widget=forms.SelectMultiple(attrs={'size': 10}), required=False)
    exclude = ('film',)


class NameDistributorsForm(forms.ModelForm):
    class Meta:
        model = NameDistributors
    status = forms.CharField(widget=forms.TextInput(attrs={'size': 5}))


class ImportSourcesForm(forms.ModelForm):
    class Meta:
        model = ImportSources
    code = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), required=False)
    source = forms.CharField(widget=forms.TextInput(attrs={'size': 17}))
    dump = forms.CharField(widget=forms.TextInput(attrs={'size': 13}), required=False)
    url = forms.CharField(widget=forms.TextInput(attrs={'size': 18}))
    
    def clean_code(self):
        if self.cleaned_data['code']:
            code = self.cleaned_data['code']
            if code == '':
                code = None
            return code
            
    def clean_dump_name(self):
        if self.cleaned_data['dump_name']:
            dump_name = self.cleaned_data['dump_name']
            if dump_name == '':
                dump_name = None
            return dump_name


class OkinoUploadForm(forms.Form):
    file = forms.FileField()


class ActionsPriceListForm(forms.ModelForm):
    class Meta:
        model = ActionsPriceList
    
    price = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), label="Цена добавления")
    price_edit = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), required=False, label="Цена изменения")
    price_delete = forms.CharField(widget=forms.TextInput(attrs={'size': 5}), required=False, label="Цена удаления")
    user_group = forms.ModelChoiceField(queryset=Group.objects.all(), label="Группа пользователей", required=False, widget=forms.Select())


    def clean_price(self):
        if self.cleaned_data['price']:
            return self.cleaned_data['price'].replace(',','.')
            
    def clean_price_edit(self):
        if self.cleaned_data['price_edit']:
            return self.cleaned_data['price_edit'].replace(',','.')
            
    def clean_price_delete(self):
        if self.cleaned_data['price_delete']:
            return self.cleaned_data['price_delete'].replace(',','.')
            
