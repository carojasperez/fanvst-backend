from django.contrib import admin
from .models import Post
from django import forms


class PostAdminForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea(attrs={'rows': 20, 'cols': 80}))
    class Meta:
        model = Post
        fields = ('content', 'short_content', 'title', 'slug', 'author',
                  'thumbnail', 'tag', 'views')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm

    list_display = ('id', 'created_at', 'title')
