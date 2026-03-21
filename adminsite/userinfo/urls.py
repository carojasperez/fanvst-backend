from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "userinfo"

router = routers.DefaultRouter()
router.register(r'data/API/user-device', views.UserDeviceAPI, 'UserDevice')
router.register(r'data/API/user-profile', views.UserProfileAPI, 'UserProfile')
router.register(r'data/API/user-picture', views.UserPicture, 'UserPicture')
router.register(r'data/API/bank-account', views.BankAccountAPI, 'BankAccount')
router.register(r'data/API/notification-preference', views.NotificationPreferenceAPI, 'NotificationPreference')

# Fanvst: Artistas y Géneros
router.register(r'data/API/genre', views.GenreListAPI, basename='Genre')
router.register(r'data/API/artist', views.ArtistListAPI, basename='Artist')

urlpatterns = [
    path('', include(router.urls)),
    path('data/API/artist/<uuid:uuid>/', views.ArtistDetailAPI.as_view(), name='ArtistDetail'),
    path('data/API/artist/<uuid:uuid>/follow/', views.FollowArtistAPI.as_view(), name='FollowArtist'),
]
