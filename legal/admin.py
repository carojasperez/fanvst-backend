from django.contrib import admin
from legal.models import ComplaintBook


@admin.register(ComplaintBook)
class ComplaintBookAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'document', 'name')
    search_fields = ['name', 'surname', 'email', 'document']
    list_filter = ['is_service', 'is_claim']


