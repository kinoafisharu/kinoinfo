# -*- coding: utf-8 -*-

import datetime
from htmlentitydefs import name2codepoint
import os
import re


def rel(*x):
    ''' генерирует системный путь  '''
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), * x)


def htmldecode(text):
    """Decode HTML entities in the given text."""
    if type(text) is unicode:
        uchr = unichr
    else:
        uchr = lambda value: value > 255 and unichr(value) or chr(value)

    def entitydecode(match, uchr=uchr):
        entity = match.group(1)
        if entity.startswith('#x'):
            return uchr(int(entity[2:], 16))
        elif entity.startswith('#'):
            return uchr(int(entity[1:]))
        elif entity in name2codepoint:
            return uchr(name2codepoint[entity])
        else:
            return match.group(0)
    charrefpat = re.compile(r'&(#(\d+|x[\da-fA-F]+)|[\w.:-]+);?')
    return charrefpat.sub(entitydecode, text)


def logger(file, text, action):
    if file == 0:
        f = open(rel('logs/load_topick.txt'), action)
    elif file == 1:
        f = open(rel('logs/clean_topick.txt'), action)
    elif file == 2:
        f = open(rel('logs/afisha_film.txt'), action)
    elif file == 3:
        f = open(rel('logs/cron.txt'), action)
    else:
        return None
    f.write(str(datetime.datetime.now()) + '| ' + text + '\n')
    f.close()
    return None


def add_model_element(model, name, value):
    ''' добавляет запись в модель '''
    if model.objects.filter(name=value):
        m = model.objects.get(name=value)
    else:
        m = model(name=value)
        m.save()
    return m
