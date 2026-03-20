from django.urls import re_path as url
from django.urls import path
from . import views
from rest_framework import routers
from admintool.financial.views import OpenQuotes


app_name = "financial"

router = routers.SimpleRouter()

# Incomes, Payments
router.register(r'data/API/pending-payment', views.PendingPayment, 'PendingPayment')
router.register(r'data/API/pending-payment-bank', views.PendingPaymentBank, 'PendingPaymentBank')

# Dashboard
router.register('data/API/open-quote', views.OpenQuotes, 'OpenQuotes')
router.register('data/API/open-works', views.OpenWorks, 'OpenWorks')
router.register('data/API/count-chamber', views.CountChambers, 'CountChambers')
router.register('data/API/count-contracted', views.CountContractedWork, 'CountContractedWork')

# Sales per month
router.register('data/API/sales-monthly', views.SalesPerMonth, 'SalesPerMonth')


urlpatterns = [
    # Register Payment (Qué Chamba legacy)
    path('data/API/register-payment/', views.RegisterPayment.as_view()),

    # Artist Payouts
    path('data/API/artist-payouts/', views.ArtistPayoutList.as_view()),
    path('data/API/artist-payout-approve/', views.ArtistPayoutApprove.as_view()),
    path('data/API/artist-payout-complete/', views.ArtistPayoutComplete.as_view()),
    path('data/API/artist-payout-cancel/', views.ArtistPayoutCancel.as_view()),
]

urlpatterns += router.urls
