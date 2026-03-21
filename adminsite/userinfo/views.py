from django.conf import settings
from rest_framework import viewsets, views
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.contrib.auth.models import User, Group
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import CreateView, ListView, UpdateView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers, permissions, status
from adminsite.functions import MediumPagination, StandardPagination
from .serializers import (UserProfileSer, UserDeviceSer, BankAccountSer,
                          PublicUserProfileSer, UserProfilePictureSer,
                          NotificationSer, ArtistPublicSer, GenreSer)
from .models import (UserDevice, Profile, BankAccount, Notification, Genre)
from django.contrib.postgres.search import SearchVector, SearchQuery
from datetime import datetime, timedelta
import pytz
from django.db import IntegrityError
from dateutil.relativedelta import relativedelta


class UserDeviceAPI(viewsets.ModelViewSet):
    '''API - UserDevice registra el token del usuario'''
    serializer_class = UserDeviceSer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
        Regresa lista de dispositivos del usuario
        """
        query_set = UserDevice.objects.filter(user=self.request.user)
        return query_set

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserProfileAPI(viewsets.ModelViewSet):
    '''API User Profile'''
    serializer_class = UserProfileSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        query_set = Profile.objects.filter(user=self.request.user)
        return query_set

    def patch(self, request):
        query_set = Profile.objects.filter(user=self.request.user).first()
        serializer = UserProfileSer(query_set, data=request.data, partial=True)
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
        query_set = Profile.objects.all()
        return query_set

    def patch(self, request):
        try:
            file = request.data['picture']
        except KeyError:
            raise serializers.ValidationError({'error': "Debe suministrar una imagen"})
        query_set = Profile.objects.filter(user=self.request.user).first()
        serializer = UserProfilePictureSer(query_set, data=request.data, partial=True)
        if serializer.is_valid():
                serializer.save(picture=file)
                return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
             }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BankAccountAPI(viewsets.ModelViewSet):
    '''API User Profile'''
    serializer_class = BankAccountSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        query_set = BankAccount.objects.filter(user=self.request.user)
        return query_set

    def patch(self, request):
        query_set = BankAccount.objects.filter(user=self.request.user).first()
        serializer = BankAccountSer(query_set, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(user=self.request.user)
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class NotificationPreferenceAPI(viewsets.ModelViewSet):
    '''Preferencias de notificaciones de los usuarios'''
    serializer_class = NotificationSer
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        query_set = Notification.objects.filter(user=self.request.user)
        return query_set

    def patch(self, request):
        query_set = Notification.objects.filter(user=self.request.user).first()
        serializer = NotificationSer(query_set, data=request.data, partial=True)
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


class ArtistDetailAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, uuid):
        try:
            profile = Profile.objects.prefetch_related(
                'genres', 'followers'
            ).get(uuid=uuid, is_artist=True, user__is_active=True)
        except Profile.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ArtistPublicSer(profile, context={'request': request})
        return Response(serializer.data)


class FollowArtistAPI(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        try:
            profile = Profile.objects.get(uuid=uuid, is_artist=True, user__is_active=True)
        except Profile.DoesNotExist:
            return Response({'detail': 'No encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        if profile.followers.filter(id=user.id).exists():
            profile.followers.remove(user)
            return Response({'following': False, 'followers_count': profile.followers.count()})
        else:
            profile.followers.add(user)
            return Response({'following': True, 'followers_count': profile.followers.count()})
