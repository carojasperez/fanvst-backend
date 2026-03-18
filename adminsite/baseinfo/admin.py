from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (Department, Province, District, Category, SubCategory,
                     Bank, Country, Membership, MembershipPromoCode)


@admin.register(Country)
class CountryAdmin(ImportExportModelAdmin):

    list_display = ('created_by', 'iso3166', 'name')
    search_fields = ['iso3166', 'name']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_by', 'country', 'name')


@admin.register(Province)
class ProvinceAdmin(ImportExportModelAdmin):

    list_display = ('id', 'created_by', 'department', 'name')
    list_filter = ['department']


@admin.register(District)
class DistrictAdmin(ImportExportModelAdmin):

    list_display = ('id', 'created_by', 'province', 'name')
    list_filter = ('province',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_by', 'name', 'is_active')


@admin.register(SubCategory)
class SubCategoryAdmin(ImportExportModelAdmin):

    list_display = ('id', 'category', 'created_by','name', 'is_active')
    list_filter = ('category',)


@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_by', 'created_at', 'name')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_by', 'created_at', 'name', 'percent')


@admin.register(MembershipPromoCode)
class MembershipPromoCodeAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'membership', 'created_at', 'valid_from',
                    'valid_to')
