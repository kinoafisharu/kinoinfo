#-*- coding: utf-8 -*-
# Django settings for kinoinfo project.

from settings import *

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Moscow'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'ru'

LANGUAGES = (
    ('ru', u'Русский'),
    ('en', u'English'),
    ('zh-cn', u'简体中文'),
)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"

MEDIA_ROOT = '/public/kinoinfo.ru/upload'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/upload/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/public/kinoinfo.ru/static'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

PATTERN_ROOT = rel('files','template')

PATTERN_URL = '/templates/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
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

ROOT_URLCONF = 'urls'

MAILRU_ID = env('KINOINFO_MAILRU_ID')
MAILRU_PRIVATE_KEY = env('KINOINFO_MAILRU_PRIVATE_KEY')
MAILRU_SECRET_KEY = env('KINOINFO_MAILRU_SECRET_KEY')
MAILRU_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/mailru/'
#MAILRU_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/mailru/'

TWITTER_ID = env('KINOINFO_TWITTER_ID') # Consumer key
TWITTER_SECRET_KEY = env('KINOINFO_TWITTER_SECRET_KEY') # Consumer secret
TWITTER_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/twitter/'
#TWITTER_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/twitter/'

GOOGLE_ID = env('KINOINFO_GOOGLE_ID')
GOOGLE_SECRET_KEY = env('KINOINFO_GOOGLE_SECRET_KEY')
GOOGLE_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/google/'
#GOOGLE_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/google/'

FACEBOOK_ID = env('KINOINFO_FACEBOOK_ID')
FACEBOOK_SECRET_KEY = env('KINOINFO_FACEBOOK_SECRET_KEY')
FACEBOOK_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/facebook/'
#FACEBOOK_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/facebook/'

VK_ID = env('KINOINFO_VK_ID')
VK_SECRET_KEY = env('KINOINFO_VK_SECRET_KEY')
VK_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/vkontakte/'
#VK_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/vkontakte/'

YANDEX_ID = env('KINOINFO_YANDEX_ID')
YANDEX_SECRET_KEY = env('KINOINFO_YANDEX_SECRET_KEY')
YANDEX_REDIRECT_URI = 'http://kinoinfo.ru/user/login/oauth/yandex/'
#YANDEX_REDIRECT_URI = 'http://127.0.0.1:8000/user/login/oauth/yandex/'

OPENID_SREG = {"requred": "nickname, email, fullname, dob, gender",}

YANDEX_OPENID_URL = 'http://openid.yandex.ru/'
#MYOPENID_OPENID_URL = 'http://myopenid.com/'

KINOHOD_APIKEY_CLIENT = env('KINOINFO_KINOHOD_APIKEY_CLIENT')

RAMBLER_TICKET_KEY = env('KINOINFO_RAMBLER_TICKET_KEY')

LINKEXCHANGE_CONFIG = rel('sape/linkexchange.cfg')

SESSION_COOKIE_AGE = 7776000
SESSION_COOKIE_DOMAIN = '.kinoinfo.ru'

EMAIL_HOST = 'mail.kinoinfo.ru'
EMAIL_PORT = 25
EMAIL_HOST_USER = 'info@kinoinfo.ru'
EMAIL_HOST_PASSWORD = env('KINOINFO_EMAIL_HOST_PASSWORD')
#EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'info@kinoinfo.ru'
SERVER_EMAIL = 'info@kinoinfo.ru'

OPENID_TRUST_ROOT = 'http://kinoinfo.ru/'
OPENID_REDIRECT_TO = 'http://kinoinfo.ru/user/login/openid/complete/'






