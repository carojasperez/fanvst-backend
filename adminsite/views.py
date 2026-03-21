from django.shortcuts import render
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth.decorators import login_required
from rest_framework import permissions
from .serializers import ChangePasswordSerializer
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import Group, User
from rest_framework.response import Response
from rest_framework import views
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import UserRegSer
def get_thumbnailer_url(image_field):
    try:
        return image_field.url
    except Exception:
        return ''
from adminsite.userinfo.models import EmailPasswordReset, EmailValidation, Profile, SocialAuth
from rest_framework.generics import CreateAPIView
from datetime import date, datetime, timedelta
from django.http import Http404, JsonResponse
from adminsite.tasks import email_notification_msg_norul, email_password_reset, email_validation
import requests
import requests
from adminsite.functions import get_paypal_token, validate_recaptcha
import secrets
import pytz
from adminsite.serializers import ChangePasswordEmailSerializer
from django.conf import settings


# Google ID token validation (requiere: pip install google-auth)
try:
    from google.oauth2 import id_token as google_id_token
    from google.auth.transport import requests as google_requests
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False


class LoginAuthToken(ObtainAuthToken):
    '''
    Permite obtener un Token para el Login desde aplicaciones Moviles
    '''
    def post(self, request, *args, **kwargs):
        response = super(
            LoginAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])

        userId = User.objects.get(id=token.user_id)
        print(userId.profile.email_confirmed)
        # En el caso de que el email no este confirmado no puede Login
        if userId.profile.email_confirmed == False:
            return Response(
                {"email_no_validated": ["Debe validar su correo."]},
                status=status.HTTP_401_UNAUTHORIZED)
        pfl = Profile.objects.get(user=userId)
        pic = get_thumbnailer_url(pfl.picture)
        # Token se envía como cookie HttpOnly (no en el body)
        resp = Response({'username': userId.username,
                         'first_name': userId.first_name,
                         'last_name': userId.last_name, 'id': userId.id,
                         'is_artist': pfl.is_artist,
                         'uuid': str(pfl.uuid),
                         'picture': pic
                         })
        resp.set_cookie(
            'auth_token',
            token.key,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Strict',
            max_age=30 * 24 * 60 * 60,  # 30 días
            path='/',
        )
        return resp


class LogoutView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        resp = Response({'detail': 'Sesión cerrada.'})
        resp.delete_cookie('auth_token', path='/')
        return resp

class SocialLoginAuth(views.APIView):
    permission_classes = [permissions.AllowAny] # Or anon users can't register
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        isNewUser = request.data.get('isNewUser', None)
        email = request.data.get('email', None)
        providerID = request.data.get('providerID', None)
        userID = request.data.get('userID', None)
        first_name = request.data.get('first_name', None)
        last_name = request.data.get('last_name', None)
        picture = request.data.get('picture', None)
        idToken = request.data.get('idToken', None)
        accessToken = request.data.get('accessToken', None)
        uid = request.data.get('uid', None)

        # Validar Google ID token si está disponible google-auth
        if providerID == 'google.com' and idToken and GOOGLE_AUTH_AVAILABLE:
            google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', None)
            if google_client_id:
                try:
                    info = google_id_token.verify_oauth2_token(
                        idToken, google_requests.Request(), google_client_id)
                    # Usar datos verificados por Google (más seguro)
                    email = info.get('email', email)
                    uid = info.get('sub', uid)
                    first_name = info.get('given_name', first_name)
                    last_name = info.get('family_name', last_name)
                    picture = info.get('picture', picture)
                except ValueError:
                    return Response({'error': 'Token de Google inválido'},
                                    status=status.HTTP_400_BAD_REQUEST)

        options = {'size': (150, 150), 'crop': True} # Profile img size

        try: # Usuario ya posee una cuenta, se le entrega el token de DRF
            user = SocialAuth.objects.get(uid=uid)

            token, created =  Token.objects.get_or_create(user=user.user)
            pfl = Profile.objects.get(user=user.user)
            pic = get_thumbnailer_url(pfl.picture)
            resp = Response(data={'username': user.user.username,
                         'first_name': user.user.first_name,
                         'last_name': user.user.last_name, 'id': user.user.id,
                         'is_artist': pfl.is_artist,
                         'uuid': str(pfl.uuid),
                         'picture': pic})
            resp.set_cookie('auth_token', token.key, httponly=True,
                            secure=not settings.DEBUG, samesite='Strict',
                            max_age=30 * 24 * 60 * 60, path='/')
            return resp
 
        except SocialAuth.DoesNotExist: # Nuevo usuario, se crea cuenta local

            # Se valida que el correo de la red social no este registrado
            try:
                User.objects.get(username=email)
                # Dado que es el mismo correo de su usuario local se aborta
                return Response({"email_exists": ["El correo ya existe"]}, 
                                status=status.HTTP_400_BAD_REQUEST)
            
            except User.DoesNotExist: # No existe, se crea su usuario local

                password = secrets.token_hex(20) # Se crea un password aleatorio
                # Creación del usuario Local
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password
                )
                
                # Creación de los datos relevantes a Social Auth
                sa = SocialAuth.objects.create(
                    user=user,
                    provider_id=providerID,
                    social_id=userID,
                    id_token=idToken,
                    access_token=accessToken,
                    picture=picture,
                    uid=uid
                )

                # Se agrega el usuario al grupo de permisos generales
                general = Group.objects.get(name='general') 
                general.user_set.add(user)

                # Obtenemos el token del usuario
                token, created =  Token.objects.get_or_create(user=user)
                pfl = Profile.objects.get(user=user)

                pfl.email_confirmed=True # Marcamos el email como confirmado
                pfl.save()

                pic = get_thumbnailer_url(pfl.picture)
                resp = Response(data={'username': user.username,
                            'first_name': user.first_name,
                            'last_name': user.last_name, 'id': user.id,
                            'is_artist': pfl.is_artist,
                            'uuid': str(pfl.uuid),
                            'picture': pic})
                resp.set_cookie('auth_token', token.key, httponly=True,
                                secure=not settings.DEBUG, samesite='Strict',
                                max_age=30 * 24 * 60 * 60, path='/')
                return resp


class UpdatePassword(views.APIView):
    '''
    An endpoint for changing password.
    Esto funciona desde el panel administrativo del usuario, por ello debe
    estar autenticado.
    '''
    permission_classes = [IsAuthenticated]
    http_method_names = ['put']

    def get_object(self, queryset=None):
        return self.request.user

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            old_password = serializer.data.get("old_password")
            if not self.object.check_password(old_password):
                return Response({"old_password": ["Wrong password."]}, 
                                status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            Token.objects.filter(user=self.request.user).delete()
            Token.objects.create(user=self.request.user)
            email_notification_msg_norul.delay(
                    self.request.user.username, self.request.user.first_name,
                    "Tu contraseña ha sido actualizada",
                    "Notificación actualización de contraseña",
                    "Le informamos que su contraseña fue actualizada de forma exitosa"
                    )
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateUserView(CreateAPIView):
    model = User
    permission_classes = [permissions.AllowAny] # Or anon users can't register
    http_method_names = ['post']
    serializer_class = UserRegSer


class CheckUserExists(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        username = self.request.query_params.get('username', None)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # return false as user does not exist
            return Response(data={'message':False})
        else:
            # Otherwise, return True
            return Response(data={'message':True})


class ValidateEmail(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        uuid1 = self.request.query_params.get('uuid1', None)
        uuid2 = self.request.query_params.get('uuid2', None)

        try:
            evalidation = EmailValidation.objects.get(
                uuid1=uuid1,
                uuid2=uuid2,
                used=False
                )
        except EmailValidation.DoesNotExist:
            # return false as uuid does not exist
            return Response(data={'message':False})
        else:
            Profile.objects.filter(
                user=evalidation.user
            ).update(email_confirmed=True)
            # Se marca como usado el Token
            EmailValidation.objects.filter(
                id=evalidation.id
            ).update(used=True)
            # Otherwise, return True
            return Response(data={'message':True})


class PassWordResetEmail(views.APIView):
    '''
    Este API genera el correo para que el usuario pueda restaurar su contraseña
    '''
    http_method_names = ['post']
    permission_classes = [permissions.AllowAny] # Or anon users can't use

    def post(self, request, *args, **kwargs):
        eaddress = request.data.get('eaddress', None) 
        gtoken = request.data.get('gtoken', None)

        # Se valida el Captcha de Google.
        valid = validate_recaptcha(gtoken)
        if valid==False or gtoken is None:
            return Response({"recaptcha": ["Recaptcha Invalido"]}, 
                status=status.HTTP_400_BAD_REQUEST)
        
        # Se procede a buscar el correo en la BD de Usuarios.
        try:
            userValid = User.objects.get(username=eaddress)
        except User.DoesNotExist:
            # User Not Found. Se responde como correo enviado.
            return Response({"corrrecto": ["Correo enviado"]}, 
                status=status.HTTP_200_OK)
        # Se generan los token y se guardan en la BD.
        token1 = secrets.token_urlsafe(100)
        token2 = secrets.token_urlsafe(100)
        
        # Expira a 15min desde hora actual.
        xdate = datetime.now(pytz.utc) + timedelta(minutes=15)

        EmailPasswordReset.objects.create(
            expire_at=xdate,
            user=userValid,
            token1=token1,
            token2=token2
        )
        # Se envia el correo al usuario.
        email_password_reset.delay(
            token1, token2, userValid.username, userValid.first_name)

        return Response({"corrrecto": ["Correo enviado"]}, 
            status=status.HTTP_200_OK)


class ValidateEmailToken(views.APIView):
    '''
    Este API valida que el Token suministrado por el usuario para restablecer
    su contraseña sea un Token valido, que este vigente (15 min de vida)
    Ademas de que comprueba a que usuario le pertenece
    '''
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        token1 = self.request.query_params.get('token1', None)
        token2 = self.request.query_params.get('token2', None)

        try:
            tokenValid = EmailPasswordReset.objects.get(
                expire_at__gt=datetime.now(pytz.utc),
                token1=token1,
                token2=token2,
                used=False
                )
        except EmailPasswordReset.DoesNotExist:
            # return false as token does not exist
            return Response(data={'message':False})
        else:
            # Otherwise, return True
            return Response(data={'message':True})


class ChangePasswordFromEmail(views.APIView):
    '''
    Este api permite al usuario modificar su contraseña a partir de un link
    seguro. Este API depende de los APIs
    views.ValidateEmailToken
    views.PassWordResetEmail
    '''
    permission_classes = [permissions.AllowAny]
    http_method_names = ['put']

    # def get_object(self, queryset=None):
    #     return self.request.user

    def put(self, request, *args, **kwargs):
        # self.object = self.get_object()
        serializer = ChangePasswordEmailSerializer(data=request.data)

        if serializer.is_valid():
            password = serializer.data.get("password")
            token1 = serializer.data.get("token1")
            token2 = serializer.data.get("token2")
            # Check token
            try:
                tokenValid = EmailPasswordReset.objects.get(
                    expire_at__gt=datetime.now(pytz.utc),
                    token1=token1,
                    token2=token2,
                    used=False
                    )
            except EmailPasswordReset.DoesNotExist:
            # return false as token does not exist or expired
                return Response({"token": ["Wrong Token or expired."]}, 
                                status=status.HTTP_400_BAD_REQUEST)
            # End Check Token
            else:
                # Mark Token as Used
                EmailPasswordReset.objects.filter(
                    id=tokenValid.id).update(used=True)

                # Get the current User
                userID = User.objects.get(id=tokenValid.user.id)

                # set_password also hashes the password that the user will get
                userID.set_password(password)
                userID.save()
                # Se regenera el Token de sesión
                Token.objects.filter(user=tokenValid.user).delete()
                Token.objects.create(user=tokenValid.user)
                # Se notifica el cambio de contraseña al correo.
                email_notification_msg_norul.delay(
                    tokenValid.user.username, tokenValid.user.first_name,
                    "Tu contraseña ha sido actualizada",
                    "Notificación actualización de contraseña",
                    "Le informamos que su contraseña fue actualizada de forma exitosa"
                    )
                # Se responde exitosamente
                return Response({"corrrecto": ["Correo enviado"]}, 
                    status=status.HTTP_200_OK)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendValidationEmail(views.APIView):
    http_method_names = ['post']
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        eaddress = request.data.get('eaddress', None)

        email_val = (
            EmailValidation.objects
            .filter(user__username=eaddress, used=False)
            .order_by('-id')
            .first()
        )

        if email_val:
            email_validation.delay(
                    str(email_val.uuid1) + '/' + str(email_val.uuid2),
                    # username, firstName
                    email_val.user.username,
                    email_val.user.first_name
                    )

        return Response({"corrrecto": ["Correo enviado"]}, 
            status=status.HTTP_200_OK)

