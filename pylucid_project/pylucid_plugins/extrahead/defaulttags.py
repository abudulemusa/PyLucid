# coding: utf-8

"""
    PyLucid {% extrahead %} block tag
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Simple django template block tag. "Redirect" extra head content
    into request.PYLUCID.extrahead
    This data would be inserted with pylucid_plugin.extrahead.context_middleware
    
    PyLucid plugins should use {% extrahead %} block tag in plugin template for
    insert e.g. CSS/JS file links into html head.

    :copyleft: 2009-2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details
"""

from django import template

register = template.Library()

JAVASCRIPT=1
STYLESHEETS=2


@register.tag
def extrahead(parser, token):
    nodelist = parser.parse(('endextrahead',))
    parser.delete_first_token()
    return ExtraheadNode(nodelist, kind=JAVASCRIPT)


@register.tag
def extrastyle(parser, token):
    nodelist=parser.parse(('endextrastyle',))
    parser.delete_first_token()
    return ExtraheadNode(nodelist, kind=STYLESHEETS)


class ExtraheadNode(template.Node):
    def __init__(self, nodelist, kind):
        self.nodelist = nodelist
        self.kind=kind

    def render(self, context):
        """ put head data into pylucid_plugin.head_files.context_middleware """
        output = self.nodelist.render(context)
        try:
            request = context["request"]
        except KeyError:
            raise RuntimeError("Plugin must use RequestContext() or request.PYLUCID.context !")

        if self.kind==JAVASCRIPT:
            obj=request.PYLUCID.extrahead
        elif self.kind==STYLESHEETS:
            obj=request.PYLUCID.extrastyle
        else:
            raise RuntimeError("unknwon kind: %s"%repr(self.kind))

        # FIXME: We check double extrahead entries, but only the whole block. This doesn't work good.
        #        We should check the real link path of every JS/CSS file here.
        if output not in obj:
            obj.append(output)
#            messages.info(request, "Insert extrahead:", output)
#        else:
#            messages.info(request, "Skip extrahead:", output)
        return u""
