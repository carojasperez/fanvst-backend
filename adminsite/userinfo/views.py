from django.conf import settings
from rest_framework import viewsets, views
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import User, Group
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from rest_framework import permissions
from adminsite.functions import MediumPagination, StandardPagination
from .serializers import (UserProfileSer, UserDeviceSer, ProfessionalSer,
                          AcademicSer, WorkExperienceSer, SkillSer,
                          BankAccountSer, PublicUserProfileSer,
                          ChamberMembershipSer, UserProfilePictureSer,
                          NotificationSer, ArtistPublicSer, GenreSer)
from .models import (UserDevice, Profile, Professional, Academic, Skill,
                     WorkExperience, BankAccount, ChamberMembership,
                     MembershipUserPromo, ProfessionalLike, Notification,
                     Genre)
from rest_framework import status
from adminsite.baseinfo.models import MembershipPromoCode, SubCategory
from django.contrib.postgres.search import SearchVector, SearchQuery
from datetime import datetime, timedelta
import pytz
from django.db import IntegrityError
from dateutil.relativedelta import relativedelta
from adminsite.userinfo.serializers import ChamberLikeCountSer
from adminsite.tasks import email_becomechamber


class UserDeviceAPI(viewsets.ModelViewSet):
    '''API - UserDevice registra el token del usuario'''
    serializer_class = UserDeviceSer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
        Regresa lista de dispositivos del usuario
        """
        query_set = UserDevice.objects.filter(user=self.request.user)

        return query_set  # .order_by('-created_at')

    def perform_create(self, serializer):
        '''
        Save the Company and User of the Logged User.
        '''
        serializer.save(user=self.request.user)


class UserProfileAPI(viewsets.ModelViewSet):
    '''API User Profile'''
    serializer_class = UserProfileSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Profile.objects.filter(user=self.request.user)

        return query_set

    def patch(self, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH
        '''
        query_set = Profile.objects.filter(user=self.request.user).first()
        serializer = UserProfileSer(query_set, data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPicture(viewsets.ModelViewSet):
    serializer_class = UserProfilePictureSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Profile.objects.all() # filter(user=self.request.user)
        return query_set

    def patch(self, request):
        try:
            file = request.data['picture']
        except KeyError:
            raise serializers.ValidationError(
                {'error': "Debe suministrar una imagen"})
        query_set = Profile.objects.filter(
            user=self.request.user).first()
        serializer = UserProfilePictureSer(query_set, data=request.data, partial=True)
        if serializer.is_valid():
                serializer.save(picture=file)
                return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BecomeChamberAPI(viewsets.ModelViewSet):
    '''API que permite al usuario convertirse en Chamber'''
    serializer_class = UserProfileSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Profile.objects.filter(user=self.request.user)

        return query_set

    def patch(self, request):
        '''
        Actualiza el perfil del usuario para convertirlo en Chamber
        '''
        query_set = Profile.objects.filter(user=self.request.user).first()
        serializer = UserProfileSer(query_set, data=request.data,
                                           partial=True)
        user = self.request.user
        if serializer.is_valid():
            serializer.save()
            # Se incluye al usuario en el grupo de permisos de Chamber
            general = Group.objects.get(name='chamber') 
            general.user_set.add(user)
            # Envia correo de notificación de registro de Chamber
            email_becomechamber.delay(user.username, user.first_name)
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfessionalAPI(viewsets.ModelViewSet):
    '''API User Profile'''
    serializer_class = ProfessionalSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Professional.objects.filter(user=self.request.user)
        return query_set
    
    def patch(self, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH
        '''
        query_set = Professional.objects.filter(user=self.request.user).first()
        serializer = ProfessionalSer(query_set, data=request.data,
                                     partial=True)
        qt = self.request.data["categories"]
        if serializer.is_valid():
            pk = serializer.save(user=self.request.user)
            obj = Professional.objects.get(id=pk.id)
            # Se eliminan las categorias anteriores
            obj.category.clear()
            # Se registran las categorias
            for q in qt:
                obj.category.add(q['id'])
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetProfessionalAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicUserProfileSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']
    '''
    Se separa en 2 Views dado que el otro tiene capacidad de edición
    Por seguridad el API de edición solo permite editar AL MISMO usuario,
    este API puede consultar la info de cualquier usuario, por lo que
    para reducir riesgo de ediciones no autorizadas se separa
    '''
    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        '''Filtra según el ID especificado'''
        try:
            prf = Professional.objects.get(uuid=uuid)
        except Professional.DoesNotExist:
            raise Http404
        query_set = Profile.objects.filter(
            user=prf.user,
            user__is_active=True
            )

        return query_set


class AcademicAPI(viewsets.ModelViewSet):
    '''API Academy Info'''
    serializer_class = AcademicSer
    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Academic.objects.filter(user=self.request.user)

        return query_set
   
    def patch(self, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH. Y queremos que solo
        se pueda editar la info del usuario logueado
        '''
        pk = self.request.data["id"]
        query_set = Academic.objects.filter(
            user=self.request.user,
            id=pk
        ).first()
        serializer = AcademicSer(query_set, data=request.data,
                                 partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        '''
        Permite guardar un registro academico al usuiario logueado
        '''
        serializer.save(user=self.request.user)
    
    def destroy(self, request, pk, format=None):
        try:
            record = Academic.objects.get(
                id=pk,
                user=self.request.user
            )
        except Academic.DoesNotExist:
            raise Http404
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetAcademyAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = AcademicSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']
    '''
    Se separa en 2 Views dado que el otro tiene capacidad de edición
    Por seguridad el API de edición solo permite editar AL MISMO usuario,
    este API puede consultar la info de cualquier usuario, por lo que
    para reducir riesgo de ediciones no autorizadas se separa
    '''
    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        '''Filtra según el ID especificado'''
        try:
            userid = Professional.objects.get(uuid=uuid)
        except Professional.DoesNotExist:
            raise Http404
        query_set = Academic.objects.filter(
            user=userid.user
            )

        return query_set


class WorkExpAPI(viewsets.ModelViewSet):
    '''API Work Experience Info'''
    serializer_class = WorkExperienceSer
    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = WorkExperience.objects.filter(user=self.request.user)

        return query_set
   
    def patch(self, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH. Y queremos que solo
        se pueda editar la info del usuario logueado
        '''
        pk = self.request.data["id"]

        query_set = WorkExperience.objects.filter(
            user=self.request.user,
            id=pk
        ).first()
        serializer = WorkExperienceSer(query_set, data=request.data,
                                       partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        '''
        Permite guardar un registro academico al usuiario logueado
        '''
        serializer.save(user=self.request.user)
    
    def destroy(self, request, pk, format=None):
        try:
            arecord = WorkExperience.objects.get(
                id=pk,
                user=self.request.user
            )
        except WorkExperience.DoesNotExist:
            raise Http404
        arecord.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetWorkExpAPI(viewsets.ModelViewSet):
    serializer_class = WorkExperienceSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']
    '''
    Se separa en 2 Views dado que el otro tiene capacidad de edición
    Por seguridad el API de edición solo permite editar AL MISMO usuario,
    este API puede consultar la info de cualquier usuario, por lo que
    para reducir riesgo de ediciones no autorizadas se separa
    '''
    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        '''Filtra según el ID especificado'''
        try:
            userid = Professional.objects.get(uuid=uuid)
        except Professional.DoesNotExist:
            raise Http404
        query_set = WorkExperience.objects.filter(
            user=userid.user
            )

        return query_set


class SkillAPI(viewsets.ModelViewSet):
    '''API Skill - Habilidades que declara el chamber tener'''
    serializer_class = SkillSer
    http_method_names = ['get', 'patch', 'post', 'delete']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Skill.objects.filter(user=self.request.user)

        return query_set
   
    def patch(self, pk, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH. Y queremos que solo
        se pueda editar la info del usuario logueado
        '''
        query_set = Skill.objects.filter(
            user=self.request.user,
            id=pk
        ).first()
        serializer = SkillSer(query_set, data=request.data,
                                       partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        '''
        Permite guardar un registro de Skill
        '''
        serializer.save(user=self.request.user)
    
    def destroy(self, request, pk, format=None):
        try:
            arecord = Skill.objects.get(
                id=pk,
                user=self.request.user
            )
        except Skill.DoesNotExist:
            raise Http404
        arecord.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetSkillAPI(viewsets.ReadOnlyModelViewSet):
    serializer_class = SkillSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']
    '''
    Se separa en 2 Views dado que el otro tiene capacidad de edición
    Por seguridad el API de edición solo permite editar AL MISMO usuario,
    este API puede consultar la info de cualquier usuario, por lo que
    para reducir riesgo de ediciones no autorizadas se separa
    '''
    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        '''Filtra según el ID especificado'''
        try:
            userid = Professional.objects.get(uuid=uuid)
        except Professional.DoesNotExist:
            raise Http404
        query_set = Skill.objects.filter(
            user=userid.user
            )

        return query_set


class BankAccountAPI(viewsets.ModelViewSet):
    '''API User Profile'''
    serializer_class = BankAccountSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = BankAccount.objects.filter(user=self.request.user)
        return query_set


    def patch(self, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH
        '''
        query_set = BankAccount.objects.filter(user=self.request.user).first()
        serializer = BankAccountSer(query_set, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetChamberList(viewsets.ModelViewSet):
    serializer_class = PublicUserProfileSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MediumPagination
    http_method_names = ['get']
    '''
    API - Obtiene un listado de los Chambers segun criterios de busqueda
    '''
    def get_queryset(self):
        '''
        Todos los filtros
        '''
        keywords = self.request.query_params.get('keywords', None)
        selectedCats = self.request.query_params.getlist('selectedCats', None)
        tarifRange = self.request.query_params.getlist('tarifRange', None)

        # Solo se muestran Chambers
        query_set = Profile.objects.filter(
            is_chamber=True,
            user__professional__isnull=False,
            user__is_active=True
        )
        # Si el usuario está logeado lo descartamos de la lista.
        if(self.request.user.is_authenticated):
            query_set = query_set.exclude(
                user=self.request.user
            )
        # Filtro por palabras
        if keywords is not None and keywords != '':
            # Agrega OR entre cada palabra para el formato de la busqueda
            keywords = keywords.lower().replace(" ", " OR ")

            query_set = query_set.filter(
                user__professional__category__keywords__search=SearchQuery(
                    keywords, search_type='websearch'
                    )).distinct()
        # Filtro de categorias
        if selectedCats is not None and selectedCats != []:
            query_set = query_set.filter(
                user__professional__category__in=selectedCats
            ).distinct()

        # Filtro por rango de tarifa
        if tarifRange is not None and tarifRange != []:
            query_set = query_set.filter(
                (Q(user__professional__tarif_from__gte=tarifRange[0]) &
                Q(user__professional__tarif_from__lte=tarifRange[1])) |
                (Q(user__professional__tarif_to__gte=tarifRange[0]) &
                Q(user__professional__tarif_to__lte=tarifRange[1]))
            )

        return query_set


class ChamberMembershipAPI(viewsets.ModelViewSet):
    serializer_class = ChamberMembershipSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve la membresía activa del Chamber
        '''
        query_set = ChamberMembership.objects.filter(
            user=self.request.user,
            is_active=True,
            )
        return query_set


class ChamberPromoCodeAPI(views.APIView):
    '''User Promo Code API'''
    http_method_names = ['post']

    def get_queryset(self):
        code = self.request.query_params.get('code', None)

        qs = ChamberMembership.objects.filter(
                user=self.request.user
            )

        return qs

    def post(self, serializer):
        '''
        Permite registrar la membresía del Chamber
        '''
        code = self.request.data.get('code', None)
        user = self.request.user

        try:
            promo = MembershipPromoCode.objects.get(
                code=code,
                valid_from__lte=datetime.now(pytz.utc),
                valid_to__gte=datetime.now(pytz.utc),
                is_active=True,
                for_chamber=True
            )
        except MembershipPromoCode.DoesNotExist:
            return Response({"code_invalid": ["El código suministrado no es valido."]}, 
                            status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Se registra el codigo de promoción como ya usado
            MembershipUserPromo.objects.create(
                user=user,
                promo=promo
            )

            # Se activa la membresía al usuario
            xdate = datetime.now(pytz.utc) + relativedelta(months=promo.months)

            ChamberMembership.objects.create(
                user=user,
                membership=promo.membership,
                from_date = datetime.now(),
                to_date = xdate
            )
        except IntegrityError:
            return Response({"code_used": ["El código suministrado ya ha sido utilizado."]}, 
                            status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"correcto": ["El código fue activado."]}, 
                        status=status.HTTP_200_OK)


class ChamberLikeAPI(views.APIView):
    '''
    API para dar like a los Chambers
    '''
    http_method_names = ['post']

    def get_queryset(self):
        qs = ProfessionalLike.objects.filter(
            user=self.request.user,
            is_active=True
        )

        return qs

    def post(self, serializer):
        '''
        Permite guardar un registro academico al usuiario logueado
        '''
        uuid = self.request.data.get('uuid', None)
        like = self.request.data.get('like', None)
        user = self.request.user

        try:
            like = ProfessionalLike.objects.get(
                user=user,
                chamber__professional__uuid=uuid
            )

            ProfessionalLike.objects.filter(id=like.id).update(
                is_active=not like.is_active
            )
            return Response({"correcto": ["Like actualizado."]}, 
                           status=status.HTTP_200_OK)
        except ProfessionalLike.DoesNotExist:
            chamber = Professional.objects.get(uuid=uuid)
            ProfessionalLike.objects.create(
                user=user,
                chamber=chamber.user
            )
            return Response({"correcto": ["Like enviado."]}, 
                            status=status.HTTP_200_OK)


class ChamberCountLikeAPI(viewsets.ModelViewSet):
    '''
    API para dar like a los Chambers
    '''
    serializer_class = ChamberLikeCountSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)

        qs = ProfessionalLike.objects.filter(
            chamber__professional__uuid=uuid,
            is_active=True
        ).values('chamber').annotate(total=Count('id')).order_by()

        return qs


class NotificationPreferenceAPI(viewsets.ModelViewSet):
    '''Preferencias de notificaciones de los usuarios'''
    serializer_class = NotificationSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = Notification.objects.filter(user=self.request.user)

        return query_set

    def patch(self, request):
        '''
        Actualiza las preferencias de notificación del usuario que efectua
        la solicitud
        '''
        query_set = Notification.objects.filter(
            user=self.request.user
        ).first()
        serializer = NotificationSer(query_set, data=request.data,
                                     partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ── Fanvst: Artistas y Géneros ─────────────────────────────────────────────────

class GenreListAPI(viewsets.ReadOnlyModelViewSet):
    '''Lista pública de géneros musicales disponibles en Fanvst.'''
    serializer_class = GenreSer
    permission_classes = [permissions.AllowAny]
    http_method_names = ['get']
    queryset = Genre.objects.all()


class ArtistListAPI(viewsets.ReadOnlyModelViewSet):
    '''
    Lista pública de artistas.
    Filtros disponibles via query params:
      - genre (slug del género)
      - search (texto libre sobre stage_name, first_name, last_name)
    '''
    serializer_class = ArtistPublicSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MediumPagination
    http_method_names = ['get']

    def get_queryset(self):
        genre_slug = self.request.query_params.get('genre', None)
        search = self.request.query_params.get('search', None)

        qs = Profile.objects.filter(
            is_artist=True,
            user__is_active=True,
        ).prefetch_related('genres', 'followers')

        if genre_slug:
            qs = qs.filter(genres__slug=genre_slug)

        if search:
            qs = qs.filter(
                Q(stage_name__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            ).distinct()

        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx


class ArtistDetailAPI(views.APIView):
    '''
    Devuelve el perfil público de un artista por su UUID.
    GET /api/artist/<uuid>/
    '''
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, uuid):
        try:
            profile = Profile.objects.prefetch_related(
                'genres', 'followers'
            ).get(uuid=uuid, is_artist=True, user__is_active=True)
        except Profile.DoesNotExist:
            return Response({'detail': 'No encontrado.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = ArtistPublicSer(profile, context={'request': request})
        return Response(serializer.data)


class FollowArtistAPI(views.APIView):
    '''
    Seguir / dejar de seguir a un artista.
    POST /api/artist/<uuid>/follow/
    El estado se alterna en cada llamada (toggle).
    Requiere autenticación.
    '''
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        try:
            profile = Profile.objects.get(
                uuid=uuid, is_artist=True, user__is_active=True)
        except Profile.DoesNotExist:
            return Response({'detail': 'No encontrado.'},
                            status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if profile.followers.filter(id=user.id).exists():
            profile.followers.remove(user)
            return Response({'following': False,
                             'followers_count': profile.followers.count()})
        else:
            profile.followers.add(user)
            return Response({'following': True,
                             'followers_count': profile.followers.count()})
