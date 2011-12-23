# -*- coding: utf-8 -*-
from django.utils import unittest
from django.test import TestCase
from .parse_util import parse_string_blocks, replace_blocks, replace_string_blocks


test_extraction_string =  """{% block test %}tr
 st

 sdf{% endblock %}"""

test_extraction_string2 = """{% block test123 %}tr s123t sdf{% endblock %}"""

test_extraction_string3 = """{% block test123 %}
            tr s123t sdf
{% endblock %}

{% block test %}test{% endblock %}
"""

test_extraction_string4 = """{% extends "emails/email.html" %}\n{% load gidsy_tags %}\n{% load profile_tags %}\n{% load account_tags %}\n{% load currency_tags %}\n{% block title %}\n  {% trans "All the best," %}\n{% endblock %}{% block message_title %}{% trans "Sorry! Not enough people booked" %} "{{ activity }}."{% endblock %}\n{% block email_notification %}{% trans "Your activity will not be taking place" %}{% endblock %}\n{% block email_title %}{% random_greeting %} {{ user.first_name }},{% endblock %}\n{% block email_subtitle %}\n  <h3>\n    {% blocktrans with slot=booking.slot min_participants=slot.get_min_participants start_date=slot.start_time|date:"l, F j" start_time=slot.start_time|date:"P" %}\n      We\'re sorry! Not enough people booked &quot;{{ activity }}&quot; on <strong>{{ start_date }}</strong> at <strong>{{ start_time }}</strong> for it to happen.\n    {% endblocktrans %}\n  </h3>\n{% endblock %}\n{% block email_message %}\n    <p>\n      {% blocktrans with confirmed_bookings=slot.booked_spots %}\n        To avoid disappointment in future, make sure to check before booking an activity how far it is from getting its minimum number of participants. \n      {% endblocktrans %}\n    </p>\n    {% if other_activities %}\n    <p>\n      You may also be interested in these other [link: activities] that already have enough people attending: (list 3 activities here)\n    </p>\n    {% endif %}\n{% endblock %}\n\n{% block signature %}\n  {% trans "All the best," %}\n{% endblock %}"""
test_replace_string = """<html>{% block test123 %}{% endblock %}</html>"""


class BlockExtraction(TestCase):
    def test_extraction(self):
        self.assertEquals("""tr
 st

 sdf""", parse_string_blocks(test_extraction_string, {})["test"])

        self.assertEquals("tr s123t sdf", parse_string_blocks(test_extraction_string2, {})["test123"])
        data = parse_string_blocks(test_extraction_string3, {})
        self.assertEquals("""
            tr s123t sdf
""",data["test123"])
        self.assertEquals("""test""",data["test"])

    def test_full_extraction(self):
        data = parse_string_blocks(test_extraction_string4, {})
        print data
        self.assertTrue(data.get("message_title", False))
        self.assertTrue(data.get("email_notification", False))
        self.assertTrue(data.get("email_title", False))
        self.assertTrue(data.get("email_subtitle", False))
        self.assertTrue(data.get("signature", False))
        self.assertTrue(data.get("title", False))
                
    def test_replace_blocks(self):
        self.assertEqual("<html>test</html>", replace_string_blocks(test_replace_string, {"test123": "test"}))