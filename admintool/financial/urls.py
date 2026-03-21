from django.urls import path
from . import views


app_name = "financial"

urlpatterns = [
    # Artist Payouts
    path('data/API/artist-payouts/', views.ArtistPayoutList.as_view()),
    path('data/API/artist-payout-approve/', views.ArtistPayoutApprove.as_view()),
    path('data/API/artist-payout-complete/', views.ArtistPayoutComplete.as_view()),
    path('data/API/artist-payout-cancel/', views.ArtistPayoutCancel.as_view()),
]
