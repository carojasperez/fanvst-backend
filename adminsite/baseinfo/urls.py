from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework import routers


app_name = "baseinfo"

router = routers.SimpleRouter()

router.register(r'data/API/department', views.DepartmentAPI, 'Department')
router.register(r'data/API/province', views.ProvinceAPI, 'Province')
router.register(r'data/API/district', views.DistrictAPI, 'District')
router.register(r'data/API/bank', views.BankAPI, 'Bank')
router.register(r'data/API/category', views.CategoryAPI, 'category')
router.register(r'data/API/sub-category', views.SubCategoryAPI, 'sub-category')
router.register(r'data/API/countries', views.CountryAPI, 'countries')


urlpatterns = [

]

urlpatterns += router.urls
