import uuid as uuid_module
from rest_framework import generics, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django.shortcuts import get_object_or_404

from .models import Genre, ArtistProfile, ArtistFollow, FanTier, FanSubscription, Campaign, CampaignContribution, CampaignReward, CampaignUpdate
from .serializers import (
    GenreSerializer, ArtistListSerializer, ArtistDetailSerializer,
    ArtistProfileUpdateSerializer,
    CampaignSerializer, CampaignCreateSerializer, ContributeSerializer,
    SubscriptionSerializer, ContributionSerializer, CampaignRewardSerializer,
    CampaignUpdateSerializer, FanTierSerializer, FanTierCreateSerializer,
    SubscriberSerializer,
)
from .pagination import ArtistPagination


def _get_artist(handle_or_uuid, qs=None):
    """Resuelve un artista por UUID o handle."""
    if qs is None:
        qs = ArtistProfile.objects.select_related('user').prefetch_related(
            'genres', 'followers', 'fan_tiers', 'campaigns'
        )
    try:
        uuid_module.UUID(str(handle_or_uuid))
        return get_object_or_404(qs, uuid=handle_or_uuid)
    except ValueError:
        return get_object_or_404(qs, handle=handle_or_uuid)


def _get_campaign(slug_or_uuid, qs=None):
    """Resuelve una campaña por UUID o slug."""
    if qs is None:
        qs = Campaign.objects.select_related('artist__user').prefetch_related('contributions')
    try:
        uuid_module.UUID(str(slug_or_uuid))
        return get_object_or_404(qs, uuid=slug_or_uuid)
    except ValueError:
        return get_object_or_404(qs, slug=slug_or_uuid)


# ── Genres ────────────────────────────────────────────────────────────────────

class GenreListView(generics.ListAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]


# ── Artists ───────────────────────────────────────────────────────────────────

class ArtistListView(generics.ListAPIView):
    serializer_class = ArtistListSerializer
    permission_classes = [AllowAny]
    pagination_class = ArtistPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['stage_name', 'bio', 'user__first_name', 'user__last_name']

    def get_queryset(self):
        qs = ArtistProfile.objects.select_related('user').prefetch_related('genres', 'followers')
        genre_slug = self.request.query_params.get('genre')
        if genre_slug:
            qs = qs.filter(genres__slug=genre_slug)
        return qs


class ArtistDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, handle_or_uuid):
        artist = _get_artist(handle_or_uuid)
        return Response(ArtistDetailSerializer(artist, context={'request': request}).data)


class ArtistFollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, handle_or_uuid):
        artist = _get_artist(handle_or_uuid, qs=ArtistProfile.objects.prefetch_related('followers'))
        follow, created = ArtistFollow.objects.get_or_create(
            fan=request.user, artist=artist
        )
        if not created:
            follow.delete()
            following = False
        else:
            following = True
        return Response({
            'following': following,
            'followers_count': artist.followers_count,
        })


# ── Campaigns ─────────────────────────────────────────────────────────────────

class CampaignListView(generics.ListAPIView):
    serializer_class = CampaignSerializer
    permission_classes = [AllowAny]
    pagination_class = ArtistPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'artist__stage_name']

    def get_queryset(self):
        qs = Campaign.objects.select_related('artist__user').prefetch_related(
            'contributions', 'artist__genres'
        ).filter(status='active')
        genre_slug = self.request.query_params.get('genre')
        if genre_slug:
            qs = qs.filter(artist__genres__slug=genre_slug)
        return qs


class CampaignDetailView(APIView):
    """Detalle de campaña — acepta UUID o slug."""
    permission_classes = [AllowAny]

    def get(self, request, slug_or_uuid):
        campaign = _get_campaign(slug_or_uuid)
        return Response(CampaignSerializer(campaign, context={'request': request}).data)


class CampaignContributeView(APIView):
    """Fan contribuye a una campaña."""
    permission_classes = [IsAuthenticated]

    def post(self, request, slug_or_uuid):
        campaign = _get_campaign(slug_or_uuid)
        if campaign.status != 'active':
            return Response({'detail': 'La campaña no está activa.'}, status=status.HTTP_400_BAD_REQUEST)

        ser = ContributeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        contribution = CampaignContribution.objects.create(
            fan=request.user,
            campaign=campaign,
            amount=ser.validated_data['amount'],
            message=ser.validated_data.get('message', ''),
            confirmed=True,
        )
        return Response({
            'id': contribution.id,
            'amount': str(contribution.amount),
            'raised_amount': str(campaign.raised_amount),
            'percent_reached': campaign.percent_reached,
            'contributors_count': campaign.contributors_count,
        }, status=status.HTTP_201_CREATED)


class ArtistCampaignView(APIView):
    """CRUD de campañas del artista autenticado."""
    permission_classes = [IsAuthenticated]

    def _artist(self, user):
        return get_object_or_404(ArtistProfile, user=user)

    def get(self, request):
        artist = self._artist(request.user)
        campaigns = artist.campaigns.prefetch_related('contributions').all()
        return Response(CampaignSerializer(campaigns, many=True, context={'request': request}).data)

    def post(self, request):
        artist = self._artist(request.user)
        ser = CampaignCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        campaign = ser.save(artist=artist)
        return Response(
            CampaignSerializer(campaign, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


# ── Subscriptions ─────────────────────────────────────────────────────────────

class TierSubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, tier_id):
        tier = get_object_or_404(FanTier, id=tier_id, is_active=True)
        sub, created = FanSubscription.objects.get_or_create(
            fan=request.user, tier=tier,
            defaults={'is_active': True}
        )
        if not created:
            sub.is_active = not sub.is_active
            sub.save(update_fields=['is_active'])
        return Response({
            'subscribed': sub.is_active,
            'subscribers_count': tier.subscribers_count,
        })


# ── Me (authenticated user data) ──────────────────────────────────────────────

class MeFollowingView(generics.ListAPIView):
    serializer_class = ArtistListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        followed_ids = self.request.user.fanvst_following.values_list('artist_id', flat=True)
        return ArtistProfile.objects.filter(id__in=followed_ids).select_related('user').prefetch_related(
            'genres', 'followers'
        )


class MeSubscriptionsView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.fanvst_subscriptions.filter(
            is_active=True
        ).select_related('tier__artist__user').prefetch_related('tier__artist__genres')


class MeContributionsView(generics.ListAPIView):
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.fanvst_contributions.filter(
            confirmed=True
        ).select_related('campaign__artist__user').order_by('-created_at')


# ── Artist dashboard (own data) ───────────────────────────────────────────────

class MyArtistProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return ArtistProfileUpdateSerializer
        return ArtistDetailSerializer

    def get_object(self):
        return get_object_or_404(ArtistProfile, user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ser = ArtistProfileUpdateSerializer(instance, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ArtistDetailSerializer(instance, context={'request': request}).data)


class ArtistPictureView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        if 'file' not in request.FILES:
            return Response({'detail': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)
        artist.picture = request.FILES['file']
        artist.save(update_fields=['picture'])
        return Response({'picture_url': artist.picture_url})


class ArtistCoverView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        if 'file' not in request.FILES:
            return Response({'detail': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)
        artist.cover_picture = request.FILES['file']
        artist.save(update_fields=['cover_picture'])
        return Response({'cover_picture_url': artist.cover_picture_url})


class CampaignCoverView(APIView):
    """Sube la imagen de portada de una campaña del artista autenticado."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request, uuid):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        campaign = get_object_or_404(Campaign, uuid=uuid, artist=artist)
        if 'file' not in request.FILES:
            return Response({'detail': 'No se envió ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)
        campaign.cover_image = request.FILES['file']
        campaign.save(update_fields=['cover_image'])
        return Response({'cover_image_url': campaign.cover_image_url})


class CampaignRewardView(APIView):
    """Lista y crea recompensas de una campaña."""
    permission_classes = [IsAuthenticated]

    def _campaign(self, request, uuid):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        return get_object_or_404(Campaign, uuid=uuid, artist=artist)

    def get(self, request, uuid):
        campaign = self._campaign(request, uuid)
        return Response(CampaignRewardSerializer(campaign.rewards.all(), many=True).data)

    def post(self, request, uuid):
        campaign = self._campaign(request, uuid)
        ser = CampaignRewardSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        reward = ser.save(campaign=campaign)
        return Response(CampaignRewardSerializer(reward).data, status=status.HTTP_201_CREATED)


class CampaignRewardDetailView(APIView):
    """Actualiza o elimina una recompensa individual."""
    permission_classes = [IsAuthenticated]

    def _reward(self, request, uuid, reward_id):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        campaign = get_object_or_404(Campaign, uuid=uuid, artist=artist)
        return get_object_or_404(CampaignReward, id=reward_id, campaign=campaign)

    def patch(self, request, uuid, reward_id):
        reward = self._reward(request, uuid, reward_id)
        ser = CampaignRewardSerializer(reward, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(CampaignRewardSerializer(reward).data)

    def delete(self, request, uuid, reward_id):
        reward = self._reward(request, uuid, reward_id)
        reward.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CampaignPublishView(APIView):
    """Cambia el status de una campaña de draft a active."""
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        campaign = get_object_or_404(Campaign, uuid=uuid, artist=artist)
        if campaign.status != 'draft':
            return Response(
                {'detail': 'Solo se pueden publicar campañas en borrador.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        campaign.status = 'active'
        campaign.save(update_fields=['status'])
        return Response(CampaignSerializer(campaign, context={'request': request}).data)


class CampaignUpdateView(APIView):
    """Lista y crea actualizaciones de una campaña del artista."""
    permission_classes = [IsAuthenticated]

    def _campaign(self, request, uuid):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        return get_object_or_404(Campaign, uuid=uuid, artist=artist)

    def get(self, request, uuid):
        campaign = self._campaign(request, uuid)
        return Response(CampaignUpdateSerializer(campaign.updates.all(), many=True).data)

    def post(self, request, uuid):
        campaign = self._campaign(request, uuid)
        ser = CampaignUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        update = ser.save(campaign=campaign)
        return Response(CampaignUpdateSerializer(update).data, status=status.HTTP_201_CREATED)


# ── Artist tier management ─────────────────────────────────────────────────────

class ArtistTierView(APIView):
    """Lista y crea planes de membresía del artista autenticado."""
    permission_classes = [IsAuthenticated]

    def _artist(self, user):
        return get_object_or_404(ArtistProfile, user=user)

    def get(self, request):
        artist = self._artist(request.user)
        tiers = artist.fan_tiers.all()
        return Response(FanTierSerializer(tiers, many=True, context={'request': request}).data)

    def post(self, request):
        artist = self._artist(request.user)
        ser = FanTierCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        tier = ser.save(artist=artist)
        return Response(FanTierSerializer(tier, context={'request': request}).data, status=status.HTTP_201_CREATED)


class ArtistTierDetailView(APIView):
    """Actualiza o elimina un plan de membresía del artista autenticado."""
    permission_classes = [IsAuthenticated]

    def _tier(self, request, tier_id):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        return get_object_or_404(FanTier, id=tier_id, artist=artist)

    def patch(self, request, tier_id):
        tier = self._tier(request, tier_id)
        ser = FanTierCreateSerializer(tier, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(FanTierSerializer(tier, context={'request': request}).data)

    def delete(self, request, tier_id):
        tier = self._tier(request, tier_id)
        tier.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ArtistSubscribersView(APIView):
    """Lista todos los suscriptores activos del artista autenticado."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        artist = get_object_or_404(ArtistProfile, user=request.user)
        subs = (FanSubscription.objects
                .filter(tier__artist=artist, is_active=True)
                .select_related('fan', 'tier')
                .order_by('-created_at'))
        # Filtro opcional por tier
        tier_id = request.query_params.get('tier_id')
        if tier_id:
            subs = subs.filter(tier_id=tier_id)
        return Response(SubscriberSerializer(subs, many=True).data)
