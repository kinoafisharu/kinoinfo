# -*- coding: utf-8 -*-
from django import forms


class MegogoUploadForm(forms.Form):
    file = forms.FileField()

