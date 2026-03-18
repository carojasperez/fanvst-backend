

from work.models import (Quote, QuoteReply, WorkOffer, WorkOfferCandidate,
                         ContractedWork, CWReview, Dispute)
from payment.models import ChamberIncome
from decimal import Decimal
from adminsite.tasks import email_notification_msg
from svc.models import Svc, SvcOpt
from datetime import date, datetime, timedelta
import pytz


def create_quote(wo, woc):
    '''
    Genera una Quote desde una WorkOffer
    '''

    wod = WorkOffer.objects.get(uuid1=wo)
    wocd = WorkOfferCandidate.objects.get(id=woc)
    status = "6" if wocd.info_required else "2"

    quote = Quote.objects.create(
        user=wod.user,
        chamber=wocd.chamber,
        work_offer=wod,
        title=wod.title,
        job_description=wod.job_description,
        expire_date=wod.expire_date,
        cost=wocd.cost,
        fee=wocd.fee,
        sale=wocd.sale,
        remote_work=wod.remote_work,
        department=wod.department,
        province=wod.province,
        district=wod.district,
        # address=wod.address,
        req_hours=wod.req_hours,
        hours=wod.hours,
        flexible_time=wod.flexible_time,
        required_days=wocd.required_days,
        how_message=wocd.how_message,
        revision=wocd.revision,
        status=status
    )

    QuoteReply.objects.create(
        quote=quote,
        message=wocd.message,
        how_message=wocd.how_message,
        required_days=wocd.required_days,
        revision=wocd.revision,
        user=wocd.chamber,
        is_client=False,
        cost=wocd.cost,
        fee=wocd.fee,
        sale=wocd.sale
    )

    # Correo cliente
    # email_notification_msg.delay(
    #         quote.user.username,
    #         quote.user.first_name,
    #         'Tu solicitud ha sido registrada',
    #         'Hemos registrado su solicitud',
    #         msg,
    #         'customer-admin/quote-detail/' + str(quote.id)
    # )
    # Correo para el Chamber
    email_notification_msg.delay(
            quote.chamber.username,
            quote.chamber.first_name,
            'Has sido seleccionado por el cliente',
            '¡Felicidades! has sido seleccionado por el cliente',
            'Se ha generado una cotización para que puedas ajustar los detalles finales con el cliente. El trabajo iniciará cuando el cliente efectúe el pago',
            'chamber-admin/quote-detail/' + str(quote.id)
    )

    return quote.id


def create_quote_svc(uuid, opt, user):
    '''
    Genera una quote desde un SVC
    '''
    svc = SvcOpt.objects.get(svc__uuid=uuid, id=opt)
    svcdate = datetime.now(pytz.utc) + timedelta(days=svc.required_days)

    quote = Quote.objects.create(
        user=user,
        chamber=svc.user,
        title=svc.svc.title,
        job_description=svc.svc.description,
        delivery_date=svcdate,
        cost=svc.cost,
        fee=svc.fee,
        sale=svc.sale,
        status='3',
        accepted=True,
        accepted_date=datetime.now(pytz.utc),
        is_svc=True,
    )

    return quote


def create_income(cw):
    '''
    Crea un registro de Pago, esto suede unicamente cuando el cliente
    da conformidad del servicio o cuando se vence el tiempo de espera
    por la confirmación del cliente.
    '''
    feeIgv = cw.po.quote.fee-cw.po.quote.fee/Decimal(1.18)

    ChamberIncome.objects.create(
        cw=cw,
        chamber=cw.chamber,
        cost=cw.po.quote.cost,
        fee=cw.po.quote.fee-feeIgv,
        fee_igv=feeIgv,
        sale=cw.po.quote.sale,
    )


def create_cw_review(cw, message, rating):
    '''
    Crea el registro correspondiente al review del cliente sobre un
    servicio contratado.
    '''
    # cw = ContractedWork.objects.get(id=id)
    c = CWReview.objects.create(
        user=cw.user,
        chamber=cw.chamber,
        cw=cw,
        message=message,
        rating=rating
    )

    create_income(cw)

    return c.id


def create_dispute(cw, title, description, customer_prop):
    '''
    Una disputa se genera cuando un cliente cancela un servicio
    que tiene fecha de ejecución inferio a la fecha actual
    '''
    dp = Dispute.objects.create(
        cw=cw,
        user=cw.user,
        chamber=cw.chamber,
        title=title,
        description=description,
        customer_prop=customer_prop,
        is_customer=True
    )

    return dp.id
