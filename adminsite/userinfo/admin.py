from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ExportMixin
from import_export import resources
from .models import (Profile, Professional, EmailValidation, Academic,
                     WorkExperience, ChamberMembership, EmailPasswordReset,
                     MembershipUserPromo, ProfessionalLike, BankAccount,
                     SocialAuth, Notification)
from django.contrib.auth.models import User


# class UserResource(resources.ModelResource):
    
#     class Meta:
#         model = User


class UserAdminResource(resources.ModelResource):

    class Meta:
        model = Profile
        fields = ('user__first_name', 'user__last_name', 'user__username',
                  'is_chamber')

@admin.register(SocialAuth)
class SocialAuthAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'provider_id', 'uid')
    list_filter = ['provider_id']
    search_fields = ['user__username', 'uid']


@admin.register(Profile)
class ProfileAdmin(ImportExportModelAdmin):
    resource_class = UserAdminResource
    list_display = ('id', 'user', 'is_chamber', 'email_confirmed')
    search_fields = ['user__first_name', 'user__username']


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'title')
    search_fields = ['user', 'title']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'paypal', 'account_type', 'account_number',
                    'cci_number')
    list_filter = ['bank']
    search_fields = ['user', 'title']


@admin.register(EmailValidation)
class EmailValidationAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'used')
    readonly_fields = ('uuid1', 'uuid2', 'created_at', 'used_at')


@admin.register(EmailPasswordReset)
class EmailPasswordResetAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'used')
    readonly_fields = ('token1', 'token2', 'created_at', 'used_at')


@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'user', 'start', 'end')


@admin.register(Academic)
class AcademicAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'user', 'start', 'end')


@admin.register(ChamberMembership)
class ChamberMembershipAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'user', 'membership', 'from_date',
                    'to_date')


@admin.register(MembershipUserPromo)
class MembershipUserPromoAdmin(admin.ModelAdmin):

    list_display = ('id',)


@admin.register(ProfessionalLike)
class ProfessionalLikeAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'chamber', 'is_active')


@admin.register(Notification)
class Notification(admin.ModelAdmin):

    list_display = ('id', 'user', 'work_offer')
