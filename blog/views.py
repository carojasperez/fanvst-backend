from django.shortcuts import render
from rest_framework import permissions
from rest_framework import viewsets
from .serializers import PostSer
from .models import Post
from adminsite.functions import MediumPagination
from django.db.models import F
from blog.serializers import PostSmallSer


class PostAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MediumPagination
    serializer_class = PostSmallSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve todos los Posts
        '''
        qs = Post.objects.filter(
            status=1
        )
        return qs


class PostDetailAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = PostSer
    http_method_names = ['get']

    def get_queryset(self):
        '''
        Devuelve el post consultado y agrega una vista al contador
        '''
        slug = self.request.query_params.get('slug', None)

        qs = Post.objects.filter(
            slug=slug,
            status=1
        )
        #  Se aumenta contador de vistas.
        qs.update(views=F('views')+1)

        return qs


class BlogAdminAPI(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    pagination_class = MediumPagination
    serializer_class = PostSer
    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        '''
        Devuelve el post consultado y agrega una vista al contador
        '''
        slug = self.request.query_params.get('slug', None)

        qs = Post.objects.all()

        if slug is not None:
            qs = qs.filter(slug=slug)

        return qs

    def perform_create(self, serializer):
        '''
        Permite guardar un registro academico al usuiario logueado
        '''
        serializer.save(author=self.request.user)


