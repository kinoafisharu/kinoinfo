# -*- coding: utf-8 -*-
from django import forms
from django.utils.encoding import smart_unicode
from django.conf import settings



class FeedbackForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'size': 20}), label='Укажите Ваш e-mail, если хотите получить ответ на Ваше сообщение', required=False)
    msg = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}), label='Текст сообщения')




