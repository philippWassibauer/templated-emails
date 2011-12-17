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
    rendered_email = ""
    try:
        settings.TEMPLATE_DEBUG = True
        template = get_template("emails%s/email.html"%path)
        rendered_email = recursive_block_replace(template, {})
    finally:
        settings.TEMPLATE_DEBUG = old_template_debug_setting

    return render_to_response(template_name, {
        "rendered_email": rendered_email,
    }, context_instance=RequestContext(request))
