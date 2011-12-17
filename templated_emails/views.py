from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from .utils import get_email_directories
from .parse_util import recursive_block_replace
from django.conf import settings
from django.template.loader import get_template
from django.template.base import Template

def index(request, template_name="templated_emails/index.html"):
    directory_tree = get_email_directories("templates/emails")
    return render_to_response(template_name, {
        "directory_tree": directory_tree,
    }, context_instance=RequestContext(request))


def view(request, path, template_name="templated_emails/view.html"):
    # get extends node
    # get all block nodes
    # do this recursive until no more extends
    # then place html in blocks
    old_template_debug_setting = settings.TEMPLATE_DEBUG
    rendered_subject = ""
    rendered_html = ""
    rendered_text = ""
    try:
        settings.TEMPLATE_DEBUG = True
        try:
            template = get_template("emails%s/email.html"%path)
            rendered_html = recursive_block_replace(template, {})
        except:
            pass # there might be no html

        try:
            template = get_template("emails%s/email.txt"%path)
            rendered_text = recursive_block_replace(template, {})
        except:
            pass # there might be no text file

        try:
            template = get_template("emails%s/short.txt"%path)
            rendered_subject = recursive_block_replace(template, {})
        except: 
            pass # there might be no html

    finally:
        settings.TEMPLATE_DEBUG = old_template_debug_setting

    return render_to_response(template_name, {
        "rendered_subject": rendered_subject,
        "rendered_html": rendered_html,
        "rendered_text": rendered_text,
    }, context_instance=RequestContext(request))
