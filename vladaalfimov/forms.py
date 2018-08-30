# -*- coding: utf-8 -*- 
import datetime

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from tinymce.widgets import TinyMCE

from base.models import Post



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        
    title = forms.CharField(widget=forms.TextInput(attrs={'size': 60}), label='Title', required=False)
    text = forms.CharField(widget=forms.Textarea(attrs={'rows': 14, 'style': "width: 100%;"}), label='Text', required=False)
