import os
import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import forms
from django.utils import simplejson
from images.forms import ImageUploadForm
from images.models import Source, Image
from lib import str_consts
from lib.test_utils import ClientTest, MediaTestComponent


class ImageUploadBaseTest(ClientTest):
    """
    Base test class for the image upload page.

    This is an abstract class of sorts, as it doesn't actually contain
    any test methods.  However, its subclasses have test methods.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_sources_with_different_keys.yaml']
    source_member_roles = [
        ('0 keys', 'user2', Source.PermTypes.ADMIN.code),
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

    def get_source_image_count(self):
        return Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

    def upload_image_test(self, filename,
                          expecting_dupe=False,
                          expected_error=None,
                          **options):
        """
        Upload a single image via the Ajax view.

        (Multi-image upload only takes place on the client side; it's really
        just a series of single-image uploads on the server side. So unit
        testing multi-image upload doesn't make sense unless we can
        test on the client side, with Selenium or something.)

        :param filename: The image file's filepath as a string, relative to
            <settings.SAMPLE_UPLOADABLES_ROOT>/data.
        :param expecting_dupe: True if we expect the image to be a duplicate
            of an existing image, False otherwise.
        :param expected_error: Expected error message, if any.
        :param options: Extra options to include in the Ajax-image-upload
            request.
        :return: Tuple of (new image id, response from Ajax-image-upload).
            This way, the calling function can do some additional checks
            if it wants to.
        """
        old_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        sample_uploadable_directory = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'data')

        sample_uploadable_path = os.path.join(sample_uploadable_directory, filename)
        file_to_upload = open(sample_uploadable_path, 'rb')

        post_dict = dict(
            file=file_to_upload,
            specify_metadata='filenames',
            skip_or_replace_duplicates='skip',
            is_uploading_points_or_annotations='off',
            is_uploading_annotations_not_just_points='yes',
            annotation_dict_id='',
        )
        post_dict.update(options)

        response = self.client.post(
            reverse('image_upload_ajax', kwargs={'source_id': self.source_id}),
            post_dict,
        )
        file_to_upload.close()
        response_content = simplejson.loads(response.content)

        self.assertStatusOK(response)

        new_source_image_count = Image.objects.filter(source=Source.objects.get(pk=self.source_id)).count()

        image_id = None

        if expected_error:

            self.assertEqual(response_content['status'], 'error')
            self.assertEqual(response_content['message'], expected_error)

            if settings.UNIT_TEST_VERBOSITY >= 1:
                print "Error message:\n{error}".format(error=response_content['message'])

            # Error, so nothing was uploaded.
            # The number of images in the source should have stayed the same.
            self.assertEqual(new_source_image_count, old_source_image_count)

        else:

            if expecting_dupe:
                # We just replaced a duplicate image.
                if post_dict['skip_or_replace_duplicates'] == 'skip':
                    self.assertEqual(response_content['status'], 'error')
                else:  # replace
                    self.assertEqual(response_content['status'], 'ok')
                    image_id = response_content['image_id']

                # The number of images in the source should have stayed the same.
                self.assertEqual(new_source_image_count, old_source_image_count)
            else:
                # We uploaded a new, non-duplicate image.
                self.assertEqual(response_content['status'], 'ok')
                image_id = response_content['image_id']

                # The number of images in the source should have gone up by 1.
                self.assertEqual(new_source_image_count, 1+old_source_image_count)

        return image_id, response


class ImageUploadGeneralTest(ImageUploadBaseTest):
    """
    Image upload tests: general.
    """
    def test_valid_png(self):
        """ .png created using the PIL. """
        self.upload_image_test('001_2012-05-01_color-grid-001.png')

    def test_valid_jpg(self):
        """ .jpg created using the PIL. """
        self.upload_image_test('001_2012-05-01_color-grid-001_jpg-valid.jpg')

    # TODO: Test a fairly large upload (at least 50 MB, or whatever
    # the upload limit is when memory is used for temp storage)?


class ImageUploadImageErrorTest(ImageUploadBaseTest):
    """
    Image upload tests: errors related to the image files, such as errors
    about corrupt images, non-images, etc.
    """
    invalid_image_error_msg = ImageUploadForm.base_fields['file'].error_messages['invalid_image']

    def test_unloadable_corrupt_png_1(self):
        """ .png with some bytes swapped around.
        PIL load() would get IOError: broken data stream when reading image file """
        self.upload_image_test(
            '001_2012-05-01_color-grid-001_png-corrupt-unloadable-1.png',
            expected_error=self.invalid_image_error_msg,
        )

    def test_unloadable_corrupt_png_2(self):
        """ .png with some bytes deleted from the end.
        PIL load() would get IndexError: string index out of range """
        self.upload_image_test(
            '001_2012-05-01_color-grid-001_png-corrupt-unloadable-2.png',
            expected_error=self.invalid_image_error_msg,
        )

    def test_unopenable_corrupt_png(self):
        """ .png with some bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        self.upload_image_test(
            '001_2012-05-01_color-grid-001_png-corrupt-unopenable.png',
            expected_error=self.invalid_image_error_msg,
        )

    def test_unloadable_corrupt_jpg(self):
        """ .jpg with bytes deleted from the end.
        PIL load() would get IOError: image file is truncated (4 bytes not processed) """
        self.upload_image_test(
            '001_2012-05-01_color-grid-001_jpg-corrupt-unloadable.jpg',
            expected_error=self.invalid_image_error_msg,
        )

    def test_unopenable_corrupt_jpg(self):
        """ .jpg with bytes deleted near the beginning.
        PIL open() would get IOError: cannot identify image file """
        self.upload_image_test(
            '001_2012-05-01_color-grid-001_jpg-corrupt-unopenable.jpg',
            expected_error=self.invalid_image_error_msg,
        )

    def test_non_image(self):
        """ .txt in UTF-8 created using Notepad++.
        NOTE: the filename will have to be valid for an
        equivalent Selenium test."""
        self.upload_image_test(
            'sample_text_file.txt',
            expected_error=self.invalid_image_error_msg,
        )

    def test_empty_file(self):
        """ 0-byte .png.
        NOTE: the filename will have to be valid for an
        equivalent Selenium test."""
        self.upload_image_test(
            'empty.png',
            expected_error=forms.FileField.default_error_messages['empty']
        )

    # TODO: Test uploading a nonexistent file (i.e. filling the file field with
    # a nonexistent filename).  However, this will probably have to be done
    # with a Selenium test.

    # TODO: Test sending the POST request with no file specified?
    # This normally won't happen unless there's a manually crafted POST
    # request, so this isn't high priority.


class ImageUploadKeysTest(ImageUploadBaseTest):
    """
    Image upload tests: related to location keys, such as checking for
    duplicate images, checking for correct specification of location
    values and date in the filename, and so on.
    """
    # Tests with duplicate images.

    def duplicate_test(self, dupe_option):
        options = dict(skip_or_replace_duplicates=dupe_option)

        self.upload_image_test('001_2012-05-01_color-grid-001.png', **options)

        # Non-duplicate
        self.upload_image_test('002_2012-06-28_color-grid-002.png', **options)

        # Duplicate
        self.upload_image_test('001_2012-05-01_color-grid-001_jpg-valid.jpg', expecting_dupe=True, **options)

        image_001 = Image.objects.get(source__pk=self.source_id, metadata__value1='001')
        image_001_name = image_001.metadata.name

        if dupe_option == 'skip':
            # Check that the image name is from the original,
            # not the skipped dupe.
            self.assertEqual(image_001_name, 'color-grid-001.png')
        else:  # 'replace'
            # Check that the image name is from the dupe
            # we just uploaded.
            self.assertEqual(image_001_name, 'color-grid-001_jpg-valid.jpg')

        # Tried to check if the upload time was correct based on skip/replace.
        # However, there's a problem: database datetime objects don't track
        # time more accurately than seconds, and this upload test tends to
        # take less than a second (perhaps much less).  So it would only
        # intermittently be a useful check.

    def test_duplicates_skip(self):
        self.duplicate_test('skip')

    def test_duplicates_replace(self):
        self.duplicate_test('replace')


    # Filename format tests (on the server side).
    #
    # Actually, filename formats should mainly be tested on the Javascript
    # side, through Selenium.  It's not a bad idea to test these on the server
    # side too, though, in case the JS is bypassed by some hacker, or in
    # case the JS fails for some reason.

    def test_filename_zero_location_keys(self):
        """
        Upload with zero location keys:
        test upload, location values, photo date, and name.
        """
        self.source_id = Source.objects.get(name='0 keys').pk

        # Without custom filename.
        image_id, response = self.upload_image_test(os.path.join('0keys', '2011-05-28.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), [])
        self.assertEqual(img.metadata.name, '2011-05-28.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2011,5,28))

        # With custom filename.
        image_id, response = self.upload_image_test(os.path.join('0keys', '2012-05-28_grid1.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), [])
        self.assertEqual(img.metadata.name, 'grid1.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2012,5,28))

    def test_filename_one_location_key(self):
        """
        Upload with zero location keys:
        test upload, location values, photo date, name, and dupe checking.
        """
        self.source_id = Source.objects.get(name='1 key').pk

        image_id, response = self.upload_image_test(os.path.join('1key', '001_2011-05-28.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['001'])
        self.assertEqual(img.metadata.name, '001_2011-05-28.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2011,5,28))

        image_id, response = self.upload_image_test(os.path.join('1key', '001_2012-05-28_rainbow-grid-one.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['001'])
        self.assertEqual(img.metadata.name, 'rainbow-grid-one.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2012,5,28))

    def test_filename_two_location_keys(self):
        self.source_id = Source.objects.get(name='2 keys').pk

        image_id, response = self.upload_image_test(os.path.join('2keys', 'rainbow_002_2011-05-28.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['rainbow', '002'])
        self.assertEqual(img.metadata.name, 'rainbow_002_2011-05-28.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2011,5,28))

        image_id, response = self.upload_image_test(os.path.join('2keys', 'cool_001_2012-05-28_cool_image_one.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['cool', '001'])
        self.assertEqual(img.metadata.name, 'cool_image_one.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2012,5,28))

    def test_filename_five_location_keys(self):
        self.source_id = Source.objects.get(name='5 keys').pk

        image_id, response = self.upload_image_test(os.path.join('5keys', 'square_img-s_elmt-m_rainbow_002_2012-05-28.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['square', 'img-s', 'elmt-m', 'rainbow', '002'])
        self.assertEqual(img.metadata.name, 'square_img-s_elmt-m_rainbow_002_2012-05-28.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2012,5,28))

        image_id, response = self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_cool_001_2012-05-28__cool_image_one_.png'))

        img = Image.objects.get(pk=image_id)
        self.assertEqual(img.get_location_value_str_list(), ['rect', 'img-m', 'elmt-l', 'cool', '001'])
        self.assertEqual(img.metadata.name, '_cool_image_one_.png')
        self.assertEqual(img.metadata.photo_date, datetime.date(2012,5,28))

    def test_filename_dupe_detection(self):
        self.source_id = Source.objects.get(name='0 keys').pk

        self.upload_image_test(os.path.join('0keys', '2012-05-28_grid1.png'))
        self.upload_image_test(os.path.join('0keys', '2011-05-28.png'))    # Year different
        self.upload_image_test(os.path.join('0keys', '2012-05-28.png'), expecting_dupe=True)

        self.source_id = Source.objects.get(name='1 key').pk

        self.upload_image_test(os.path.join('1key', '001_2012-05-28_rainbow-grid-one.png'))
        self.upload_image_test(os.path.join('1key', '002_2012-05-28.png'))    # Number different
        self.upload_image_test(os.path.join('1key', '001_2011-05-28.png'))    # Year different
        self.upload_image_test(os.path.join('1key', '002_2011-05-28.png'))    # Both different
        self.upload_image_test(os.path.join('1key', '001_2012-05-28.png'), expecting_dupe=True)

        self.source_id = Source.objects.get(name='2 keys').pk

        self.upload_image_test(os.path.join('2keys', 'cool_001_2012-05-28_cool_image_one.png'))
        self.upload_image_test(os.path.join('2keys', 'rainbow_001_2012-05-28.png'))    # Color different
        self.upload_image_test(os.path.join('2keys', 'cool_002_2012-05-28.png'))    # Number different
        self.upload_image_test(os.path.join('2keys', 'cool_001_2011-05-28.png'))    # Year different
        self.upload_image_test(os.path.join('2keys', 'cool_001_2012-05-28.png'), expecting_dupe=True)

        self.source_id = Source.objects.get(name='5 keys').pk

        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_cool_001_2012-05-28__cool_image_one_.png'))
        self.upload_image_test(os.path.join('5keys', 'square_img-m_elmt-l_cool_001_2012-05-28.png'))    # Shape different
        self.upload_image_test(os.path.join('5keys', 'rect_img-s_elmt-l_cool_001_2012-05-28.png'))    # Image size different
        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-m_cool_001_2012-05-28.png'))    # Element size different
        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_rainbow_001_2012-05-28.png'))    # Color different
        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_cool_002_2012-05-28.png'))    # Number different
        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_cool_001_2011-05-28.png'))    # Year different
        self.upload_image_test(os.path.join('5keys', 'rect_img-m_elmt-l_cool_001_2012-05-28.png'), expecting_dupe=True)


    def test_filename_not_enough_location_values(self):
        self.source_id = Source.objects.get(name='2 keys').pk

        self.upload_image_test(
            os.path.join('1key', '001_2011-05-28.png'),
            expected_error=str_consts.FILENAME_PARSE_ERROR_STR,
        )

    def test_filename_too_many_location_values(self):
        self.source_id = Source.objects.get(name='1 key').pk

        # Upload a 2-location-value filename.
        # We'll end up attempting to parse the second value
        # as a date, and that will fail.
        self.upload_image_test(
            os.path.join('2keys', 'cool_001_2012-05-28.png'),
            expected_error=str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token='001'),
        )

    def test_filename_date_formats(self):
        self.source_id = Source.objects.get(name='1 key').pk

        # Valid dates.

        self.upload_image_test(
            os.path.join('dates', '002_2012-02-29.png'),
        )
        self.upload_image_test(
            os.path.join('dates', '003_2012-2-29.png'),
        )
        self.upload_image_test(
            os.path.join('dates', '004_2012-2-2.png'),
        )

        # Incorrect number of hyphens.

        self.upload_image_test(
            os.path.join('dates', '001_20120229.png'),
            expected_error=str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token='20120229'),
        )
        self.upload_image_test(
            os.path.join('dates', '001_2012-0229.png'),
            expected_error=str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token='2012-0229'),
        )
        self.upload_image_test(
            os.path.join('dates', '001_2012-02-2-9.png'),
            expected_error=str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token='2012-02-2-9'),
        )

        # Incorrect or missing y/m/d.

        # Missing
        self.upload_image_test(
            os.path.join('dates', '001_2012--29.png'),
            expected_error=str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='2012--29'),
        )
        # Not a number
        self.upload_image_test(
            os.path.join('dates', '001_2012-02-ab.png'),
            expected_error=str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='2012-02-ab'),
        )
        # Day out of range (for the month)
        self.upload_image_test(
            os.path.join('dates', '001_2012-02-30.png'),
            expected_error=str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='2012-02-30'),
        )
        # Month out of range
        self.upload_image_test(
            os.path.join('dates', '001_2012-00-01.png'),
            expected_error=str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='2012-00-01'),
        )
        # Year out of range
        self.upload_image_test(
            os.path.join('dates', '001_10000-01-01.png'),
            expected_error=str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='10000-01-01'),
        )
        # Could test more dates, but would kind of boil down to whether the
        # built-in library datetime is doing its job or not.