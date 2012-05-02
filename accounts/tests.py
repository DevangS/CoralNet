from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from lib.test_utils import ClientTest


class AddUserTest(ClientTest):
    fixtures = ['test_users.yaml']

    def test_add_user_page(self):
        """Go to the add user page."""
        self.client.login(username='superuser_user', password='secret')
        response = self.client.get(reverse('signup'))
        self.assertStatusOK(response)

    # TODO: Add tests that submit the Add User form with errors.
    # TODO: Add a test (or modify an old test?) to check that a new, unactivated user can't login yet.

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

        # Check various permissions.
        self.assertFalse(response.context['user'].is_superuser)
        # Should be able to access own account or profile functions, but not
        # others' account or profile functions.
        for url_name in ['userena_email_change',
                         'userena_password_change',
                         'userena_profile_edit',
                         ]:
            response = self.client.get(reverse(url_name, kwargs={'username': new_user_username}))
            self.assertStatusOK(response)
            self.assertTemplateNotUsed(response, 'permission_denied.html')
            response = self.client.get(reverse(url_name, kwargs={'username': 'superuser_user'}))
            self.assertEqual(response.status_code, 403)

        # Can we log out and then log back in as the new user?
        self.client.logout()
        self.assertTrue(self.client.login(
            username=new_user_username,
            password=new_user_password,
        ))

class SigninTest(ClientTest):
    fixtures = ['test_users.yaml']

    def test_signin_page(self):
        """Go to the signin page while logged out."""
        response = self.client.get(reverse('signin'))
        self.assertStatusOK(response)

    # TODO: Add tests that submit the signin form with errors.

    def signin_success(self, identification_method, remember_me):
        """
        Submit the Signin form correctly, then check that we're signed in.
        """
        if identification_method == 'username':
            identification = 'user2'
            user = User.objects.get(username=identification)
        elif identification_method == 'email':
            identification = 'user2@example.com'
            user = User.objects.get(email=identification)
        else:
            raise ValueError('Invalid identification method.')

        # TODO: Test for cookies when remember_me=True?
        response = self.client.post(reverse('signin'), follow=True, data=dict(
            identification=identification,
            password='secret',
            remember_me=remember_me,
        ))
        # TODO: Test when the user has at least one source (should go to source list)
        self.assertRedirects(response, reverse('source_about'))

        # Check that we're signed in.
        self.assertTrue(self.client.session.has_key('_auth_user_id'))
        self.assertEqual(self.client.session['_auth_user_id'], user.pk)

        # Log out to prepare for a possible next test run of this function
        # with different parameters.
        self.client.logout()

    def test_signin_success(self):
        self.signin_success(identification_method='username', remember_me=True)
        self.signin_success(identification_method='username', remember_me=False)
        self.signin_success(identification_method='email', remember_me=True)
        self.signin_success(identification_method='email', remember_me=False)

