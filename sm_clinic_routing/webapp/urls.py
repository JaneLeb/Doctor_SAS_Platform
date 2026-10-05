"""URL-маршруты приложения webapp."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.process, name="process"),
    path("doctor/<str:card_id>/", views.doctor_view, name="doctor"),
    path("patient/<str:card_id>/", views.patient_view, name="patient"),
    path("dashboard/", views.dashboard, name="dashboard"),
]