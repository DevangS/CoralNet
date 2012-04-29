from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from userena.managers import UserenaManager


class BaseTest(TestCase):
    fixtures = []

    def setUp(self):
        self.setAccountPerms()
        self.setTestSpecificPerms()

    def setAccountPerms(self):
        # TODO: is the below necessary, or is adding these permissions done by magic anyway?
        #
        # Give account and profile permissions to each user.
        # It's less annoying to do this dynamically than it is to include
        # the permissions in the fixtures for every user.
        #UserenaManager().check_permissions()
        pass

    def setTestSpecificPerms(self):
        """
        Individual test classes can override this stub method
        to set permissions (source member lists, etc.).
        This has two advantages over specifying permissions in fixtures:
        (1) Each test can set permissions fit for that particular test.
        (2) It's tedious to specify permissions in fixtures.
        """
        pass


class ClientTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.client = Client()


class IndexTest(ClientTest):
    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)