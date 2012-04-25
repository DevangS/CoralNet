from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


class IndexTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)


class SourceAboutTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_source_about(self):
        response = self.client.get(reverse('source_about'))
        self.assertEqual(response.status_code, 200)
