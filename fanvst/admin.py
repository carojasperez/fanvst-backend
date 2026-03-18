from django.contrib import admin
from .models import (
    Genre, ArtistProfile, ArtistFollow,
    FanTier, FanSubscription,
    Campaign, CampaignContribution,
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ArtistProfile)
class ArtistProfileAdmin(admin.ModelAdmin):
    list_display = ('stage_name', 'artist_type', 'location_display', 'verified', 'followers_count')
    list_filter = ('artist_type', 'verified', 'genres')
    search_fields = ('stage_name', 'user__email')
    filter_horizontal = ('genres',)
    readonly_fields = ('uuid', 'created_at', 'updated_at')


@admin.register(FanTier)
class FanTierAdmin(admin.ModelAdmin):
    list_display = ('artist', 'name', 'price', 'currency', 'is_active', 'sort_order')
    list_filter = ('is_active', 'currency')
    search_fields = ('artist__stage_name', 'name')


@admin.register(FanSubscription)
class FanSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('fan', 'tier', 'is_active', 'created_at', 'expires_at')
    list_filter = ('is_active',)
    raw_id_fields = ('fan', 'tier')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'status', 'goal_amount', 'raised_amount',
                    'percent_reached', 'deadline')
    list_filter = ('status', 'currency')
    search_fields = ('title', 'artist__stage_name')
    readonly_fields = ('uuid', 'created_at', 'updated_at', 'raised_amount', 'percent_reached')

    def raised_amount(self, obj):
        return obj.raised_amount
    raised_amount.short_description = 'Recaudado'

    def percent_reached(self, obj):
        return f'{obj.percent_reached}%'
    percent_reached.short_description = '% alcanzado'


@admin.register(CampaignContribution)
class CampaignContributionAdmin(admin.ModelAdmin):
    list_display = ('fan', 'campaign', 'amount', 'confirmed', 'created_at')
    list_filter = ('confirmed',)
    raw_id_fields = ('fan', 'campaign')
