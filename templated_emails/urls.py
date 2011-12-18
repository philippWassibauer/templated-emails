from django.conf.urls.defaults import *
from .views import *

urlpatterns = patterns('',
    url(r'^$', index, name="templated_emails_index"),
    url(r'^view(?P<path>[\w.+-_/]+)$', view, name="templated_email_view"),
)
