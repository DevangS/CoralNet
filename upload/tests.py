from collections import defaultdict
import os
import datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import forms
from django.utils import simplejson
from annotations.model_utils import AnnotationAreaUtils
from annotations.models import Annotation
from images.forms import ImageUploadForm
from images.model_utils import PointGen
from images.models import Source, Image, Point
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

    def get_full_upload_options(self, specified_options):
        full_options = dict(self.default_upload_params)
        full_options.update(specified_options)
        return full_options

    def upload_image_test(self, filename,
                          expecting_dupe=False,
                          expected_error=None,
                          **options):
        """
        Upload a single image via the Ajax view, and perform a few checks
        to see that the upload worked.

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
        old_source_image_count = self.get_source_image_count()

        image_id, response = self.upload_image(filename, **options)
        response_content = simplejson.loads(response.content)

        new_source_image_count = self.get_source_image_count()

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
                full_options = self.get_full_upload_options(options)

                if full_options['skip_or_replace_duplicates'] == 'skip':
                    self.assertEqual(response_content['status'], 'error')
                else:  # replace
                    self.assertEqual(response_content['status'], 'ok')

                # The number of images in the source should have stayed the same.
                self.assertEqual(new_source_image_count, old_source_image_count)
            else:
                # We uploaded a new, non-duplicate image.
                self.assertEqual(response_content['status'], 'ok')

                # The number of images in the source should have gone up by 1.
                self.assertEqual(new_source_image_count, 1+old_source_image_count)

        return image_id, response

    def check_fields_for_non_annotation_upload(self, img):

        # Uploading without points/annotations.
        self.assertFalse(img.status.annotatedByHuman)
        self.assertEqual(img.point_generation_method, img.source.default_point_generation_method)
        self.assertEqual(img.metadata.annotation_area, img.source.image_annotation_area)

    def upload_image_test_with_field_checks(self, filename,
                                            expecting_dupe=False,
                                            expected_error=None,
                                            **options):
        """
        Like upload_image_test(), but with additional checks that the
        various image fields are set correctly.
        """
        datetime_before_upload = datetime.datetime.now().replace(microsecond=0)

        image_id, response = self.upload_image_test(
            filename,
            expecting_dupe,
            expected_error,
            **options
        )

        img = Image.objects.get(pk=image_id)

        # Not sure if we can check the file location in a cross-platform way,
        # so we'll skip a check of original_file.path for now.
        if settings.UNIT_TEST_VERBOSITY >= 1:
            print "Uploaded file's path: {path}".format(path=img.original_file.path)

        self.assertEqual(img.original_height, 400)
        self.assertEqual(img.original_width, 400)

        # This check is of limited use since database datetimes (in
        # MySQL 5.1 at least) get truncated to whole seconds. But it still
        # doesn't hurt to check.
        self.assertTrue(datetime_before_upload <= img.upload_date)
        self.assertTrue(img.upload_date <= datetime.datetime.now().replace(microsecond=0))

        # Check that the user who uploaded the image is the
        # currently logged in user.
        self.assertEqual(img.uploaded_by.id, self.client.session['_auth_user_id'])

        # Status fields.
        self.assertFalse(img.status.preprocessed)
        self.assertTrue(img.status.hasRandomPoints)
        self.assertFalse(img.status.featuresExtracted)
        self.assertFalse(img.status.annotatedByRobot)
        self.assertFalse(img.status.featureFileHasHumanLabels)
        self.assertFalse(img.status.usedInCurrentModel)

        # cm height.
        self.assertEqual(img.metadata.height_in_cm, img.source.image_height_in_cm)

        full_options = self.get_full_upload_options(options)

        if full_options['is_uploading_points_or_annotations'] == 'on':

            # Uploading with points/annotations.

            # Pointgen method and annotation area should both indicate that
            # points have been imported.
            self.assertEqual(
                PointGen.db_to_args_format(img.point_generation_method)['point_generation_type'],
                PointGen.Types.IMPORTED,
            )
            self.assertEqual(
                img.metadata.annotation_area,
                AnnotationAreaUtils.IMPORTED_STR,
            )

            # Depending on whether we're uploading annotations, the
            # annotatedByHuman status flag may or may not apply.
            if full_options['is_uploading_annotations_not_just_points'] == 'yes':
                # Points + annotations upload.
                self.assertTrue(img.status.annotatedByHuman)

            else:  # 'no'
                # Points only upload.
                self.assertFalse(img.status.annotatedByHuman)

        else:  # 'off'

            self.check_fields_for_non_annotation_upload(img)

        # Other metadata fields aren't covered here because:
        # - name, photo_date, value1/2/3/4/5: covered by filename tests
        # - latitude, longitude, depth, camera, photographer, water_quality,
        #   strobes, framing, balance, comments: not specifiable from the
        #   upload page

        return image_id, response


class UploadValidImageTest(ImageUploadBaseTest):
    """
    Valid images.
    """
    def test_valid_png(self):
        """ .png created using the PIL. """
        self.upload_image_test('001_2012-05-01_color-grid-001.png')

    def test_valid_jpg(self):
        """ .jpg created using the PIL. """
        self.upload_image_test('001_2012-05-01_color-grid-001_jpg-valid.jpg')

    # TODO: Test a fairly large upload (at least 50 MB, or whatever
    # the upload limit is when memory is used for temp storage)?

class UploadImageFieldsTest(ImageUploadBaseTest):
    """
    Upload an image and see if all the fields have been set correctly.
    """
    def test_basic_image_fields(self):
        self.upload_image_test_with_field_checks('001_2012-05-01_color-grid-001.png')

class UploadDupeImageTest(ImageUploadBaseTest):
    """
    Duplicate images.
    """
    def duplicate_upload_test(self, dupe_option):
        options = dict(skip_or_replace_duplicates=dupe_option)

        self.upload_image_test('001_2012-05-01_color-grid-001.png', **options)

        # Non-duplicate
        self.upload_image_test('002_2012-06-28_color-grid-002.png', **options)

        # Duplicate
        datetime_before_dupe_upload = datetime.datetime.now().replace(microsecond=0)
        self.upload_image_test('001_2012-05-01_color-grid-001_jpg-valid.jpg', expecting_dupe=True, **options)

        image_001 = Image.objects.get(source__pk=self.source_id, metadata__value1__name='001')
        image_001_name = image_001.metadata.name

        if dupe_option == 'skip':

            # Check that the image name is from the original,
            # not the skipped dupe.
            self.assertEqual(image_001_name, 'color-grid-001.png')
            # Sanity check of the datetime of upload.
            # This check is of limited use since database datetimes (in MySQL 5.1 at least)
            # get truncated to whole seconds. But it still doesn't hurt to check.
            self.assertTrue(image_001.upload_date <= datetime_before_dupe_upload)

        else:  # 'replace'

            # Check that the image name is from the dupe
            # we just uploaded.
            self.assertEqual(image_001_name, 'color-grid-001_jpg-valid.jpg')
            # Sanity check of the datetime of upload.
            self.assertTrue(datetime_before_dupe_upload <= image_001.upload_date)


    def test_duplicate_upload_with_skip(self):
        self.duplicate_upload_test('skip')

    def test_duplicate_upload_with_replace(self):
        self.duplicate_upload_test('replace')


class UploadInvalidImageTest(ImageUploadBaseTest):
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


class UploadFilenameCheckTest(ImageUploadBaseTest):
    """
    Image upload tests: related to filename checking.
    Checking for correct number of location values, duplicate images,
    correct date format, recognition of the custom name at the end,
    and so on.

    Note that these are tests on the actual image upload operation.
    We actually expect the ajax-image-upload-preview to get these checks
    right in the first place.  What we are testing here is: if the
    Javascript is somehow faulty and allows the user to bypass the upload
    preview, could we catch filename errors on the server side as well?
    """

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


class PreviewFilenameTest(ImageUploadBaseTest):

    def test_status_types(self):
        """
        Try one error, one ok, and one dupe, all in the same preview batch.
        Check that all the expected returned information is present and correct.
        """
        image_id, response = self.upload_image_test(os.path.join('1key', '001_2011-05-28.png'))

        files = [
            ('rainbow_001_2011-05-28.png', 'error', None),
            ('002_2011-05-28.png', 'ok', '002;2011'),
            ('001_2011-06-19.png', 'dupe', '001;2011'),
        ]
        filenames = [f[0] for f in files]

        response = self.client.post(
            reverse('image_upload_preview_ajax', kwargs={'source_id': self.source_id}),
            {'filenames[]': filenames},
        )
        response_content = simplejson.loads(response.content)
        status_list = response_content['statusList']

        for index, f in enumerate(files):
            expected_status = f[1]
            self.assertEqual(status_list[index]['status'], expected_status)

            expected_metadata_key = f[2]
            if expected_metadata_key is not None:
                self.assertEqual(status_list[index]['metadataKey'], expected_metadata_key)

            # Yeah, this is ugly code...
            if index == 2:
                # Dupe; two more values to check.
                self.assertEqual(status_list[index]['url'], reverse('image_detail', args=[image_id]))
                self.assertEqual(status_list[index]['title'], Image.objects.get(pk=image_id).get_image_element_title())

                if settings.UNIT_TEST_VERBOSITY >= 1:
                    print "Dupe image URL: {url}".format(url=status_list[index]['url'])
                    print "Dupe image title: {title}".format(title=status_list[index]['title'])

    def test_dupe_detection(self):
        """
        Dupes and non-dupes should be detected as such.

        Not going to test all the filenames in the upload tests all
        over again.  Just a sampling, as a sanity check that filename
        checks behave the same between preview and upload.
        """
        self.upload_image_test(os.path.join('1key', '001_2012-05-28_rainbow-grid-one.png'))

        files = [
            ('002_2012-05-28.png', 'ok'),    # Number different
            ('001_2011-05-28.png', 'ok'),    # Year different
            ('002_2011-05-28.png', 'ok'),    # Both different
            ('001_2012-05-28.png', 'dupe'),
        ]
        filenames = [f[0] for f in files]

        response = self.client.post(
            reverse('image_upload_preview_ajax', kwargs={'source_id': self.source_id}),
            {'filenames[]': filenames},
        )
        response_content = simplejson.loads(response.content)
        status_list = response_content['statusList']

        for index, expected_status in enumerate([f[1] for f in files]):
            self.assertEqual(status_list[index]['status'], expected_status)

    def test_filename_errors(self):
        """
        Error messages should be returned as expected.

        Again, not going to test all the same filenames as
        the upload tests.
        """
        files = [
            ('2011-05-28.png', str_consts.FILENAME_PARSE_ERROR_STR),
            ('001_20120229.png', str_consts.FILENAME_DATE_PARSE_ERROR_FMTSTR.format(date_token='20120229')),
            ('001_2012-02-30.png', str_consts.FILENAME_DATE_VALUE_ERROR_FMTSTR.format(date_token='2012-02-30')),
            ('001_2011-01-01.png', str_consts.UPLOAD_PREVIEW_SAME_METADATA_ERROR_FMTSTR.format(metadata='001 2011')),
            ('001_2011-05-28.png', str_consts.UPLOAD_PREVIEW_SAME_METADATA_ERROR_FMTSTR.format(metadata='001 2011')),
        ]
        filenames = [f[0] for f in files]

        response = self.client.post(
            reverse('image_upload_preview_ajax', kwargs={'source_id': self.source_id}),
            {'filenames[]': filenames},
        )
        response_content = simplejson.loads(response.content)
        status_list = response_content['statusList']

        for index, expected_error in enumerate([f[1] for f in files]):
            self.assertEqual(status_list[index]['status'], 'error')
            self.assertEqual(status_list[index]['message'], expected_error)


class AnnotationUploadBaseTest(ImageUploadBaseTest):

    def check_annotation_file(self, annotations_filename, **options):

        annotations_file_dir = os.path.join(settings.SAMPLE_UPLOADABLES_ROOT, 'annotations_txt')
        annotations_filepath = os.path.join(annotations_file_dir, annotations_filename)
        annotations_file = open(annotations_filepath, 'rb')

        options.update(annotations_file=annotations_file)

        response = self.client.post(
            reverse('annotation_file_check_ajax', kwargs={'source_id': self.source_id}),
            options,
        )
        annotations_file.close()

        self.assertStatusOK(response)
        response_content = simplejson.loads(response.content)

        return response_content

    def upload_and_check_annotations(self, annotations_filename, image_filenames,
                                     expected_annotations_per_image,
                                     expected_annotations, **extra_options):

        options = dict(
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        options.update(extra_options)

        # Perform the annotation file check.
        response_content = self.check_annotation_file(annotations_filename, **options)

        self.assertEqual(response_content['status'], 'ok')

        annotations_per_image = response_content['annotations_per_image']

        # Check annotations_per_image for correctness:
        # Check keys.
        self.assertEqual(
            set(annotations_per_image.keys()),
            set(expected_annotations_per_image.keys()),
        )
        # Check values.
        self.assertEqual(annotations_per_image, expected_annotations_per_image)

        # Modify options so we can pass it into the image-upload view.
        options['annotation_dict_id'] = response_content['annotation_dict_id']

        actual_annotations = defaultdict(set)

        for image_filename in image_filenames:

            # Upload the file, and test that the upload succeeds and that
            # image fields are set correctly.
            image_id, response = self.upload_image_test_with_field_checks(
                image_filename,
                **options
            )

            img = Image.objects.get(pk=image_id)
            img_title = img.get_image_element_title()

            # Test that points/annotations were generated correctly.
            pts = Point.objects.filter(image=img)

            for pt in pts:
                if options['is_uploading_annotations_not_just_points'] == 'yes':
                    anno = Annotation.objects.get(point=pt)
                    actual_annotations[img_title].add( (pt.row, pt.column, anno.label.code) )
                else:  # 'no'
                    actual_annotations[img_title].add( (pt.row, pt.column))


        # All images we specified should have annotations, and there
        # shouldn't be any annotations for images we didn't specify.
        self.assertEqual(set(actual_annotations.keys()), set(expected_annotations.keys()))

        # All the annotations we specified should be there.
        for img_key in expected_annotations:
            self.assertEqual(actual_annotations[img_key], expected_annotations[img_key])


class AnnotationUploadTest(AnnotationUploadBaseTest):

    fixtures = ['test_users.yaml', 'test_labels.yaml',
                'test_labelsets.yaml', 'test_sources_with_labelsets.yaml']
    source_member_roles = [
        ('Labelset 2keys', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        ClientTest.setUp(self)
        self.client.login(username='user2', password='secret')
        self.source_id = Source.objects.get(name='Labelset 2keys').pk

        # Files to upload.
        self.image_filenames = [
            os.path.join('2keys', 'cool_001_2011-05-28.png'),
            os.path.join('2keys', 'cool_001_2012-05-28.png'),
            os.path.join('2keys', 'cool_002_2011-05-28.png'),
        ]

        # Number of annotations that should be recognized by the annotation
        # file check.  Note that the annotation file check does not know
        # what image files are actually going to be uploaded; so if the
        # annotation file contains annotations for image A, then it would
        # report an annotation count for image A even if A isn't uploaded.
        self.expected_annotations_per_image = {
            'cool;001;2011': 3,
            'cool;001;2012': 2,
            'cool;002;2011': 1,
            'will_not_be_uploaded;025;2004': 1,
        }

        # The annotations that should actually be created after the upload
        # completes.
        self.expected_annotations = {
            '2011 cool 001': set([
                (200, 300, 'Scarlet'),
                (50, 250, 'Lime'),
                (10, 10, 'Turq'),
            ]),
            '2012 cool 001': set([
                (1, 1, 'UMarine'),
                (400, 400, 'Lime'),
            ]),
            '2011 cool 002': set([
                (160, 40, 'Turq'),
            ]),
        }

        # Same as expected_annotations, but for the points-only option.
        self.expected_points = {
            '2011 cool 001': set([
                (200, 300),
                (50, 250),
                (10, 10),
            ]),
            '2012 cool 001': set([
                (1, 1),
                (400, 400),
            ]),
            '2011 cool 002': set([
                (160, 40),
            ]),
        }

    def test_annotation_upload(self):

        annotations_filename = 'colors_2keys_001.txt'

        self.upload_and_check_annotations(
            annotations_filename, self.image_filenames,
            self.expected_annotations_per_image,
            self.expected_annotations,
        )

    def test_points_only_with_labels_in_file(self):

        # Test with labels in the file.
        annotations_filename = 'colors_2keys_001.txt'

        self.upload_and_check_annotations(
            annotations_filename, self.image_filenames,
            self.expected_annotations_per_image,
            self.expected_points,
            is_uploading_annotations_not_just_points='no',
        )

    def test_points_only_without_labels_in_file(self):

        # Test without labels in the file.
        annotations_filename = 'colors_2keys_001_no_labels.txt'

        self.upload_and_check_annotations(
            annotations_filename, self.image_filenames,
            self.expected_annotations_per_image,
            self.expected_points,
            is_uploading_annotations_not_just_points='no',
        )

    def test_upload_an_image_with_zero_annotations_specified(self):

        annotations_filename = 'colors_2keys_001.txt'
        options = dict(
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='no',
        )

        response_content = self.check_annotation_file(
            annotations_filename,
            **options
        )

        # Run an image upload, avoiding most of the checks
        # that the other tests run.
        image_id, response = self.upload_image_test(
            os.path.join('2keys', 'rainbow_002_2012-05-28.png'),
            annotation_dict_id=response_content['annotation_dict_id'],
            **options
        )

        # Just check that the image fields are what we'd
        # expect for an image that doesn't have annotations
        # specified for it.  (i.e., it should have points
        # automatically generated.)
        img = Image.objects.get(pk=image_id)
        self.check_fields_for_non_annotation_upload(img)


class AnnotationUploadErrorTest(AnnotationUploadBaseTest):

    fixtures = ['test_users.yaml', 'test_labels.yaml',
                'test_labelsets.yaml', 'test_sources_with_labelsets.yaml']
    source_member_roles = [
        ('Labelset 2keys', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        ClientTest.setUp(self)
        self.client.login(username='user2', password='secret')
        self.source_id = Source.objects.get(name='Labelset 2keys').pk

    def test_annotations_on_and_no_annotation_dict(self):
        """
        Corner case that the client side code should prevent,
        but it's worth a test anyway.
        """
        options = dict(
            is_uploading_points_or_annotations='on',
        )

        image_id, response = self.upload_image(
            os.path.join('2keys', 'rainbow_002_2012-05-28.png'),
            **options
        )

        response_content = simplejson.loads(response.content)
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(response_content['message'], str_consts.UPLOAD_ANNOTATIONS_ON_AND_NO_ANNOTATION_DICT_ERROR_STR)

    def test_token_count_error(self):
        # Labels expected, too few tokens
        response_content = self.check_annotation_file(
            'colors_2keys_001_no_labels.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200; 300",
                error=str_consts.ANNOTATION_CHECK_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=6,
                    num_words_found=5,
                )
            )
        )

        # Labels expected, too many tokens
        response_content = self.check_annotation_file(
            'colors_2keys_error_too_many_tokens.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200; 300; Scarlet; UMarine",
                error=str_consts.ANNOTATION_CHECK_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=6,
                    num_words_found=7,
                )
            )
        )

        # Labels not expected, too few tokens
        response_content = self.check_annotation_file(
            'colors_2keys_error_too_few_tokens.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='no',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200",
                error=str_consts.ANNOTATION_CHECK_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=5,
                    num_words_found=4,
                )
            )
        )

        # Labels not expected, too few tokens
        response_content = self.check_annotation_file(
            'colors_2keys_error_too_many_tokens.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='no',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200; 300; Scarlet; UMarine",
                error=str_consts.ANNOTATION_CHECK_TOKEN_COUNT_ERROR_FMTSTR.format(
                    num_words_expected=5,
                    num_words_found=7,
                )
            )
        )

    def test_label_not_in_database(self):
        response_content = self.check_annotation_file(
            'colors_2keys_error_label_not_in_database.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200; 300; Yellow",
                error=str_consts.ANNOTATION_CHECK_LABEL_NOT_IN_DATABASE_ERROR_FMTSTR.format(
                    label_code='Yellow',
                )
            )
        )

    def test_label_not_in_labelset(self):
        response_content = self.check_annotation_file(
            'colors_2keys_error_label_not_in_labelset.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 2011; 200; 300; Forest",
                error=str_consts.ANNOTATION_CHECK_LABEL_NOT_IN_LABELSET_ERROR_FMTSTR.format(
                    label_code='Forest',
                )
            )
        )

    def test_invalid_year(self):
        response_content = self.check_annotation_file(
            'colors_2keys_error_invalid_year.txt',
            is_uploading_points_or_annotations='on',
            is_uploading_annotations_not_just_points='yes',
        )
        self.assertEqual(response_content['status'], 'error')
        self.assertEqual(
            response_content['message'],
            str_consts.ANNOTATION_CHECK_FULL_ERROR_MESSAGE_FMTSTR.format(
                line_num="1",
                line="cool; 001; 04-26-2011; 200; 300; Scarlet",
                error=str_consts.ANNOTATION_CHECK_YEAR_ERROR_FMTSTR.format(
                    year='04-2',
                )
            )
        )
