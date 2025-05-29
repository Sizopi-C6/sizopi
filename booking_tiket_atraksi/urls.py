from django.urls import path
from . import views  

urlpatterns = [
    path('form/', views.pengunjung_reservasi_tiket, name='pengunjung_reservasi_tiket'), 
    path('pengunjung-detail/', views.pengunjung_detail_reservasi, name='pengunjung_detail_reservasi'),
    path('pengunjung-edit/<str:nama_atraksi>/', views.pengunjung_edit_reservasi, name='pengunjung_edit_reservasi'),
    path('staf-data/', views.staf_data_reservasi, name='staf_data_reservasi'),
    path('staf-edit/<str:username>/<str:nama_atraksi>/', views.staf_edit_reservasi, name='staf_edit_reservasi'),
]
