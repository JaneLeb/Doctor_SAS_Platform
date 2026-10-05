"""
Django settings для веб-обёртки ArtKnit.

Веб-интерфейс переиспользует ядро маршрутизации из src/
и генерирует HTML-экраны через существующие Jinja2-шаблоны.
"""

from pathlib import Path

# Корень проекта sm_clinic_routing/ (где лежат manage.py, src/, config/)
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-artknit-local-dev-only-key"

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Минимальный набор приложений — БД и модели не требуются,
# маршруты сохраняются в output/routes_audit.jsonl как и в CLI.
INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "webapp",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "webapp" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "web.wsgi.application"

# SQLite нужен только для служебных нужд Django; приложение моделей не использует.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# Шаблоны используют встроенные стили; статические файлы не требуются.
STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"