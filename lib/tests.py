# Tests for non-app-specific pages.
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from lib import msg_consts, str_consts
from lib.test_utils import ClientTest


class IndexTest(ClientTest):
    """
    Test the site index page.
    """
    def test_index(self):
        response = self.client.get(reverse('index'))
        self.assertStatusOK(response)


class ContactTest(ClientTest):
    """
    Test the Contact Us page.
    """
    fixtures = ['test_users.yaml']

    def test_contact_success(self):
        username = 'user2'
        user_email = User.objects.get(username='user2').email
        self.client.login(username=username, password='secret')

        # Reach the page
        response = self.client.get(reverse('contact'))
        self.assertStatusOK(response)

        # Submit the form
        subject = "Subject goes here"
        message = "Message\ngoes here."
        response = self.client.post(reverse('contact'), dict(
            subject=subject,
            message=message,
        ))
        self.assertStatusOK(response)
        # Check that we got the expected top-of-page message.
        self.assertMessages(
            response,
            [msg_consts.CONTACT_EMAIL_SENT],
        )

        # Check that 1 email was sent.
        self.assertEqual(len(mail.outbox), 1)
        contact_email = mail.outbox[0]

        # Check that the email's "to" field is equal to settings.ADMINS.
        self.assertEqual(len(contact_email.to), len(settings.ADMINS))
        for admin_name, admin_email in settings.ADMINS:
            self.assertIn(admin_email, contact_email.to)

        # Check the subject.
        self.assertEqual(
            contact_email.subject,
            "{prefix}{unprefixed_subject}".format(
                prefix=settings.EMAIL_SUBJECT_PREFIX,
                unprefixed_subject=str_consts.CONTACT_EMAIL_SUBJECT_FMTSTR.format(
                    username=username,
                    base_subject=subject,
                )
            ),
        )
        if settings.UNIT_TEST_VERBOSITY >= 1:
            print "Email subject:\n{subject}".format(subject=contact_email.subject)

        # Check the message/body.
        self.assertEqual(
            contact_email.body,
            str_consts.CONTACT_EMAIL_MESSAGE_FMTSTR.format(
                username=username,
                user_email=user_email,
                base_message=message,
            ),
        )
        if settings.UNIT_TEST_VERBOSITY >= 1:
            print "Email message:\n{message}".format(message=contact_email.body)

    def test_contact_errors(self):
        self.client.login(username='user2', password='secret')

        response = self.client.get(reverse('contact'))
        self.assertStatusOK(response)

        # TODO: Trigger the 'field is required' errors.

        # TODO: See if you can get character limit errors. They might be
        # possible with manually crafted POST requests.

        # TODO: Any way to get a BadHeaderError from the user's subject and
        # message input? Maybe some special characters in the subject, like
        # a newline? That could be possible with manually crafted POST
        # requests.