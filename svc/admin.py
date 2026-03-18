from django.contrib import admin
from .models import (Svc, SvcOpt, SvcInclude, SvcImage)

@admin.register(SvcInclude)
class ScvIncludeAdmin(admin.ModelAdmin):
    
    list_display = ('user', 'sub_category', 'name')
    search_fields = ['name']
    list_filter = ['sub_category', 'is_active']


@admin.register(Svc)
class SvcAdmin(admin.ModelAdmin):

    list_display = ('user', 'uuid', 'title', 'sub_category', 'is_active',
                    'is_published')
    list_filter = ['is_active', 'is_published']
    search_fields = ['uuid', 'title']


@admin.register(SvcOpt)
class SvcOptAdmin(admin.ModelAdmin):

    list_display = ('user', 'svc', 'level', 'cost', 'fee', 'sale')
    list_filter = ['level']


@admin.register(SvcImage)
class SvcImageAdmin(admin.ModelAdmin):

    list_display = ('user', 'svc')
    search_fields = ['svc']



