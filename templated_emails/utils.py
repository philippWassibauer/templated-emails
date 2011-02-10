from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template import Template, Context
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

def send_html_email(recipients, template_path, context={},
                    from_email=settings.DEFAULT_FROM_EMAIL):
    current_site = Site.objects.get(id=settings.SITE_ID)
    context["current_site"] = current_site
    context["STATIC_URL"] = settings.STATIC_URL
    
    context = Context(context)
    subject = render_to_string("%s/short.txt"%template_path, context)\
                                .replace('\n', '').replace('\r', '')
    text = render_to_string("%s/email.txt"%template_path, context)
    
    body = None
    try: # TODO: this is not the right way to do it, but it works for now and I will come back to it
        body = render_to_string("%s/email.html"%template_path, context)
    except:
        pass
    
    msg = EmailMultiAlternatives(subject, text, from_email, recipients)
    
    if body:
        msg.attach_alternative(body, "text/html")
        
    msg.send()

