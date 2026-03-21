from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ExportMixin
from import_export import resources
from .models import (Profile, EmailValidation, EmailPasswordReset,
                     BankAccount, SocialAuth, Notification)
from django.contrib.auth.models import User


class UserAdminResource(resources.ModelResource):

    class Meta:
        model = Profile
        fields = ('user__first_name', 'user__last_name', 'user__username')


@admin.register(SocialAuth)
class SocialAuthAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'provider_id', 'uid')
    list_filter = ['provider_id']
    search_fields = ['user__username', 'uid']


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    resource_class = UserAdminResource
    list_display = ('id', 'user', 'email_confirmed', 'is_artist', 'stage_name')
    search_fields = ['user__first_name', 'user__username', 'stage_name']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'paypal', 'account_type', 'account_number',
                    'cci_number')
    list_filter = ['bank']
    search_fields = ['user__username', 'user__first_name']


@admin.register(EmailValidation)
class EmailValidationAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'used')
    readonly_fields = ('uuid1', 'uuid2', 'created_at', 'used_at')


@admin.register(EmailPasswordReset)
class EmailPasswordResetAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'used')
    readonly_fields = ('token1', 'token2', 'created_at', 'used_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):

    list_display = ('id', 'user')
