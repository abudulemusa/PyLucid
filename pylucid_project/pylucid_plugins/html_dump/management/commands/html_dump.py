# coding: utf-8

"""
    HTML Dump
    ~~~~~~~~~
    
    Create static html cache files.
    
    To browse the snapshot e.g.:
        .../html_snapshot$ python -m SimpleHTTPServer


    :copyleft: 2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

from optparse import make_option
import os
import sys
import time
import codecs
import traceback

if __name__ == "__main__":
    sys.path.insert(0, os.path.expanduser(r"~/page_instance/"))
    os.environ["DJANGO_SETTINGS_MODULE"] = "pylucid_project.settings"
    from django.core import management
    management.call_command("html_dump",
        os.path.expanduser(r"~/page_instance/html_snapshot"),
        page_traceback=True
    )
    sys.exit()

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from django.test.client import Client

from django_tools.unittest_utils.BrowserDebug import debug_response

from pylucid_project.apps.pylucid.models import PageMeta, PageTree, BanEntry



class Command(BaseCommand):
    help = 'create static html snapshot of a PyLucid CMS site'
    args = "output_path"
    option_list = BaseCommand.option_list + (
        make_option('--page_traceback', action='store_true',
            help='Add traceback to error pages.'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError(
                "No output path specified. Please provide the output path in the command line."
            )

        self.stdout.write(u"\nGenerate static html snapshot in:\n")
        self.output_path = os.path.normpath(os.path.abspath(args[0]))
        self.stdout.write(u"%r\n" % self.output_path)

        self.page_traceback = options.get("page_traceback", False)
        self.show_traceback = options.get('traceback', False)

        # Don't add django-process info stat line
        settings.PROCESSINFO.ADD_INFO = False
        settings.DEBUG = True

        BanEntry.objects.all().delete()

        anonymous_user = AnonymousUser()

        root_pagetree = PageTree.objects.get_root_page(user=anonymous_user)
        root_pagemetas = PageMeta.objects.filter(pagetree=root_pagetree)
        context = {"root_pagemetas": root_pagemetas}
        self.create_file_from_templates("/", "html_dump/index_page.html", context)

        client = Client(HTML_DUMP=True)
        page_tree_queryset = PageTree.objects.all_accessible(user=anonymous_user, filter_showlinks=False)
        page_meta_queryset = PageMeta.objects.filter(pagetree__in=page_tree_queryset)
        page_count = 0
        total_start_time = time.time()
        for page_meta in page_meta_queryset:
            page_count += 1
            url = page_meta.get_absolute_url()
            start_time = time.time()
            try:
                response = client.get(url,
                    HTTP_ACCEPT_LANGUAGE=page_meta.language.code
                )
            except Exception, err:
                traceback_string = traceback.format_exc()
                if self.page_traceback or settings.DEBUG or self.show_traceback:
                    msg = traceback_string
                else:
                    msg = err

                self.stderr.write(self.style.ERROR('Error getting %r: %s\n' % (url, msg)))

                if self.page_traceback:
                    context = {"traceback": traceback_string}
                else:
                    context = {}

                self.create_file_from_templates(url, "html_dump/error_page.html", context)
                continue

            render_duration = time.time() - start_time

            status_code = response.status_code
            content_type = response["content-type"].split(";", 1)[0]

            if status_code != 200:
                self.stderr.write(self.style.ERROR("Handle status code %r not implemented, skip. (url: %r)\n" % (status_code, url)))
                debug_response(response);sys.exit()
                continue

            if content_type != "text/html":
                self.stderr.write(self.style.ERROR("Handle content type %r not implemented, skip. (url: %r)\n" % (content_type, url)))
                continue

            if '<ul class="messages">' in response.content:
                self.stderr.write(self.style.NOTICE("Waring: Page contains messages!\n"))

            print "%s - %.2fsec" % (url, render_duration)
            #print url, response.status_code, content_type

            self.create_html_file(url, response.content)
#            break

        total_duration = time.time() - total_start_time
        self.stdout.write(u"\nStore %i pages in %.2fsec.\n" % (page_count, total_duration))

    def create_html_file(self, url, content):
        filepath = os.path.join(self.output_path, url.strip("/"))
        if not os.path.isdir(filepath):
            self.stdout.write(u"Info: Create path: %r\n" % filepath)
            os.makedirs(filepath)

        filename = os.path.join(filepath, "index.html")
        #self.stdout.write(u"Create %r\n" % filename)

        with codecs.open(filename, "w", settings.DEFAULT_CHARSET) as f:
            f.write(content)

        self.stdout.write(u"Saved in %r\n" % filename)

    def create_file_from_templates(self, url, template_name, context):
        content = render_to_string(template_name, context)
        self.create_html_file(url, content)
