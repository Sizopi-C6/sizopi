from django.urls import path
from . import views

urlpatterns = [
    path('rekam-medis-hewan/', views.rekam_medis_hewan, name='rekam_medis_hewan'),
]