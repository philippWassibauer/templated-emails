import logging

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.conf import settings
from django.template.loader import get_template
from django.template.base import Template

from .utils import get_email_directories
from .parse_util import recursive_block_replace

logger = logging.getLogger('templated_emails')

def index(request, template_name="templated_emails/index.html"):
    if not request.user.is_superuser:
        raise Http404
    else:
        directory_tree = get_email_directories(settings.EMAIL_TEMPLATES_DIRECTORY)
        return render_to_response(template_name, {
            "directory_tree": directory_tree,
        }, context_instance=RequestContext(request))


def view(request, path, template_name="templated_emails/view.html"):
    if not request.user.is_superuser:
        raise Http404
    else:
        # get extends node
        # get all block nodes
        # do this recursive until no more extends
        # then place html in blocks
        rendered_subject = ""
        rendered_html = ""
        rendered_text = ""

        try:
            template = get_template("emails%s/email.html"%path)
            rendered_html = recursive_block_replace(template, {})
        except:
            logger.exception("Error rendering templated email email.html")

        try:
            template = get_template("emails%s/email.txt"%path)
            rendered_text = recursive_block_replace(template, {})
        except:
            logger.exception("Error rendering templated email email.txt")

        try:
            template = get_template("emails%s/short.txt"%path)
            rendered_subject = recursive_block_replace(template, {})
        except:
            logger.exception("Error rendering templated email short.txt")

        return render_to_response(template_name, {
            "rendered_subject": rendered_subject,
            "rendered_html": rendered_html,
            "rendered_text": rendered_text,
        }, context_instance=RequestContext(request))
