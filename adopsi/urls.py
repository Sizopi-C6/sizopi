from django.urls import path
from .views import program_adopsi_admin, form_adopsi_hewan, program_adopsi_pengunjung, sertifikat_adopsi, laporan_kondisi_hewan, perpanjang_periode, daftar_adopter, riwayat_adopter

app_name = 'adopsi'
urlpatterns = [
    path('admin/', program_adopsi_admin, name='adopsi_admin'),
    path('admin/form-adopsi-hewan', form_adopsi_hewan, name='form_adopsi_hewan'),
    path('', program_adopsi_pengunjung, name='adopsi_pengunjung'),
    path('sertifikat_adopsi/', sertifikat_adopsi, name='sertifikat_adopsi'),
    path('laporan-kondisi-hewan/', laporan_kondisi_hewan, name='laporan_kondisi_hewan'),
    path('perpanjang-periode/', perpanjang_periode, name='perpanjang_periode'),
    path('admin/daftar-adopter/', daftar_adopter, name='daftar_adopter'),
    path('admin/riwayat-adopter/<int:adopter_id>/', riwayat_adopter, name='riwayat_adopter'),
]