from django.urls import path
from . import views

urlpatterns = [
    path('daftar-hewan/', views.daftar_hewan, name='daftar_hewan'),
    path('rekam-medis-hewan/<uuid:animal_id>/', views.rekam_medis_hewan, name='rekam_medis_hewan'),
    path('jadwal-pemeriksaan/<uuid:animal_id>/', views.penjadwalan_pemeriksaan_kesehatan, name='penjadwalan_pemeriksaan_kesehatan'),
    path('pemberian-pakan/<uuid:animal_id>/', views.pemberian_pakan, name='pemberian_pakan'),
]