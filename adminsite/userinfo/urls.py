from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework import routers


app_name = "userinfo"

router = routers.SimpleRouter()

# APIs Privados Actualizar Perfil
router.register(r'data/API/profile', views.UserProfileAPI, 'UserProfile')
router.register(r'data/API/profile-picture', views.UserPicture, 'UserPicture')
router.register(r'data/API/become-chamber', views.BecomeChamberAPI, 'BecomeChamberAPI')
router.register(r'data/API/professional', views.ProfessionalAPI, 'Professional')
router.register(r'data/API/academic', views.AcademicAPI, 'Academic')
router.register(r'data/API/experience', views.WorkExpAPI, 'experience')
router.register(r'data/API/skill', views.SkillAPI, 'skill')
router.register(r'data/API/bank-account', views.BankAccountAPI, 'bank-account')
router.register(r'data/API/chamber-membership', views.ChamberMembershipAPI, 'ChamberMembershipAPI')
router.register(r'data/API/user-notification', views.NotificationPreferenceAPI, 'NotificationPreferenceAPI')

# APis Publicos Mostrar info del Perfil. Oculta lo que no queremos mostrar
router.register(r'data/API/GetProfessionalAPI',
                views.GetProfessionalAPI, 'GetProfessionalAPI')

router.register(r'data/API/GetSkillAPI',
                views.GetSkillAPI, 'GetSkillAPI')

router.register(r'data/API/GetAcademyAPI',
                views.GetAcademyAPI, 'GetAcademyAPI')

router.register(r'data/API/GetWorkExpAPI',
                views.GetWorkExpAPI, 'GetWorkExpAPI')

router.register(r'data/API/GetChamberList',
                views.GetChamberList, 'GetChamberList')

router.register(r'data/API/ChamberCountLikeAPI',
                views.ChamberCountLikeAPI, 'ChamberCountLikeAPI')

# Fanvst: artistas y géneros
router.register(r'data/API/genres', views.GenreListAPI, 'genres')
router.register(r'data/API/artists', views.ArtistListAPI, 'artists')


urlpatterns = [

    path('data/API/ChamberPromoCodeAPI/', views.ChamberPromoCodeAPI.as_view()),
    path('data/API/ChamberLikeAPI/', views.ChamberLikeAPI.as_view()),

    # Fanvst: perfil individual de artista y follow
    path('data/API/artist/<uuid:uuid>/',
         views.ArtistDetailAPI.as_view(), name='artist-detail'),
    path('data/API/artist/<uuid:uuid>/follow/',
         views.FollowArtistAPI.as_view(), name='artist-follow'),
]

urlpatterns += router.urls
