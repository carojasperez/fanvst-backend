from django.urls import path
from .views import (
    GenreListView,
    ArtistListView, ArtistDetailView, ArtistFollowView, ArtistTipView, TipPaypalConfirmView,
    CampaignListView, CampaignDetailView, CampaignContributeView, CampaignContributePaypalView,
    ArtistCampaignView, ArtistCampaignDetailView,
    TierSubscribeView,
    MeFollowingView, MeSubscriptionsView, MeContributionsView, MeTipsView,
    MeFanProfileView,
    MyArtistProfileView, ArtistPictureView, ArtistCoverView,
    CampaignCoverView, CampaignRewardView, CampaignRewardDetailView, CampaignPublishView,
    CampaignUpdateView,
    ArtistTierView, ArtistTierDetailView,
    ArtistSubscribersView,
)

urlpatterns = [
    # Genres
    path('genres/', GenreListView.as_view()),

    # Artists
    path('artists/', ArtistListView.as_view()),
    path('artist/<str:handle_or_uuid>/', ArtistDetailView.as_view()),
    path('artist/<str:handle_or_uuid>/follow/', ArtistFollowView.as_view()),
    path('artist/<str:handle_or_uuid>/tip/',         ArtistTipView.as_view()),
    path('artist/<str:handle_or_uuid>/tip/confirm/', TipPaypalConfirmView.as_view()),

    # Campaigns — <str:slug_or_uuid> acepta tanto UUID como slug
    path('campaigns/', CampaignListView.as_view()),
    path('campaign/<str:slug_or_uuid>/', CampaignDetailView.as_view()),
    path('campaign/<str:slug_or_uuid>/contribute/',         CampaignContributeView.as_view()),
    path('campaign/<str:slug_or_uuid>/contribute/confirm/', CampaignContributePaypalView.as_view()),

    # Subscriptions
    path('tier/<int:tier_id>/subscribe/', TierSubscribeView.as_view()),

    # Me (authenticated)
    path('me/following/', MeFollowingView.as_view()),
    path('me/fan-profile/', MeFanProfileView.as_view()),
    path('me/subscriptions/', MeSubscriptionsView.as_view()),
    path('me/contributions/', MeContributionsView.as_view()),
    path('me/tips/', MeTipsView.as_view()),
    path('me/artist-profile/', MyArtistProfileView.as_view()),
    path('me/artist-profile/picture/', ArtistPictureView.as_view()),
    path('me/artist-profile/cover/', ArtistCoverView.as_view()),
    path('me/campaigns/', ArtistCampaignView.as_view()),
    path('me/campaigns/<uuid:uuid>/', ArtistCampaignDetailView.as_view()),
    path('me/campaigns/<uuid:uuid>/cover/', CampaignCoverView.as_view()),
    path('me/campaigns/<uuid:uuid>/rewards/', CampaignRewardView.as_view()),
    path('me/campaigns/<uuid:uuid>/rewards/<int:reward_id>/', CampaignRewardDetailView.as_view()),
    path('me/campaigns/<uuid:uuid>/publish/', CampaignPublishView.as_view()),
    path('me/campaigns/<uuid:uuid>/updates/', CampaignUpdateView.as_view()),
    path('me/tiers/', ArtistTierView.as_view()),
    path('me/tiers/<int:tier_id>/', ArtistTierDetailView.as_view()),
    path('me/subscribers/', ArtistSubscribersView.as_view()),
]
