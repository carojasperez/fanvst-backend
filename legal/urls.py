from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework import routers


app_name = "legal"

router = routers.SimpleRouter()

router.register(r'data/API/complaint-bo', views.ComplaintBookAPI, 'ComplaintBookAPI')

urlpatterns = [
    url(r'^data/API/complaint-book', views.CreateComplaintView.as_view()),
]

urlpatterns += router.urls
