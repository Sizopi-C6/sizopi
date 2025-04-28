from django.urls import path
from .views import program_adopsi_admin, program_adopsi_pengunjung, daftar_adopter, riwayat_adopter

app_name = 'adopsi'
urlpatterns = [
    path('admin/', program_adopsi_admin, name='adopsi_admin'),
    path('', program_adopsi_pengunjung, name='adopsi_pengunjung'),
    path('admin/daftar-adopter/', daftar_adopter, name='daftar_adopter'),
    path('admin/riwayat-adopter/<int:adopter_id>/', riwayat_adopter, name='riwayat_adopter'),
]