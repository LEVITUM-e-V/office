"""
Django settings for office project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from os import environ
from configurations import Configuration
from dotenv import load_dotenv

load_dotenv()


class Common(Configuration):

    BASE_DIR = Path(__file__).resolve().parent.parent
    SECRET_KEY = environ.get('SECRET_KEY', "django-insecure-bzvb1*88!5o*^e$!lha777m^cnfk8rfcr(o6&+8!)9&g5f!2#$")

    OIDC_RP_CLIENT_ID = environ['OIDC_RP_CLIENT_ID']
    OIDC_RP_CLIENT_SECRET = environ['OIDC_RP_CLIENT_SECRET']

    OIDC_OP_AUTHORIZATION_ENDPOINT = environ['OIDC_OP_AUTHORIZATION_ENDPOINT']
    OIDC_OP_TOKEN_ENDPOINT = environ['OIDC_OP_TOKEN_ENDPOINT']
    OIDC_OP_USER_ENDPOINT = environ['OIDC_OP_USER_ENDPOINT']

    OIDC_RP_SIGN_ALGO = environ['OIDC_RP_SIGN_ALGO']
    OIDC_OP_JWKS_ENDPOINT = environ['OIDC_OP_JWKS_ENDPOINT']

    LOGIN_REDIRECT_URL = "/"
    LOGOUT_REDIRECT_URL = "/"

    # Application definition

    INSTALLED_APPS = [
        "core.apps.CoreConfig",
        "django.contrib.humanize",
        "django.contrib.admin",
        "django.contrib.auth",
        'mozilla_django_oidc',
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        'mozilla_django_oidc.middleware.SessionRefresh',
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ]

    ROOT_URLCONF = "office.urls"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ]

    WSGI_APPLICATION = "office.wsgi.application"

    AUTH_USER_MODEL = 'core.User'
    LOGIN_REDIRECT_URL = '/core/'
    LOGIN_URL = '/login/'
    LOGOUT_REDIRECT_URL = '/logout/'

    # Password validation
    # https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

    AUTHENTICATION_BACKENDS = (
        'core.oidc.MyOIDCAB',
    )

    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]


    # Internationalization
    # https://docs.djangoproject.com/en/4.1/topics/i18n/

    LANGUAGE_CODE = "en-us"

    TIME_ZONE = "Europe/Berlin"

    USE_I18N = True

    USE_TZ = True


    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.1/howto/static-files/

    STATIC_URL = "static/"

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


class Dev(Common):
    DEBUG = True
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Common.BASE_DIR / "db.sqlite3",
        }
    }


class Prod(Common):
    DEBUG = str(environ.get('DEBUG', 0)) in ['1', 'True', 'true']
    STATIC_ROOT = "/app/static"
    ALLOWED_HOSTS = environ.get('ALLOWED_HOSTS', '').split(',')
    CSRF_TRUSTED_ORIGINS = environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'office',
            'USER': 'dbuser',
            'PASSWORD': 'dbpass',
            'HOST': 'db',
            'PORT': '5432',
        }
    }
