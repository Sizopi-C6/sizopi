from django.urls import path
from . import views

urlpatterns = [
    path('data-atraksi/', views.data_atraksi, name='data_atraksi'),
    path('tambah-atraksi/', views.tambah_atraksi, name='tambah_atraksi'),
    path('edit-atraksi/<str:nama_atraksi>/', views.edit_atraksi, name='edit_atraksi'),
    path('data-wahana/', views.data_wahana, name='data_wahana'),
    path('tambah-wahana/', views.tambah_wahana, name='tambah_wahana'),  
    path('edit-wahana/<str:nama_wahana>/', views.edit_wahana, name='edit_wahana'),
]
