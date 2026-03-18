from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import permissions, serializers, views
from adminsite.functions import SmallPagination, MediumPagination
from .serializers import PublicSvcSer
from .models import Svc, SvcOpt
from svc.serializers import ChamberSvcImageSer, ChamberSvcSer, SvcImageSer, SvcIncludeSer, SvcOptDetailSer, SvcOptSer, SvcSer
from django.db.models import Min, Sum
from rest_framework.response import Response
from svc.models import SvcImage, SvcInclude
from django.http import Http404
from rest_framework import status
from django.contrib.postgres.search import SearchQuery


class PublicSvcList(viewsets.ModelViewSet):
    '''
    API que muestra los SVC de todos los Chambers.
    '''
    serializer_class = PublicSvcSer
    pagination_class = SmallPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        En el caso de que se especifique un uuid se busca el svc en especifico
        Si se especifica un usruuid se busca los svcs del chamber
        '''
        uuid = self.request.query_params.get('uuid', None)
        usruuid = self.request.query_params.get('usruuid', None)
        homeview = self.request.query_params.get('homeview', None) # Home

        qs = Svc.objects.filter(
            is_active=True,
            is_published=True,
            user__is_active=True
            ).annotate(price_from=Min('svcopt__sale'))

        if uuid is not None:
            qs = qs.filter(uuid=uuid)

        if usruuid is not None:
            qs = qs.filter(
                user__professional__uuid=usruuid
                )

        if homeview is not None: # Aleatoriamente muestra algunos svs
            qs = qs[:4]

        return qs


class PublicSvcWall(viewsets.ModelViewSet):
    '''
    API que muestra los SVC de todos los Chambers.
    '''
    serializer_class = PublicSvcSer
    pagination_class = MediumPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get_queryset(self):
        '''
        En el caso de que se especifique un uuid se busca el svc en especifico
        Si se especifica un usruuid se busca los svcs del chamber
        '''
        keywords = self.request.query_params.get('keywords', None)
        selectedCat = self.request.query_params.get('selectedCats', None)

        qs = Svc.objects.filter(
            is_active=True,
            is_published=True,
            user__is_active=True
            ).annotate(price_from=Min('svcopt__sale'))

        # Filtro por palabras
        if keywords is not None and keywords != '':
            # Agrega OR entre cada palabra para el formato de la busqueda
            keywords = keywords.lower().replace(" ", " OR ")

            qs = qs.filter(
                title__search=SearchQuery(
                    keywords, search_type='websearch'
                    )).distinct()

        # Filtro de categorias
        if selectedCat is not None and selectedCat !='':
            qs = qs.filter(
                sub_category=selectedCat
            ).distinct()

        return qs


class PublicSvcOpt(viewsets.ModelViewSet):
    '''
    API que muestra los OPT del SVC.
    '''
    serializer_class = SvcOptSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    http_method_names = ['get']

    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        qs = SvcOpt.objects.filter(svc__uuid=uuid)

        return qs


class SvcOptDetail(viewsets.ModelViewSet):
    '''
    API que muestra un SVC + OPT en especifico.
    - Utilizado en formulario de pago de SVC
    '''
    serializer_class = SvcOptDetailSer
    http_method_names = ['get']

    def get_queryset(self):

        uuid = self.request.query_params.get('uuid', None)
        opt = self.request.query_params.get('opt', None)

        qs = SvcOpt.objects.filter(
            svc__is_active=True,
            svc__uuid=uuid,
            id=opt
            )

        return qs


class ChamberSvcList(viewsets.ModelViewSet):
    '''
    API que muestra los SVC del Chamber que efectua la consulta.
    '''
    serializer_class = SvcSer
    pagination_class = SmallPagination
    http_method_names = ['get']

    def get_queryset(self):
        uuid = self.request.query_params.get('uuid', None)
        user = self.request.user

        qs = Svc.objects.filter(
            is_active=True,
            user=user
            ).annotate(price_from=Min('svcopt__sale')).order_by('-id')

        if uuid is not None:
            qs = qs.filter(
            uuid=uuid
        )

        return qs


class ChamberSvc(viewsets.ModelViewSet):
    '''
    API para gestionar el SVC de un Chamber
    '''
    serializer_class = ChamberSvcSer
    http_method_names = ['post', 'patch']

    def get_queryset(self):
        """
        Regresa lista de svc del usuario
        """
        query_set = Svc.objects.filter(user=self.request.user)

        return query_set

    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def patch(self, pk, request):

        query_set = Svc.objects.filter(
            user=self.request.user,
            id=pk
        ).first()
        serializer = ChamberSvcSer(query_set, data=request.data,
                                   partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChamberSvcImage(viewsets.ModelViewSet):
    serializer_class = ChamberSvcImageSer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        query_set = SvcImage.objects.filter(user=self.request.user)
        return query_set

    def perform_create(self, serializer):
        user=self.request.user
        uuid = self.request.data['uuid']

        try:
            file = self.request.data['picture']
        except KeyError:
            raise serializers.ValidationError(
                {'error': "Debe suministrar una imagen"})
        svc = Svc.objects.get(uuid=uuid)

        if serializer.is_valid():
                serializer.save(picture=file, svc=svc, user=user)

    def destroy(self, request, pk, format=None):
        try:
            record = SvcImage.objects.get(
                id=pk,
                user=self.request.user
            )
        except SvcImage.DoesNotExist:
            raise Http404
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChamberSvcOpt(viewsets.ModelViewSet):
    serializer_class = SvcOptSer
    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        '''Filtra info del Chamber'''
        qs = SvcOpt.objects.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        uuid = self.request.data["uuid"]
        ic = self.request.data["icd"]
        user = self.request.user
        svc = Svc.objects.get(uuid=uuid)
        pk = serializer.save(
            user=user,
            svc=svc
            )
        obj = SvcOpt.objects.get(id=pk.id)
        for q in ic:
            obj.includes.add(q['id'])

    def patch(self, request):
        uuid = self.request.data["uuid"] # uuid del SVC
        ic = self.request.data["icd"]
        sId = self.request.data["id"]

        user = self.request.user

        query_set = SvcOpt.objects.filter(
            user=self.request.user,
            id=sId
        ).first()

        serializer = SvcOptSer(query_set, data=request.data,
                                   partial=True)

        if serializer.is_valid():
            pk = serializer.save()

            obj = SvcOpt.objects.get(id=pk.id)
            # Se eliminan los include anteriores
            obj.includes.clear()

            for q in ic:
                obj.includes.add(q['id'])
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SvcIncludeList(viewsets.ModelViewSet):
    serializer_class = SvcIncludeSer
    http_method_names = ['get']

    def get_queryset(self):
        '''Filtra el listado según la categoría consultada'''
        cat = self.request.query_params.get('sub_category', None)

        query_set = SvcInclude.objects.filter(
            sub_category=cat
        )
        return query_set


class PublishSvc(views.APIView):
    '''
    Permite que el chamber publique el servicio si se cumplen las condiciones:
    1. Tener al menos una imagen.
    1. Tener al menos una tarifa
    '''
    def get_queryset(self):
        user = self.request.user
        uuid = self.request.data["uuid"] # uuid del SVC 
        query_set = Svc.objects.filter(
            uuid=uuid,
            user=user
            )

        return query_set

    def post(self, request):
        user = self.request.user
        uuid = self.request.data["uuid"] # uuid del SVC
        published = self.request.data["published"]

        if published==True: # No se valida cuando quiere Despublicar
            # Se valida que el Svc tenga imagenes
            images = SvcImage.objects.filter(
                svc__uuid=uuid,
                user=self.request.user
            ).count()

            opts = SvcOpt.objects.filter(
                svc__uuid=uuid,
                user=self.request.user
            ).count()

            if images==0 or opts==0:
                raise serializers.ValidationError(
                    {'error': "El servicio debe tener al menos una imagen"})

        svc = Svc.objects.get(
            uuid=uuid,
            user=user
            )
        svc.is_published=published
        svc.save()

        return Response({"corrrecto": ["Servicio publicado"]}, 
            status=status.HTTP_200_OK)
