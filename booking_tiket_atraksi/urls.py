from django.urls import path
from . import views  

urlpatterns = [
    path('pengunjung/booking/', views.pengunjung_data_booking, name='pengunjung_data_booking'), 
    path('pengunjung/', views.pengunjung_data_reservasi, name='pengunjung_data_reservasi'), 
    path('pengunjung/edit/<uuid:reservasi_id>/', views.pengunjung_edit_reservasi, name='pengunjung_edit_reservasi'),
    path('pengunjung/form/<uuid:reservasi_id>/', views.pengunjung_form_reservasi, name='pengunjung_form_reservasi'),
    path('pengunjung/detail/<uuid:reservasi_id>/', views.pengunjung_detail_reservasi, name='pengunjung_detail_reservasi'),

    path('staf/atraksi/', views.staf_data_atraksi, name='staf_data_atraksi'),
    path('staf/wahana/', views.staf_data_wahana, name='staf_data_wahana'),
    path('staf/edit/<uuid:reservasi_id>/', views.staf_edit_reservasi, name='staf_edit_reservasi'),
]
