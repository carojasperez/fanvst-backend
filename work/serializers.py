'''
Serializer for Location and Locality Models
'''
from rest_framework import serializers
from .models import CancelReason, Quote, QuoteReply, DisputeReply
from adminsite.userinfo.serializers import ProfessionalSer, PublicUserProfileSer, PublicUserSer
from work.models import QuoteFile, CWMessage, CWReview, ContractedWork, Dispute, WorkOffer, WorkOfferCandidate
from adminsite.baseinfo.serializers import SubCategorySer
from adminsite.userinfo.serializers import PrivateUserProfileSer


class CancelReasonSer(serializers.ModelSerializer):

    class Meta:
        model = CancelReason
        fields = ('id', 'code', 'name')


class QuoteSer(serializers.ModelSerializer):

    user = PublicUserSer(read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    status_id = serializers.CharField(source='status', read_only=True)
    chamber = ProfessionalSer(source='chamber.professional', read_only=True)
    thumbnail = serializers.SerializerMethodField(read_only=True)
    userthumbnail = serializers.SerializerMethodField(read_only=True)
    user_since = serializers.DateTimeField(format="%Y/%m", read_only=True,
                                           source='user.profile.created_at')
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')
    # servicedate_text = serializers.DateField(format="%d/%m/%Y",
    #                                          read_only=True, source='service_date')
    time_text = serializers.TimeField(format="%H:%M",
                                      read_only=True, source='time')

    class Meta:
        model = Quote
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'created_by', 'chamber',
                            'status', 'delivery_date')

    def get_thumbnail(self, qt):
        try:
            return qt.chamber.profile.picture.url
        except Exception:
            return ''

    def get_userthumbnail(self, qt):
        try:
            return (
                qt.user.profile.picture
                ).url
        except Exception:
            return ''


class QuoteReplySer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')
    user = PublicUserSer(read_only=True)

    class Meta:
        model = QuoteReply
        fields = '__all__'

    def get_thumbnail(self, qt):
        try:
            return (
                qt.user.profile.picture
                ).url
        except Exception:
            return ''


class CancelQuoteSer(serializers.ModelSerializer):
    cancel_reason = serializers.CharField(max_length=3, required=True)

    class Meta:
        model = Quote
        fields = ('id', 'cancelled', 'cancel_reason', 'cancelled_date', 'status')
        read_only_fields = ['cancelled_date']

    def validate_cancel_reason(self, data):
        try:
            id = CancelReason.objects.get(
                code=data
                )

        except CancelReason.DoesNotExist:
            raise serializers.ValidationError(
                "Código de cancelación no valido")
        return id


class WorkOfferSer(serializers.ModelSerializer):
    user = PublicUserSer(read_only=True)
    status = serializers.CharField(source='get_status_display', read_only=True)
    status_id = serializers.CharField(source='status', read_only=True)
    owner = serializers.BooleanField(read_only=True)
    createdat_text = serializers.DateTimeField(
        format="%d/%m/%Y %H:%M", read_only=True, source='created_at')
    expire_date_text = serializers.DateField(
        format="%d/%m/%Y", read_only=True, source='expire_date')
    category_name = SubCategorySer(
        source='category', read_only=True, many=True)
    summary = serializers.SerializerMethodField() 

    def get_summary(self, obj):
        return obj.job_description[:200]

    class Meta:
        model = WorkOffer
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'created_by', 'summary',
                            'status')


class WorkOfferCandidateSer(serializers.ModelSerializer):
    chamber = ProfessionalSer(source='chamber.professional', read_only=True)
    countrytxt = serializers.CharField(source='chamber.profile.country', read_only=True)
    thumbnail = serializers.SerializerMethodField(read_only=True)
    createdat_text = serializers.DateTimeField(
        format="%d/%m/%Y %H:%M", read_only=True, source='created_at')

    class Meta:
        model = WorkOfferCandidate
        fields = '__all__'
        read_only_fields = ('chamber', 'work_offer', 'countrytxt', 'created_at',
                            'created_by', 'status')

    def get_thumbnail(self, wc):
        try:
            return (
                wc.chamber.profile.picture
                ).url
        except Exception:
            return ''

    def get_countrytxt(self, wc):
        try:
            return wc.country.name
        except Exception:
            return ''

class ContractedWorkSer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)
    status_id = serializers.CharField(source='status', read_only=True)
    quote = QuoteSer(read_only=True, source="po.quote")
    chamber = PrivateUserProfileSer(read_only=True, source="chamber.profile")

    class Meta:
        model = ContractedWork
        fields = '__all__'


class CWMessageSer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')
    user = PublicUserSer(read_only=True)

    class Meta:
        model = CWMessage
        fields = '__all__'

    def get_thumbnail(self, qt):
        try:
            return (
                qt.user.profile.picture
                ).url
        except Exception:
            return ''


class QuoteFileSer(serializers.ModelSerializer):
    filesize = serializers.CharField(source='file.size', read_only=True)

    class Meta:
        model = QuoteFile
        fields = ('file', 'filename', 'filesize')


class CWReviewSer(serializers.ModelSerializer):
    user = PublicUserSer(read_only=True)
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')

    class Meta:
        model = CWReview
        fields = '__all__'


class DisputeSer(serializers.ModelSerializer):
    status = serializers.CharField(source='get_status_display', read_only=True)
    status_id = serializers.CharField(source='status', read_only=True)
    cw = ContractedWorkSer(read_only=True)
    chamber = PrivateUserProfileSer(read_only=True, source="chamber.profile")
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')

    class Meta:
        model = Dispute
        fields = '__all__'


class DisputeReplySer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    createdat_text = serializers.DateTimeField(format="%d/%m/%Y %H:%M",
                                               read_only=True, source='created_at')
    user = PublicUserSer(read_only=True)

    class Meta:
        model = DisputeReply
        fields = '__all__'

    def get_thumbnail(self, qt):
        try:
            return (
                qt.user.profile.picture
                ).url
        except Exception:
            return ''
