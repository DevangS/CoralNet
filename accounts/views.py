from guardian.decorators import permission_required_or_403
from userena.decorators import secure_required
import userena.views as userena_views
from accounts.forms import UserAddForm

@secure_required
@permission_required_or_403('auth.add_user')
def user_add(request):
    """
    Add a user using a subclass of Userena's SignupForm,
    which takes care of Profile creation, adding necessary
    user permissions, password generation, and sending an
    activation email.
    """
    return userena_views.signup(
        request,
        signup_form=UserAddForm,
        template_name='accounts/user_add_form.html',
    )
