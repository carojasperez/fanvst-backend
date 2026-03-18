from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from .serializers import ComplaintBookSer
from legal.models import ComplaintBook
from rest_framework import permissions
from rest_framework import viewsets
from adminsite.tasks import complaint_book_email

# def complaint_book_email(toemail, name, title, subtitle, msg):

class CreateComplaintView(CreateAPIView):
    '''
    Efectua el registro en el libro de reclamaciones
    '''
    model = ComplaintBook
    permission_classes = [permissions.AllowAny] # Personas No registradas deben poder hacer el registro
    http_method_names = ['post']
    serializer_class = ComplaintBookSer

    def perform_create(self, serializer):
        complaint = serializer.save()
        complaint_book_email(complaint)


class ComplaintBookAPI(viewsets.ModelViewSet):
    '''
    Permite visualizar y gestionar las reclamaciones
    generadas desde el libro de reclamaciones
    '''
    http_method_names = ['get']
    permissions_classes = [permissions.IsAdminUser]
    serializer_class = ComplaintBookSer

    def get_queryset(self):
        qs = ComplaintBook.objects.all()
        return qs
