from django.urls import path

from . import views

app_name = 'wallet'

urlpatterns = [
    path('balance/', views.WalletBalanceView.as_view(), name='balance'),
    path('transactions/', views.WalletTransactionListView.as_view(), name='transactions'),
    path('payout/', views.PayoutRequestView.as_view(), name='payout-list-create'),
    path('payout/<int:pk>/', views.PayoutRequestDetailView.as_view(), name='payout-detail'),
    path('payment/create/', views.CreatePaymentView.as_view(), name='payment-create'),
    path('payment/confirm/', views.ConfirmPaymentView.as_view(), name='payment-confirm'),
    path('payment/webhook/', views.DlocalWebhookView.as_view(), name='payment-webhook'),
]
