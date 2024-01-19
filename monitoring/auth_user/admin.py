from django.contrib import admin
from .models import Floor, Sensor
from django.utils.html import format_html
from django import forms
from django.contrib import admin
from .models import User  # Импорт вашей модели пользователя

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff')  # Укажите здесь поля, которые вы хотите отображать


class SensorInline(admin.TabularInline):
    model = Sensor
    extra = 1

class FloorAdmin(admin.ModelAdmin):
    filter_horizontal = ('users',)
    inlines = [SensorInline]
    list_display = ('floor_number', 'image_preview', 'associated_users',)
    list_filter = ('users',)
    readonly_fields = ['image_preview']

    '''Метод сортировки (неудобный)'''
    # def set(self, obj):
    #     return obj.set
    # set.admin_order_field = 'set__name'
    def get_queryset(self, request):
        qs = super(FloorAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def associated_users(self, obj):
        return ", ".join([user.username for user in obj.users.all()])

    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()

    def image_preview(self, obj):
        return format_html('<img src="{}" width="80" height="50" />', obj.image.url)

    associated_users.short_description = 'Пользователи'
    image_preview.short_description = 'Предпросмотр изображения'


admin.site.register(Floor, FloorAdmin)