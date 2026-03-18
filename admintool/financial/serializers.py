
from rest_framework import serializers
from django.contrib.auth.models import User
from payment.models import ChamberIncome, PaymentMP
from adminsite.userinfo.serializers import BankAccountSer, UserProfileSer, UserSer
from work.models import ContractedWork, Quote, WorkOffer
from adminsite.userinfo.models import Profile


class PaymentMPSer(serializers.ModelSerializer):

    class Meta:
        model = PaymentMP
        fields = ('fee_amount', 'last_four_digits')


class PedingPaymentSer(serializers.ModelSerializer):
    payment = PaymentMPSer(many=False, read_only=True, source="cw.po.payment")
    chamber = UserSer(many=False, read_only=True)
    profile = UserProfileSer(many=False, read_only=True, source="chamber.profile")
    bank = BankAccountSer(many=False, source="chamber.bankaccount")
    status = serializers.CharField(source='get_status_display',
                                       read_only=True)
    class Meta:
        model = ChamberIncome
        fields = ('id', 'chamber', 'status', 'cost', 'fee', 'fee_igv', 'sale',
                  'bank', 'created_at', 'payment', 'profile')


class OpenQuotesSer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = ('total', 'status')

    def get_total(self, obj):
        return obj['total']


class OpenWorksSer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = WorkOffer
        fields = ('total', 'status')

    def get_total(self, obj):
        return obj['total']


class CountChamberSer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ('total', 'is_chamber')

    def get_total(self, obj):
        return obj['total']


class CountContractedWorkSer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = ContractedWork
        fields = ('total', 'status')

    def get_total(self, obj):
        return obj['total']


class SalesPerMonthSer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()
    month = serializers.SerializerMethodField()

    class Meta:
        model = ChamberIncome
        fields = ('total', 'month')

    def get_total(self, obj):
        return obj['total']

    def get_month(self, obj):
        return obj['created_at__month']


