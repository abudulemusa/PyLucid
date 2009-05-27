# coding:utf-8

import test_tools # before django imports!

from django.conf import settings
from django.test import TransactionTestCase

from django_tools.unittest.unittest_base import BaseTestCase, direct_run


class AdminSiteTest(BaseTestCase, TransactionTestCase):
    ADMIN_SITE_URL = '/%s/' % settings.ADMIN_URL_PREFIX
    
    def test_login_page(self):
        response = self.client.get(self.ADMIN_SITE_URL)
        self.assertResponse(response,
            must_contain=("PyLucid", "PyLucid - Log in"),
            must_not_contain=("error", "Traceback")
        )
        
    def test_summary_page(self):
        self.login(usertype="superuser")
        response = self.client.get(self.ADMIN_SITE_URL)
        self.assertResponse(response,
            must_contain=("PyLucid", "Page trees", "Page contents"),
            must_not_contain=("Log in", "error", "Traceback")
        )


if __name__ == "__main__":
    # Run this unitest directly
    direct_run(__file__)