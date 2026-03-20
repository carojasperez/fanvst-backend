from decimal import Decimal
from rest_framework import serializers
from .models import Genre, ArtistProfile, FanProfile, FanTier, FanSubscription, Campaign, CampaignContribution, CampaignReward, CampaignUpdate, DirectTip


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class FanTierSerializer(serializers.ModelSerializer):
    subscribers_count = serializers.IntegerField(read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FanTier
        fields = ('id', 'name', 'description', 'price', 'currency',
                  'sort_order', 'subscribers_count', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscriptions.filter(fan=request.user, is_active=True).exists()
        return False


class FanTierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FanTier
        fields = ('id', 'name', 'description', 'price', 'currency', 'sort_order')

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('El precio debe ser mayor a 0.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tier = getattr(self, 'instance', None)
        if not tier:
            return attrs

        has_active_subscribers = tier.subscriptions.filter(is_active=True).exists()
        if not has_active_subscribers:
            return attrs

        price_changed = 'price' in self.initial_data and attrs.get('price', tier.price) != tier.price
        currency_changed = 'currency' in self.initial_data and attrs.get('currency', tier.currency) != tier.currency

        if price_changed or currency_changed:
            raise serializers.ValidationError({
                'detail': (
                    'No puedes cambiar precio o moneda de un plan con suscriptores activos. '
                    'Crea un nuevo plan para nuevos precios.'
                )
            })

        return attrs


class CampaignRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignReward
        fields = ('id', 'title', 'description', 'min_amount', 'sort_order')


class CampaignUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignUpdate
        fields = ('id', 'title', 'body', 'created_at')


class ArtistMiniSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ArtistProfile
        fields = ('uuid', 'handle', 'stage_name', 'picture_url', 'verified')

    def get_picture_url(self, obj):
        return obj.picture_url


class CampaignSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField()
    artist = ArtistMiniSerializer(read_only=True)
    raised_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    percent_reached = serializers.IntegerField(read_only=True)
    contributors_count = serializers.IntegerField(read_only=True)
    cover_image_url = serializers.SerializerMethodField()
    rewards = CampaignRewardSerializer(many=True, read_only=True)
    updates = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = (
            'uuid', 'slug', 'artist', 'title', 'description', 'cover_image_url',
            'goal_amount', 'raised_amount', 'percent_reached', 'currency',
            'deadline', 'status', 'contributors_count', 'created_at', 'rewards', 'updates',
        )

    def get_updates(self, obj):
        qs = obj.updates.all()[:10]
        return CampaignUpdateSerializer(qs, many=True).data

    def get_cover_image_url(self, obj):
        return obj.cover_image_url


class CampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = ('title', 'description', 'goal_amount', 'currency', 'deadline')

    def validate_goal_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('La meta debe ser mayor a 0.')
        return value


class ContributeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=8, decimal_places=2,
        min_value=Decimal('1'),
    )
    message = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')


class ArtistListSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField()
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    picture_url = serializers.SerializerMethodField()
    cover_picture_url = serializers.SerializerMethodField()
    artist_type_text = serializers.CharField(source='get_artist_type_display')
    genres = GenreSerializer(many=True, read_only=True)
    followers_count = serializers.IntegerField(read_only=True)
    active_campaigns_count = serializers.IntegerField(read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = ArtistProfile
        fields = (
            'uuid', 'handle', 'first_name', 'last_name', 'stage_name', 'bio',
            'picture_url', 'cover_picture_url', 'artist_type',
            'artist_type_text', 'location_display', 'verified',
            'genres', 'followers_count', 'active_campaigns_count', 'is_following',
            'instagram', 'spotify', 'youtube', 'tiktok', 'soundcloud', 'website',
        )

    def get_picture_url(self, obj):
        return obj.picture_url

    def get_cover_picture_url(self, obj):
        return obj.cover_picture_url

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(fan=request.user).exists()
        return False


class ArtistDetailSerializer(ArtistListSerializer):
    fan_tiers = FanTierSerializer(many=True, read_only=True)
    campaigns = CampaignSerializer(many=True, read_only=True)

    class Meta(ArtistListSerializer.Meta):
        fields = ArtistListSerializer.Meta.fields + ('fan_tiers', 'campaigns')


class SubscriptionSerializer(serializers.ModelSerializer):
    tier = FanTierSerializer(read_only=True)
    artist = serializers.SerializerMethodField()

    class Meta:
        model = FanSubscription
        fields = ('id', 'tier', 'artist', 'is_active', 'created_at', 'expires_at')

    def get_artist(self, obj):
        return ArtistMiniSerializer(obj.tier.artist, context=self.context).data


class SubscriberSerializer(serializers.ModelSerializer):
    """Suscriptor visto desde la perspectiva del artista."""
    fan_alias    = serializers.SerializerMethodField()
    tier_id      = serializers.IntegerField(source='tier.id', read_only=True)
    tier_name    = serializers.CharField(source='tier.name', read_only=True)
    tier_price   = serializers.DecimalField(source='tier.price', max_digits=8, decimal_places=2, read_only=True)
    tier_currency = serializers.CharField(source='tier.currency', read_only=True)

    class Meta:
        model = FanSubscription
        fields = ('id', 'fan_alias', 'tier_id', 'tier_name',
                  'tier_price', 'tier_currency', 'created_at')

    def get_fan_alias(self, obj):
        return _fan_public_label(obj.fan)


class ContributionSerializer(serializers.ModelSerializer):
    campaign = CampaignSerializer(read_only=True)

    class Meta:
        model = CampaignContribution
        fields = ('id', 'campaign', 'amount', 'confirmed', 'message', 'created_at')


class TipSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=8, decimal_places=2,
        min_value=Decimal('1'),
    )
    currency = serializers.CharField(max_length=3, default='USD')
    message  = serializers.CharField(max_length=500, required=False, allow_blank=True, default='')


class FanProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FanProfile
        fields = ('uuid', 'public_alias', 'show_real_name_to_artists')
        read_only_fields = ('uuid',)

    def validate_public_alias(self, value):
        alias = value.strip()
        if alias:
            return alias

        request = self.context.get('request')
        if not request:
            return alias

        return f'Fan {request.user.id}'


def _fan_public_label(user):
    profile = getattr(user, 'fan_profile', None)
    if profile and profile.show_real_name_to_artists:
        first_name = (user.first_name or '').strip()
        last_name = (user.last_name or '').strip()
        full_name = f'{first_name} {last_name}'.strip()
        if full_name:
            return full_name
        if first_name:
            return first_name

    alias = (profile.public_alias if profile else '').strip() if profile else ''
    if alias:
        return alias
    return f'Fan {user.id}'


class DirectTipSerializer(serializers.ModelSerializer):
    fan_alias = serializers.SerializerMethodField()

    class Meta:
        model  = DirectTip
        fields = ('id', 'fan_alias', 'amount', 'currency', 'message', 'created_at')

    def get_fan_alias(self, obj):
        return _fan_public_label(obj.fan)


class CampaignEditSerializer(serializers.ModelSerializer):
    """Permite al artista editar su campaña. goal_amount solo se acepta en status=draft."""
    class Meta:
        model = Campaign
        fields = ('title', 'description', 'goal_amount', 'deadline')

    def validate_goal_amount(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError('La meta debe ser mayor a 0.')
        return value


class ArtistProfileUpdateSerializer(serializers.ModelSerializer):
    genres = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Genre.objects.all(), required=False
    )

    class Meta:
        model = ArtistProfile
        fields = ('handle', 'stage_name', 'bio', 'location_display', 'artist_type', 'genres',
                  'instagram', 'spotify', 'youtube', 'tiktok', 'soundcloud', 'website')
