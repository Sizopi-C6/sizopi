from django.urls import path
from . import views  

urlpatterns = [
    path('pengunjung/tambah-reservasi/', views.reservasi_tiket, name='reservasi_tiket'), 
    path('pengunjung/detail-reservasi/', views.detail_reservasi, name='detail_reservasi'),
    path('pengunjung/edit-reservasi/<str:nama_atraksi>/', views.pengunjung_edit_reservasi, name='pengunjung_edit_reservasi'),
    path('admin/daftar-reservasi/', views.daftar_reservasi, name='daftar_reservasi'),
    path('admin/edit-reservasi/<str:username>/<str:nama_atraksi>/<str:tanggal>/', views.staf_edit_reservasi, name='edit_reservasi'),
]
