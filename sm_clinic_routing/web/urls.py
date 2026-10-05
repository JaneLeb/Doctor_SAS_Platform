"""Корневые URL веб-интерфейса ArtKnit."""
from django.urls import include, path

urlpatterns = [
    path("", include("webapp.urls")),
]