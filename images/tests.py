import os
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms.fields import FileField, Field
from guardian.shortcuts import get_objects_for_user
from images.forms import MultipleImageField, ImageUploadForm
from images.model_utils import PointGen
from images.models import Source, Image
from images.tasks import PreprocessImages, MakeFeatures, Classify, addLabelsToFeatures, trainRobot
from images.utils import image_upload_success_message
from lib import msg_consts
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
        """
        Test the source_list page as a certain user.
        If username is None, then the test is done while logged out.
        """
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
        """
        Test the source_list page as a certain user.
        If username is None, then the test is done while logged out.
        """
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
        """
        Test that certain users are able to access the
        page, and that certain other users are denied.
        """
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

    def setUp(self):
        super(SourceEditTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

    def test_source_edit_permissions(self):
        """
        Test that certain users are able to access the
        page, and that certain other users are denied.
        """
        self.permission_required_page_test(
            protected_url=reverse('source_edit', kwargs={'source_id': self.source_id}),
            denied_users=[dict(username='user3', password='secret')],
            accepted_users=[dict(username='user2', password='secret')],
        )

    def test_source_edit_success(self):
        """
        Successful edit of an existing source.
        """
        self.client.login(username='user2', password='secret')
        response = self.client.post(reverse('source_edit', kwargs={'source_id': self.source_id}), dict(
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
            kwargs={'source_id': self.source_id}
        ))

    # TODO: Test other successful and unsuccessful inputs for the
    # edit source form.


class ImageUploadBaseTest(ClientTest):
    """
    Base test class for the image upload page.

    This is an abstract class of sorts, as it doesn't actually contain
    any test methods.  However, its subclasses have test methods.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_sources_with_different_keys.yaml']
    source_member_roles = [
        ('1 key', 'user2', Source.PermTypes.ADMIN.code),
        ('2 keys', 'user2', Source.PermTypes.ADMIN.code),
        ('5 keys', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageUploadBaseTest, self).setUp()

        # Default user; individual tests are free to change it
        self.client.login(username='user2', password='secret')

        # Default source; individual tests are free to change it
        self.source_id = Source.objects.get(name='1 key').pk

    def upload_images_test(self, filenames, subdirectory=None,
                           expect_success=True, expected_dupes=0,
                           expected_errors=None, expected_invalid=None,
                           **options):
        """
        Upload a number of images.

        subdirectory - If the files to upload are in a subdirectory of
            /sample_uploadables/data, as opposed to directly in
            /sample_uploadables/data, then this is the name of the
            subdirectory it's in.  Should be a string with no slash.
        filenames - The filename as a string, if uploading one file; the
            filenames as a list of strings, if uploading multiple files.
        expect_success - True if expecting to successfully upload, False
            if expecting errors upon submitting the form.  An
            AssertionError is thrown if any of the checks for
            success/non-success do not pass.
        expected_dupes - Number of the uploaded images that are expected to
            be duplicates of existing images.
        expected_errors - A dict of expected form errors.  An AssertionError
            is thrown if expected errors != actual errors.
        expected_invalid - Filename string of a file that is expected to get
            an invalid-image error.  Basically, a shortcut for expected_errors
            in the special case that we're expecting a single invalid-image
            error.  Usage should be disjoint from expected_errors.
        """
        if isinstance(filenames, basestring):
            filenames = [filenames]

        old_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        if subdirectory:
            sample_uploadable_directory = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'data', subdirectory)
        else:
            sample_uploadable_directory = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'data')

        files_to_upload = []
        for filename in filenames:
            sample_uploadable_path = os.path.join(sample_uploadable_directory, filename)
            f = open(sample_uploadable_path, 'rb')
            files_to_upload.append(f)

        post_dict = dict(
            files=files_to_upload,
            skip_or_replace_duplicates='skip',
            specify_metadata='filenames',
        )
        post_dict.update(options)

        response = self.client.post(reverse('image_upload', kwargs={'source_id': self.source_id}), post_dict)
        for uploaded_file in files_to_upload:
            uploaded_file.close()

        self.assertStatusOK(response)

        new_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        # TODO: Accommodate partial successes (some uploaded, some not)?

        if expect_success:

            dupe_option = post_dict['skip_or_replace_duplicates']
            if dupe_option == 'skip':
                expected_num_images_uploaded = len(filenames) - expected_dupes
            else:  # 'replace'
                expected_num_images_uploaded = len(filenames)

            # The 'uploaded images' display on the success page should include
            # up to 5 images.
            # TODO: If more than 5 were uploaded, check that the correct 5 images are shown?
            self.assertEqual(len(response.context['uploadedImages']), min(expected_num_images_uploaded, 5))

            # The number of images in the source should be correct.
            self.assertEqual(new_source_image_count, len(filenames)+old_source_image_count-expected_dupes)

            # The correct page-top messages should be in the context.
            self.assertMessages(response, [image_upload_success_message(
                num_images_uploaded=expected_num_images_uploaded,
                num_dupes=expected_dupes,
                dupe_option=dupe_option,
                num_annotations=0,
            )])
        else:
            # There should be no images in the 'uploaded images' display.
            self.assertEqual(len(response.context['uploadedImages']), 0)

            # The number of images in the source should have stayed the same.
            self.assertEqual(new_source_image_count, old_source_image_count)

            # The correct page-top messages should be in the context.
            self.assertMessages(response, [msg_consts.FORM_ERRORS])

        # Check that the appropriate form errors have been raised.
        if expected_errors:
            self.assertFormErrors(
                response,
                'imageForm',
                expected_errors,
            )
        # TODO: Put the invalid-image special case in ImageUploadImageErrorTest,
        # instead of in this general test method?
        if expected_invalid:
            self.assertFormErrors(
                response,
                'imageForm',
                {'files': [u"{0}{1}".format(
                        MultipleImageField.default_error_messages['error_on'].format(expected_invalid),
                        MultipleImageField.default_error_messages['invalid_image'],
                )]}
            )

        # If the rest of the test wants to do anything else with the response,
        # then it can.
        return response

    def files_error_dict(self, filenames_and_errors):
        """
        Takes a list of (filename, error message without "filename: " prefix)
        tuples. Returns an error dict with the "files" field's errors filled
        in accordingly.  This error dict can then be passed in as the
        expected_errors of the image upload function.
        """
        return {'files':
            [u"{0}{1}".format(
                MultipleImageField.default_error_messages['error_on'].format(filename),
                error
            )
            for filename, error in filenames_and_errors]
        }


class ImageUploadGeneralTest(ImageUploadBaseTest):
    """
    Image upload tests: general.
    """
    def test_valid_png(self):
        """ .png created using the PIL. """
        self.upload_images_test('001_2012-05-01_color-grid-001.png')

    def test_valid_jpg(self):
        """ .jpg created using the PIL. """
        self.upload_images_test('001_2012-05-01_color-grid-001_jpg-valid.jpg')

    # Multi-file upload tests.

    def test_valid_two(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '002_2012-06-28_color-grid-002.png',])

    def test_valid_five(self):
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '002_2012-06-28_color-grid-002.png',
                                 '003_2012-06-28_color-grid-003.png',
                                 '004_2012-06-28_color-grid-004.png',
                                 '005_2012-06-28_color-grid-005.png',])

    def test_valid_six(self):
        """After upload, there should be only five just-uploaded images linked
        on the success page."""
        self.upload_images_test(['001_2012-05-01_color-grid-001.png',
                                 '002_2012-06-28_color-grid-002.png',
                                 '003_2012-06-28_color-grid-003.png',
                                 '004_2012-06-28_color-grid-004.png',
                                 '005_2012-06-28_color-grid-005.png',
                                 '006_2012-06-28_color-grid-006.png',])

    # TODO: Test a fairly large upload (at least 50 MB, or whatever
    # the upload limit is when memory is used for temp storage)?


class ImageUploadImageErrorTest(ImageUploadBaseTest):
    """
    Image upload tests: errors related to the image files, such as errors
    about corrupt images, non-images, etc.
    """
    def invalid_files_error_dict(self, filenames):
        return self.files_error_dict(
            [(filename, MultipleImageField.default_error_messages['invalid_image'])
             for filename in filenames]
        )

    def test_unloadable_corrupt_png_1(self):
        """ .png with some bytes swapped around.
        PIL load() would get IOError: broken data stream when reading image file """
        filename = '001_2012-05-01_color-grid-001_png-corrupt-unloadable-1.png'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_unloadable_corrupt_png_2(self):
        """ .png with some bytes deleted from the end.
        PIL load() would get IndexError: string index out of range """
        filename = '001_2012-05-01_color-grid-001_png-corrupt-unloadable-2.png'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_unopenable_corrupt_png(self):
        """ .png with some bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        filename = '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_unloadable_corrupt_jpg(self):
        """ .jpg with bytes deleted from the end.
        PIL load() would get IOError: image file is truncated (4 bytes not processed) """
        filename = '001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_unopenable_corrupt_jpg(self):
        """ .jpg with bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        filename = '001_2012-05-01_color-grid-001_jpg-corrupt-unopenable.jpg'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_non_image(self):
        """ .txt in UTF-8 created using Notepad++.
        NOTE: the filename will have to be valid for an
        equivalent Selenium test."""
        filename = 'sample_text_file.txt'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename]),
        )

    def test_empty_file(self):
        """ 0-byte .png.
        NOTE: the filename will have to be valid for an
        equivalent Selenium test."""
        filename = 'empty.png'
        self.upload_images_test(
            filename, expect_success=False,
            expected_errors=self.files_error_dict([
                (filename, FileField.default_error_messages['empty'])
            ])
        )

    # Multi-file upload tests.

    def test_invalid_two(self):
        filename1 = '001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg'
        filename2 = '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename1]),
        )

    def test_valid_and_non_image(self):
        filename1 = '001_2012-05-01_color-grid-001.png'
        filename2 = 'sample_text_file.txt'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename2]),
        )

    def test_valid_and_unopenable_image(self):
        filename1 = '001_2012-05-01_color-grid-001.png'
        filename2 = '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename2]),
        )

    def test_valid_and_unloadable_image(self):
        filename1 = '001_2012-05-01_color-grid-001.png'
        filename2 = '001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename2]),
        )

    # Do the valid-invalid pairs again, with the image order swapped.
    #
    # The image order actually matters, because the FileInput class
    # validates only the last item of the list (and we want to make
    # sure we don't have this behavior).

    def test_non_image_and_valid(self):
        filename1 = 'sample_text_file.txt'
        filename2 = '001_2012-05-01_color-grid-001.png'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename1]),
        )

    def test_unopenable_image_and_valid(self):
        filename1 = '001_2012-05-01_color-grid-001_jpg-corrupt-unopenable.jpg'
        filename2 = '001_2012-05-01_color-grid-001.png'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename1]),
        )

    def test_unloadable_image_and_valid(self):
        filename1 = '001_2012-05-01_color-grid-001_png-corrupt-unloadable-1.png'
        filename2 = '001_2012-05-01_color-grid-001.png'
        self.upload_images_test(
            [filename1, filename2], expect_success=False,
            expected_errors=self.invalid_files_error_dict([filename1]),
        )

    # TODO: Test uploading a nonexistent file (i.e. filling the file field with
    # a nonexistent filename).  However, this will probably have to be done
    # with a Selenium test.

    def test_no_images_specified(self):
        self.upload_images_test(
            [], expect_success=False,
            expected_errors={
                'files': [
                    u"{m}".format(m=Field.default_error_messages['required'])
                ]
            }
        )


class ImageUploadKeysTest(ImageUploadBaseTest):
    """
    Image upload tests: related to location keys, such as checking for
    duplicate images, checking for correct specification of keys and date
    in the filename, and so on.
    """
    # Tests with duplicate images.

    def duplicate_test(self, dupe_option):
        self.upload_images_test(
            ['001_2012-05-01_color-grid-001.png',
             '002_2012-06-28_color-grid-002.png',],
            skip_or_replace_duplicates=dupe_option,
        )

        # Duplicate
        self.upload_images_test(
            ['001_2012-05-01_color-grid-001_jpg-valid.jpg',],
            expected_dupes=1,
            skip_or_replace_duplicates=dupe_option,
        )
        # Check that we really did/didn't replace the original
        image_001_name = Image.objects.get(source__pk=self.source_id, metadata__value1='001').metadata.name
        if dupe_option == 'skip':
            self.assertEqual(image_001_name, 'color-grid-001.png')
        else:  # 'replace'
            self.assertEqual(image_001_name, 'color-grid-001_jpg-valid.jpg')

        # Non-duplicate
        self.upload_images_test(
            ['003_2012-06-28_color-grid-003.png',],
            skip_or_replace_duplicates=dupe_option,
        )

        # Multiple duplicates + non-duplicate
        self.upload_images_test(
            ['001_2012-05-01_color-grid-001.png',
             '002_2012-06-28_color-grid-002.png',
             '004_2012-06-28_color-grid-004.png',],
            expected_dupes=2,
            skip_or_replace_duplicates=dupe_option,
        )

    def test_duplicates_skip(self):
        self.duplicate_test('skip')

    def test_duplicates_replace(self):
        self.duplicate_test('replace')

    def test_duplicates_within_same_upload(self):
        """
        At least two images in the same upload are duplicates
        of each other. This is an error case, and the JS side should really
        catch this before the upload is allowed to start, but a server
        side check is still a good idea just in case.

        The first image should be uploaded and subsequent duplicates
        should be skipped.
        """
        self.upload_images_test(
            ['001_2012-05-01_color-grid-001.png',
             '001_2012-05-01_color-grid-001_jpg-valid.jpg',
             '002_2012-05-29_color-grid-001_large.png',
             '002_2012-06-28_color-grid-002.png',
             '003_2012-06-28_color-grid-003.png',],
            expected_errors=self.files_error_dict([
                ('001_2012-05-01_color-grid-001_jpg-valid.jpg', ImageUploadForm.error_messages['duplicate_image']),
                ('002_2012-06-28_color-grid-002.png', ImageUploadForm.error_messages['duplicate_image']),
            ])
        )


    # Filename format tests (on the server side).
    #
    # Actually, filename formats should mainly be tested on the Javascript
    # side, through Selenium.  It's not a bad idea to test these on the server
    # side too, though, in case the JS is bypassed by some hacker, or in
    # case the JS fails for some reason.

    def test_filename_zero_location_keys(self):
        pass  # TODO

    def test_filename_one_location_key(self):
        pass  # TODO

    def test_filename_two_location_keys(self):
        pass  # TODO

    def test_filename_five_location_keys(self):
        pass  # TODO

    def test_filename_with_original_filename(self):
        pass  # TODO

    def test_filename_not_enough_location_keys(self):
        pass  # TODO

    def test_filename_too_many_location_keys(self):
        pass  # TODO

    def test_filename_incorrect_date_format(self):
        pass  # TODO (Might want multiple incorrect date tests?)


class ImageViewTest(ClientTest):
    """
    Test the image view page.
    This is an abstract class that doesn't actually have any tests.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageViewTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

    def view_page_with_image(self, image_file):
        self.client.login(username='user2', password='secret')

        self.image_id = self.upload_image(self.source_id, image_file)

        response = self.client.get(reverse('image_detail', kwargs={'image_id': self.image_id}))
        self.assertStatusOK(response)

        # Try fetching the page a second time, to make sure thumbnail
        # generation doesn't go nuts.
        response = self.client.get(reverse('image_detail', kwargs={'image_id': self.image_id}))
        self.assertStatusOK(response)

        # TODO: Add more checks.

    def test_view_page_with_small_image(self):
        self.view_page_with_image('001_2012-05-01_color-grid-001.png')

    def test_view_page_with_large_image(self):
        self.view_page_with_image('002_2012-05-29_color-grid-001_large.png')


class ImageProcessingTaskTest(ClientTest):
    """
    Test the image processing tasks' logic with respect to
    database interfacing, preparation for subsequent tasks,
    and final results.

    Don't explicitly check for certain input/output files.
    Simply check that running task n prepares for task n+1
    in a sequence of tasks.
    """
    extra_components = [MediaTestComponent, ProcessingTestComponent]
    fixtures = ['test_users.yaml', 'test_sources.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(ImageProcessingTaskTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

        self.client.login(username='user2', password='secret')

        self.image_id = self.upload_image(self.source_id, '001_2012-05-01_color-grid-001.png')

    def test_preprocess_task(self):
        # The uploaded image should start out not preprocessed.
        # Otherwise, we need to change the setup code so that
        # the prepared image has preprocessed == False.
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, False)

        # Run task, attempt 1.
        result = PreprocessImages.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should be preprocessed, and process_date should be set
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
        process_date = Image.objects.get(pk=self.image_id).process_date
        self.assertNotEqual(process_date, None)

        # Run task, attempt 2.
        result = PreprocessImages.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have exited without re-doing the preprocess
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
        # process_date should have stayed the same
        self.assertEqual(Image.objects.get(pk=self.image_id).process_date, process_date)

    def test_make_features_task(self):
        # Preprocess the image first.
        result = PreprocessImages.delay(self.image_id)
        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)

        # Sanity check: features have not been made yet
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, False)

        # Run task, attempt 1.
        result = MakeFeatures.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have extracted features
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)

        # Run task, attempt 2.
        result = MakeFeatures.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have exited without re-doing the feature making
        # TODO: Check file ctime/mtime to check that it wasn't redone?
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)

#    def test_add_feature_labels_task(self):
#        # Preprocess and feature-extract first.
#        result = PreprocessImages.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
#        result = MakeFeatures.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)
#
#        # TODO: The image needs to be human annotated first.
#
#        # Sanity check: haven't added labels to features yet
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, False)
#
#        # Run task, attempt 1.
#        result = addLabelsToFeatures.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have added labels to features
#        # TODO: Check file ctime/mtime to check that the file was changed
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)
#
#        # Run task, attempt 2.
#        result = addLabelsToFeatures.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have exited without re-doing label adding
#        # TODO: Check file ctime/mtime to check that it wasn't redone?
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)
#
#    def test_train_robot_task(self):
#        # TODO
#        #trainRobot
#        pass
#
#    def test_classify_task(self):
#        # Preprocess and feature-extract first.
#        result = PreprocessImages.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
#        result = MakeFeatures.delay(self.image_id)
#        self.assertTrue(result.successful())
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)
#
#        # TODO: Do other preparation tasks.
#
#        # Sanity check: not classified yet
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, False)
#
#        # Run task, attempt 1.
#        result = Classify.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have classified the image
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, True)
#
#        # Run task, attempt 2.
#        result = Classify.delay(self.image_id)
#        # Check that the task didn't encounter an exception
#        self.assertTrue(result.successful())
#
#        # Should have exited without re-doing the classification
#        # TODO: Check file ctime/mtime to check that it wasn't redone?
#        self.assertEqual(Image.objects.get(pk=self.image_id).status.annotatedByRobot, True)