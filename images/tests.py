from django.core.urlresolvers import reverse
from lib.tests import ClientTest


class SourceAboutTest(ClientTest):
    def test_source_about(self):
        response = self.client.get(reverse('source_about'))
        self.assertEqual(response.status_code, 200)


class SourceListTest(ClientTest):
    def test_source_list(self):
        # TODO: Add tests of this view for logged in users,
        # as well as tests with actual sources in the database.
        response = self.client.get(reverse('source_list'))
        self.assertRedirects(response, reverse('source_about'))
