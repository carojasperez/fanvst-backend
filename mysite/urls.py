"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('bo/', include('adminsite.urls', namespace='bo')),
    # URLs limpias de auth (Fanvst)
    path('auth/', include('adminsite.auth_urls')),
    path('userinfo/', include('adminsite.userinfo.urls', namespace='userinfo')),
    path('baseinfo/', include('adminsite.baseinfo.urls', namespace='baseinfo')),
    path('legal/', include('legal.urls', namespace='legal')),
    path('blog/', include('blog.urls', namespace='blog')),

    # Wallet & Payouts (artista autenticado)
    path('wallet/', include('wallet.urls', namespace='wallet')),

    # URLS Administrativas - Solo Staff LetsCloud
    path('financial/', include('admintool.financial.urls', namespace='financial')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)