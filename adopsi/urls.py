from django.urls import path
from .views import program_adopsi_admin

app_name = 'adopsi'
urlpatterns = [
    path('admin/', program_adopsi_admin, name='adopsi_admin'),
]
