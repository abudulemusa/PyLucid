# coding:utf-8

from pprint import pformat

from django import forms
from django.db import models
from django.conf import settings
from django.core import urlresolvers
from django.db import connection, backend
from django.template import RequestContext
from django.contrib.sites.models import Site
from django.shortcuts import render_to_response
from django.views.debug import get_safe_settings
from django.utils.importlib import import_module
from django.db.models import get_apps, get_models
from django.contrib.auth.models import User, Group, Permission
from django.utils.translation import ugettext_lazy as _

from pylucid.markup import hightlighter
from pylucid.decorators import check_permissions, render_to

from pylucid_admin.admin_menu import AdminMenu

def install(request):
    """ insert PyLucid admin views into PageTree """
    output = []

    admin_menu = AdminMenu(request, output)
    menu_section_entry = admin_menu.get_or_create_section("internals")

    admin_menu.add_menu_entry(
        parent=menu_section_entry,
        name="form generator", title="Form generator from existing models.",
        url_name="Internal-form_generator"
    )
    admin_menu.add_menu_entry(
        parent=menu_section_entry,
        name="show internals", title="Display some internal information.",
        url_name="Internal-show_internals"
    )

    return "\n".join(output)

#-----------------------------------------------------------------------------

@check_permissions(superuser_only=True)
@render_to("internals/show_internals.html")
def show_internals(request):
    apps_info = []
    for app in get_apps():
        model_info = []
        for model in get_models(app):
            model_info.append({
                "name":model._meta.object_name,
            })
        apps_info.append({
            "app_name": app.__name__,
            "app_models": model_info,
        })

    # from http://www.djangosnippets.org/snippets/1434/
    # generate a list of (pattern-name, pattern) tuples
    resolver = urlresolvers.get_resolver(None)
    print resolver.reverse_dict.items()
    urlpatterns = sorted([
        (key, value[0][0][0])
        for key, value in resolver.reverse_dict.items()
        if isinstance(key, basestring)
    ])

    context = {
        "title": "Show internals",

        "permissions": Permission.objects.all(),

        "urlpatterns": urlpatterns,
        "settings": hightlighter.make_html(pformat(get_safe_settings()), source_type="py"),

        "db_backend_name": backend.Database.__name__,
        "db_backend_module": backend.Database.__file__,
        "db_backend_version": getattr(backend.Database, "version", "?"),

        "apps_info": apps_info,

        "db_table_names": sorted(connection.introspection.table_names()),
        "django_tables": sorted(connection.introspection.django_table_names()),

        "request_meta": hightlighter.make_html(pformat(request.META), source_type="py"),
    }
    return context

    return render_to_response('internals/show_internals.html', context,
        context_instance=RequestContext(request)
    )

#-----------------------------------------------------------------------------

def textform_for_model(model):
    """
    based on http://www.djangosnippets.org/snippets/458/
    """
    opts = model._meta
    field_list = []
    for f in opts.fields + opts.many_to_many:
        if not f.editable:
            continue
        formfield = f.formfield()
        if formfield:
            kw = []
            for a in  ('queryset', 'maxlength', 'label', 'initial', 'help_text', 'required'):
                if hasattr(formfield, a):
                    attr = getattr(formfield, a)
                    if a in ("label", "help_text"): # "translate" lazy text
                        attr = unicode(attr)

                    if attr in [True, False, None]:
                        if a == 'required' and attr == True: # Don't add default
                            continue
                        if a == 'initial' and attr == None: # Don't add default
                            continue
                        kw.append("%s=%s" % (a, attr))
                    elif a == 'queryset':
                        kw.append("%s=%s" % (a, "%s.objects.all()" % attr.model.__name__))
                    elif attr:
                        kw.append("%s=_('%s')" % (a, attr))

            f_text = "    %s = forms.%s(%s)" % (f.name, formfield.__class__.__name__ , ', '.join(kw))
            field_list.append(f_text)
    return "class %sForm(forms.Form):\n" % model.__name__ + '\n'.join(field_list)


@check_permissions(superuser_only=True)
@render_to("internals/form_generator.html")
def form_generator(request, model_no=None):
    apps = models.get_apps()
    app_models = []
    for app in apps:
        app_models += models.get_models(app)

    models_dict = {}
    for no, model in enumerate(app_models):
        models_dict[no] = model

    if model_no:
        model = models_dict[int(model_no)]
        sourcecode = textform_for_model(model)

        output = hightlighter.make_html(sourcecode, source_type="py")
    else:
        output = None

    context = {
        "title": "Form generator",
        "models_dict": models_dict,
        "output": output,
    }
    return context