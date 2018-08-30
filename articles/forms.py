# -*- coding: utf-8 -*- 
from django import forms
from base.models import Articles, DjangoSite
from tinymce.widgets import TinyMCE

class ArticlesForm(forms.ModelForm):
    class Meta:
        model = Articles
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), label='Название')
    text = forms.CharField(widget=TinyMCE(attrs={'cols': 100, 'rows': 12}), label='Текст')
    site = forms.IntegerField(required=False)
    
    def clean_site(self):
        site = DjangoSite.objects.get_current()
        return site
