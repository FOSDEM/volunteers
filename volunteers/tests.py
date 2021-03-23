"""
Tests to be run via "manage.py test"
"""

from unittest.mock import patch
from django.test import TestCase
from volunteers.views import promo


class PromoTestCase(TestCase):
    @patch('volunteers.views.render')
    def test_promo_view_renders_static_page(self, render_mock):
        static_promo_page_content = 'Some promo page'
        render_mock.return_value = static_promo_page_content
        ret = promo(None)
        self.assertEqual(ret, static_promo_page_content)
