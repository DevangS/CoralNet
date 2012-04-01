from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render_to_response
from django.template.context import RequestContext
from guardian.decorators import permission_required_or_403
from userena.decorators import secure_required
from accounts.forms import UserAddForm

@secure_required
@permission_required_or_403('auth.add_user')
def user_add(request):
    """
    Add a user using a subclass of Userena's SignupForm,
    which takes care of Profile creation, adding necessary
    user permissions, password generation, and sending an
    activation email.

    The only reason this doesn't use userena.views.signup is
    that userena.views.signup logs out the current user (the
    admin user) after a user is added. (That makes sense for
    creating an account for yourself, but not for creating
    someone else's account.)
    """
    form = UserAddForm()

    if request.method == 'POST':
        form = UserAddForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()

            redirect_to = reverse(
                'userena_signup_complete',
                kwargs={'username': user.username}
            )
            return redirect(redirect_to)

    return render_to_response('accounts/user_add_form.html', {
        'form': form,
        },
        context_instance=RequestContext(request)
    )
