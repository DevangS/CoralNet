# Tests for non-app-specific pages.
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail, validators
from django.core.urlresolvers import reverse
from lib import msg_consts, str_consts
from lib.forms import ContactForm
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

    def test_contact_error_required(self):
        """
        'field is required' errors.
        """
        self.client.login(username='user2', password='secret')

        # Message is missing.
        response = self.client.post(reverse('contact'), dict(
            subject="Subject goes here",
            message="",
        ))
        self.assertStatusOK(response)
        self.assertMessages(response, [msg_consts.FORM_ERRORS])
        self.assertFormErrors(response, 'contact_form', {
            'message': [forms.Field.default_error_messages['required']],
        })

        # Subject is missing.
        response = self.client.post(reverse('contact'), dict(
            subject="",
            message="Message\ngoes here.",
        ))
        self.assertStatusOK(response)
        self.assertMessages(response, [msg_consts.FORM_ERRORS])
        self.assertFormErrors(response, 'contact_form', {
            'subject': [forms.Field.default_error_messages['required']],
        })

    def test_contact_error_char_limit(self):
        """
        'ensure at most x chars' errors.
        """
        self.client.login(username='user2', password='secret')

        subject_max_length = ContactForm.base_fields['subject'].max_length
        message_max_length = ContactForm.base_fields['message'].max_length

        # Subject and message are too long.
        response = self.client.post(reverse('contact'), dict(
            subject="1"*(subject_max_length+1),
            message="1"*(message_max_length+1),
        ))
        self.assertStatusOK(response)
        self.assertMessages(response, [msg_consts.FORM_ERRORS])
        self.assertFormErrors(response, 'contact_form', {
            'subject': [validators.MaxLengthValidator.message % {
                'limit_value': subject_max_length,
                'show_value': subject_max_length+1,
            }],
            'message': [validators.MaxLengthValidator.message % {
                'limit_value': message_max_length,
                'show_value': message_max_length+1,
            }],
        })

    # TODO: How to test for a BadHeaderError?
    # Putting a newline in the subject isn't getting such an error for me.

#        self.client.login(username='user2', password='secret')
#
#        response = self.client.post(reverse('contact'), dict(
#            subject="Subject goes here\ncc:spamvictim@example.com",
#            message="Message goes here",
#        ))
#
#        self.assertStatusOK(response)
#        self.assertMessages(response, [msg_consts.EMAIL_BAD_HEADER])