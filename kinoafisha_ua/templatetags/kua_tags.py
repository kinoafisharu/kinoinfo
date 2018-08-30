# -*- coding: utf-8 -*- 
from django import template
from django.template import RequestContext
from django.conf import settings
from base.models import Articles
from articles.views import pagination
register = template.Library()


@register.inclusion_tag('user/kua_openid.html')
def kua_user_openid(message=''):
    return {'message': message}
    
@register.inclusion_tag('user/kua_email.html')
def kua_user_email():
    return {'value': 0}

@register.inclusion_tag('user/kua_livejournal.html')
def kua_user_lj():
    return {'value': 0}
    

@register.inclusion_tag('articles/kua_articles_menu.html', takes_context = True)
def kua_articles_menu(context):
    page = context['request'].GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    articles = Articles.objects.filter(site=settings.SITE_ID).order_by('id')
    p, page = pagination(page, articles, 6)
    return {'p': p, 'page': page, 'user': context['user']}

