import random

from django.contrib.auth.models import User

from annotations.models import Annotation
from images.models import Source, Image, Point, Robot
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
    fixtures = [
        'test_users.yaml',
        'test_labels.yaml',
        'test_labelsets.yaml',
        'test_sources_with_labelsets.yaml',
    ]
    source_member_roles = [
        ('Labelset 1key', 'user2', Source.PermTypes.ADMIN.code),
    ]

    def upload_images(self):
        # Sub-classes can override this to upload more images as needed.
        self.image_id = self.upload_image('001_2012-05-01_color-grid-001.png')[0]

    def add_human_annotations(self, image_id):
        # Add human annotations to an image.
        # For each point, pick a label randomly from the source's labelset.

        source = Source.objects.get(pk=self.source_id)
        img = Image.objects.get(pk=image_id)
        points = Point.objects.filter(image=img)
        labels = source.labelset.labels.all()

        for pt in points:
            label = random.choice(labels)
            anno = Annotation(
                point=pt,
                image=img,
                source=source,
                user=User.objects.get(username=self.username),
                label=label,
            )
            anno.save()
        img.status.annotatedByHuman = True
        img.status.save()

    def setUp(self):
        super(ImageProcessingTaskTest, self).setUp()
        self.source_id = Source.objects.get(name='Labelset 1key').pk

        self.client.login(username='user2', password='secret')
        self.username = 'user2'

        self.upload_images()

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


    def test_add_feature_labels_task(self):


        # Preprocess and feature-extract first.
        result = PreprocessImages.delay(self.image_id)
        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=self.image_id).status.preprocessed, True)
        result = MakeFeatures.delay(self.image_id)
        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featuresExtracted, True)

        # Add human annotations.
        self.add_human_annotations(self.image_id)


        # Sanity check: haven't added labels to features yet
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, False)


        # Run task, attempt 1.
        result = addLabelsToFeatures.delay(self.image_id)
        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())

        # Should have added labels to features
        # TODO: Check file ctime/mtime to check that the file was changed
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)


        # Run task, attempt 2.
        result = addLabelsToFeatures.delay(self.image_id)
        self.assertTrue(result.successful())

        # Should have exited without re-doing label adding
        # TODO: Check file ctime/mtime to check that it wasn't redone?
        self.assertEqual(Image.objects.get(pk=self.image_id).status.featureFileHasHumanLabels, True)


class MultiImageProcessingTaskTest(ImageProcessingTaskTest):


    def upload_images(self):


        # As of the time of writing, the requirement for training a robot
        # is to have 5 images with annotations.  So upload at least 5.
        self.upload_image('001_2012-05-01_color-grid-001.png')
        self.upload_image('002_2012-06-28_color-grid-002.png')
        self.upload_image('003_2012-06-28_color-grid-003.png')
        self.upload_image('004_2012-06-28_color-grid-004.png')
        self.upload_image('005_2012-06-28_color-grid-005.png')


    def test_train_robot_task(self):


        # Take at least (min number for training) images.  Preprocess,
        # feature extract, and add human annotations to the features.
        source_images = Image.objects.filter(source__pk=self.source_id)

        for img in source_images:
            PreprocessImages.delay(img.id)
            MakeFeatures.delay(img.id)
            self.add_human_annotations(img.id)
            addLabelsToFeatures.delay(img.id)

        # From now on, this variable may be out of date.
        # del it to avoid mistakes.
        del source_images


        # Create a robot.
        result = trainRobot.delay(self.source_id)
        self.assertTrue(result.successful())


        source_images = Image.objects.filter(source__pk=self.source_id)

        for img in source_images:
            self.assertTrue(img.status.usedInCurrentModel)


    def test_classify_task(self):


        # Take at least (min number for training) images.  Preprocess,
        # feature extract, and add human annotations to the features.
        source_images = Image.objects.filter(source__pk=self.source_id)

        for img in source_images:
            PreprocessImages.delay(img.id)
            MakeFeatures.delay(img.id)
            self.add_human_annotations(img.id)
            addLabelsToFeatures.delay(img.id)

        # From now on, this variable may be out of date.
        # del it to avoid mistakes.
        del source_images


        # Create a robot.
        result = trainRobot.delay(self.source_id)
        self.assertTrue(result.successful())


        # Upload a new image.
        img_id = self.upload_image('006_2012-06-28_color-grid-006.png')[0]

        # Preprocess and feature extract.
        PreprocessImages.delay(img_id)
        MakeFeatures.delay(img_id)
        # Sanity check: not classified yet
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, False)


        # Run task, attempt 1.
        result = Classify.delay(img_id)

        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())
        # Should have classified the image
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)


        # Run task, attempt 2.
        result = Classify.delay(img_id)

        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())
        # Should have exited without re-doing the classification
        # TODO: Check file ctime/mtime to check that it wasn't redone?
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)