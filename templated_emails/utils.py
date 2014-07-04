import logging
import os
import threading

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Context, TemplateDoesNotExist
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.utils.translation import get_language, activate
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model


try:
    from celery.task import task
except ImportError:
    task = lambda f: f

use_pynliner = getattr(settings, 'TEMPLATEDEMAILS_USE_PYNLINER', False)
use_celery = getattr(settings, 'TEMPLATEDEMAILS_USE_CELERY', False)
use_threading = not use_celery

pynliner = None
if use_pynliner:
    try:
        import pynliner
    except ImportError:
        pass


class LanguageStoreNotAvailable(Exception):
    pass


def get_email_directories(dir):
    directory_tree = False
    for name in os.listdir(dir):
        if os.path.isdir(os.path.join(dir, name)):
            if directory_tree == False:
                directory_tree = {}
            directory_tree[name] = get_email_directories(os.path.join(dir, name))
    return directory_tree


def send_templated_email(recipients, template_path, context=None,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    fail_silently=False, extra_headers=None):
    """
        recipients can be either a list of emails or a list of users,
        if it is users the system will change to the language that the
        user has set as theyr mother toungue
    """
    recipient_pks = [r.pk for r in recipients if isinstance(r, get_user_model())]
    recipient_emails = [e for e in recipients if not isinstance(e, get_user_model())]
    send = _send_task.delay if use_celery else _send
    msg = send(recipient_pks, recipient_emails, template_path, context, from_email,
         fail_silently, extra_headers=extra_headers)

    return msg


class SendThread(threading.Thread):
    def __init__(self, recipient, current_language, current_site, default_context,
                 subject_path, text_path, html_path, from_email=settings.DEFAULT_FROM_EMAIL,
                 fail_silently=False):
        self.recipient = recipient
        self.current_language = current_language
        self.current_site = current_site
        self.default_context = default_context
        self.subject_path = subject_path
        self.text_path = text_path
        self.html_path = html_path
        self.from_email = from_email
        self.fail_silently = fail_silently
        super(SendThread, self).__init__()

    def run(self):
        recipient = self.recipient
        if isinstance(recipient, get_user_model()):
            email = recipient.email
            try:
                language = get_users_language(recipient)
            except LanguageStoreNotAvailable:
                language = None

            if language is not None:
                activate(language)
        else:
            email = recipient

        # populate per-recipient context
        context = Context(self.default_context)
        context['recipient'] = recipient
        context['email'] = email

        # load email subject, strip and remove line breaks
        subject = render_to_string(self.subject_path, context).strip()
        subject = "".join(subject.splitlines())  # this must be a single line
        text = render_to_string(self.text_path, context)

        msg = EmailMultiAlternatives(subject, text, self.from_email, [email])

        # try to attach the html variant
        try:
            body = render_to_string(self.html_path, context)
            if pynliner:
                body = pynliner.fromString(body)
            msg.attach_alternative(body, "text/html")
        except TemplateDoesNotExist:
            logging.info("Email sent without HTML, since %s not found" % self.html_path)

        msg.send(fail_silently=self.fail_silently)

        # reset environment to original language
        if isinstance(recipient, get_user_model()):
            activate(self.current_language)


def _send(recipient_pks, recipient_emails, template_path, context, from_email,
          fail_silently, extra_headers=None):
    recipients = list(get_user_model().objects.filter(pk__in=recipient_pks))
    recipients += recipient_emails

    current_language = get_language()
    current_site = Site.objects.get(id=settings.SITE_ID)

    default_context = context or {}
    default_context["current_site"] = current_site
    default_context["STATIC_URL"] = settings.STATIC_URL

    subject_path = "%s/short.txt" % template_path
    text_path = "%s/email.txt" % template_path
    html_path = "%s/email.html" % template_path

    for recipient in recipients:
        if use_threading:
            SendThread(recipient, current_language, current_site, default_context, subject_path,
                       text_path, html_path, from_email, fail_silently).start()
            return
        # if it is user, get the email and switch the language
        if isinstance(recipient, get_user_model()):
            email = recipient.email
            try:
                language = get_users_language(recipient)
            except LanguageStoreNotAvailable:
                language = None

            if language is not None:
                # activate the user's language
                activate(language)
        else:
            email = recipient

        # populate per-recipient context
        context = Context(default_context)
        context['recipient'] = recipient
        context['email'] = email

        # load email subject, strip and remove line breaks
        subject = render_to_string(subject_path, context).strip()
        subject = "".join(subject.splitlines())  # this must be a single line
        text = render_to_string(text_path, context)

        msg = EmailMultiAlternatives(subject, text, from_email, [email],
                                     headers=extra_headers)

        # try to attach the html variant
        try:
            body = render_to_string(html_path, context)
            if pynliner:
                body = pynliner.fromString(body)
            msg.attach_alternative(body, "text/html")
        except TemplateDoesNotExist:
            logging.info("Email sent without HTML, since %s not found" % html_path)

        msg.send(fail_silently=fail_silently)

        # reset environment to original language
        if isinstance(recipient, get_user_model()):
            activate(current_language)

        return msg
if use_celery:
    _send_task = task(_send)


def get_users_language(user):
    """
    Returns site-specific language for this user. Raises
    LanguageStoreNotAvailable if this site does not use translated
    notifications.
    """
    if getattr(settings, 'NOTIFICATION_LANGUAGE_MODULE', False):
        try:
            app_label, model_name = settings.NOTIFICATION_LANGUAGE_MODULE.split('.')
            model = models.get_model(app_label, model_name)
            language_model = model._default_manager.get(user__id__exact=user.id)
            if hasattr(language_model, 'language'):
                return language_model.language
        except (ImportError, ImproperlyConfigured, model.DoesNotExist):
            raise LanguageStoreNotAvailable
    raise LanguageStoreNotAvailable
