from django.contrib import admin
from .models import (Payment, PaymentMP, PurchaseOrder, ChamberIncome,
                    PaymentPaypal)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = ('user', 'payment_id', 'creation_date', 'amount')


@admin.register(PaymentMP)
class PaymentMPAdmin(admin.ModelAdmin):

    list_display = ('user', 'payment_id', 'creation_date', 'transaction_amount')


@admin.register(PaymentPaypal)
class PaymentPaypalAdmin(admin.ModelAdmin):

    list_display = ('user', 'payment_id', 'creation_date', 'purchase_amount')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'created_at', 'quote', 'payment', 'price')


@admin.register(ChamberIncome)
class ChamberIncomeAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'chamber', 'cost', 'fee', 'fee_igv',
                    'payment_date', 'sale', 'status')
