"""
Django settings for freyr_app project.
"""

import os
from pathlib import Path
import configparser

# BASE_DIR
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# PATHS
TENSORS_PATH = os.path.join(BASE_DIR, 'tensors')
CLUSTERS_PATH = os.path.join(TENSORS_PATH, 'clusters')
AUDIO_PATH = os.path.join(BASE_DIR, 'audio_cache')

# ML MODELS
ML_MODELS = os.path.join(BASE_DIR, 'ml_models')
KALDI = os.path.join(ML_MODELS, 'kaldi')

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static_files')

# CONFIG.INI
config = configparser.ConfigParser()
CONFIG_INI_PATH = os.path.join(BASE_DIR, 'config.ini')
config.read(CONFIG_INI_PATH)

# ML Batch Size
BATCH_SIZE = int(config['ML']['BATCH_SIZE'])

# SECURITY
SECRET_KEY = config['DJANGO']['SECRET_KEY']
DEBUG = True
ALLOWED_HOSTS = ['*']
# https://stackoverflow.com/a/56190379
# if "celery" in sys.argv[0]:
#     DEBUG = False

# Application definition

INSTALLED_APPS = [
    'bootstrap4',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'django_extensions',
    'import_export',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'freyr_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.joinpath('core/templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'freyr_app.wsgi.application'

# Database
if 'POSTGRES' in config:
    DATABASES = {
        'default': {
            'ENGINE': config['POSTGRES']['ENGINE'],
            'NAME': config['POSTGRES']['NAME'],
            'USER': config['POSTGRES']['USER'],
            'PASSWORD': config['POSTGRES']['PASSWORD'],
            'HOST': config['POSTGRES']['HOST'],
            'PORT': config['POSTGRES']['PORT'],
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# LOGGING
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s'
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file',
            'filename': 'debug.log',
            'maxBytes': 20*1024*1024,
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
}