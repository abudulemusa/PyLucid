# coding: utf-8

"""
    PyLucid plugin API unittest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Test the plugin API with the unittest plugin. This plugin would be
    symlinked into "./pylucid_project/pylucid_plugins/" before the test
    starts. This would be done in pylucid_project.tests.test_tools.test_runner.

    Last commit info:
    ~~~~~~~~~~~~~~~~~
    $LastChangedDate:$
    $Rev:$
    $Author: JensDiemer $

    :copyleft: 2009 by the PyLucid team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import test_tools # before django imports!

from django.conf import settings

from django_tools.unittest import unittest_base

from pylucid_project.tests.test_tools.pylucid_test_data import TestSites, TestLanguages
from pylucid_project.tests.test_tools import basetest
from pylucid_project.tests import unittest_plugin

UNITTEST_GET_PREFIX = "?%s=" % unittest_plugin.views.GET_KEY




class PluginGetViewTest(basetest.BaseUnittest):
    def test_get_view_none_response(self):
        """ http_get_view() returns None, the normal PageContent would be used. """
        url = UNITTEST_GET_PREFIX + unittest_plugin.views.ACTION_NONE_RESPONSE
        response = self.client.get(url)
        self.assertResponse(response,
            must_contain=(
                '1-rootpage content', # PageContent
                '<title>1-rootpage title',
            ),
            must_not_contain=(
                "Traceback",
                unittest_plugin.views.STRING_RESPONSE,
            ),
        )
        
    def test_get_view_string_response(self):
        """ http_get_view() returns a string, witch replace the PageContent. """
        url = UNITTEST_GET_PREFIX + unittest_plugin.views.ACTION_STRING_RESPONSE
        response = self.client.get(url)
        self.assertResponse(response,
            must_contain=(
                unittest_plugin.views.STRING_RESPONSE,
                '<title>1-rootpage title',
            ),
            must_not_contain=(
                "Traceback",
                '1-rootpage content', # normal page content
            ),
        )
        
    def test_get_view_HttpResponse(self):
        """ http_get_view() returns a django.http.HttpResponse object. """
        url = UNITTEST_GET_PREFIX + unittest_plugin.views.ACTION_HTTP_RESPONSE
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.content, unittest_plugin.views.HTTP_RESPONSE)
        
    def test_get_view_Redirect(self):
        """ http_get_view() returns a django.http.HttpResponseRedirect object. """
        url = UNITTEST_GET_PREFIX + unittest_plugin.views.ACTION_REDIRECT
        response = self.client.get(url)
        self.assertRedirects(response, expected_url=unittest_plugin.views.REDIRECT_URL, status_code=302)


class PluginPageTest(basetest.BaseUnittest):
    def test_root_page(self):
        """
        Test the root view on all sites and in all test languages.
        """
        for site in TestSites():
            for language in TestLanguages():
                url = "/%s/%s/" % (language.code, unittest_plugin.PLUGIN_PAGE_URL)
                response = self.client.get(url)
                self.assertContentLanguage(response, language.code)
                self.assertResponse(response,
                    must_contain=(
                        unittest_plugin.views.PLUGINPAGE_ROOT_STRING_RESPONSE,
                        '3-pluginpage title (lang:%(lang)s, site:%(site_name)s) %(site_name)s' % {
                            "lang": language.code,
                            "site_name": site.name,
                        },
                    ),
                    must_not_contain=(
                        "Traceback",
                        '1-rootpage content', # normal page content
                    ),
                )
                
    def test_urls_args(self):
        """ Test arguments in urls. """
        test_no = 0
        for site in TestSites():
            for language in TestLanguages():
                test_no += 1
                site_name = site.name.replace(" ", "-")
                url = "/%s/%s/args_test/url_arg_%s/%s/" % (
                    language.code, unittest_plugin.PLUGIN_PAGE_URL, test_no, site_name
                )
                response = self.client.get(url)
                self.failUnlessEqual(response.status_code, 200)
                should_be = "%s [u'url_arg_%s'] [u'%s']" % (
                    unittest_plugin.views.PLUGINPAGE_URL_ARGS_PREFIX, test_no, site_name
                )
                self.failUnlessEqual(response.content, should_be)
        
    def test_HttpResponse(self):
        """
        Test a "url sub view" unittest_plugin.test_HttpResponse().
        The view returns a HttpResponse object.
        """
        url = "/%s/%s/test_HttpResponse/" % (self.default_lang_code, unittest_plugin.PLUGIN_PAGE_URL)
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.content, unittest_plugin.views.PLUGINPAGE_HTTP_RESPONSE)

    def test_plugin_template(self):
        """ Test the render_to_response() with own template witch use {% extends template_name %} """
        for site in TestSites():
            for language in TestLanguages():
                url = "/%s/%s/test_plugin_template/" % (language.code, unittest_plugin.PLUGIN_PAGE_URL)
                response = self.client.get(url)
                self.assertResponse(response,
                    must_contain=(
                        unittest_plugin.views.PLUGINPAGE_TEMPLATE_RESPONSE,
                        '3-pluginpage title (lang:%(lang)s, site:%(site_name)s) %(site_name)s' % {
                            "lang": language.code,
                            "site_name": site.name,
                        },
                    ),
                    must_not_contain=(
                        "Traceback",
                        '1-rootpage content', # normal page content
                    ),
                )

    def test_return_none(self):
        """ Test if a PagePlugin returns None -> This must raise a error. """
        url = "/%s/%s/test_return_none/" % (self.default_lang_code, unittest_plugin.PLUGIN_PAGE_URL)
        self.assertRaises(RuntimeError, self.client.get, url)
    
    def test_url_reverse(self):
        """ Test the django url reverse function in a PagePlugin. """
        for language in TestLanguages():
            url_prefix = "/%s/%s" % (language.code, unittest_plugin.PLUGIN_PAGE_URL)
            url_data = {
                "UnittestPlugin-view_root": "%s/" % url_prefix,
                "UnittestPlugin-test_HttpResponse": "%s/test_HttpResponse/" % url_prefix,
            }
            
            for url_name, sould_url in url_data.iteritems():
                url = "%s/test_url_reverse/%s/" % (url_prefix, url_name)
                response = self.client.get(url)
                self.failUnlessEqual(response.status_code, 200)
                should_be = "%s ['%s']" % (unittest_plugin.views.PLUGINPAGE_URL_REVERSE_PREFIX, sould_url)
                self.failUnlessEqual(response.content, should_be)

    def test_PyLucid_api(self):
        """ Test the PyLucid API """
        for site in TestSites():
            for language in TestLanguages():
                url = "/%s/%s/test_PyLucid_api/" % (language.code, unittest_plugin.PLUGIN_PAGE_URL)
                response = self.client.get(url)
                self.assertResponse(response,
                    must_contain=(
                        unittest_plugin.views.PLUGINPAGE_API_TEST_PAGE_MSG,
                        unittest_plugin.views.PLUGINPAGE_API_TEST_CONTENT,
                        '3-pluginpage title (lang:%(lang)s, site:%(site_name)s) %(site_name)s' % {
                            "lang": language.code,
                            "site_name": site.name,
                        },
                        "context_middlewares: {u&#39;breadcrumb&#39;: &lt;pylucid_plugins.breadcrumb",
                        "default_lang_code: %s" % self.default_lang_code,
                        "default_lang_entry: &lt;Language: Language %s" % self.default_lang_code,
                        "lang_entry: &lt;Language: Language %s" % language.code,
                        (
                            "page_template: u&#39;&lt;html&gt;&lt;head&gt;&lt;title&gt;"
                            "{{ page_title }} %s&lt;/title&gt;"
                        ) % site.name,
                        (
                            "pagetree: &lt;PageTree: PageTree &#39;3-pluginpage&#39;"
                            " (site: %s, type: PluginPage)&gt;"
                        ) % site.name,
                        "system_preferences: {&#39;lang_code&#39;: u&#39;%s&#39;}" % self.default_lang_code,
                    ),
                    must_not_contain=(
                        "Traceback",
                        '1-rootpage content', # normal page content
                    ),
                )


if __name__ == "__main__":
    # Run this unitest directly
    unittest_base.direct_run(__file__)