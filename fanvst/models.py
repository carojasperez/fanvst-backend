import uuid
from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils.text import slugify
from django.contrib.auth.models import User


def artist_picture_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'artists/{instance.uuid}/picture.{ext}'


def artist_cover_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'artists/{instance.uuid}/cover.{ext}'


def campaign_cover_path(instance, filename):
    ext = filename.rsplit('.', 1)[-1]
    return f'campaigns/{instance.uuid}/cover.{ext}'


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


ARTIST_TYPE_CHOICES = [
    ('solo', 'Solista'),
    ('band', 'Banda'),
    ('duo', 'Dúo'),
    ('collective', 'Colectivo'),
]

CURRENCY_CHOICES = [
    ('USD', 'USD'),
    ('PEN', 'PEN'),
]


class ArtistProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='artist_profile')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    stage_name = models.CharField(max_length=200)
    handle = models.SlugField(max_length=60, unique=True, null=True, blank=True,
                              help_text='Identificador único tipo @handle (ej: monlaferte)')
    bio = models.TextField(blank=True)
    picture = models.ImageField(upload_to=artist_picture_path, blank=True, null=True)
    cover_picture = models.ImageField(upload_to=artist_cover_path, blank=True, null=True)
    artist_type = models.CharField(max_length=20, choices=ARTIST_TYPE_CHOICES, default='solo')
    location_display = models.CharField(max_length=200, blank=True)
    verified = models.BooleanField(default=False)
    genres = models.ManyToManyField(Genre, blank=True, related_name='artists')

    # Redes sociales
    instagram   = models.URLField(blank=True)
    spotify     = models.URLField(blank=True)
    youtube     = models.URLField(blank=True)
    tiktok      = models.URLField(blank=True)
    soundcloud  = models.URLField(blank=True)
    website     = models.URLField(blank=True)

    class Meta:
        ordering = ['stage_name']

    def __str__(self):
        return self.stage_name

    @property
    def picture_url(self):
        try:
            return self.picture.url
        except Exception:
            return ''

    @property
    def cover_picture_url(self):
        try:
            return self.cover_picture.url
        except Exception:
            return ''

    @property
    def followers_count(self):
        return self.followers.count()

    @property
    def active_campaigns_count(self):
        return self.campaigns.filter(status='active').count()


class ArtistFollow(models.Model):
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fanvst_following')
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fan', 'artist')

    def __str__(self):
        return f'{self.fan} → {self.artist}'


class FanTier(models.Model):
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='fan_tiers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'price']

    def __str__(self):
        return f'{self.artist.stage_name} — {self.name}'

    @property
    def subscribers_count(self):
        return self.subscriptions.filter(is_active=True).count()


class FanSubscription(models.Model):
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fanvst_subscriptions')
    tier = models.ForeignKey(FanTier, on_delete=models.CASCADE, related_name='subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('fan', 'tier')

    def __str__(self):
        return f'{self.fan} → {self.tier}'


CAMPAIGN_STATUS_CHOICES = [
    ('draft', 'Borrador'),
    ('active', 'Activa'),
    ('completed', 'Completada'),
    ('cancelled', 'Cancelada'),
]


class Campaign(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    artist = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, related_name='campaigns')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True, null=True, blank=True, db_index=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=campaign_cover_path, blank=True, null=True)
    goal_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default='draft')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.artist.stage_name} — {self.title}'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or 'campaign'
            self.slug = f'{base}-{str(self.uuid)[:8]}'
        super().save(*args, **kwargs)

    @property
    def raised_amount(self):
        total = self.contributions.filter(confirmed=True).aggregate(
            total=Sum('amount')
        )['total']
        return total or Decimal('0')

    @property
    def cover_image_url(self):
        try:
            return self.cover_image.url
        except Exception:
            return ''

    @property
    def percent_reached(self):
        if not self.goal_amount:
            return 0
        return min(int((self.raised_amount / self.goal_amount) * 100), 100)

    @property
    def contributors_count(self):
        return self.contributions.filter(confirmed=True).values('fan').distinct().count()


class CampaignContribution(models.Model):
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fanvst_contributions')
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='contributions')
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    confirmed = models.BooleanField(default=False)
    message = models.TextField(blank=True)

    def __str__(self):
        return f'{self.fan} → {self.campaign} (${self.amount})'


class CampaignReward(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='rewards')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    min_amount = models.DecimalField(max_digits=8, decimal_places=2)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['min_amount', 'sort_order']

    def __str__(self):
        return f'{self.campaign} — {self.title}'


class CampaignUpdate(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='updates')
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    body = models.TextField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.campaign} — {self.title}'


class FanProfile(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fan_profile')
    favorite_genres = models.ManyToManyField(Genre, blank=True, related_name='fans')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Fan: {self.user.username}'
