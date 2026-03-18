from django.shortcuts import render
from django.db.models import Case, CharField, Q, Value, When, BooleanField
from rest_framework import viewsets
from rest_framework import views
from django.http import Http404, JsonResponse
from .serializers import (QuoteSer, QuoteReplySer, CWMessageSer, DisputeSer,
                          DisputeReplySer)
from work.models import QuoteFile, CWMessage, CWReview, ContractedWork, Dispute, DisputeReply, Quote, QuoteReply, WorkOffer, WorkOfferCandidate
from django.contrib.auth.models import User
from adminsite.functions import MediumPagination, SmallPagination, StandardPagination
from adminsite.tasks import available_works, email_notification_msg, email_notification_msg_norul, finished_notification
from work.serializers import QuoteFileSer, CWReviewSer, CancelQuoteSer, CancelReason, ContractedWorkSer, WorkOfferCandidateSer, WorkOfferSer
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import permissions
from rest_framework import status
from django.db import transaction
from django.db import IntegrityError
from .functions import create_quote, create_cw_review, create_dispute
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, date, timedelta
from django.contrib.postgres.search import SearchQuery
import pytz


class QuoteAPI(viewsets.ModelViewSet):
    '''API Quote Info'''
    serializer_class = QuoteSer
    pagination_class = SmallPagination
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        qt = self.request.query_params.get('quote', None)
        customer = self.request.query_params.get('customer', None)
        if customer is not None:
            query_set = Quote.objects.filter(
                user=self.request.user
            )
        if customer is None:
            query_set = Quote.objects.filter(
                chamber=self.request.user
            )

        if qt is not None:
            query_set = query_set.filter(
                id = qt
            )

        return query_set
   
    def perform_create(self, serializer):
        '''
        Permite crear la cotización
        '''
        qt = self.request.data["chamber"]
        chamber = User.objects.get(
            professional__uuid=qt
        )
        quote = serializer.save(user=self.request.user,
                        chamber=chamber, status='0')
        msg = {'title': quote.title, 'description': quote.job_description}
        # Correo cliente
        email_notification_msg.delay(
                quote.user.username,
                quote.user.first_name,
                'Tu solicitud ha sido registrada',
                'Hemos registrado su solicitud',
                msg,
                'customer-admin/quote-detail/' + str(quote.id)
        )
        # Correo para el Chamber
        email_notification_msg.delay(
                quote.chamber.username,
                quote.chamber.first_name,
                'Tienes una solicitud de cotización',
                'Has recibido una solicitud de cotización',
                msg,
                'chamber-admin/quote-detail/' + str(quote.id)
        )


class QuoteReplyAPI(viewsets.ModelViewSet):
    '''API Quote Reply'''
    serializer_class = QuoteReplySer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        qt = self.request.query_params.get('quote', None)

        query_set = QuoteReply.objects.filter(
            Q(quote__user=self.request.user) |
            Q(quote__chamber=self.request.user),
            quote=qt
            )

        return query_set

    def perform_create(self, serializer):
        '''
        Permite crear la cotización
        '''

        quote = self.request.data["quote"]
        status = self.request.data.get("quote_status", None)
        cost = self.request.data.get("cost", None)
        # TODO: Es necesario colocar una validación de la venta y Fee en Backend
        reply = serializer.save(user=self.request.user)
        # Se actualiza el estado de la coti
        if status is not None and cost is not None:
            Quote.objects.filter(
                id=quote
            ).update(
                status=status,
                cost=reply.cost,
                fee=reply.fee,
                sale=reply.sale,
                how_message=reply.how_message,
                required_days=reply.required_days,
                revision=reply.revision
                )
        # Correo de notificación
        quote = Quote.objects.get(id=quote)

        if reply.user == quote.user: # El cliente ha escrito el msj
            fromemail = quote.user.username
            toemail = quote.chamber.username
            # Correo de notificación al Chamber
            email_notification_msg.delay(
                    toemail,
                    quote.chamber.first_name,
                    'Tienes un nuevo mensaje',
                    'Has recibido un mensaje de tu cliente',
                    {'description': reply.message},
                    'chamber-admin/quote-detail/' + str(quote.id)
            )

        else: # El Chamber ha escrito el msj
            fromemail = quote.chamber.username
            toemail = quote.user.username
            # Correo de notificación al cliente
            email_notification_msg.delay(
                    toemail,
                    quote.user.first_name,
                    'Tienes un nuevo mensaje',
                    'Has recibido un mensaje de tu Chamber',
                    {'description': reply.message},
                    'chamber-admin/quote-detail/' + str(quote.id)
            )


class CancelQuoteAPI(viewsets.ModelViewSet):
    '''API Quote Reply'''
    serializer_class = CancelQuoteSer
    http_method_names = ['patch', 'get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        qt = self.request.query_params.get('quote', None)
        is_chamber = self.request.query_params.get('is_chamber', None)
        query_set = Quote.objects.filter(
            Q(user=self.request.user) |
            Q(chamber=self.request.user),
            # id=qt
            )

        return query_set

    def patch(self, pk, request):
        '''
        Es necesario re escribir el metodo debido que por defecto DRF
        solicita un ID para poder hacer PATCH. Y queremos que solo
        se pueda editar la info del usuario logueado
        '''
        query_set = Quote.objects.filter(
            Q(user=self.request.user) |
            Q(chamber=self.request.user),
            id=pk
        ).first()
        serializer = CancelQuoteSer(query_set, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(cancelled_date=datetime.now(pytz.utc))
            return Response(serializer.data)
        return Response({
            'error': 'ERROR',
            'message': serializer.errors
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class WorkOfferApi(viewsets.ModelViewSet):
    '''
    APi que permite gestionar las ofertas de trabajo de los clientes
    '''
    serializer_class = WorkOfferSer
    pagination_class = SmallPagination
    http_method_names = ['post', 'get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        uuid = self.request.query_params.get('uuid', None)
        query_set = WorkOffer.objects.filter(
            Q(user=self.request.user)
        )
        if uuid is not None:
            query_set = query_set.filter(uuid1=uuid)

        return query_set

    def perform_create(self, serializer):
        '''
        Permite crear la oferta de trabajo
        '''
        # quote = self.request.data["quote"]
        # status = self.request.data.get("quote_status", None)
        # qt = self.request.query_params.get('categories', None)
        qt = self.request.data["categories"]
        pk = serializer.save(user=self.request.user)
        obj = WorkOffer.objects.get(id=pk.id)
        for q in qt:
            obj.category.add(q['id'])


class PublicWorkOfferApi(viewsets.ModelViewSet):
    '''
    APi que permite visualizar de forma publica las ofertas de trabajo
    registradas por los diversos usuarios de la plataforma
    '''
    serializer_class = WorkOfferSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MediumPagination
    http_method_names = ['get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        uuid = self.request.query_params.get('uuid', None)
        keywords = self.request.query_params.get('keywords', None)
        selectedCats = self.request.query_params.getlist('selectedCats', None)
        tarifRange = self.request.query_params.getlist('tarifRange', None)

        user=self.request.user
        query_set = WorkOffer.objects.filter(
            Q(status=0) | Q(status=1) | Q(status=2)
        )
        if uuid is not None:
            query_set = query_set.filter(uuid1=uuid)
        if self.request.user.is_authenticated:
            # query_set = query_set.exclude(user=user)
            query_set = query_set.annotate(
                owner=Case(
                    When(user=user, then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
            ))

        # Filtro por palabras
        if keywords is not None and keywords != '':
            # Agrega OR entre cada palabra para el formato de la busqueda
            keywords = keywords.lower().replace(" ", " OR ")

            query_set = query_set.filter(
                category__keywords__search=SearchQuery(
                    keywords, search_type='websearch'
                    )).distinct()

        # Filtro de categorias
        if selectedCats is not None and selectedCats != []:
            query_set = query_set.filter(
                category__in=selectedCats
            ).distinct()
        # Filtro por rango de tarifa
        if tarifRange is not None and tarifRange != []:
            query_set = query_set.filter(
                ((Q(tarif_to__gte=tarifRange[0]) &
                Q(tarif_to__lte=tarifRange[1]))) &
                Q(say_price=True)
            )

        return query_set


class WorkOfferCandidateApi(viewsets.ModelViewSet):
    '''
    APi que permite visualizar los candidatos postulados a una chamba
    '''
    serializer_class = WorkOfferCandidateSer
    pagination_class = MediumPagination
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        uuid = self.request.query_params.get('uuid', None)
        query_set = WorkOfferCandidate.objects.filter(
            work_offer__uuid1=uuid,
            # work_offer__status=0
            )

        return query_set

    def perform_create(self, serializer):
        '''
        Permite registrar un candidato a una oferta laboral
        '''
        offer = self.request.data.get("workOffer", None)

        try:
            work_offer = WorkOffer.objects.get(uuid1=offer)
        except WorkOffer.DoesNotExist:
            return Http404
        # qt = self.request.query_params.get('categories', None)
        try:
            serializer.save(
                chamber=self.request.user,
                work_offer=work_offer
                )
            email_notification_msg.delay(
                work_offer.user.username,
                work_offer.user.first_name,
                'Has recibido una propuesta en tu pedido',
                'Tienes una propuesta de uno de nuestros Chambers',
                serializer.data.get("message", ''),
                'customer-admin/work-detail/' + str(work_offer.uuid1)

            )
        except IntegrityError:
            raise serializers.ValidationError(
                {'duplicated': "Ya se ha postulado a esta oferta"})


class PublicWorkOfferCandidate(viewsets.ModelViewSet):
    '''
    APi que permite visualizar de forma publica las ofertas de trabajo
    registradas por los diversos usuarios de la plataforma
    '''
    serializer_class = WorkOfferCandidateSer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = MediumPagination
    http_method_names = ['get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        uuid = self.request.query_params.get('uuid', None)
        query_set = WorkOfferCandidate.objects.filter(
            work_offer__uuid1=uuid,
            work_offer__status=0
            )

        return query_set


class AcceptWorkCandidate(views.APIView):
    '''
    Permite aceptar una propuesta de un candidato a la WorkOffer.
    Solo el autor de la WorkOffer puede hacer esto.
    '''
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        '''
        Se actualiza el status de WorkOffer y se crea la Quote
        '''
        wo = request.data.get('wo', None)  # WorkOffer UUID
        woc = request.data.get('woc', None)  # WorkOfferCandidate ID
        user = self.request.user

        WorkOfferCandidate.objects.filter(
            id=woc,
            work_offer__uuid1=wo, # Valida que el candidato sea de la oferta
            work_offer__user=user # Valida propietario de la oferta
        ).update(
            customer_accepted=True,
            accepted_date=datetime.now(pytz.utc)
        )

        WorkOffer.objects.filter(
            user=user,
            uuid1=wo
        ).update(
            accepted=True,
            status='1',
            accepted_date=datetime.now(pytz.utc)
        )
        quote = create_quote(wo, woc)

        return JsonResponse({
                'status': 'ok',
                'quote': quote
            })


class ContractedWorksApi(viewsets.ModelViewSet):
    '''
    Api para gestionar los servicios contratados
    '''
    serializer_class = ContractedWorkSer
    pagination_class = MediumPagination
    http_method_named = ['get']

    def get_queryset(self):
        '''Filtra la busqueda por solo los usuarios involucrados'''
        user = self.request.user
        customer = self.request.query_params.get('customer', None)
        cw = self.request.query_params.get('cw', None)

        if customer is not None:
            qs = ContractedWork.objects.filter(
                user=self.request.user
            )
        if customer is None:
            qs = ContractedWork.objects.filter(
                chamber=self.request.user
            )
        
        if cw is not None:
                qs = qs.filter(
                id = cw
        )

        return qs


class CWMessageAPI(viewsets.ModelViewSet):
    '''API CW Messages API'''
    serializer_class = CWMessageSer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = CWMessage.objects.filter(
            Q(cw__user=self.request.user) |
            Q(cw__chamber=self.request.user),
            cw=cw
            )

        return query_set

    def perform_create(self, serializer):
        '''
        Registra un nuevo mensaje
        '''
        reply = serializer.save(user=self.request.user)

        if reply.user == reply.cw.user: # El cliente ha escrito el msj
            # Correo al Chamber
            toemail = reply.cw.chamber.username
            name = reply.cw.chamber.first_name
            title = 'Has recibido un mensaje de tu cliente'
            url = 'chamber-admin/contracted/' + str(reply.cw.id)

        else: # El Chamber ha escrito el msj
            # Correo al Cliente
            toemail = reply.cw.user.username
            name = reply.cw.user.first_name
            title = 'Has recibido un mensaje de tu chamber'
            url = 'customer-admin/contracted/' + str(reply.cw.id)

        email_notification_msg.delay(
                toemail,
                name,
                'Tienes un nuevo mensaje',
                title,
                {'description': reply.message},
                url
        )


class CWReviewAPI(viewsets.ModelViewSet):
    '''API CW Review API'''
    serializer_class = CWReviewSer
    http_method_names = ['get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = CWReview.objects.filter(
            Q(cw__user=self.request.user) |
            Q(cw__chamber=self.request.user),
            cw=cw
            )
        return query_set


class QuoteFileAPI(viewsets.ModelViewSet):
    serializer_class = QuoteFileSer
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        quote = self.request.query_params.get('quote', None)

        query_set = QuoteFile.objects.filter(
            Q(quote__user=self.request.user) |
            Q(quote__chamber=self.request.user),
            quote=quote)

        return query_set

    def perform_create(self, serializer):
        user=self.request.user
        quote=self.request.data['quote']
        is_customer=False

        try:
            file = self.request.data['file']
            filename = self.request.data['filename']
        except KeyError:
            raise serializers.ValidationError(
                {'error': "Debe suministrar un archivo"})
        quote = Quote.objects.get(
            Q(user=user) |
            Q(chamber=user),
            id=quote
            )
        if(quote.user==user):
            is_customer=True
        if serializer.is_valid():
                serializer.save(file=file, filename=filename,
                                quote=quote, user=user,
                                is_client=is_customer)

    def destroy(self, request, pk, format=None):
        try:
            record = QuoteFile.objects.get(
                id=pk,
                user=self.request.user
            )
        except QuoteFile.DoesNotExist:
            raise Http404
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CWReviewPublicAPI(viewsets.ModelViewSet):
    '''
    API CW Review API
    Permite ver los reviews que ha recibido un Chamber, esta api debe funcionar
    sin autenticación, ya que forma parte de una sección pública de la web.
    '''
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = SmallPagination
    serializer_class = CWReviewSer
    http_method_names = ['get']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        uuid = self.request.query_params.get('uuid', None)

        query_set = CWReview.objects.filter(
            chamber__professional__uuid=uuid
            )
        return query_set


class CWFinishAPI(views.APIView):
    '''
    Permite finalizar un servicio contratado
    '''
    http_method_names = ['post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = ContractedWork.objects.filter(
            user=self.request.user,
            id=cw
            )

        return query_set

    @transaction.atomic
    def post(self, request):
        '''
        Se actualiza el status de WorkOffer y se crea la Quote
        '''
        cw = request.data.get('cw', None)  # Contracted Work ID
        message = request.data.get('message', '')  # Contracted Work ID
        rating = request.data.get('rating', None)  # Contracted Work ID
        user = self.request.user

        cwd = ContractedWork.objects.get(
            id=cw,
            user=user # Valida propietario de la oferta
        )

        cwd.status=1 # Status finalizado
        cwd.finished_date=datetime.now(pytz.utc)

        cwd.save()

        # Registro de review y pago
        review = create_cw_review(cwd, message, rating)

        finished_notification.delay(
            cwd.chamber.username, # toemail
            cwd.chamber.first_name, # Chamber Name
            cwd.user.first_name, # Customer Name
            message,
            cwd.id
        )

        return JsonResponse({
                'status': 'ok',
                'review': review
            })


class CWChamberFinishAPI(views.APIView):
    '''
    Permite al Chamber finalizar un servicio contratado
    # TODO: Notificar de alguna forma a quechamba para iniciar
    el reembolso
    '''
    http_method_names = ['post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = ContractedWork.objects.filter(
            chamber=self.request.user,
            id=cw
            )

        return query_set

    @transaction.atomic
    def post(self, request):
        '''
        Se actualiza el status de WorkOffer y se crea la Quote
        '''
        cw = request.data.get('cw', None)  # Contracted Work ID
        user = self.request.user

        ContractedWork.objects.filter(
            id=cw,
            chamber=user # Valida chamber de la oferta
        ).update(
            status=2,
            finished_date=datetime.now(pytz.utc)
        )
        # Se obtiene los datos del CW
        cwd = ContractedWork.objects.get(id=cw)

        # TODO: Notificar al cliente.
        msg = {'title': cwd.po.quote.title,
               'description': '''Tu Chamber ha marcado el trabajo como 
                                 finalizado, te invitamos a dar conformidad del
                                 servicio, de no dar conformidad en las próximas
                                 72 horas, procederemos a liberar el pago del
                                 Chamber. Muchas gracias por utilizar Qué Chamba'''}
        email_notification_msg.delay(
                cwd.user.username,
                cwd.user.first_name,
                'Tu Chamba fue finalizada',
                'Chamba Finalizada',
                msg,
                'customer-admin/contracted/' + str(cwd.id)
        )

        return JsonResponse({
                'status': 'ok'
            })


class CWCancelWork(views.APIView):
    '''
    Permite Cancelar un servicio contratado
    '''
    http_method_names = ['post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = ContractedWork.objects.filter(
            user=self.request.user,
            id=cw
            )

        return query_set

    @transaction.atomic
    def post(self, request):
        '''
        Se procede con la cancelación del trabajo
        '''
        cw = request.data.get('cw', None)  # Contracted Work ID
        reason_code = request.data.get('reason', None)
        title = request.data.get('title', None)
        description = request.data.get('reason', None)
        # user = self.request.user

        if reason_code is not None:
            reason = CancelReason.objects.get(code=reason_code)

        try:
            work = ContractedWork.objects.get(
                Q(user=self.request.user) |
                Q(chamber=self.request.user),
                id=cw
            )
        except ContractedWork.DoesNotExist:
            return Http404

        if work.user == self.request.user: # Validamos que sea el cliente
            ''' 
            Si el cliente cancela posterior a la fecha del servicio
            Debe crear una disputa. Esto para validar que el Chamber no haya
            realizado ya el trabajo.
            '''
            delvdateplus = work.po.quote.delivery_date + timedelta(days=10)
            if delvdateplus > date.today():
                ContractedWork.objects.filter(id=work.id).update(
                status=5, # 5: Cancelado por cliente
                cancelled_date=datetime.now(pytz.utc)
                )
            else:
                '''
                Se impide cancelar la chamba, este caso solo debe suceder si el
                cliente burla el frontend, ya que esta misma validación la hace
                el frontend.
                '''
                return Response("No es posible cancelar este servicio",
                                status=status.HTTP_400_BAD_REQUEST)

        if work.chamber == self.request.user: # Validamos que sea el Chamber
            '''
            El Chamber puede cancelar en cualquier momento, cuando este cancela
            se procede con la devolución Integra del monto pagado por el cliente
            '''
            ContractedWork.objects.filter(id=work.id).update(
            status=4, # 4: Cancelado por Chamber
            cancelled_date=datetime.now(pytz.utc),
            cancel_reason=reason
            )
        return JsonResponse({
                'status': 'ok'
            })


class CWCancelWorkWDispute(views.APIView):
    '''
    Cuando un servicio ha pasado su fecha de ejecución, este no puede ser
    cancelado sin pasar por una disputa con el Chamber, esto para validar
    que en efecto no se haya realizado el trabajo.
    '''
    http_method_names = ['post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        cw = self.request.query_params.get('cw', None)

        query_set = ContractedWork.objects.filter(
            user=self.request.user,
            id=cw
            )

        return query_set

    @transaction.atomic
    def post(self, request):
        '''
        Se procede con la cancelación del trabajo
        '''
        cw = request.data.get('cw', None)  # Contracted Work ID
        reason_code = request.data.get('reason', None)
        title = request.data.get('title', None)
        description = request.data.get('description', None)
        customer_prop = request.data.get('customer_prop', None)

        try:
            work = ContractedWork.objects.get(
                Q(user=self.request.user),
                id=cw
            )
        except ContractedWork.DoesNotExist:
            return Http404

        if work.user == self.request.user: # Validamos que sea el cliente
            ContractedWork.objects.filter(id=work.id).update(
                status=5, # 5: Cancelado por cliente
                cancelled_date=datetime.now(pytz.utc)
            )
            dp = create_dispute(work, title, description, customer_prop)

            return JsonResponse({
                    'status': 'ok',
                    'dp': dp
                })
        else:
            return Response({
                'error': 'ERROR'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CWAvailableWork(views.APIView):
    '''
    API que activa el envio de las Chambas disponibles a la BD de usuarios
    registrados.
    '''
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ['post']

    def post(self, request):
        # qt = self.request.query_params.get('quote', None)
        available_works.delay()

        return Response({"corrrecto": ["Correos enviados"]}, 
                status=status.HTTP_200_OK)


class DisputeAPI(viewsets.ModelViewSet):
    '''Dispute API'''
    serializer_class = DisputeSer
    pagination_class = SmallPagination
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        dp = self.request.query_params.get('dispute', None)
        customer = self.request.query_params.get('customer', None)
        if customer is not None:
            query_set = Dispute.objects.filter(
                user=self.request.user
            )
        if customer is None:
            query_set = Dispute.objects.filter(
                chamber=self.request.user
            )

        if dp is not None:
            query_set = query_set.filter(
                id = dp
            )

        return query_set


class DisputeReplyAPI(viewsets.ModelViewSet):
    '''API Dispute Reply'''
    serializer_class = DisputeReplySer
    http_method_names = ['get', 'post']

    def get_queryset(self):
        '''Filtra al usuario de la consulta'''
        dp = self.request.query_params.get('dispute', None)

        query_set = DisputeReply.objects.filter(
            Q(dispute__user=self.request.user) |
            Q(dispute__chamber=self.request.user),
            dispute=dp
            )

        return query_set

    def perform_create(self, serializer):
        '''
        Permite enviar un mensaje para la disputa
        '''
        dispute = self.request.data["dispute"]
        status = self.request.data.get("quote_status", None)
        prop = self.request.data.get("prop", None)

        reply = serializer.save(user=self.request.user)
        # Se actualiza el estado de la disputa
        if prop is not None:
            qt = Dispute.objects.filter(
                id=dispute
            ).update(
                status=status,
                prop=reply.cost,
                )
        
        if reply.user == reply.dispute.user: # El cliente ha escrito el msj
            # Correo al Chamber
            toemail = reply.dispute.chamber.username
            name = reply.dispute.chamber.first_name
            title = 'Reclamo - Has recibido un mensaje'
            url = 'chamber-admin/dispute-detai/' + str(reply.dispute.id)

        else: # El Chamber ha escrito el msj
            # Correo al Cliente
            toemail = reply.dispute.user.username
            name = reply.dispute.user.first_name
            title = 'Reclamo - Has recibido un mensaje'
            url = 'customer-admin/dispute-detail/' + str(reply.dispute.id)

        email_notification_msg.delay(
                toemail,
                name,
                'Tienes un nuevo mensaje',
                title,
                {'description': reply.message},
                url
        )
