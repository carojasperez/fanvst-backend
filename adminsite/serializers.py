'''
Serializer for Location and Locality Models
'''
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
import django.contrib.auth.password_validation as validators
import threading
from adminsite.functions import validate_recaptcha
from adminsite.tasks import email_validation
from adminsite.userinfo.models import EmailValidation


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validators.validate_password(value)
        return value


class ChangePasswordEmailSerializer(serializers.Serializer):
    """
    Serializer for password change endpoint.
    Este funciona por medio del link de recuperar contraseña
    """
    password = serializers.CharField(required=True)
    token1 = serializers.CharField(required=True)
    token2 = serializers.CharField(required=True)


ACCOUNT_TYPE_CHOICES = (('fan', 'Fan'), ('artist', 'Artista'))


class UserRegSer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    gtoken = serializers.CharField(write_only=True)
    account_type = serializers.ChoiceField(
        choices=ACCOUNT_TYPE_CHOICES, write_only=True, default='fan'
    )

    def create(self, validated_data):
        from fanvst.models import ArtistProfile, FanProfile

        username = validated_data['username']
        firstName = validated_data['first_name']
        lastName = validated_data['last_name']
        gtoken = validated_data['gtoken']
        account_type = validated_data.get('account_type', 'fan')

        valid = validate_recaptcha(gtoken)
        if valid == False:
            raise serializers.ValidationError(
                {'recaptcha': "Recaptcha Invalido"}
            )
        user = User.objects.create(
            username=username,
            first_name=firstName,
            last_name=lastName,
            email=username
        )
        user.set_password(validated_data['password'])
        user.save()

        # Setear tipo de cuenta en Profile (creado por signal post_save)
        profile = user.profile
        if account_type == 'artist':
            profile.is_artist = True
            profile.save()
            ArtistProfile.objects.create(
                user=user,
                stage_name=firstName,
            )
        else:
            FanProfile.objects.create(user=user, public_alias=f"Fan {user.id}"[:50])

        email_val = EmailValidation.objects.create(user=user)

        email_validation.delay(
            str(email_val.uuid1) + '/' + str(email_val.uuid2),
            username, firstName
        )

        return user

    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "password", "gtoken", "account_type")



# class DateTimeLocalTimeZone(serializers.DateTimeField):
#     '''Solución al bug de timezone de django rest'''
#     def to_representation(self, value):
#         value = timezone.localtime(value)
#         return super(DateTimeLocalTimeZone, self).to_representation(value)


# class UserProfileSerializer(serializers.ModelSerializer):
#     user = UserSerializer(many=False, read_only=True)

#     class Meta:
#         model = Profile
#         fields = '__all__'
#         read_only_fields = ('admin', 'user', 'company')


# class UserDeviceSerializer(serializers.ModelSerializer):
#     user = UserSerializer(many=False, read_only=True)

#     class Meta:
#         model = UserDevice
#         fields = ('user', 'device_info', 'device_token')
