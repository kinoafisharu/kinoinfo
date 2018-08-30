# -*- coding: utf-8 -*- 
from django import forms
from django.core import validators


from base.models import News



class LetsGetNewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'text', 'visible']
        
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), label='Title', required=False)
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 14, 'style': "width: 100%;"}), label='Text', required=False)
