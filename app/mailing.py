from flask.ext.mail import Message
from app import mail, app
from flask import url_for
from threading import Thread


def send_async_email(msg):
    mail.send(msg)


def send_awaiting_confirm_mail(user):
    """
    Send the awaiting for confirmation mail to the user.
    """
    subject = "We're waiting for your confirmation!!"
    msg = Message(subject=subject, sender=app.config['DEFAULT_MAIL_SENDER'], recipients=[user.email])
    confirmation_url = url_for('activate_user', user_id=user.id, _external=True)
    msg.body = "Dear %s, click here to confirm: %s" % (user.username, confirmation_url)
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


def send_subscription_confirmed_mail(user):
    """
    Send the awaiting for confirmation mail to the user.
    """
    subject = "Thanks for your registration!!"
    msg = Message(subject=subject, sender=app.config['DEFAULT_MAIL_SENDER'], recipients=[user.email])
    msg.body = "Dear %s, you have been activated successfully!" % user.username
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()
