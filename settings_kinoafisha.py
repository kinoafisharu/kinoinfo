#-*- coding: utf-8 -*-
# Django settings for kinoinfo project.

from settings import *
'''
import logging.config

logging.config.fileConfig(
    rel('sape/logging.cfg'),
    {'basedir': rel('sape/')}
)
'''

DEBUG = False
#DEBUG = True
#TEMPLATE_DEBUG = DEBUG


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'kinoinfodb',
        'USER': 'kinoinfo',
        'PASSWORD': env('PASSWORD_DB_AWS'),
        'HOST': env('HOST_DB_AWS'),
        'PORT': '',
    },

    'afisha': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'asteroid_kino',
        'USER': 'kinoinfo',
        'PASSWORD': env('PASSWORD_DB_AWS'),
        'HOST': env('HOST_DB_AWS'),
        'PORT': '',
    },
}


TIME_ZONE = 'Europe/Moscow'

LANGUAGE_CODE = 'ru-RU'

SITE_ID = 5

USE_I18N = True

USE_L10N = True

MEDIA_ROOT = rel('upload/')

MEDIA_URL = '/upload/'

STATIC_ROOT = rel('static/')

STATIC_URL = '/static/'

PATTERN_ROOT = rel('files','template')

PATTERN_URL = '/templates/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

TINYMCE_DEFAULT_CONFIG = {
    'plugins': 'wordcount',
    'theme': "advanced",
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'theme_advanced_buttons1' : "bullist, link, unlink, undo, redo, formatselect, fontsizeselect, alignleft, aligncenter, alignright, alignfull, bold, italic, underline",
    'theme_advanced_toolbar_location' : "top",
    'theme_advanced_toolbar_align' : "left",
    'theme_advanced_statusbar_location' : "bottom",
    'theme_advanced_resizing' : False,
    'formats' : {
        'alignleft' : {'selector' : 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table,img', 'classes' : 'align-left'},
        'aligncenter' : {'selector' : 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table,img', 'classes' : 'align-center'},
        'alignright' : {'selector' : 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table,img', 'classes' : 'align-right'},
        'alignfull' : {'selector' : 'p,h1,h2,h3,h4,h5,h6,td,th,div,ul,ol,li,table,img', 'classes' : 'align-justify'},
        'strikethrough' : {'inline' : 'del'},
        'italic' : {'inline' : 'em'},
        'bold' : {'inline' : 'strong'},
        'underline' : {'inline' : 'u'}
    },
    'pagebreak_separator' : ""
}

TINYMCE_COMPRESSOR = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

TEMPLATE_DIRS = (
    rel('base','templates'),
)

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#   'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'dajaxice.finders.DajaxiceFinder',
)

ROOT_URLCONF = 'urls_kinoafisha'

MAILRU_ID = env('MAILRU_ID')
MAILRU_PRIVATE_KEY = env('MAILRU_PRIVATE_KEY')
MAILRU_SECRET_KEY = env('MAILRU_SECRET_KEY')
MAILRU_REDIRECT_URI = 'http://kinoafisha.ru/user/login/oauth/mailru/'
#MAILRU_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/mailru/'

TWITTER_ID = env('TWITTER_ID') # Consumer key
TWITTER_SECRET_KEY = env('TWITTER_SECRET_KEY') # Consumer secret
TWITTER_REDIRECT_URI = 'http://kinoafisha.ru/user/login/oauth/twitter/'
#TWITTER_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/twitter/'

GOOGLE_ID = env('GOOGLE_ID')
GOOGLE_SECRET_KEY = env('GOOGLE_SECRET_KEY')
GOOGLE_REDIRECT_URI = 'http://kinoafisha.ru/user/login/oauth/google/'
#GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/google/'

FACEBOOK_ID = env('FACEBOOK_ID')
FACEBOOK_SECRET_KEY = env('FACEBOOK_SECRET_KEY')
FACEBOOK_REDIRECT_URI = 'http://kinoafisha.ru/user/login/oauth/facebook/'
#FACEBOOK_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/facebook/'

VK_ID = env('VK_ID')
VK_SECRET_KEY = env('VK_SECRET_KEY')
VK_REDIRECT_URI = 'http://kinoafisha.ru/user/login/oauth/vkontakte/'
#VK_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/vkontakte/'

YANDEX_ID = env('YANDEX_ID')
YANDEX_SECRET_KEY = env('YANDEX_SECRET_KEY')
YANDEX_REDIRECT_URI = 'http://www.kinoafisha.ru/user/login/oauth/yandex/'
#YANDEX_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/yandex/'


OPENID_SREG = {"requred": "nickname, email, fullname, dob, gender",}

YANDEX_OPENID_URL = 'http://openid.yandex.ru/'
#MYOPENID_OPENID_URL = 'http://myopenid.com/'

LINKEXCHANGE_CONFIG = rel('sape/linkexchange.cfg')

SESSION_COOKIE_AGE = 31556926
SESSION_COOKIE_DOMAIN = '.kinoafisha.ru'


EMAIL_HOST = 'mail.kinoinfo.ru'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'info@kinoafisha.ru'
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
#EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'info@kinoafisha.ru'
SERVER_EMAIL = 'info@kinoafisha.ru'

OPENID_TRUST_ROOT = 'http://kinoafisha.ru/'
OPENID_REDIRECT_TO = 'http://kinoafisha.ru/user/login/openid/complete/'

KINOHOD_APIKEY_CLIENT = env('KINOHOD_APIKEY_CLIENT')

RAMBLER_TICKET_KEY = env('RAMBLER_TICKET_KEY')

KINOAFISHA_EXT = rel('kinoafisha' ,'ext')