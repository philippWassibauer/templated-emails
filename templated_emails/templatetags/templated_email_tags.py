from django.template.base import Library
import textwrap

register = Library()


@register.filter(is_safe=True)
def dedent(text):
    """
    Removes indentation of text. Useful in text emails that otherwise can't be
    indented.

    Example usage::

        {% filter dedent %}
            My text
            {% if something %}
                another text
            {% endif %}
        {% endfilter %}

    This example would return this HTML::

        My text

        another text
    """
    return textwrap.dedent(text)
