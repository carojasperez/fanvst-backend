from rest_framework import serializers
from .models import Svc, SvcImage
from adminsite.userinfo.serializers import PubUserProfileSer, PublicUserSer
from svc.models import SvcInclude, SvcOpt


class SvcImageSer(serializers.ModelSerializer):
    
    class Meta:
        model = SvcImage
        fields = ('picture', 'id')


class PublicSvcSer(serializers.ModelSerializer):
    user = PublicUserSer(many=False)
    price_from = serializers.IntegerField()
    profile = PubUserProfileSer(read_only=True, source="user.profile")
    svcimage = SvcImageSer(many=True)
    user_since = serializers.DateTimeField(format="%Y/%m", read_only=True,
                                           source='user.profile.created_at')

    class Meta:
        model = Svc
        fields = ('id', 'user', 'profile', 'svcimage',
                  'user_since', 'price_from', 'title', 'description', 'uuid')


class SvcIncludeSer(serializers.ModelSerializer):
    
    class Meta:
        model = SvcInclude
        fields = ('id', 'name')


class SvcOptSer(serializers.ModelSerializer):
    includes = SvcIncludeSer(many=True, read_only=True)

    class Meta:
        model = SvcOpt
        fields = '__all__'
        read_only_fields = ('svc', 'user')


class SvcSer(serializers.ModelSerializer):
    user = PublicUserSer(many=False)
    price_from = serializers.IntegerField()
    profile = PubUserProfileSer(read_only=True, source="user.profile")
    svcimage = SvcImageSer(many=True)
    svcopt = SvcOptSer(many=True)
    subcategory_text = serializers.CharField(source='sub_category.name',
                                             read_only=True)
    user_since = serializers.DateTimeField(format="%Y/%m", read_only=True,
                                           source='user.profile.created_at')

    class Meta:
        model = Svc
        fields = ('id', 'created_at', 'user', 'profile', 'svcimage',
                  'user_since', 'price_from', 'title', 'description', 'uuid',
                  'is_active', 'sub_category', 'subcategory_text', 'svcopt',
                  'is_published')


class ChamberSvcSer(serializers.ModelSerializer):

    class Meta:
        model = Svc
        fields = '__all__'
        read_only_fields = ['is_published']
        extra_kwargs = {'user': {'required': False}}



class SvcOptDetailSer(serializers.ModelSerializer):
    user = PublicUserSer(many=False)
    profile = PubUserProfileSer(read_only=True, source="user.profile")
    title = serializers.CharField(source="svc.title")
    # svcimage = PublicSvcSer(many=True, source="svc.scvimage")
    svcimage = SvcImageSer(many=True, source="svc.svcimage")
    includes = SvcIncludeSer(many=True)
    user_since = serializers.DateTimeField(format="%Y/%m", read_only=True,
                                           source='user.profile.created_at')

    class Meta:
        model = SvcOpt
        fields = ('user', 'title', 'profile', 'user_since', 'svcimage', 'level',
                  'sale', 'includes', 'required_days', 'revision')


class ChamberSvcImageSer(serializers.ModelSerializer):
    
    class Meta:
        model = SvcImage
        fields = ('picture',)