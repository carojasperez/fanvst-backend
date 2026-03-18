from celery import shared_task
from django.core.mail import EmailMessage
from django.template import loader
from django.contrib.auth.models import User
from work.models import WorkOffer


@shared_task
def email_validation(token, toemail, name):
    '''
    Envía el correo de validación de la cuenta de usuario.
    '''
    html_message = loader.render_to_string(
            'email_validation.html',
            {
                'title': "Hola " + name + "! gracias por registrarte en Qué Chamba",
                'token': token,
                'usermail': toemail
            })

    email = EmailMessage("Hola " + name + ", por favor verifica tu cuenta",
                         html_message,  # Body
                        #  from_email="noresponder@quechamba.com",
                         to=[toemail],  # [tomail],  # TO
                         # reply_to=[srv.company.email]
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def email_becomechamber(toemail, name):
    '''
    Envía corre de notificación de registro como Chamber
    '''
    html_message = loader.render_to_string(
            'welcome_chamber.html',
            {
                'title': "¡Hola " + name + "! Te has registrado como Chamber",
                 'usermail': toemail
            })

    email = EmailMessage("Hola " + name + ", ¡Gracias por convertirte en Chamber!",
                         html_message,  # Body
                        #  from_email="noresponder@quechamba.com",
                         to=[toemail],  # [tomail],  # TO
                         # reply_to=[srv.company.email]
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def email_password_reset(token1, token2, toemail, name):
    '''
    Envía el correo de reset de passwords
    '''
    html_message = loader.render_to_string(
            'password_reset.html',
            {
                'title': "Correo de recuperación de contraseña",
                'token1': token1,
                'token2': token2,
                'usermail': toemail
            })

    email = EmailMessage("Hola " + name + ", En este correo encontrarás lo necesario para reiniciar tu contraseña",
                         html_message,  # Body
                        #  from_email="noresponder@quechamba.com",
                         to=[toemail],  # [tomail],  # TO
                         # reply_to=[srv.company.email]
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def email_notification_msg(toemail, name, title, subtitle, msg, url):
    '''
    Envía el correo de notificaciones relacionadas a mensajes entre el cliente
    y el chamber
    '''
    html_message = loader.render_to_string(
            'notification_message.html',
            {
                'subtitle': subtitle,
                # 'usermail': toemail,
                'msg': msg,
                'url': url
            })

    email = EmailMessage("Hola " + name + ", " + title,
                         html_message,  # Body
                        #  from_email="noresponder@quechamba.com",
                         to=[toemail],  # [tomail],  # TO
                         # reply_to=[srv.company.email]
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def email_notification_msg_norul(toemail, name, title, subtitle, msg):
    '''
    Envía el correo de notificaciones relacionadas a mensajes entre el cliente
    y el chamber
    '''
    html_message = loader.render_to_string(
            'notification_message_nourl.html',
            {
                'subtitle': subtitle,
                # 'usermail': toemail,
                'msg': msg
            })

    email = EmailMessage("Hola " + name + ", " + title,
                         html_message,  # Body
                        #  from_email="noresponder@quechamba.com",
                         to=[toemail],  # [tomail],  # TO
                         # reply_to=[srv.company.email]
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def payment_notification(toemail, name, price, id):
    '''
    Envía el correo de confirmación de pago al Cliente
    '''
    html_message = loader.render_to_string(
            'payment_notification.html',
            {
                'subtitle': 'Su pago fue registrado correctamente',
                'usermail': toemail,
                'price': price,
                'id': id
            })

    email = EmailMessage("Hola " + name + ", Hemos recibido tu pago",
                         html_message,  # Body
                         to=[toemail],  # [tomail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def contracted_notification(toemail, name, customer, id):
    '''
    Envía el correo de confirmación de contrato al Chamber
    '''
    html_message = loader.render_to_string(
            'contracted_notification.html',
            {
                'usermail': toemail,
                'name': name,
                'customer': customer,
                'id': id
            })

    email = EmailMessage("Hola " + name + ", ¡Conseguiste la Chamba!",
                         html_message,  # Body
                         to=[toemail],  # [tomail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def finished_notification(toemail, name, customer, review, id):
    '''
    Envía el correo de finalización del trabajo al Chamber
    '''
    html_message = loader.render_to_string(
            'finished_notification.html',
            {
                'usermail': toemail,
                'name': name,
                'customer': customer,
                'review': review,
                'id': id
            })

    email = EmailMessage("¡Felicidades " + name + "!, Has finalizado una chamba",
                         html_message,  # Body
                         to=[toemail],  # [tomail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def deposit_notification(toemail, name, dp, cw):
    '''
    Envía el correo de notificación de pago al Chamber
    '''
    html_message = loader.render_to_string(
            'deposit_notification.html',
            {
                'usermail': toemail,
                'name': name,
                'dp': dp,
                'cw': cw
            })

    email = EmailMessage("Notificación de pago - Chamba #: "+str(cw),
                         html_message,  # Body
                         to=[toemail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def complaint_book_email(complaint):
    '''
    Envía al correo del cliente una copia del libro de reclamaciones
    '''
    html_message = loader.render_to_string(
            'complaint_book.html',
            {
                'subtitle': complaint.id,
                'usermail': complaint.email,
                'msg': complaint
            })

    email = EmailMessage("Copia Libro de Reclamaciones QuéChamba",
                         html_message,  # Body
                         to=[complaint.email],  # [tomail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def available_works():
    '''
    Envía correo de las nuevas ofertas de trabajo disponibles
    '''
    users = User.objects.filter(
            notification__work_offer=True
        ).values()

    offers = WorkOffer.objects.filter(
        status=0
        )[:5]
    for user in users:
        html_message = loader.render_to_string(
                'available_works.html',
                {
                    'offers': offers,
                    'user': user,
                    'title': 'Resumen de ofertas de trabajo de la semana'
                })
        email = EmailMessage("Hola " +  user['first_name'] + "! Tenemos nuevas Chambas que podrían interesarte",
                            html_message,  # Body
                            to=[user['username']],  # [tomail],  # TO
                            )
        email.content_subtype = "html"
        email.send()