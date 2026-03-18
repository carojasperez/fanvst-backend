
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Tag, Post
from adminsite.userinfo.serializers import PublicUserSer


class TagSer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name')


class PostSer(serializers.ModelSerializer):
    tag = TagSer(read_only=True)
    author = PublicUserSer(read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'title', 'short_content', 'content', 'created_at',
                  'thumbnail', 'slug', 'views', 'tag', 'author', 'status')


class PostSmallSer(serializers.ModelSerializer):
    '''
    No incluye el campo Content por su peso
    '''
    tag = TagSer(read_only=True)
    author = PublicUserSer(read_only=True)
    created_at = serializers.DateTimeField(format="%d/%m/%Y %H:%M", read_only=True)

    class Meta:
        model = Post
        fields = ('id', 'title', 'short_content', 'created_at',
                  'thumbnail', 'slug', 'views', 'tag', 'author', 'status')
