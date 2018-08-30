# -*- coding: utf-8 -*- 
from django import template
from django.template import RequestContext
from django.conf import settings
from base.models import Articles
from articles.views import pagination
register = template.Library()



@register.simple_tag
def umrunet_advert_brand_piclink():
    url = open('%s/background_url_umru.net.txt' % settings.API_EX_PATH, 'r').read()
    return url
    
@register.simple_tag
def umrunet_advert_brand_img():
    img = '%sbg/brand_umru.net.jpg' % settings.MEDIA_URL
    return img

@register.inclusion_tag('panel/umrunet_panel_menu.html', takes_context = True)
def umrunet_panel_menu(context):
    return {'value': 0, 'user': context['user']}
    
@register.inclusion_tag('user/umrunet_openid.html')
def umrunet_user_openid(message=''):
    return {'message': message}
    
@register.inclusion_tag('user/umrunet_email.html')
def umrunet_user_email():
    return {'value': 0}

@register.inclusion_tag('user/umrunet_livejournal.html')
def umrunet_user_lj():
    return {'value': 0}
    
@register.inclusion_tag('articles/umrunet_articles_menu.html', takes_context = True)
def umrunet_articles_menu(context):
    page = context['request'].GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    articles = Articles.objects.filter(site=settings.SITE_ID).order_by('id')
    p, page = pagination(page, articles, 6)
    return {'p': p, 'page': page, 'user': context['user']}

