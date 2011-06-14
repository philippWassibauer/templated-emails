from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
import logging
from django.template.loader import get_template
from django.utils.translation import ugettext, get_language, activate
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User

class LanguageStoreNotAvailable(Exception):
    pass

def send_templated_email(recipients, template_path, context={},
                    from_email=settings.DEFAULT_FROM_EMAIL):
    """
        recipients can be either a list of emails of a list of users,
        if it is users the system will change to the language that the
        user has set as theyr mother toungue
    """
    current_language = get_language()
    for recipient in recipients:
        # if it is user, get the email and switch the language
        if isinstance(recipient, User):
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
            
        current_site = Site.objects.get(id=settings.SITE_ID)
        context["current_site"] = current_site
        context["STATIC_URL"] = settings.STATIC_URL
        
        context = Context(context)
        subject = render_to_string("%s/short.txt"%template_path, context)\
                                    .replace('\n', '').replace('\r', '')
        #import nose; nose.tools.set_trace()
        text = render_to_string("%s/email.txt"%template_path, context)
        
        body = None
        body_template = None
        html_path = "%s/email.html"%template_path
        try:
            body_template = get_template(html_path)
        except TemplateDoesNotExist:
            logging.info("Email sent without HTML, since %s not found"%html_path)
        
        msg = EmailMultiAlternatives(subject, text, from_email, [email])
        
        if body_template:
            body = render_to_string(html_path, context)
            if getattr(settings, "TEMPLATEDEMAILS_USE_PYNLINER", False):
                import pynliner
                body = pynliner.fromString(body)
            msg.attach_alternative(body, "text/html")
    
        msg.send()
        
        # reset environment to original language
        if isinstance(recipient, User):
            activate(current_language)


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
