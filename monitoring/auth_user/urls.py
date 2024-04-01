from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin

urlpatterns = [
    path('', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('get_sensor_data/<str:sensor_name>/<str:username>', views.get_sensor_data, name='get_sensor_data'),
    path('get_sensor_data_history/<str:sensor_name>/<str:username>', views.get_sensor_data_history, name='get_sensor_data_history'),
    path('get_floors_and_sensors/', views.get_floors_and_sensors, name='get_floors_and_sensors'),
    path('monitoring/', views.monitoring_view, name='monitoring'),
    path('download_data/', views.download_data, name='download_data'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
