# -*- coding: utf-8 -*-
# Django settings for project project.
import os
import logging.config

# DEBUG = True
import environ

DEBUG = True

env = environ.Env()
env.read_env('.env')

ALLOWED_HOSTS = ['*']

# TEMPLATE_DEBUG = DEBUG

def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)


def mk_dir(list):
    for i in list:
        try:
            os.makedirs(i)
        except OSError:
            pass


ADMINS = (
    # ('Yuriy', 'twohothearts@gmail.com'),
)
# mysqldump --host=chromium.locum.ru -u kinoinfodb -p asteroiDd_cherr98 > kinoinfodb.sql
MANAGERS = ADMINS
#
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

    'story': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'asteroid_story',
        'USER': 'kinoinfo',
        'PASSWORD': env('PASSWORD_DB_AWS'),
        'HOST': env('HOST_DB_AWS'),
        'PORT': '',
    }
}

TIME_ZONE = 'Europe/Moscow'

LANGUAGE_CODE = 'ru'

LANGUAGES = (
    ('ru', ('Russian')),
    ('uk', ('Ukrainian')),
)

LOCALE_PATHS = (
    os.path.join(os.path.dirname(__file__), 'locale'),
)

SITE_ID = 1

USE_I18N = True

USE_L10N = True

MEDIA_ROOT = rel('upload/')

MEDIA_URL = '/upload/'

STATIC_ROOT = rel('static/')

STATIC_URL = '/static/'

GEOIP_PATH = rel('user_registration/geoip/')

PATTERN_ROOT = rel('files', 'template')

PATTERN_URL = '/templates/'

ADMIN_MEDIA_PREFIX = '/static/admin/'

STATICFILES_DIRS = (
    # '/public/kinoinfo.ru/static/'
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    'dajaxice.finders.DajaxiceFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = env('SECRET_KEY')

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.CacheMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django_openid_consumer.middleware.OpenIDMiddleware',
    'base.middleware.SubdomainMiddleware',
)

ROOT_URLCONF = 'urls'
# ROOT_URLCONF = 'kinoinfo.urls'

TEMPLATE_DIRS = (
    rel('base', 'templates'),
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': rel('templates'),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',
    'linkexchange_django.context_processors.linkexchange',
    # 'base.context_processors.base_processor',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 'django.contrib.admindocs',
    # 'django_extensions',
    'base',
    'api',
    'kinoinfo_folder',
    'kinoafisha',
    'slideblok',
    'dajaxice',
    'registration',
    'django_openid_consumer',
    'user_registration',
    'release_parser',
    'linkexchange_django',
    'articles',
    'tinymce',
    'movie_online',
    'feedback',
    'umrunet',
    'googlecharts',
    'kinoafisha_ua',
    'organizations',
    'vsetiinter_net',
    'film',
    'news',
    'person',
    'letsgetrhythm',
    'vladaalfimov',
    'imiagroup',
    'forums',
    'music',
    'linkanoid',
    'pmprepare',
    'storages'
)

API_EX_PATH = rel('api/examples')

API_STEP = 500
API_GUEST_LIMIT = 10
API_CLIENT_LIMIT = 500

API_DUMP_PATH = rel('%s/dump' % API_EX_PATH)
API_CLIENTS_PATH = rel('api/clients')

KINOBILETY_PATH = '%s/kinobilety' % API_EX_PATH

ADV_REPORTS = '%s/adv_reports' % API_EX_PATH

NOF_DUMP_PATH = '%s/nof' % API_DUMP_PATH
LOG_DUMP_PATH = '%s/log' % API_DUMP_PATH

ORGANIZATIONS_FOLDER = '/organizations'
NEWS_FOLDER = '/news'
GALLERY_FOLDER = '/gallery'

try:
    os.makedirs(rel('api/examples/dump'))
except OSError:
    pass

AVATARS = MEDIA_ROOT + '/avatars'
AVATAR_FOLDER = MEDIA_ROOT + '/profiles'
INVOICES_TMP = MEDIA_ROOT + '/invoices_pdf_tmp'
BACKGROUND_PATH = MEDIA_ROOT + '/bg'
CRON_LOG_PATH = API_EX_PATH + '/cron_log'
SUCCESS_LOG_PATH = API_EX_PATH + '/success'
POSTERS_UA_PATH = MEDIA_ROOT + '/films/posters/uk'
POSTERS_EN_PATH = MEDIA_ROOT + '/films/posters/en'
WF_PATH = MEDIA_ROOT + '/forums'
PERSONS_IMGS = MEDIA_ROOT + '/persons'
MUSIC_PLAYER = MEDIA_ROOT + '/player'
BUTTONS = MEDIA_ROOT + '/btn'
ADV = MEDIA_ROOT + '/adv'
PROFILE_BG = MEDIA_ROOT + '/profiles_bg'
TORRENT_PATH = MEDIA_ROOT + '/torrent'
BOOKING_EXCEL_PATH = MEDIA_ROOT + '/booking_excel'

ORGANIZATIONS_PATH = MEDIA_ROOT + ORGANIZATIONS_FOLDER
NEWS_PATH = MEDIA_ROOT + NEWS_FOLDER
GALLERY_PATH = MEDIA_ROOT + GALLERY_FOLDER
SEO_PATH = API_EX_PATH + '/SEO'

mk_dir([
    AVATARS,
    AVATAR_FOLDER,
    INVOICES_TMP,
    BACKGROUND_PATH,
    CRON_LOG_PATH,
    SUCCESS_LOG_PATH,
    POSTERS_UA_PATH,
    POSTERS_EN_PATH,
    ORGANIZATIONS_PATH,
    NEWS_PATH,
    GALLERY_PATH,
    WF_PATH,
    PERSONS_IMGS,
    MUSIC_PLAYER,
    BUTTONS,
    ADV,
    PROFILE_BG,
    SEO_PATH,
    KINOBILETY_PATH,
    ADV_REPORTS,
    TORRENT_PATH,
    BOOKING_EXCEL_PATH,
])

API_DUMPS_LIST = (
    'cinema', 'persons', 'city_dir', 'genre_dir', 'hall', 'hall_dir', 'film1990',
    'metro_dir', 'sources', 'film_posters', 'film_trailers', 'film1990_1999',
    'film2000_2009', 'film2010_2011', 'film2012', 'film2013', 'film2014', 'schedule',
    'imovie', 'screens', 'movie_reviews', 'imdb_rate', 'country_dir',
    'films_name', 'theater', 'releases_ua', 'screens_v2', 'schedule_v2',
    'film_v3_1990',
    'film_v3_1990_1999', 'film_v3_2000_2009', 'film_v3_2010_2011', 'film_v3_2012', 'film_v3_2013', 'film_v3_2014',
    'film_v4_1990',
    'film_v4_1990_1999', 'film_v4_2000_2009', 'film_v4_2010_2011', 'film_v4_2012', 'film_v4_2013', 'film_v4_2014',
)
PARSER_DUMPS_LIST = (
    'kinometro_ru', 'film_ru', 'film_releases', 'cmc_schedules', 'cmc_kid_schedules', 'cmc_good_films',
)

CLICKATELL_USER = env('CLICKATELL_USER')
CLICKATELL_PSWD = env('CLICKATELL_PSWD')
CLICKATELL_API_ID = '3506413'

# http://api.clickatell.com/http/sendmsg?user=kinoinfo&password=[PASSWORD]&api_id=3506413&to=79180642091&text=Message


# цены по форматам
PRICES = {
    0: 41,  # отключение фона
    1: 42,  # рекламный блок текстовый (весь сайт)
    2: 43,  # фон (весь сайт)
    3: 44,  # фон (страница юзера)
    4: 45,  # рекламный блок (страница юзера)
    5: 46,  # рекламный блок swf объект (весь сайт)
    6: 47,  # рекламный блок текст (моб.версия сайта)
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'base.profile'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_tbl',  # rel('cache'),
        'OPTIONS': {
            'MAX_ENTRIES': 50000
        }
    }
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'logfile': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': rel('LOGGING.TXT')
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'kinoinfo'
AWS_S3_HOST = 's3.eu-central-1.amazonaws.com'
# logging.config.fileConfig(
#    rel('sape/logging.cfg'),
#    {'basedir': rel('sape/')}
# )

# _db_settings = DATABASES

try:
    from local_settings import *
except ImportError:
    pass

# DATABASES['afisha'] = _db_settings['afisha']