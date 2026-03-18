from django.contrib import admin
from .models import (Quote, QuoteReply, CancelReason, WorkOffer, CWMessage,
                     WorkOfferCandidate, ContractedWork, CWReview, Dispute,
                     DisputeReply, QuoteFile)


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'chamber', 'created_at', 'remote_work')
    list_filter = ['remote_work']
    search_fields = ['user__username']


@admin.register(QuoteReply)
class QuoteReplyAdmin(admin.ModelAdmin):

    list_display = ('id', 'quote', 'created_at', 'is_client', 'user')


@admin.register(CancelReason)
class CancelReasonAdmin(admin.ModelAdmin):

    list_display = ('created_by', 'created_at', 'code', 'name')


@admin.register(WorkOffer)
class WorkOfferAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'title', 'created_at', 'say_price',
                    'tarif_from', 'tarif_to', 'status', 'uuid1')

    list_filter = ['status']
    search_fields = ['user__username']

@admin.register(WorkOfferCandidate)
class WorkOfferCandidateAdmin(admin.ModelAdmin):

    list_display = ('id', 'chamber', 'work_offer', 'created_at')


@admin.register(ContractedWork)
class ContractedWorkAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'po')


@admin.register(CWMessage)
class CWMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')


@admin.register(CWReview)
class CWReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')


@admin.register(QuoteFile)
class QuoteFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'is_client', 'created_at', 'quote')


@admin.register(Dispute)
class CWReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')


@admin.register(DisputeReply)
class CWReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
