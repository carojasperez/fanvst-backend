'''
Serializer for Location and Locality Models
'''
from rest_framework import serializers
from adminsite.userinfo.models import BankAccount, Genre, Notification, Profile, UserDevice
from adminsite.baseinfo.serializers import BankSer, DistrictSer, MembershipSer, SubCategorySer
from django.contrib.auth.models import User
from django.utils import timezone


def _img_url(image_field):
    try:
        return image_field.url
    except Exception:
        return ''


class UserSer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'full_name', 'username', 'email')

    def get_full_name(self, obj):
        return '{} {}'.format(obj.first_name, obj.last_name)


class PublicUserSer(serializers.ModelSerializer):
    '''
    No se muestra info privada como el correo electronico.
    '''

    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class UserProfileSer(serializers.ModelSerializer):
    user = UserSer(many=False)
    birthday_text = serializers.DateField(format="%d-%m-%Y", read_only=True,
                                          source='birthday')
    province_text = serializers.CharField(read_only=True, source='province')
    department_text = serializers.CharField(read_only=True, source='department')
    document_type_text = serializers.CharField(source='get_document_type_display')

    class Meta:
        model = Profile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'picture')

    def update(self, instance, validated_data):
        # Permite actualizar modelo relacionado User
        nested_serializer = self.fields['user']
        nested_instance = instance.user
        nested_data = validated_data.pop('user')
        nested_serializer.update(nested_instance, nested_data)
        return super(UserProfileSer, self).update(instance, validated_data)


class UserProfilePictureSer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ('picture',)


class PublicUserProfileSer(serializers.ModelSerializer):
    user = PublicUserSer(many=False)
    gender_text = serializers.CharField(source='get_gender_display')
    countrytxt = serializers.CharField(source='country')
    thumbnail = serializers.SerializerMethodField(read_only=True)
    user_since = serializers.DateTimeField(format="%Y/%m", read_only=True,
                                           source='user.profile.created_at')

    class Meta:
        model = Profile
        fields = ('user', 'gender', 'gender_text', 'countrytxt',
                   'thumbnail', 'user_since')

    def get_thumbnail(self, pfl):
        return _img_url(pfl.picture)
    
    def get_countrytxt(self, pfl):
        try:
            return pfl.country.name
        except Exception:
            return ''


class PubUserProfileSer(serializers.ModelSerializer):
    '''
    Modelo enfocado en SVC internacionales
    '''
    user = PublicUserSer(many=False)
    countrytxt = serializers.CharField(source='country')
    thumbnail = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = ('user', 'thumbnail', 'countrytxt')

    def get_thumbnail(self, pfl):
        return _img_url(pfl.picture)

    def get_countrytxt(self, pfl):
        try:
            return pfl.country.name
        except Exception:
            return ''


class PrivateUserProfileSer(serializers.ModelSerializer):
    '''
    Expone información sensible del usuario, solo debe usarse en vistas
    accesibles solo por el.
    '''
    username = serializers.CharField(source='user.username')
    countrytxt = serializers.CharField(source='country')

    class Meta:
        model = Profile
        fields = ('address1', 'countrytxt', 'city', 'state', 'phone1',
                  'username')

    def get_countrytxt(self, pfl):
        try:
            return pfl.country.name
        except Exception:
            return ''


class UserDeviceSer(serializers.ModelSerializer):
    user = UserSer(many=False, read_only=True)

    class Meta:
        model = UserDevice
        fields = ('user', 'device_info', 'device_token')


class BankAccountSer(serializers.ModelSerializer):
    bank_text = BankSer(read_only=True, source="bank")

    class Meta:
        model = BankAccount
        read_only_fields = ('user', 'created_at', 'updated_at')
        fields = ('bank', 'bank_text', 'account_type', 'account_number',
                  'cci_number', 'paypal')


class NotificationSer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = ('user',)


class GenreSer(serializers.ModelSerializer):
    '''Serializer público para géneros musicales.'''

    class Meta:
        model = Genre
        fields = ('id', 'name', 'slug')


class ArtistPublicSer(serializers.ModelSerializer):
    '''
    Serializer público para el perfil de artista.
    Expone sólo la información visible en la tarjeta y página de artista.
    '''
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    genres = GenreSer(many=True, read_only=True)
    followers_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()
    picture_url = serializers.SerializerMethodField()
    cover_picture_url = serializers.SerializerMethodField()
    artist_type_text = serializers.CharField(
        source='get_artist_type_display', read_only=True)

    class Meta:
        model = Profile
        fields = (
            'uuid', 'first_name', 'last_name', 'stage_name', 'bio',
            'picture_url', 'cover_picture_url', 'artist_type',
            'artist_type_text', 'location_display', 'verified',
            'genres', 'followers_count', 'is_following',
        )

    def get_followers_count(self, obj):
        return obj.followers.count()

    def get_is_following(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False

    def get_picture_url(self, obj):
        if obj.picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.picture.url)
            return obj.picture.url
        return ''

    def get_cover_picture_url(self, obj):
        if obj.cover_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.cover_picture.url)
            return obj.cover_picture.url
        return ''
