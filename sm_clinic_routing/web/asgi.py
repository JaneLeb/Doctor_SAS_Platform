"""ASGI config для веб-обёртки ArtKnit."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")

application = get_asgi_application()