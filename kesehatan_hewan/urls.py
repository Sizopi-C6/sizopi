from django.urls import path
from . import views

urlpatterns = [
    path('rekam-medis-hewan/', views.rekam_medis_hewan, name='rekam_medis_hewan'),
    path('penjadwalan-pemeriksaan-kesehatan/', views.penjadwalan_pemeriksaan_kesehatan, name='penjadwalan_pemeriksaan_kesehatan'),
    path('pemberian-pakan/', views.pemberian_pakan, name='pemberian_pakan'),
]