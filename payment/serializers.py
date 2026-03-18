from rest_framework import serializers
from payment.models import ChamberIncome, PaymentMP, PaymentPaypal, PurchaseOrder
from adminsite.userinfo.serializers import PrivateUserProfileSer, ProfessionalSer, PublicUserSer, UserSer
from work.serializers import ContractedWorkSer


class PublicPaymentSer(serializers.ModelSerializer):
    '''
    Expone unicamente los datos que deben ver visibles por los usuarios
    '''

    class Meta:
        model = PaymentPaypal
        fields = ('payer_email_address')


class PurchaseOrderSer(serializers.ModelSerializer):
    profile = PrivateUserProfileSer(read_only=True, source="user.profile")
    chamber = ProfessionalSer(source='quote.chamber.professional', read_only=True)
    user = UserSer(read_only=True)
    payment = PublicPaymentSer(read_only=True)
    thumbnail = serializers.SerializerMethodField(read_only=True)
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')
    '''
    Serializer para el modelo Purchase Order
    '''
    class Meta:
        model = PurchaseOrder
        fields = '__all__'

    def get_thumbnail(self, qt):
        try:
            return qt.quote.chamber.profile.picture.url
        except Exception:
            return ''


class ChamberIncomeSer(serializers.ModelSerializer):

    status = serializers.CharField(source='get_status_display', read_only=True)
    status_id = serializers.CharField(source='status', read_only=True)
    payment_date_text = serializers.DateTimeField(
        format="%d/%m/%Y %H:%M", read_only=True, source='payment_date')
    cw = ContractedWorkSer(read_only=True)

    class Meta:
        model = ChamberIncome
        fields = '__all__'
