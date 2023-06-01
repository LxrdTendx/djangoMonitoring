from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import os
from django.conf import settings
import re
from django.shortcuts import render, redirect


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
def profile_view(request):
    user_images_dir = os.path.join(settings.STATIC_ROOT, request.user.username)
    floor_images = {}
    sensors_data = {}

    if os.path.exists(user_images_dir):
        image_files = [f for f in os.listdir(user_images_dir) if f.endswith('.png')]
        floor_images = {f.split()[-1].split('.')[0]: f for f in image_files}

        # Load sensors data
        json_file_path = os.path.join(user_images_dir, 'sensors.json')
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as json_file:
                sensors_data = json.load(json_file)

    return render(request, 'auth_user/profile.html', {
        'floor_images': floor_images,
        'sensors_data': sensors_data,
    })



def logout_view(request):
    logout(request)
    return redirect('login')  # Перенаправление на страницу входа после выхода


def add_sensor(request):
    if request.method == 'POST':
        form = SensorForm(request.POST)
        if form.is_valid():
            new_sensor = form.save(commit=False)
            new_sensor.user = request.user
            new_sensor.save()
            return redirect('profile')
    else:
        form = SensorForm()

    return render(request, 'auth_user/add_sensor.html', {'form': form})

