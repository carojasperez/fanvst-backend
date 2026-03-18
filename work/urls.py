from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework import routers


app_name = "work"

router = routers.SimpleRouter()

# Quote Apis
router.register(r'data/API/quote', views.QuoteAPI, 'QuoteAPI')
router.register(r'data/API/quote-reply', views.QuoteReplyAPI, 'QuoteReplyAPI')
router.register(r'data/API/quote-patch', views.CancelQuoteAPI, 'CancelQuoteAPI')
router.register(r'data/API/quote-file', views.QuoteFileAPI, 'QuoteFileAPI')

# Work Offer Apis
router.register(r'data/API/work-offer', views.WorkOfferApi, 'WorkOffer')
router.register(r'data/API/work-offer-candidate',
                views.WorkOfferCandidateApi, 'WorkOfferCandidateApi')


# Work Offer Public Apis
router.register(
    r'data/API/public-work-offer', views.PublicWorkOfferApi, 'PublicWorkOffer')

router.register(
    r'data/API/public-work-candidate',
    views.PublicWorkOfferCandidate, 'PublicWorkOfferCandidate')

# CW Works Apis
router.register(
    r'data/API/contracted-works',
    views.ContractedWorksApi, 'ContractedWorksApi')

router.register(r'data/API/cw-message', views.CWMessageAPI, 'CWMessageAPI')

router.register(r'data/API/cw-review', views.CWReviewAPI, 'CWReviewAPI')

router.register(r'data/API/cw-review-public', views.CWReviewPublicAPI, 'CWReviewPublicAPI')


# Dispute Apis
router.register(r'data/API/dispute', views.DisputeAPI, 'DisputeAPI')
router.register(r'data/API/dispute-message',
                views.DisputeReplyAPI, 'DisputeReplyAPI')

urlpatterns = [

    path('data/API/accept-work-offer-candidate/',
         views.AcceptWorkCandidate.as_view()),

    # Contracted
    path('data/API/finish-contracted-work-customer/',
         views.CWFinishAPI.as_view()),

    path('data/API/cfinish-contracted-work-customer/',
         views.CWChamberFinishAPI.as_view()),

    path('data/API/cancel-contracted-work/',
         views.CWCancelWork.as_view()),

    path('data/API/cancel-cw-w-dispute/',
         views.CWCancelWorkWDispute.as_view()),

    # Work Offer Email
    path('data/API/send-cw-available-works/',
         views.CWAvailableWork.as_view())

]

urlpatterns += router.urls
