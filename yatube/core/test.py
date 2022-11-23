from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase


User = get_user_model()


class CoreTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.client = Client(enforce_csrf_checks=True)
        self.client_02 = Client(enforce_csrf_checks=False)
        cache.clear()

    def test_page_not_found_returns_404(self):
        response = self.client.get('/non-existent/page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_template_custum_404_page(self):
        template = 'core/404.html'
        url_page = '/non-existent/page/'
        response = self.client.get(url_page)
        self.assertTemplateUsed(response, template)

    def test_template_custum_403_page(self):
        response = self.client_02.post('/create/')
        self.assertTrue(response, 'core/403csrf.html')
