from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from lib.tests import ClientTest


class AddUserTest(ClientTest):
    fixtures = ['test_users.json']

    def test_add_user_page(self):
        """Go to the add user page."""
        self.client.login(username='superuser_user', password='secret')
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    # TODO: Add tests that submit the Add User form with errors.

    def test_add_user_success(self):
        """
        Submit the Add User form correctly, follow the activation email's
        link, and check that the new user was added correctly.
        """
        self.client.login(username='superuser_user', password='secret')

        # Submit the add user form.
        new_user_username = 'alice'
        new_user_email = 'alice123@example.com'
        response = self.client.post(reverse('signup'), dict(
            username=new_user_username,
            email=new_user_email,
        ))

        self.assertEqual(len(mail.outbox), 1)
        self.assertRedirects(response, reverse(
            'userena_signup_complete',
            kwargs={'username': new_user_username},
        ))

        # Activation email checks.
        activation_email = mail.outbox[0]
        self.assertEqual(len(activation_email.to), 1)
        self.assertEqual(activation_email.to[0], new_user_email)
        self.assertTrue(new_user_username in activation_email.body)

        # Search the email for the new user's password and activation link.
        # Password: should be preceded with the words "password is:".
        # (Feels hackish to search this way though...)
        # Activation link: should be the only link in the email, i.e.
        # the only "word" with '://' in it.
        activation_link = None
        new_user_password = None
        prev_word = None
        prev_prev_word = None
        for word in activation_email.body.split():
            if prev_prev_word == 'password' and prev_word == 'is:':
                new_user_password = word
            if '://' in word:
                activation_link = word
            prev_prev_word = prev_word
            prev_word = word
        self.assertIsNotNone(new_user_password)
        self.assertIsNotNone(activation_link)

        # Activation link should redirect to the profile detail page...
        response = self.client.get(activation_link)
        self.assertRedirects(response, reverse('userena_profile_detail', kwargs={'username': new_user_username}))
        # ...and should log us in as the new user.
        response = self.client.get(activation_link, follow=True)
        self.assertEqual(response.context['user'].username, new_user_username)
        # In the meantime, check that the new user isn't a superuser.
        self.assertFalse(response.context['user'].is_superuser)
        # TODO: Check various permissions.
        # E.g., can change own email/password, can't change others' email/password, etc.

        # Can we log out and then log back in as the new user?
        self.client.logout()
        self.assertTrue(self.client.login(
            username=new_user_username,
            password=new_user_password,
        ))

class SigninTest(ClientTest):
    fixtures = ['test_users.json']

    def test_signin_success(self):
        """
        Submit the Signin form correctly, then check that we're signed in.
        """
        # TODO: Verify that signing in by email works too
        response = self.client.post(reverse('signin'), follow=True, data=dict(
            identification='normal_user',
            password='secret',
        ))
        # TODO: Test when the user has at least one source (should go to source list)
        self.assertRedirects(response, reverse('source_about'))

        # Check that we're signed in.
        user = User.objects.get(username='normal_user')
        self.assertTrue(self.client.session.has_key('_auth_user_id'))
        self.assertEqual(self.client.session['_auth_user_id'], user.pk)

