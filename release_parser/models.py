# -*- coding: utf-8 -*-
from django.db import models

class MyStoryStrUsers(models.Model):
    nick = models.CharField(max_length=63)
    date_reg = models.DateTimeField()
    first = models.CharField(max_length=63)
    last = models.CharField(max_length=63)
    password = models.CharField(max_length=80, db_column='pass')
    session = models.IntegerField()
    time = models.DateTimeField()
    status = models.CharField(max_length=4)
    flag_del = models.BooleanField()
    wait = models.BooleanField()
    last_g = models.CharField(max_length=64)
    phone = models.CharField(max_length=63)
    favorit = models.BooleanField()
    money = models.IntegerField()
    
    class Meta:
        db_table = u'str_users'
        managed = False


class MyStoryStrArticles(models.Model):
    type = models.IntegerField()
    name = models.TextField()
    text = models.TextField()
    date = models.DateTimeField()
    user = models.ForeignKey(MyStoryStrUsers, db_column='user')
    flag_del = models.BooleanField()
    count = models.IntegerField()
    view = models.BooleanField()
    plus = models.IntegerField()
    minus = models.IntegerField()
    money = models.IntegerField()
    flags = models.CharField(max_length=6)
    date_r = models.BooleanField()
    class Meta:
        db_table = u'str_articles'
        managed = False


class MyStoryArticles(models.Model):
    type = models.BooleanField()
    name = models.TextField()
    text = models.TextField()
    date = models.DateTimeField()
    user = models.ForeignKey(MyStoryStrUsers, db_column='user')
    flag_del = models.BooleanField()
    count = models.IntegerField()
    class Meta:
        db_table = u'articles'
        managed = False


