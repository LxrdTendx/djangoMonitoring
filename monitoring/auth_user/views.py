import pandas as pd
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
import psycopg2
from .models import Floor, Sensor



@login_required
def download_data(request):
    # Получение параметров из запроса
    file_format = request.GET.get('format', 'csv')
    date_range = request.GET.get('range', 'day')

    # Загрузка данных для пользователя
    sensors_data = load_sensor_data_for_user(request.user, date_range)

    # Создание Excel или CSV на основе выбранного формата
    if file_format == 'xlsx':
        # Используем ExcelWriter для записи в разные листы
        with pd.ExcelWriter('sensors_data.xlsx') as writer:
            for sheet_name, data in sensors_data.items():
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        with open('sensors_data.xlsx', 'rb') as excel:
            response = HttpResponse(excel.read(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="sensors_data.xlsx"'
        return response
    else:
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = 'attachment; filename="sensors_data.csv"'
        # Для CSV выбираем первый набор данных (или другую логику)
        first_sheet_name = next(iter(sensors_data))
        df = pd.DataFrame(sensors_data[first_sheet_name])
        df.to_csv(response, index=False, encoding='utf-8-sig')  # Кодировка
        return response



def load_sensor_data_for_user(user, date_range):
    # Определите временной диапазон
    now = timezone.now()
    if date_range == 'day':
        start_date = now - timedelta(days=1)
    elif date_range == 'month':
        start_date = now - timedelta(days=30)
    else:  # 'year'
        start_date = now - timedelta(days=365)

    # Получите все этажи пользователя
    floors = Floor.objects.filter(users=user).order_by('floor_number')

    # Подготовьте словарь для данных
    sensors_data = {}

    # Используйте вашу конфигурацию для подключения к БД
    conn = psycopg2.connect(
        user='test',
        password='sownh12345',
        host='45.12.74.4',
        port='5432',
        database='postgres'
    )
    cur = conn.cursor()



    # Извлеките данные для каждого датчика
    for floor in floors:
        for sensor in floor.sensors.all():

            # Название листа (также используется как имя файла)
            sheet_name = f"Этаж_{floor.floor_number}-{sensor.name}"
            table_name = user.username  # Имя пользователя как имя таблиц
            # Выполните запрос и сохраните результаты
            params = (sensor.name, start_date.strftime('%Y-%m-%d'))

            # Используйте их в запросе
            cur.execute("""
                SELECT date_of_take, time_of_take, temper, co2, wet 
                FROM brb 
                WHERE sensor_name = %s AND date_of_take >= %s
                ORDER BY date_of_take DESC, time_of_take DESC
            """, params)

            rows = cur.fetchall()


            # Компонуйте данные в словарь
            sensor_data_list = [{
                'Дата': row[0],
                'Время': row[1],
                'Температура': row[2],
                'CO2': row[3],
                'Влажность': row[4]
            } for row in rows]

            # Добавьте данные в словарь для данного листа
            sensors_data[sheet_name] = sensor_data_list

    conn.close()
    return sensors_data






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

    # Получаем тип датчика
    cur.execute(f"SELECT sensor_type FROM {table_name} WHERE sensor_name = %s ORDER BY date_of_take DESC, time_of_take DESC LIMIT 1", (sensor_name,))
    sensor_type_result = cur.fetchone()
    sensor_type = sensor_type_result[0] if sensor_type_result else None

    # Формируем запрос в зависимости от типа датчика
    if sensor_type == 'wet':
        query = f"SELECT * FROM {table_name} WHERE sensor_name = %s ORDER BY date_of_take DESC, time_of_take DESC LIMIT 50"
    else:  # Для mult или других типов
        query = f"SELECT * FROM {table_name} WHERE sensor_name = %s AND temper != 0 AND co2 != 0 AND wet != 0 ORDER BY date_of_take DESC, time_of_take DESC LIMIT 25"

    cur.execute(query, (sensor_name,))
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

@login_required
def monitoring_view(request):
    floors = Floor.objects.filter(users=request.user).order_by('floor_number').prefetch_related('sensors')
    return render(request, 'many_monitoring.html', {'floors': floors})

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

    # Получите изображения и номера этажей из базы данных
    floors = Floor.objects.filter(users=request.user).order_by('floor_number')
    floor_numbers = [floor.floor_number for floor in floors]
    sensors = Sensor.objects.filter(floor__in=floors)

    return render(request, 'profile.html', {
        'user': request.user,
        'floors': floors,
        'floor_numbers': floor_numbers,
        'sensors': sensors,
    })

def get_floors_and_sensors(request):
    floors = Floor.objects.filter(users=request.user).prefetch_related('sensors')
    response_data = {}

    for floor in floors:
        sensors_data = [{"name": sensor.name, "type": sensor.sensor_type} for sensor in floor.sensors.all()]
        response_data[f"Этаж {floor.floor_number}"] = sensors_data

    return JsonResponse(response_data)

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




