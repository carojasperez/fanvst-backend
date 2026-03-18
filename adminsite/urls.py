from django.urls import re_path as url
from django.urls import path, include
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import (LoginAuthToken, UpdatePassword, CreateUserView,
                    CheckUserExists, ValidateEmail, PassWordResetEmail)
from rest_framework import routers
from adminsite.views import ChangePasswordFromEmail, ResendValidationEmail, SocialLoginAuth, ValidateEmailToken


app_name = "adminsite"

router = routers.SimpleRouter()


urlpatterns = [
    # Auth API V1
    url(r'^authentication/engine/23d3054a-2ac4-431c-8606-cf223d537fa4/V1/',
        LoginAuthToken.as_view()),

    # Auth API Social V1
    url(r'^authentication-social/engine/23d3054a-2ac4-431c-8606-cf223d537fa4/V1/',
        SocialLoginAuth.as_view()),

    url(r'^authentication/passwd/change/2ac4-431c-8606-cf223d537fa4/V1/',
        UpdatePassword.as_view()),

    url(r'^authentication/user/reg/d37f8bf4-b616-42d9-8e0b-f48a9435fc62/V1/',
        CreateUserView.as_view()),

    url(r'^authentication/user/check/d37f8bf4-b616-42d9-8e0b-f48a9435fc62/V1/',
        CheckUserExists.as_view()),

    url(r'^authentication/user/validate-email/d37f8bf4-b616-42d9-8e0b-f48a9435fc62/V1/',
        ValidateEmail.as_view()),

    url(r'^authentication/user/reset-passwords/c246eb48-1faa-4a8f-bc24-721e9cee6d5b/V1/',
        PassWordResetEmail.as_view()),

    url(r'^authentication/user/validate-email-token/2067f3bb-66cf-44fa-9dff-125114fd2d5e/V1/',
        ValidateEmailToken.as_view()),

    url(r'^authentication/user/change-password-femail/1a69abf4-ec8a-4429-b97a-5ded75ab2c39/V1/',
        ChangePasswordFromEmail.as_view()),

    url(r'^authentication/user/resend-validation-email/f28ddddf-e54d-4dcd-befa-352652f0fad1/V1/',
        ResendValidationEmail.as_view()),

    path('payment-gateway/mercado-pago/e97e8281-1d3e-4038-95ef-98f89e3071da',
         views.PaymentGate.as_view()),

    path('data/API/payment-gateway/paypal/e97e8281-1d3e-4038-95ef-98f89e3071da/',
         views.PaymentGatePaypal.as_view()),

    # Fanvst public API
    path('data/API/', include('fanvst.urls')),

    # path('email-test2', TemplateView.as_view(
    #         template_name="deposit_notification.html"), name='index'),

]

urlpatterns += router.urls
