# Utility classes and functions for tests.
import os
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.simple import DjangoTestSuiteRunner
from userena.managers import UserenaManager
from CoralNet.exceptions import TestfileDirectoryError
from images.models import Source


class MyTestSuiteRunner(DjangoTestSuiteRunner):
    def setup_test_environment(self, **kwargs):
        DjangoTestSuiteRunner.setup_test_environment(self, **kwargs)

        # Directories for media and processing files that are
        # used or generated during unit tests.
        settings.MEDIA_ROOT = settings.TEST_MEDIA_ROOT
        settings.PROCESSING_ROOT = settings.TEST_PROCESSING_ROOT

        # The Celery daemon uses the regular Django database, while
        # the testing framework uses a separate database.  Therefore,
        # we can't get task results from the daemon during a test.
        #
        # The best solution for now is to not use the daemon, and
        # simply block and wait for the result as the task runs.
        # More info: http://docs.celeryproject.org/en/latest/django/unit-testing.html
        settings.CELERY_ALWAYS_EAGER = True


class BaseTest(TestCase):
    fixtures = []
    source_member_roles = []
    extra_components = []

    def __init__(self, *args, **kwargs):
        TestCase.__init__(self, *args, **kwargs)
        self.extra_components = [cls() for cls in self.extra_components]

    def setUp(self):
        self.setAccountPerms()
        self.setTestSpecificPerms()
        for component in self.extra_components:
            component.setUp()

    def tearDown(self):
        for component in self.extra_components:
            component.tearDown()

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
        Set permissions specific to the test class, e.g. source permissions.
        This has two advantages over specifying permissions in fixtures:
        (1) Can easily set permissions specific to a particular test class.
        (2) It's tedious to specify permissions in fixtures.
        """
        for role in self.source_member_roles:
            source = Source.objects.get(name=role[0])
            user = User.objects.get(username=role[1])
            source.assign_role(user, role[2])


class ClientTest(BaseTest):
    def setUp(self):
        BaseTest.setUp(self)
        self.client = Client()

    def assertStatusOK(self, response):
        self.assertEqual(response.status_code, 200)

    def login_required_page_test(self, protected_url, username, password):
        """
        Going to a login-required page while logged out should trigger a
        redirect to the login page.  Then once the user logs in, they
        should be redirected to the page they requested.
        """
        self.client.logout()
        response = self.client.get(protected_url)

        # This URL isn't built with django.utils.http.urlencode() because
        # (1) urlencode() unfortunately escapes the '/' in its arguments, and
        # (2) str concatenation should be safe when there's no possibility of
        # malicious input.
        url_signin_with_protected_page_next = reverse('signin') + '?next=' + protected_url
        self.assertRedirects(response, url_signin_with_protected_page_next)

        response = self.client.post(url_signin_with_protected_page_next, dict(
            identification=username,
            password=password,
        ))
        self.assertRedirects(response, protected_url)

    def permission_required_page_test(self, protected_url,
                                      denied_users, accepted_users):
        """
        Going to a permission-required page...
        - while logged out: should show the permission-denied template.
        - while logged in as a user without sufficient permission: should
        show the permission-denied template.
        - while logged in a a user with sufficient permission: should show
        the page they requested.
        """
        self.client.logout()
        response = self.client.get(protected_url)
        self.assertStatusOK(response)
        # TODO: Make permission_denied.html a constant
        self.assertTemplateUsed(response, 'permission_denied.html')

        for user in denied_users:
            self.client.login(username=user['username'], password=user['password'])
            response = self.client.get(protected_url)
            self.assertStatusOK(response)
            self.assertTemplateUsed(response, 'permission_denied.html')

        for user in accepted_users:
            self.client.login(username=user['username'], password=user['password'])
            response = self.client.get(protected_url)
            self.assertStatusOK(response)
            self.assertTemplateNotUsed(response, 'permission_denied.html')


class FilesTestComponent(object):
    test_directory = ''
    test_directory_name = ""

    testfile_directory_setup_error_fmtstr = (
        "The test setup routine found files in the {0} directory ({1}):\n"
        "{2}\nPlease check that {0} is set correctly, and check that "
        "all files are cleared from this directory before running the test."
    )
    testfile_directory_teardown_error_fmtstr = (
        "The test teardown routine found unexpected files in the {0} directory ({1})!:\n"
        "{2}\nThese files seem to have been created prior to the test. "
        "Please delete these files or move them elsewhere."
    )

    def raise_testfile_directory_error(self, unexpected_filenames, message_format_str):
        if len(unexpected_filenames) > 10:
            unexpected_filenames_str = '\n'.join(unexpected_filenames[:10]) + "\n(And others)"
        else:
            unexpected_filenames_str = '\n'.join(unexpected_filenames)
        error_message = message_format_str.format(
            self.test_directory_name, self.test_directory, unexpected_filenames_str)
        raise TestfileDirectoryError(error_message)


    # TODO: Decide whether to on-the-fly generate subdirectories that are
    # needed, or expect that the subdirectories are there to begin with.
    # On-the-fly generation requires changes to the actual application code.

    def setUp(self):
        unexpected_filenames = []
        # The test-file directory must have no files prior to the test.
        for dirname, dirnames, filenames in os.walk(self.test_directory):
            for filename in filenames:
                unexpected_filenames.append(os.path.join(dirname, filename))

                # If we find enough unexpected files, just abort.
                # No need to burn resources listing all the unexpected files.
                if len(unexpected_filenames) > 10:
                    self.raise_testfile_directory_error(unexpected_filenames, self.testfile_directory_setup_error_fmtstr)

        if unexpected_filenames:
            self.raise_testfile_directory_error(unexpected_filenames, self.testfile_directory_setup_error_fmtstr)
#            raise TestfileDirectoryError("The test setup routine found files in the {0} directory ({1}):\n{2}"
#            " Please check that {0} is set correctly, and that all files are cleared from this directory before running the test.".format(
#                self.test_directory_name, self.test_directory, unexpected_filenames_str))

        # If you want to test the ability to detect unexpected files
        # on tearDown, stick some code right here to add files to the
        # test-file directory.

#        if self.test_directory_name == 'TEST_PROCESSING_ROOT':
#            for i in range(0,10):
#                f = open(os.path.join(settings.TEST_PROCESSING_ROOT, 'stuff{0}.txt'.format(i)), 'w')
#                f.close()

        # Save a timestamp just before the tests start.
        # This will allow an extra sanity check in tearDown().
        self.timestamp_before_tests = datetime.datetime.now()

    def tearDown(self):
        unexpected_filenames = []
        # Walk recursively through the test-file directory.
        # Delete files that were generated by the test.  Raise an error
        # if unidentified files are found.
        for dirname, dirnames, filenames in os.walk(self.test_directory):
            for filename in filenames:
                leftover_test_filename = os.path.join(dirname, filename)
                ctime = os.stat(leftover_test_filename).st_ctime

                if datetime.datetime.fromtimestamp(ctime) < self.timestamp_before_tests:
                    # The file was created or moved to this directory before the test started.
                    # It doesn't belong here! (This is a real corner case because the
                    # file needs to materialize in the directory AFTER the setUp check...
                    # but we want to be really careful about file deletions.)
                    unexpected_filenames.append(leftover_test_filename)
                else:
                    # It's a file generated by the test; remove it.
                    os.remove(leftover_test_filename)

        if unexpected_filenames:
            self.raise_testfile_directory_error(unexpected_filenames, self.testfile_directory_teardown_error_fmtstr)
#            if len(unexpected_filenames) > 10:
#                unexpected_filenames_str = '\n'.join(unexpected_filenames[:10]) + "\n(And {0} others)".format(len(unexpected_filenames) - 10)
#            else:
#                unexpected_filenames_str = '\n'.join(unexpected_filenames)
#            error_message = ("The test teardown routine found unexpected files in the {0} directory ({1})!:\n{2}".format(
#                             self.test_directory_name, self.test_directory, unexpected_filenames_str)
#                             + "These files seem to have been created prior to the test. Please delete these files or move them elsewhere.")
#            raise TestfileDirectoryError(error_message)

class MediaTestComponent(FilesTestComponent):
    test_directory = settings.TEST_MEDIA_ROOT
    test_directory_name = "TEST_MEDIA_ROOT"
#    def setUp(self):
#        if os.listdir(settings.TEST_MEDIA_ROOT):
#            raise ValueError("The TEST_MEDIA_ROOT directory ({0}) is not empty. Please make sure that this directory is empty before running this test.".format(settings.TEST_MEDIA_ROOT))
#        self.time_before_tests = datetime.datetime.now()
#    def tearDown(self):
#        pass

class ProcessingTestComponent(FilesTestComponent):
    test_directory = settings.TEST_PROCESSING_ROOT
    test_directory_name = "TEST_PROCESSING_ROOT"
#    def setUp(self):
#        if os.listdir(settings.TEST_PROCESSING_ROOT):
#            raise ValueError("The TEST_PROCESSING_ROOT directory ({0}) is not empty. Please make sure that this directory is empty before running this test.".format(settings.TEST_PROCESSING_ROOT))
#        self.timestamp_before_tests = datetime.datetime.now()
#    def tearDown(self):
#        unexpected_filenames = []
#        for dirname, dirnames, filenames in os.walk(settings.TEST_PROCESSING_ROOT):
#            for filename in filenames:
#                leftover_test_filename = os.path.join(dirname, filename)
#                if os.stat(leftover_test_filename).ctime < self.timestamp_before_tests:
#                    # The file was created before the test started. There's a problem!
#                    unexpected_filenames.append(leftover_test_filename)
#                else:
#                    os.remove(leftover_test_filename)
#        if unexpected_filenames:
#            raise ValueError("There were unexpected files in the TEST_PROCESSING_ROOT directory ({0})!".format(settings.TEST_PROCESSING_ROOT))