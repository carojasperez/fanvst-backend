from django.urls import re_path as url
from django.urls import path
from . import views
from rest_framework import routers


app_name = "svc"

router = routers.SimpleRouter()

# Public Svc APis
router.register(r'data/API/public-svc', views.PublicSvcList, 'PublicSvcList')
router.register(r'data/API/public-svc-wall', views.PublicSvcWall, 'PublicSvcWall')
router.register(r'data/API/public-optsvc', views.PublicSvcOpt, 'PublicSvcOpt')

router.register(r'data/API/svcopt-detail', views.SvcOptDetail, 'SvcOptDetail')

# Private Apis
router.register(r'data/API/svc-list', views.ChamberSvcList, 'ChamberSvcList')
router.register(r'data/API/svc-manage', views.ChamberSvc, 'ChamberSvc')
router.register(r'data/API/svc-picture', views.ChamberSvcImage, 'svcPicture')
router.register(r'data/API/include-list', views.SvcIncludeList, 'SvcIncludeList')
router.register(r'data/API/svc-opt', views.ChamberSvcOpt, 'ChamberSvcOpt')


urlpatterns = [

    path('data/API/publish-chamber-svc/',
         views.PublishSvc.as_view()),

]

urlpatterns += router.urls
