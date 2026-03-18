from django.urls import re_path as url
from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from rest_framework import routers


app_name = "payment"

router = routers.SimpleRouter()

# Purchase Order Apis
router.register(r'data/API/purchase-order', views.PurchaseOrderAPI, 'PurchaseOrderAPI')


router.register(r'data/API/chamber-income', views.ChamberIncomeApi,
                'ChamberIncomeApi')


urlpatterns = [

]

urlpatterns += router.urls
