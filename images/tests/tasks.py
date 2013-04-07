from images.models import Source, Image
from images.tasks import PreprocessImages, MakeFeatures, Classify, addLabelsToFeatures, trainRobot
from lib.test_utils import ProcessingTestComponent, ClientTest, MediaTestComponent


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

        self.image_id = self.upload_image('001_2012-05-01_color-grid-001.png')[0]

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