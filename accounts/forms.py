from userena.forms import SignupForm
from userena.models import UserenaSignup
from accounts.utils import send_activation_email_with_password
from CoralNet.utils import rand_string

class UserAddForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)
        # The password will be auto-generated; no need for password fields.
        del self.fields['password1']
        del self.fields['password2']

    def clean(self):
        # Password field checking doesn't apply.
        return self.cleaned_data

    def save(self):
        # Randomly generate a password.
        username, email, password = (self.cleaned_data['username'],
                                     self.cleaned_data['email'],
                                     rand_string(10))

        new_user = UserenaSignup.objects.create_inactive_user(username, email, password, send_email=False)

        # Send the activation email. Include the generated password.
        userena_signup_obj = UserenaSignup.objects.get(user__username=username)
        send_activation_email_with_password(userena_signup_obj, password)

        return new_user
