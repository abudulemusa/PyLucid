# coding: utf-8

"""
    PyLucid extrahead
    ~~~~~~~~~~~~~~~~~

    Stores extra JS/CSS head content.
    A instance would be added to request.PYLUCID.extrahead in:
        pylucid.system.pylucid_objects

    Used in e.g.:
        pylucid_plugin.extrahead.context_middleware
        pylucid.shortcuts.render_pylucid_response

    :copyleft: 2009-2012 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


import os
import inspect

from django.conf import settings
from django_tools.utils.messages import failsafe_message


FILEPATH_SPLIT = "pylucid_project"

DEBUG_INFO = """\
<!-- extrahead %(kind)s from %(fileinfo)s - START -->
%(content)s
<!-- extrahead %(kind)s from %(fileinfo)s - END -->"""


class ExtraHeadBase(list):
    """
    Simple store extra html head content from plugins.
    """
    def __init__(self, *args, **kwargs):
        super(ExtraHeadBase, self).__init__(*args, **kwargs)

        if settings.DEBUG:
            # For self._get_fileinfo():
            self.basename = os.path.basename(__file__)
            if self.basename.endswith(".pyc"):
                # cut: ".pyc" -> ".py"
                self.basename = self.basename[:-1]

            if self.kind == "js":
                # Turn debug mode in JavaScript on
                list.append(self, DEBUG_INFO % {
                        "fileinfo": os.path.basename(__file__),
                        "content": (
                            '<script type="text/javascript">'
                            'var debug=true;'
                            'log("debug is on");'
                            '</script>'
                        ),
                        "kind": self.kind,
                    }
                )

    def append(self, content):
        """ add new content """
        content = content.strip()
        if settings.DEBUG:
            # Add debug info around content.
            fileinfo = self._get_fileinfo()
            content = DEBUG_INFO % {
                "fileinfo": fileinfo,
                "content": content,
                "kind": self.kind,
            }
            # Check kind in a simple way
            if self.kind == "js":
                if "</style>" in content or '<link rel="stylesheet"' in content:
                    failsafe_message("Waring: Seems that extrahead (for JS only) contains styles!")
            elif self.kind == "css":
                if "</script>" in content:
                    failsafe_message("Waring: Seems that extrastyle (for CSS only) contains javascript!")
            else:
                raise RuntimeError()

        list.append(self, content)

    def get(self):
        """ return all extra head content """
        return "\n".join(self)

    def _get_fileinfo(self):
        """ return fileinfo: Where from the extra head content comes? """
        try:
            for stack_frame in inspect.stack():
                filepath = stack_frame[1]
                lineno = stack_frame[2]

                # go forward in the stack, to outside of this file.
                if os.path.basename(filepath) != self.basename:
                    break

            filepath = "..." + filepath.split(FILEPATH_SPLIT, 1)[1]
            return "%s line %s" % (filepath, lineno)
        except Exception, e:
            return "(inspect Error: %s)" % e


class ExtraHead(ExtraHeadBase):
    kind = "js"

class ExtraStyle(ExtraHeadBase):
    kind = "css"
