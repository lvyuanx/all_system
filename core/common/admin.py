from django.contrib import admin
from .models import ProvinceCode, CityCode, DistrictCode

@admin.register(ProvinceCode)
class ProvinceCodeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']  # 必须有
    list_display = ['code', 'name']

@admin.register(CityCode)
class CityCodeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']  # 必须有
    list_display = ['code', 'name', 'province']
    

@admin.register(DistrictCode)
class DistrictCodeAdmin(admin.ModelAdmin):
    search_fields = ['name', 'code']  # 必须有
    list_display = ['code', 'name', 'city']
    