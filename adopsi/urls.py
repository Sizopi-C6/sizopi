from django.urls import path
from .views import program_adopsi_admin, form_adopsi_hewan, program_adopsi_pengunjung, daftar_adopter, riwayat_adopter

app_name = 'adopsi'
urlpatterns = [
    path('admin/', program_adopsi_admin, name='adopsi_admin'),
    path('admin/form_adopsi_hewan', form_adopsi_hewan, name='form_adopsi_hewan'),
    path('', program_adopsi_pengunjung, name='adopsi_pengunjung'),
    path('admin/daftar-adopter/', daftar_adopter, name='daftar_adopter'),
    path('admin/riwayat-adopter/<int:adopter_id>/', riwayat_adopter, name='riwayat_adopter'),
]