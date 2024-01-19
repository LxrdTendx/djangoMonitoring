from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import User
from django.db import models

class User(AbstractUser):
    pass


class Floor(models.Model):
    image = models.ImageField(upload_to='floors/')
    floor_number = models.PositiveIntegerField()
    users = models.ManyToManyField(User, related_name='floors')

    def __str__(self):
        return f"Этаж {self.floor_number}"

class Sensor(models.Model):
    SENSOR_TYPES = [
        ('mult', 'mult'),
        ('wet', 'wet'),
        # Добавьте другие типы датчиков по необходимости
    ]

    name = models.CharField(max_length=100)
    sensor_type = models.CharField(max_length=10, choices=SENSOR_TYPES)
    x_coordinate = models.PositiveIntegerField()
    y_coordinate = models.PositiveIntegerField()
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='sensors')

    def __str__(self):
        return self.name