# -*- coding: utf-8 -*-
from django import forms


class NewsImageUploadForm(forms.Form):
    file = forms.ImageField()

