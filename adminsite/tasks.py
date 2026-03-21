from celery import shared_task
from django.core.mail import EmailMessage
from django.template import loader
from django.contrib.auth.models import User


@shared_task
def email_validation(token, toemail, name):
    '''
    Envía el correo de validación de la cuenta de usuario.
    '''
    html_message = loader.render_to_string(
            'email_validation.html',
            {
                'title': "Hola " + name + "! gracias por registrarte en Fanvst",
                'token': token,
                'usermail': toemail
            })

    email = EmailMessage("Hola " + name + ", por favor verifica tu cuenta",
                         html_message,  # Body
                         to=[toemail],  # TO
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
                         to=[toemail],  # TO
                         )
    email.content_subtype = "html"
    email.send()


@shared_task
def email_notification_msg_norul(toemail, name, title, subtitle, msg):
    '''
    Envía el correo de notificaciones generales
    '''
    html_message = loader.render_to_string(
            'notification_message_nourl.html',
            {
                'subtitle': subtitle,
                'msg': msg
            })

    email = EmailMessage("Hola " + name + ", " + title,
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

    email = EmailMessage("Copia Libro de Reclamaciones Fanvst",
                         html_message,  # Body
                         to=[complaint.email],  # TO
                         )
    email.content_subtype = "html"
    email.send()