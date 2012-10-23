# coding: utf-8

"""
    PyLucid sitemap
    ~~~~~~~~~~~~~~~

    ToDo: Use the Template to generate the Sitemap tree.
    But there is no recuse-Tag in the django template engine :(
    - http://www.python-forum.de/topic-9655.html
    - http://groups.google.com/group/django-users/browse_thread/thread/3bd2812a3d0f7700/14f61279e0e9fd90

    :copyleft: 2007-2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v2 or above, see LICENSE for more details
"""


from pylucid_project.apps.pylucid.decorators import render_to
from pylucid_project.apps.pylucid.models import PageTree
from pylucid_project.apps.pylucid.system.pylucid_plugin import build_template_names


@render_to()
def lucidTag(request):
    """ Create the sitemap tree """
    user = request.user

    # Get a pylucid.tree_model.TreeGenerator instance with all accessible PageTree for the current user
    tree = PageTree.objects.get_tree(user, filter_showlinks=True)

    # add all PageMeta objects into tree
    tree.add_pagemeta(request)

    #tree.debug()

    context = {
        "nodes": tree.get_first_nodes(),
        "template_name": build_template_names(request, "SiteMap/SiteMap.html"),
    }
    return context
