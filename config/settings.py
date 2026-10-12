"""
Django settings for The Shape of Work.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Vercel sets VERCEL=1 and Render sets RENDER=true. The live site is read-only:
# content is edited locally in the admin panel, then db.sqlite3 and media/ are
# committed and pushed.
IS_VERCEL = os.environ.get("VERCEL") == "1"
IS_RENDER = os.environ.get("RENDER") == "true"
IS_LIVE = IS_VERCEL or IS_RENDER

if IS_LIVE:
    # Set DJANGO_SECRET_KEY in the host's environment variables (render.yaml
    # generates one on Render).
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    # Local development only; the live site uses its own key.
    SECRET_KEY = "django-insecure-!r@%+r$o0a*j6=cd1d&#n%ws8x1gqf*8xt61ly73lld&+t+2-v"

DEBUG = not IS_LIVE

ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".vercel.app", ".onrender.com"]


# Applications

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Our apps
    "core",
    "dashboard",
    "datahub",
    "adminpanel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves the static files (CSS, charts, video) on Render
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.dashboard_nav",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Language and time

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Manila"
USE_I18N = True
USE_TZ = True


# Static files (CSS, images) and uploaded files

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # filled by collectstatic on Render

if IS_RENDER:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
    }

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Sign-in for the admin panel

LOGIN_URL = "adminpanel:login"
LOGIN_REDIRECT_URL = "adminpanel:home"
LOGOUT_REDIRECT_URL = "core:home"


# Project settings

# Folder that holds the DAX Studio export (data/raw), the cleaned CSVs (data/clean)
# and the province map file (data/geo).
DATA_DIR = BASE_DIR / "data"

# Your Power BI "Publish to web" link (the whole report).
POWERBI_REPORT_URL = (
    "https://app.powerbi.com/view?r=eyJrIjoiMTYzNDhiMDItZTAwNi00NDk3LTk3NjQtOWZmZTAwOTkwYjQwIiwidCI6IjYzODljNWQ0LTlhNGYtNDJhZC1iMzg4LTA1ODQ5MmM2OTdiZiIsImMiOjEwfQ%3D%3D"
)
