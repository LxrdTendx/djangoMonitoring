from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import os
from django.conf import settings
import re
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import psycopg2


@login_required
def get_sensor_data(request, sensor_name, username):
    conn = psycopg2.connect(
        user='test',
        password='sownh12345',
        host='45.12.74.4',
        port='5432',
        database='postgres'
    )
    table_name = username
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} WHERE sensor_name = %s ORDER BY date_of_take DESC, time_of_take DESC LIMIT 1", (sensor_name,))
    result = cur.fetchone()

    if result:
        # Assumes that the result is a list with each element corresponding to a part of the sensor string
        sensor_data = {
            'id': result[0],
            'name': result[1],
            'type': result[2],
            'temperature': result[3],
            'co2': result[4],
            'humidity': result[5],
            'time': result[6],
            'date': result[7],
        }
    else:
        sensor_data = {
            'id': None,
            'name': None,
            'type': None,
            'temperature': None,
            'co2': None,
            'humidity': None,
            'date': None,
            'time': None,
        }


    return JsonResponse(sensor_data)


def get_sensor_data_history(request, sensor_name, username):
    """
    Get the last 100 sensor data for a specific sensor.
    """
    table_name = username
    conn = psycopg2.connect(
        user='test',
        password='sownh12345',
        host='45.12.74.4',
        port='5432',
        database='postgres'
    )

    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name} WHERE sensor_name = %s AND temper != 0 AND co2 != 0 AND wet != 0 ORDER BY date_of_take DESC, time_of_take DESC LIMIT 10000", (sensor_name,))
    rows = cur.fetchall()

    data = []
    for row in rows:
        data.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'temperature': row[3],
            'co2': row[4],
            'humidity': row[5],
            'time': row[6],
            'date': row[7],

        })

    conn.close()
    data.reverse()

    return JsonResponse(data, safe=False)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('profile')
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

@login_required
def profile(request):
    username = request.user.username
    user_dir = os.path.join('auth_user/templates', username)

    if os.path.isdir(user_dir):
        image_files = [f for f in os.listdir(user_dir) if f.endswith('.png')]
        floor_numbers = [re.search(r'(\d+)\.png$', f).group(1) for f in image_files]

    else:
        image_files = []
        floor_numbers = []

    return render(request, 'profile.html', {
        'user': request.user,
        'image_files': image_files,
        'floor_numbers': floor_numbers,
    })

@login_required
@login_required
def profile_view(request):
    user_images_dir = os.path.join(settings.STATIC_ROOT, request.user.username)
    floor_images = {}
    sensors_data = {}
    sensor_names = ['temperature', 'co2', 'humidity']

    if os.path.exists(user_images_dir):
        image_files = [f for f in os.listdir(user_images_dir) if f.endswith('.png')]
        floor_images = {f.split()[-1].split('.')[0]: f for f in image_files}

        # Load sensors data
        for sensor in sensor_names:
            sensors_data[sensor] = get_sensor_data(request, sensor)

    return render(request, 'auth_user/profile.html', {
        'floor_images': floor_images,
        'sensors_data': sensors_data,
    })


def logout_view(request):
    logout(request)
    return redirect('login')  # Перенаправление на страницу входа после выхода



