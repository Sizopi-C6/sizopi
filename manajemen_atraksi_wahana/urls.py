from django.urls import path
from . import views

urlpatterns = [
    path('manajemen-atraksi/', views.data_atraksi, name='data_atraksi'),
    path('manajemen-atraksi/tambah/', views.tambah_atraksi, name='tambah_atraksi'),
    path('manajemen-atraksi/edit/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('manajemen-wahana/', views.data_wahana, name='data_wahana'),
    path('manajemen-wahana/tambah/', views.tambah_wahana, name='tambah_wahana'),  
    path('manajemen-wahana/edit/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
]
