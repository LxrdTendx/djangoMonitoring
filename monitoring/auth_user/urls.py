from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('get_sensor_data/<str:sensor_name>', views.get_sensor_data, name='get_sensor_data'),
    path('get_sensor_data_history/<str:sensor_name>', views.get_sensor_data_history, name='get_sensor_history_data'),
]
