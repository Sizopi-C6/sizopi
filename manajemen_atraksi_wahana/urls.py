from django.urls import path
from . import views

urlpatterns = [
    path('atraksi/', views.data_atraksi, name='data_atraksi'),
    path('atraksi/tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('atraksi/edit/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('wahana/', views.data_wahana, name='data_wahana'),
    path('wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),  
    path('wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
]
