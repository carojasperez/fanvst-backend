"""
URLs limpias para el sistema de auth de Fanvst.
Registradas en mysite/urls.py como path('auth/', include('adminsite.auth_urls'))

Endpoints disponibles:
  POST /auth/login/                  → LoginAuthToken
  POST /auth/login-social/           → SocialLoginAuth
  PUT  /auth/change-password/        → UpdatePassword
  POST /auth/register/               → CreateUserView
  GET  /auth/check-username/         → CheckUserExists
  GET  /auth/validate-email/         → ValidateEmail
  POST /auth/reset-password/         → PassWordResetEmail
  GET  /auth/validate-reset-token/   → ValidateEmailToken
  PUT  /auth/set-password/           → ChangePasswordFromEmail
  POST /auth/resend-validation/      → ResendValidationEmail
"""
from django.urls import path
from adminsite.views import (
    LoginAuthToken, SocialLoginAuth, UpdatePassword,
    CreateUserView, CheckUserExists, ValidateEmail,
    PassWordResetEmail, ValidateEmailToken,
    ChangePasswordFromEmail, ResendValidationEmail,
    LogoutView,
)

urlpatterns = [
    path('login/',                LoginAuthToken.as_view()),
    path('login-social/',         SocialLoginAuth.as_view()),
    path('change-password/',      UpdatePassword.as_view()),
    path('register/',             CreateUserView.as_view()),
    path('check-username/',       CheckUserExists.as_view()),
    path('validate-email/',       ValidateEmail.as_view()),
    path('reset-password/',       PassWordResetEmail.as_view()),
    path('validate-reset-token/', ValidateEmailToken.as_view()),
    path('set-password/',         ChangePasswordFromEmail.as_view()),
    path('resend-validation/',    ResendValidationEmail.as_view()),
    path('logout/',               LogoutView.as_view()),
]
