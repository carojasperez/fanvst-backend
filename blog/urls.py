from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import PostAPI
from rest_framework import routers


app_name = "blog"

router = routers.SimpleRouter()

router.register(r'data/API/blog-list', views.PostAPI, 'BlogAPI'),

router.register(r'data/API/blog-detail', views.PostDetailAPI, 'PostDetailAPI')

# URL Admin de Blog
router.register(r'data/API/blog-admin', views.BlogAdminAPI, 'BlogAdminAPI')


urlpatterns = [
    # url(r'^authentication/engine/23d3054a-2ac4-431c-8606-cf223d537fa4/V1/',
    #     LoginAuthToken.as_view()),

]

urlpatterns += router.urls
