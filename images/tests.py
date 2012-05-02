from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from guardian.shortcuts import get_objects_for_user
from images.model_utils import PointGen
from images.models import Source
from lib.tests import ClientTest


class SourceAboutTest(ClientTest):
    """
    Test the About Sources page.
    """
    def test_source_about(self):
        response = self.client.get(reverse('source_about'))
        self.assertEqual(response.status_code, 200)


class SourceListTestWithSources(ClientTest):
    """
    Test the source list page when there's at least one source.
    """

    fixtures = ['test_users.yaml', 'test_sources.yaml']

    def setTestSpecificPerms(self):
        source_member_roles = [
            ('public1', 'user2', Source.PermTypes.ADMIN.code),
            ('public1', 'user4', Source.PermTypes.EDIT.code),
            ('private1', 'user3', Source.PermTypes.ADMIN.code),
            ('private1', 'user4', Source.PermTypes.VIEW.code),
        ]
        for role in source_member_roles:
            source = Source.objects.get(name=role[0])
            user = User.objects.get(username=role[1])
            source.assign_role(user, role[2])

    def source_list_as_user(self, username, password,
                            num_your_sources_predicted,
                            num_other_public_sources_predicted):
        # Sign in
        user = None
        if username is not None:
            user = User.objects.get(username=username)
            self.client.login(username=username, password=password)

        response = self.client.get(reverse('source_list'))

        if user is None or num_your_sources_predicted == 0:
            # Redirects to source_about page
            self.assertRedirects(response, reverse('source_about'))

            # 2 public sources
            response = self.client.get(reverse('source_list'), follow=True)
            public_sources = response.context['public_sources']
            self.assertEqual(len(public_sources), 2)
            for source in public_sources:
                self.assertEqual(source.visibility, Source.VisibilityTypes.PUBLIC)
        else:
            # Goes to source_list page
            self.assertEqual(response.status_code, 200)
            your_sources_predicted = get_objects_for_user(user, Source.PermTypes.VIEW.fullCode)

            # Sources this user is a member of
            your_sources = response.context['your_sources']
            self.assertEqual(len(your_sources), num_your_sources_predicted)
            for source_dict in your_sources:
                source = Source.objects.get(pk=source_dict['id'])
                self.assertTrue(source in your_sources_predicted)
                self.assertEqual(source.get_member_role(user), source_dict['your_role'])

            # Public sources this user isn't a member of
            other_public_sources = response.context['other_public_sources']
            self.assertEqual(len(other_public_sources), num_other_public_sources_predicted)
            for source in other_public_sources:
                self.assertFalse(source in your_sources_predicted)
                self.assertEqual(source.visibility, Source.VisibilityTypes.PUBLIC)

        self.client.logout()

    def test_source_list(self):
        self.source_list_as_user(
            None, None,
            num_your_sources_predicted=0, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'user2', 'secret',
            num_your_sources_predicted=1, num_other_public_sources_predicted=1,
        )
        self.source_list_as_user(
            'user3', 'secret',
            num_your_sources_predicted=1, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'user4', 'secret',
            num_your_sources_predicted=2, num_other_public_sources_predicted=1,
        )
        self.source_list_as_user(
            'user5', 'secret',
            num_your_sources_predicted=0, num_other_public_sources_predicted=2,
        )
        self.source_list_as_user(
            'superuser_user', 'secret',
            num_your_sources_predicted=4, num_other_public_sources_predicted=0,
        )


class SourceListTestWithoutSources(ClientTest):
    """
    Test the source list page when there are no sources on the entire site.
    (A corner case to be sure, but testable material nonetheless.)
    """

    fixtures = ['test_users.yaml']

    def source_list_as_user(self, username, password):
        if username is not None:
            self.client.login(username=username, password=password)

        # Redirect to source_about
        response = self.client.get(reverse('source_list'))
        self.assertRedirects(response, reverse('source_about'))

        # 0 public sources
        response = self.client.get(reverse('source_list'), follow=True)
        self.assertEqual(len(response.context['public_sources']), 0)

        self.client.logout()

    def test_source_list(self):
        self.source_list_as_user(None, None)
        self.source_list_as_user('user2', 'secret')


class SourceNewTest(ClientTest):
    """
    Test the New Source page.
    """
    fixtures = ['test_users.yaml']

    def test_source_new_not_logged_in(self):
        """
        Going to the New Source page while logged out should trigger a
        redirect to the login page.  Then once the user logs in, they
        should be redirected to the New Source page.
        """
        response = self.client.get(reverse('source_new'))

        # This URL isn't built with django.utils.http.urlencode() because
        # (1) urlencode() unfortunately escapes the '/' in its arguments, and
        # (2) str concatenation should be safe when there's no possibility of
        # malicious input.
        url_signin_with_source_new_next = reverse('signin') + '?next=' + reverse('source_new')
        self.assertRedirects(response, url_signin_with_source_new_next)

        response = self.client.post(url_signin_with_source_new_next, dict(
            identification='user2',
            password='secret',
        ))
        self.assertRedirects(response, reverse('source_new'))

    def test_source_new_success(self):
        """
        Successful creation of a new source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.get(reverse('source_new'))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('source_new'), dict(
            name='Test Source',
            visibility=Source.VisibilityTypes.PRIVATE,
            point_generation_type=PointGen.Types.SIMPLE,
            simple_number_of_points=200,
            image_height_in_cm=50,
            min_x=0,
            max_x=100,
            min_y=0,
            max_y=100,
        ))
        self.assertRedirects(response, reverse('source_main',
            kwargs={
                'source_id': Source.objects.latest('create_date').pk
            }
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # new source form.