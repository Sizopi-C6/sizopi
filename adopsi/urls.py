from django.urls import path
from . import views

app_name = 'adopsi'

urlpatterns = [
    # Admin
    path('admin/', views.program_adopsi_admin, name='adopsi_admin'),
    path('animal-detail/<str:animal_id>/', views.get_animal_adoption_detail, name='get_animal_adoption_detail'),
    path('update-status/', views.update_adoption_status, name='update_adoption_status'),
    path('terminate/', views.terminate_adoption, name='terminate_adoption'),
    
    # Form and verification
    path('form/', views.form_adopsi_hewan, name='form_adopsi_hewan'),
    path('verify-account/', views.verify_adopter_account, name='verify_adopter_account'),
    path('submit-form/', views.submit_adoption_form, name='submit_adoption_form'),
    
    # Pengunjung/Adopter
    path('', views.program_adopsi_pengunjung, name='adopsi_pengunjung'),
    path('laporan/', views.laporan_kondisi_hewan, name='laporan_kondisi_hewan'),
    path('sertifikat/', views.sertifikat_adopsi, name='sertifikat_adopsi'),
    path('perpanjang/', views.perpanjang_periode, name='perpanjang_periode'),
    path('berhenti/', views.berhenti_adopsi, name='berhenti_adopsi'),
    
    # Adopter management
    path('adopter/', views.daftar_adopter, name='daftar_adopter'),
    path('adopter/<str:adopter_id>/riwayat/', views.riwayat_adopter, name='riwayat_adopter'),
    path('adopter/delete/', views.delete_adopter, name='delete_adopter'),
    path('adopter/delete-riwayat/', views.delete_riwayat_adopsi, name='delete_riwayat_adopsi'),
]