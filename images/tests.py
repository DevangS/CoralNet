import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from guardian.shortcuts import get_objects_for_user
from images.model_utils import PointGen
from images.models import Source, Image
from images.tasks import PreprocessImages
from lib.test_utils import ClientTest, BaseTest, MediaTestComponent, ProcessingTestComponent


class SourceAboutTest(ClientTest):
    """
    Test the About Sources page.
    """
    def test_source_about(self):
        response = self.client.get(reverse('source_about'))
        self.assertStatusOK(response)


class SourceListTestWithSources(ClientTest):
    """
    Test the source list page when there's at least one source.
    """

    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
        ('public1', 'user4', Source.PermTypes.EDIT.code),
        ('private1', 'user3', Source.PermTypes.ADMIN.code),
        ('private1', 'user4', Source.PermTypes.VIEW.code),
    ]

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
            self.assertStatusOK(response)
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

    def test_source_new_permissions(self):
        self.login_required_page_test(
            protected_url=reverse('source_new'),
            username='user2',
            password='secret',
        )

    def test_source_new_success(self):
        """
        Successful creation of a new source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.get(reverse('source_new'))
        self.assertStatusOK(response)

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
        # TODO: Check that the source_main context reflects the source info.
        self.assertRedirects(response, reverse('source_main',
            kwargs={
                'source_id': Source.objects.latest('create_date').pk
            }
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # new source form.


class SourceEditTest(ClientTest):
    """
    Test the Edit Source page.
    """
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
        ('public1', 'user4', Source.PermTypes.EDIT.code),
        ('private1', 'user3', Source.PermTypes.ADMIN.code),
        ('private1', 'user4', Source.PermTypes.VIEW.code),
    ]
    PUBLIC1_PK = None

    def setUp(self):
        ClientTest.setUp(self)
        self.PUBLIC1_PK = Source.objects.get(name='public1').pk

    def test_source_edit_permissions(self):
        self.permission_required_page_test(
            protected_url=reverse('source_edit', kwargs={'source_id': self.PUBLIC1_PK}),
            denied_users=[dict(username='user3', password='secret')],
            accepted_users=[dict(username='user2', password='secret')],
        )

    def test_source_edit_success(self):
        """
        Successful edit of an existing source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.post(reverse('source_edit', kwargs={'source_id': self.PUBLIC1_PK}), dict(
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
        # TODO: Check that the source_main context reflects the source edits.
        self.assertRedirects(response, reverse('source_main',
            kwargs={'source_id': self.PUBLIC1_PK}
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # edit source form.


# TODO: Create a test robot model file, and then generate robot annotations from it, to see if creating revisions still works.

class ImageProcessingTaskTest(ClientTest):
    """
    Test the image processing tasks' logic with respect to
    database interfacing and input/output files.
    """
    extra_components = [MediaTestComponent, ProcessingTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]
    PUBLIC1_PK = 1
    IMAGE1_PK = 1

    def setUp(self):
        BaseTest.setUp(self)

        # Upload initial images
        self.client.login(username='user2', password='secret')
        sample_uploadable_path = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'data', '001_2012-05-01_color-grid-001.png')
        #sample_uploadable_path = 'C:\\Users\\Stephen\\Documents\\CVCE\\Test_images\\Label_thumbnails\\hard-coral.jpg'
        f = open(sample_uploadable_path, 'rb')
        response = self.client.post(reverse('image_upload', kwargs={'source_id': self.PUBLIC1_PK}), dict(
            files=f,
            skip_or_replace_duplicates='skip',
            specify_metadata='filenames',
        ))
        f.close()

        # TODO: Move these asserts to a separate test that specifically
        # tests uploads.
        self.assertStatusOK(response)
#        print ['message: '+m.message for m in list(response.context['messages'])]
#        print ['imageForm error: ' + k + ': ' + str(error_list) for k,error_list in response.context['imageForm'].errors.iteritems()]
#        print ['optionsForm error: ' + k + ': ' + str(error_list) for k,error_list in response.context['optionsForm'].errors.iteritems()]

        self.assertEqual(len(response.context['uploadedImages']), 1)

    def test_preprocess_task(self):
        self.assertEqual(Image.objects.get(pk=self.IMAGE1_PK).status.preprocessed, False)

        result = PreprocessImages.delay(self.IMAGE1_PK)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should be preprocessed, and process_date should be set
        self.assertEqual(Image.objects.get(pk=self.IMAGE1_PK).status.preprocessed, True)
        process_date = Image.objects.get(pk=self.IMAGE1_PK).process_date
        self.assertNotEqual(process_date, None)

        result = PreprocessImages.delay(self.IMAGE1_PK)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have exited without re-doing the preprocess
        self.assertEqual(Image.objects.get(pk=self.IMAGE1_PK).status.preprocessed, True)
        # process_date should have stayed the same
        self.assertEqual(Image.objects.get(pk=self.IMAGE1_PK).process_date, process_date)