from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


class ClientTest(TestCase):
    def setUp(self):
        self.client = Client()


class IndexTest(ClientTest):
    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)