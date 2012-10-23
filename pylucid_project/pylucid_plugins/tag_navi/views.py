# coding: utf-8

"""
    PyLucid tag navigation
    ~~~~~~~~~~~~~~~~~~~~~~
    
    A tag based navigation.

    :copyleft: 2008-2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v2 or above, see LICENSE for more details
"""


from django.utils.translation import ugettext as _

# http://code.google.com/p/django-tagging/
from tagging.models import Tag, TaggedItem

from pylucid_project.apps.pylucid.decorators import render_to
from pylucid_project.apps.pylucid.models import PageMeta
from pylucid_project.apps.pylucid.system.pylucid_plugin import build_template_names


@render_to()#, debug=True)
def http_get_view(request):
    tags = request.GET["tag_navi"]
    entries = TaggedItem.objects.get_by_model(PageMeta, tags)

    # add breadcrumb link
    breadcrumb_context_middlewares = request.PYLUCID.context_middlewares["breadcrumb"]
    title = _("All '%s' tagged items" % tags)
    breadcrumb_context_middlewares.add_link(title, title, url=request.get_full_path())

    context = {
        "page_robots": "noindex,nofollow",
        "entries": entries,
        "tags": tags,
        "template_name": build_template_names(request, "tag_navi/tag_list.html"),
    }
    return context


@render_to()#, debug=True)
def lucidTag(request):
    current_pagemeta = request.PYLUCID.pagemeta
    tags = current_pagemeta.tags
    context = {
        "pagemeta": current_pagemeta,
        "template_name": build_template_names(request, "tag_navi/tag_link_list.html"),
    }
    return context
