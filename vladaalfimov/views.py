#-*- coding: utf-8 -*-
import operator
import datetime
import time
import json
from random import randrange

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.template.context import RequestContext

from bs4 import BeautifulSoup

from base.models import *
from api.func import get_client_ip, get_country_by_ip, age_limits, resize_image
from user_registration.views import get_usercard
from user_registration.func import login_counter, only_superuser, md5_string_generate, only_superuser_or_admin
from news.views import cut_description
from vladaalfimov.forms import *
from organizations.forms import OrganizationImageSlideUploadForm
from kinoinfo_folder.func import low
from articles.views import pagination as pagi
from news.forms import NewsImageUploadForm
from news.views import news_edit, cut_description

@never_cache
def index(request):
    current_site = request.current_site
    site_name = current_site.name
    links = {}
    with open('%s/vlada_main_links.xml' % settings.API_EX_PATH, 'r') as f:
        links_tmp = BeautifulSoup(f.read())
        for i in links_tmp.findAll('link'):
            links[i['id']] = i['value']
    slug = 'vlada-alfimov-design'
    return render_to_response('vladaalfimov/index_new.html', {'site_name': site_name, 'current_site': current_site, 'links': links, 'slug': slug}, context_instance=RequestContext(request))


@never_cache
def about(request):
    from organizations.views import org
    
    current_site = request.current_site
    if current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
    elif current_site.domain == 'pm-prepare.com':
        slug = 'pmprepare'
        
        
    data = org(request, slug, offers=False)
    
    if data == 'redirect':
        return HttpResponseRedirect(reverse('about'))
    else:
        data['title'] = 'About Us'
        data['current_site'] = current_site
        data['site_name'] = current_site.name
        data['slug'] = slug
        return render_to_response('vladaalfimov/about_new.html', data, context_instance=RequestContext(request))


@never_cache
def main(request, id):

    current_site = request.current_site
    site_name = current_site.name

    data = {
        'new_design': (1, 'When You Need A New Design'),
        'letsget': (2, 'About Us'),
        'community': (3, 'Community Centres'),
        'healthy': (4, 'Healthy Drumming Program'),
        'info': (5, 'Drums And Percussion Info'),
        'bands': (6, 'My Bands And Events'),
    }
    
    titles = data.get(id)
    
    post_id, title = titles
    
    post, created = Post.objects.get_or_create(pk=post_id, defaults={'pk': post_id})
    
    if request.POST and (request.user.is_superuser or request.is_admin):
        form = PostForm(request.POST)
        if form.is_valid():
            post.title = form.cleaned_data['title']
            post.text = form.cleaned_data['text']
            post.visible = form.cleaned_data['visible']
            post.save()
            return HttpResponseRedirect(request.get_full_path())
    
    form = PostForm(
        initial={
            'title': post.title,
            'text': post.text,
            'visible': post.visible,
        })

    if current_site.domain == 'letsgetrhythm.com.au':
        slug = 'lets-get-rhythm'
        template = 'main.html'
    elif current_site.domain == 'vladaalfimovdesign.com.au':
        slug = 'vlada-alfimov-design'
        template = 'main_new.html'
    elif current_site.domain == 'imiagroup.com.au':
        slug = 'imia-group'
        template = 'main_new.html'

    return render_to_response('vladaalfimov/%s' % template, {'form': form, 'post': post, 'title': title, 'site_name': site_name, 'current_site': current_site, 'slug': slug}, context_instance=RequestContext(request))
    

def gallery_func(request, vid, menu, access, slug='', org_type=True, user_id=None):
    current_site = request.current_site
    site_name = current_site.name
    subdomain = request.subdomain
    flash = False

    if org_type:
        if slug:
            folder = slug
        else:
            if current_site.domain == 'letsgetrhythm.com.au':
                slug = 'lets-get-rhythm'
                folder = 'letsget_gallery'
            elif current_site.domain == 'vladaalfimovdesign.com.au':
                slug = 'vlada-alfimov-design'
                folder = 'vlada'
            elif current_site.domain == 'imiagroup.com.au':
                slug = 'imia-group'
                folder = 'imiagroup'
                flash = True
            elif current_site.domain == 'vsetiinter.net':
                slug = subdomain
                folder = subdomain
                site_name = subdomain
    else:
        folder = user_id
        slug = ''
    
    photos = list(ProjectsGallery.objects.select_related('photo').filter(orgsubmenu=menu).values('id', 'title', 'description', 'photo__file', 'photo__status', 'projectsgallerylang__title', 'projectsgallerylang__description', 'projectsgallerylang__language'))
    
    if request.POST and access:
        if 'slides' in request.FILES:
            img_path = '%s/%s' % (settings.GALLERY_PATH, folder)
            try: os.makedirs(img_path)
            except OSError: pass

            #try:
            if 'slides' in request.FILES:

                files = request.FILES.getlist('slides')

                for i in files:
                    file_format = low(i.name)
                    if flash:
                        img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif|swf)$', file_format)
                    else:
                        img_format = re.findall(r'\.(jpg|png|jpeg|bmp|gif)$', file_format)
                    if img_format:
                        img_obj = i.read()
                        img_name = '%s.%s' % (md5_string_generate(randrange(9999)), img_format[0])
                        img_path_tmp = '%s/%s' % (img_path, img_name)

                        with open(img_path_tmp, 'wb') as f:
                            f.write(img_obj)

                        if not flash:
                            resized = resize_image(1000, None, img_obj, 1500)
                            if resized:
                                resized.save(img_path_tmp)

                        img_name_tmp = '%s/%s/%s' % (settings.GALLERY_FOLDER, folder, img_name)

                        img_object = Images.objects.create(file=img_name_tmp, status=1)
                        obj = ProjectsGallery.objects.create(photo=img_object)
                        menu.gallery.add(obj)
                        
                        #if flash:
                        #    attr = 'Флэш объект'
                        #else:
                        attr = 'Изображение'

                        ActionsLog.objects.create(
                            profile = request.profile,
                            object = '7',
                            action = '1',
                            object_id = obj.id,
                            attributes = attr,
                            site = current_site,
                        )
                        
                return 'redirect'
            #except IOError:
            #    open('%s/ddd.txt' % settings.API_DUMP_PATH, 'a').write('*** ' + str(request.FILES.getlist('slides')) + '\n')
                
    count = len(photos)
    
    
    
    language = None
    if request.current_site.domain == 'imiagroup.com.au':
        try: language = Language.objects.get(code=request.current_language)
        except Language.DoesNotExist: pass
    
    photos_data = {}
    for i in photos:
    
        title = i['title']
        title_lang = ''
        description = i['description']
        description_lang = ''
        
        if language:
            if i['projectsgallerylang__title'] and i['projectsgallerylang__language'] == language.id:
                title_lang = i['projectsgallerylang__title']
            if i['projectsgallerylang__description'] and i['projectsgallerylang__language'] == language.id:
                description_lang = i['projectsgallerylang__description']

        if photos_data.get(i['id']):
            if title_lang:
                photos_data[i['id']]['title'] = title_lang
            if description_lang:
                photos_data[i['id']]['description'] = description_lang
        else:
            if title_lang:
                title = title_lang
            if description_lang:
                description = description_lang

            ext = low(i['photo__file']).split('.')[-1]
            flash = True if ext == u'swf' else False

            photos_data[i['id']] = {'title': title, 'description': description, 'id': i['id'], 'file': i['photo__file'], 'flash': flash, 'status': i['photo__status']}


    photos_data = sorted(photos_data.values(), key=operator.itemgetter('id'), reverse=True)
    
    
    page_types = ()
    page_type = menu.page_type
    if count == 0:
        page_types = PAGE_TYPES_CHOICES

    return {'photos': photos_data, 'title': menu.name, 'slug': slug, 'site_name': site_name, 'current_site': current_site, 'count': count, 'page_type': page_type, 'page_types': page_types, 'vid': vid}




@never_cache
def gallery(request, vid):
    current_site = request.current_site
    if current_site.domain == 'letsgetrhythm.com.au':
        template = 'vladaalfimov/gallery.html'
    elif current_site.domain in ('vladaalfimovdesign.com.au', 'imiagroup.com.au'):
        template = 'vladaalfimov/gallery_new.html'
    elif current_site.domain == 'vsetiinter.net':
        template = 'vladaalfimov/gallery.html'
        
    menu = get_object_or_404(OrgSubMenu, pk=vid)
    
    access = True if request.user.is_superuser or request.is_admin else False
    
    data = gallery_func(request, vid, menu, access)
    if data == 'redirect':
        return HttpResponseRedirect(reverse("gallery", kwargs={'vid': vid}))
        
    return render_to_response(template, data, context_instance=RequestContext(request))



@never_cache
def blog(request):
    current_site = request.current_site
    site_name = current_site.name
    title = 'Blog'
    
    filter = {'site': current_site, 'reader_type': None}
    if not request.user.is_superuser:
        filter['visible'] = True
        
    news = News.objects.select_related('autor').filter(**filter).order_by('-dtime')

    page = request.GET.get('page')
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    
    p, page = pagi(page, news, 6)
    
    news_ids = []
    news_data = []
    for ind, i in enumerate(p.object_list):
        description = cut_description(i.text, True, 250)
        video = True if i.video else False
        news_data.append({'obj': i, 'description': description, 'video': video})

    tags = list(NewsTags.objects.filter(news__site=current_site).values_list('name', flat=True))

    return render_to_response('vladaalfimov/blog.html', {'news_data': news_data, 'p': p, 'page': page, 'current_site': current_site, 'site_name': site_name, 'title': title, 'tags': tags}, context_instance=RequestContext(request))
    
    
@never_cache
def post(request, id, slug):
    current_site = request.current_site
    site_name = current_site.name

    filter = {'site': current_site, 'reader_type': None, 'pk': id}
    if not request.user.is_superuser:
        filter['visible'] = True

    try:
        news = News.objects.select_related('autor').get(**filter)
    except News.DoesNotExist:
        raise Http404
    
    is_editor = True if request.user.is_superuser or request.is_admin else False

    if request.POST:
        return news_edit(request, is_editor, news, id, [])
        
    form = ''
    org_id = None
    tags = []
    o_tags_list = []
    if request.user.is_superuser or request.is_admin:
        org_id = Organization.objects.get(uni_slug=slug).id
        form = NewsImageUploadForm()
        tags = list(NewsTags.objects.filter(news__site=current_site).values_list('name', flat=True))
        
        o_tags = news.tags.all()
        empty_tags = 6 - o_tags.count()
        o_tags_list = [{'id': i.id, 'name': i.name} for i in o_tags]
        o_tags_list = sorted(o_tags_list, key=operator.itemgetter('name'))
        for i in range(empty_tags):
            o_tags_list.append({'id': 99999999 + i + 1, 'name': ''})

    # Видео
    trailer_code = news.video if news.video else ''
    trailer_url = ''

    if trailer_code:
        trailer = BeautifulSoup(trailer_code, from_encoding='utf-8')
        trailer = trailer.find('iframe')
        if trailer:
            trailer_url = 'http:%s' % trailer['src']
            trailer_code = trailer
            trailer_code['width'] = 250
            trailer_code['height'] = 150
        else:
            trailer_code = ''

    trailer = str(trailer_code)

    description = cut_description(news.text, False, 160)
    
    return render_to_response('vladaalfimov/blog_post.html', {'news': news, 'description': description, 'tags': tags, 'o_tags_list': o_tags_list, 'form': form, 'video_url': trailer_url, 'video': trailer, 'org_id': org_id, 'current_site': current_site, 'site_name': site_name}, context_instance=RequestContext(request))
    
@only_superuser_or_admin
@never_cache
def set_social_icons(request):
    current_site = request.current_site
    site_name = current_site.name
    title = 'Set Social Icons'
    
    if request.POST:
        data = {
            "fb_vis": request.POST.get('fb_vis'),
            "fb_url": request.POST.get('fb_url') if 'http' in request.POST.get('fb_url') else 'http://%s' % request.POST.get('fb_url'),
            "inst_vis": request.POST.get('inst_vis'),
            "inst_url": request.POST.get('inst_url') if 'http' in request.POST.get('inst_url') else 'http://%s' % request.POST.get('inst_url'),
            "tw_vis": request.POST.get('tw_vis'),
            "tw_url": request.POST.get('tw_url') if 'http' in request.POST.get('tw_url') else 'http://%s' % request.POST.get('tw_url'),
            "pin_vis": request.POST.get('pin_vis'),
            "pin_url": request.POST.get('pin_url') if 'http' in request.POST.get('pin_url') else 'http://%s' % request.POST.get('pin_url'),
            "goo_vis": request.POST.get('goo_vis'),
            "goo_url": request.POST.get('goo_url') if 'http' in request.POST.get('goo_url') else 'http://%s' % request.POST.get('goo_url')
        }
        with open('%s/%s_social_icons.json' % (settings.API_EX_PATH, request.current_site.domain), 'w') as f:
            json.dump(data, f)
        return HttpResponseRedirect(reverse('set_social_icons'))
                
    with open('%s/%s_social_icons.json' % (settings.API_EX_PATH, current_site.domain), 'r') as f:
        data = json.loads(f.read())

    return render_to_response('vladaalfimov/social_icons.html', {'current_site': current_site, 'site_name': site_name, 'title': title, 'data': data}, context_instance=RequestContext(request))
    
    
