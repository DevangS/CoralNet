from django.core.urlresolvers import reverse
from images.models import Source
from lib.test_utils import ClientTest, MediaTestComponent


class AnnotationToolTest(ClientTest):
    """
    Test the image view page.
    This is an abstract class that doesn't actually have any tests.
    """
    extra_components = [MediaTestComponent]
    fixtures = ['test_users.yaml', 'test_labels.yaml',
                'test_labelsets.yaml', 'test_sources_with_labelsets.yaml']
    source_member_roles = [
        ('public1', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def setUp(self):
        super(AnnotationToolTest, self).setUp()
        self.source_id = Source.objects.get(name='public1').pk

    def annotation_tool_with_image(self, image_file):
        self.client.login(username='user2', password='secret')

        image_id = self.upload_image(self.source_id, image_file)

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
