from django.template.loader_tags import ExtendsNode
from django.conf import settings
import re

def recursive_block_replace(template, data=None, replace_static_url=True, replace_trans=True,
                            replace_with=True, replace_if=True):
    #check the extends
    # first try to replace with current data
    if isinstance(template.nodelist[0], ExtendsNode):
        # load more data using the current blocks
        data = parse_blocks(template, data)
        data = fill_blocks(template, data)
        return recursive_block_replace(template.nodelist[0].get_parent(""), data)
    else:
        final_string = replace_blocks(template, data)
        if replace_static_url:
            final_string = final_string.replace("{{ STATIC_URL }}", settings.STATIC_URL)
        if replace_trans:
            p = re.compile('(\{% blocktrans .* %\})', re.IGNORECASE)
            final_string = p.sub('', final_string)

            p = re.compile('(\{% blocktrans %\})', re.IGNORECASE)
            final_string = p.sub('', final_string)

            p = re.compile('(\{% endblocktrans %\})', re.IGNORECASE)
            final_string = p.sub('', final_string)

            final_string = re.sub(r"\{% trans (.+) %\}", lambda x: x.group(1)[1:-1], final_string)
        if replace_with:
            p = re.compile('(\{% with .+ %\})', re.MULTILINE|re.IGNORECASE)
            final_string = p.sub('', final_string)

            p = re.compile('(\{% endwith %\})', re.MULTILINE|re.IGNORECASE)
            final_string = p.sub('', final_string)

        if replace_if:
            p = re.compile('(\{% if .+ %\})', re.MULTILINE|re.IGNORECASE)
            final_string = p.sub(lambda x: "<div class='if'>%s</div><div class='if-body'>"%x.group(1), final_string)

            p = re.compile('(\{% endif %\})', re.MULTILINE|re.IGNORECASE)
            final_string = p.sub(lambda x: "</div><div class='end-if'>%s</div>"%x.group(1), final_string)

        return final_string


def replace_blocks(template, data):
    template_string = read_file(template.nodelist[0].source[0].name)
    return replace_string_blocks(template_string, data)


def replace_string_blocks(string, data):
    for key in data:
        regex_string = '\{% block '+key+' %\}([\s\S\n\r\w]*?)\{% endblock %\}'
        p = re.compile(regex_string, re.MULTILINE|re.IGNORECASE)
        string = p.sub(data[key], string)

    # replace the last blocks
    p2 = re.compile('(\{% block [a-zA-Z0-9_]+ %\})', re.MULTILINE|re.IGNORECASE)
    string = p2.sub('', string)

    p2 = re.compile('(\{% endblock %\})', re.MULTILINE|re.IGNORECASE)
    string = p2.sub('', string)

    return string


def fill_blocks(template, data):
    return data


def parse_blocks(template, data):
    data = parse_string_blocks(read_file(template.nodelist[0].source[0].name),
                               data)
    return data


def parse_string_blocks(string, data):
    # find all blocks
    regex = re.compile("\{% block ([a-zA-Z0-9_]+) %\}([\s\S\n\r\w]*?)\{% endblock %\}",
                       re.DOTALL|re.MULTILINE|re.IGNORECASE)
    m = regex.findall(string)
    for item in m:
        print item[0]
        data[item[0]] = item[1]
    return data


def read_file(path):
    file = open(path, "r")
    return file.read()
