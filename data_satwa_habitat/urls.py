from django.urls import path
from data_satwa_habitat.views import *

app_name = 'data_satwa_habitat'

urlpatterns = [
    path('tambah-satwa/', tambah_satwa, name='tambah_satwa'),
    path('list-satwa/', show_list_satwa, name='show_list_satwa'),
    path('edit-satwa/<uuid:id>/', edit_satwa, name='edit_satwa'),
    path('delete-satwa/<uuid:id>/', delete_satwa, name='delete_satwa'),

    path('habitat/', list_habitat, name='list_habitat'),
    path('tambah-habitat/', tambah_habitat, name='tambah_habitat'),
    path('edit-habitat/<str:habitat_nama>/', edit_habitat, name='edit_habitat'),
    path('habitat/<str:habitat_nama>/', detail_habitat, name='detail_habitat'),
    path('delete-habitat/<str:habitat_nama>/', delete_habitat, name='delete_habitat'),
]