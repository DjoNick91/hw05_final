from django.test import TestCase, Client
from http import HTTPStatus


class ViewTestClass(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_error_page(self):
        """Тестирование страницы 404"""
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
