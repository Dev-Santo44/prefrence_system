"""
Django settings for preference_site project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "fallback-dev-secret-key-change-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# ── Installed Apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "preference_app",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "preference_site.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "preference_site.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE":   os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME":     os.getenv("DB_NAME", "postgres"),
        "USER":     os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST":     os.getenv("DB_HOST", "localhost"),
        "PORT":     os.getenv("DB_PORT", "5432"),
    }
}

# ── Authentication ────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "preference_app.User"

LOGIN_URL          = "/"
LOGIN_REDIRECT_URL = "/survey/"
LOGOUT_REDIRECT_URL = "/"

# ── Password validators ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 6}},
]

# ── Internationalization ──────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

# ── Static & Media Files ─────────────────────────────────────────────────────
STATIC_URL  = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media (Default to Local, but Google Cloud Storage if configured)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Google Cloud Storage Configuration
GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")
GS_PROJECT_ID = os.getenv("GS_PROJECT_ID")
GS_CREDENTIALS_JSON = os.getenv("GS_CREDENTIALS_JSON")

if all([GS_BUCKET_NAME, GS_PROJECT_ID, GS_CREDENTIALS_JSON]):
    try:
        import json
        from google.oauth2 import service_account

        cred_dict = json.loads(GS_CREDENTIALS_JSON.strip("'"))
        GS_CREDENTIALS = service_account.Credentials.from_service_account_info(cred_dict)

        GS_DEFAULT_ACL = None # Required for Uniform Bucket-Level Access
        GS_QUERYSTRING_AUTH = False
        
        STORAGES = {
            "default": {
                "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
                "OPTIONS": {
                    "bucket_name": GS_BUCKET_NAME,
                    "project_id": GS_PROJECT_ID,
                    "credentials": GS_CREDENTIALS,
                    "default_acl": None,
                    "querystring_auth": False,
                },
            },
            "staticfiles": {
                "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
            },
        }
        MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/"
        print(f"✅ GCS storage active — bucket: {GS_BUCKET_NAME}")
    except Exception as e:
        print(f"⚠️  GCS credentials failed to load ({e}), falling back to local storage.")
        STORAGES = {
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
        }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Message storage ──────────────────────────────────────────────────────────
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.DEBUG:   "debug",
    messages.INFO:    "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR:   "error",
}

# MEDIA_ROOT is only used when falling back to local FileSystemStorage.
# GCS active: MEDIA_URL is already set to the GCS public URL above.
MEDIA_ROOT = BASE_DIR / "media"
