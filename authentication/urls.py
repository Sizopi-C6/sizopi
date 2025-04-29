from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('login/', views.login_page, name='login'),
    path('register-pilih/', views.register_pilih, name='register_pilih'),
    path('register-pengunjung/', views.register_pengunjung, name='register_pengunjung'),
    path('register-dokter-hewan/', views.register_dokter_hewan, name='register_dokter_hewan'),
    path('register-staff/', views.register_staff, name='register_staff'),
    path('logout/', views.logout_view, name='logout'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),  # Fixed typo
    path('ubah-password/', views.password_change_view, name='ubah_password'),  # Changed to custom view
]