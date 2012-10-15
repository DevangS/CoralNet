from django.conf import settings
from django.core.urlresolvers import reverse
from annotations.model_utils import AnnotationAreaUtils
from images.model_utils import PointGen
from images.models import Source, Image, Point
from lib.test_utils import ClientTest, MediaTestComponent


class AnnotationToolTest(ClientTest):
    """
    Test the annotation tool page.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_labels.yaml',
                'test_labelsets.yaml', 'test_sources_with_labelsets.yaml']
    source_member_roles = [
        ('Labelset 1key', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(AnnotationToolTest, self).setUp()
        self.source_id = Source.objects.get(name='Labelset 1key').pk

    def annotation_tool_with_image(self, image_file):
        self.client.login(username='user2', password='secret')

        image_id = self.upload_image(image_file)[0]

        response = self.client.get(reverse('annotation_tool', kwargs={'image_id': image_id}))
        self.assertStatusOK(response)

        # Try fetching the page a second time, to make sure thumbnail
        # generation doesn't go nuts.
        response = self.client.get(reverse('annotation_tool', kwargs={'image_id': image_id}))
        self.assertStatusOK(response)

        # TODO: Add more checks.

    def test_annotation_tool_with_small_image(self):
        self.annotation_tool_with_image('001_2012-05-01_color-grid-001.png')

    def test_annotation_tool_with_large_image(self):
        self.annotation_tool_with_image('002_2012-05-29_color-grid-001_large.png')


class PointGenTest(ClientTest):
    """
    Test generation of annotation points.
    """
    extra_components = [MediaTestComponent]
    fixtures = [
        'test_users.yaml',
        'test_sources_with_different_pointgen_params.yaml'
    ]
    source_member_roles = [
        ('Pointgen simple 1', 'user2', Source.PermTypes.ADMIN.code),
        ('Pointgen simple 2', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(PointGenTest, self).setUp()
        self.client.login(username='user2', password='secret')

    def pointgen_check(self, image_id):
        """
        Check that an image had annotation points generated as
        specified in the point generation method field.

        :param image_id: The id of the image to check.
        """
        img = Image.objects.get(pk=image_id)
        img_width = img.original_width
        img_height = img.original_height
        pointgen_args = PointGen.db_to_args_format(img.point_generation_method)

        points = Point.objects.filter(image=img)
        self.assertEqual(points.count(), pointgen_args['simple_number_of_points'])

        # Find the expected annotation area, expressed in pixels.
        d = AnnotationAreaUtils.db_format_to_numbers(img.metadata.annotation_area)
        annoarea_type = d.pop('type')
        if annoarea_type == AnnotationAreaUtils.TYPE_PERCENTAGES:
            area = AnnotationAreaUtils.percentages_to_pixels(width=img_width, height=img_height, **d)
        elif annoarea_type == AnnotationAreaUtils.TYPE_PIXELS:
            area = d
        elif annoarea_type == AnnotationAreaUtils.TYPE_IMPORTED:
            area = dict(min_x=1, max_x=img_width, min_y=1, max_y=img_height)
        else:
            raise ValueError("Unknown annotation area type.")

        if settings.UNIT_TEST_VERBOSITY >= 1:
            print "{pointgen_method}".format(
                pointgen_method=img.point_gen_method_display(),
            )
            print "{annotation_area}".format(
                annotation_area=img.annotation_area_display(),
            )
            print "Image dimensions: {width} x {height} pixels".format(
                width=img_width, height=img_height,
            )
            print "X bounds: ({min_x}, {max_x}) Y bounds: ({min_y}, {max_y})".format(
                **area
            )

        for pt in points:
            self.assertTrue(area['min_x'] <= pt.column)
            self.assertTrue(pt.column <= area['max_x'])
            self.assertTrue(area['min_y'] <= pt.row)
            self.assertTrue(pt.row <= area['max_y'])

            if settings.UNIT_TEST_VERBOSITY >= 1:
                print "({col}, {row})".format(col=pt.column, row=pt.row)

    def test_pointgen_on_image_upload(self):
        """
        Test that annotation points are generated correctly upon an
        image upload.

        Test two different sources (with different pointgen parameters) and
        two different images (of different width/height) for each source.
        """
        image_ids = []

        self.source_id = Source.objects.get(name='Pointgen simple 1').id

        image_ids.append(self.upload_image('001_2012-10-14_small-rect.png')[0])
        image_ids.append(self.upload_image('002_2012-10-14_tiny-rect.png')[0])

        self.source_id = Source.objects.get(name='Pointgen simple 2').id

        image_ids.append(self.upload_image('001_2012-10-14_small-rect.png')[0])
        image_ids.append(self.upload_image('002_2012-10-14_tiny-rect.png')[0])

        for image_id in image_ids:
            self.pointgen_check(image_id)

    # TODO: Test stratified random and uniform grid as well, not just simple random.
    # TODO: Test unusual annotation areas: min and max very close or the same, and decimal percentages.
    # TODO: Check points' annotation statuses?