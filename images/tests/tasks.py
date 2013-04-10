import os
import random
from django.conf import settings

from django.contrib.auth.models import User
from accounts.utils import get_robot_user, get_imported_user

from annotations.models import Annotation
from images.models import Source, Image, Point, Robot
from images.tasks import PreprocessImages, MakeFeatures, Classify, addLabelsToFeatures, trainRobot
from lib.test_utils import ProcessingTestComponent, ClientTest, MediaTestComponent


class ImageProcessingTaskBaseTest(ClientTest):
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


        # Implemented by subclasses.
        raise NotImplementedError


    def add_human_annotations(self, image_id, user=None):
        """
        Add human annotations to an image.

        :param user - The user who will be the annotator of these
        annotations.  If not specified, default to the User of
        self.username.
        """


        source = Source.objects.get(pk=self.source_id)
        img = Image.objects.get(pk=image_id)
        points = Point.objects.filter(image=img)
        labels = source.labelset.labels.all()
        if user is None:
            user = User.objects.get(username=self.username)

        # For each point, pick a label randomly from the source's labelset.
        for pt in points:
            label = random.choice(labels)
            anno = Annotation(
                point=pt,
                image=img,
                source=source,
                user=user,
                label=label,
            )
            anno.save()
        img.status.annotatedByHuman = True
        img.status.save()


    def setUp(self):


        super(ImageProcessingTaskBaseTest, self).setUp()
        self.source_id = Source.objects.get(name='Labelset 1key').pk

        self.client.login(username='user2', password='secret')
        self.username = 'user2'

        self.upload_images()


class SingleImageProcessingTaskTest(ImageProcessingTaskBaseTest):


    def upload_images(self):


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


class MultiImageProcessingTaskTest(ImageProcessingTaskBaseTest):


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


        # Take at least (min number for training) images.
        # Preprocess, feature extract, and add human annotations to
        # the features.
        for img in Image.objects.filter(source__pk=self.source_id):
            PreprocessImages.delay(img.id)
            MakeFeatures.delay(img.id)
            self.add_human_annotations(img.id)
            addLabelsToFeatures.delay(img.id)


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
        # Check that the image's actual Annotation objects are there.
        # Should have 1 annotation per point.
        self.assertEqual(
            Annotation.objects.filter(image__pk=img_id).count(),
            Point.objects.filter(image__pk=img_id).count(),
        )

        # TODO: Check that the history entries are there?


        # Run task, attempt 2.
        result = Classify.delay(img_id)

        # Check that the task didn't encounter an exception
        self.assertTrue(result.successful())
        # Should have exited without re-doing the classification
        # TODO: Check file ctime/mtime to check that it wasn't redone?
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)


    def test_reclassify(self):
        """
        Test that we can classify an image twice with two different robots,
        and that the robot annotations are actually updated on the second
        classification.

        Note: this test is able to catch errors ONLY if the two different
        robots assign different labels to the image points.
        """


        # Take at least (min number for training) images.
        # Preprocess, feature extract, and add human annotations to
        # the features.
        for img in Image.objects.filter(source__pk=self.source_id):
            PreprocessImages.delay(img.id)
            MakeFeatures.delay(img.id)
            self.add_human_annotations(img.id)
            addLabelsToFeatures.delay(img.id)

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


        # Classify, 1st time.
        result = Classify.delay(img_id)

        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)

        num_points = Point.objects.filter(image__pk=img_id).count()
        self.assertEqual(
            Annotation.objects.filter(image__pk=img_id).count(),
            num_points,
        )


        # Verify that the points match those in the label file output by the
        # classification task.
        label_filename = os.path.join(
            settings.PROCESSING_ROOT,
            'images',
            'classify',
            '{img_id}_{process_date}.txt'.format(
                img_id=str(img_id),
                process_date=Image.objects.get(pk=img_id).get_process_date_short_str(),
            )
        )

        label_file = open(label_filename)

        # The label file should have one label id per line, with each line
        # corresponding to one point of the image.
        labels_in_label_file = dict()
        point_num = 1

        for line in label_file:

            line = line.strip()
            if line == '':
                continue

            label_id = int(line)
            labels_in_label_file[point_num] = label_id
            point_num += 1

        label_file.close()

        for point_num in range(1, num_points+1):

            label_id = Annotation.objects.get(image__pk=img_id, point__point_number=point_num).label.id
            self.assertEqual(label_id, labels_in_label_file[point_num])


        # Add another training image.
        extra_training_img_id = self.upload_image(
            os.path.join('1key', '001_2011-05-28.png')
        )[0]
        PreprocessImages.delay(extra_training_img_id)
        MakeFeatures.delay(extra_training_img_id)
        self.add_human_annotations(extra_training_img_id)
        addLabelsToFeatures.delay(extra_training_img_id)

        # Create another robot.
        result = trainRobot.delay(self.source_id)
        self.assertTrue(result.successful())


        # Classify, 2nd time.
        result = Classify.delay(img_id)

        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)

        # We'd better still have one annotation per point
        # (not two annotations per point).
        self.assertEqual(
            Annotation.objects.filter(image__pk=img_id).count(),
            Point.objects.filter(image__pk=img_id).count(),
        )


        # Verify, again, that the points match those in the label file output
        # by the classification task.
        label_file = open(label_filename)

        labels_in_label_file = dict()
        point_num = 1

        for line in label_file:

            line = line.strip()
            if line == '':
                continue

            label_id = int(line)
            labels_in_label_file[point_num] = label_id
            point_num += 1

        label_file.close()

        for point_num in range(1, num_points+1):

            label_id = Annotation.objects.get(image__pk=img_id, point__point_number=point_num).label.id
            self.assertEqual(label_id, labels_in_label_file[point_num])


        # TODO: Check that new history entries are created / not created accordingly?


    def helper_classify_does_not_overwrite_manual_annotations(self, annotator_user):
        """
        Helper function for the tests that follow.
        """


        # Take at least (min number for training) images.
        # Preprocess, feature extract, and add human annotations to
        # the features.
        for img in Image.objects.filter(source__pk=self.source_id):
            PreprocessImages.delay(img.id)
            MakeFeatures.delay(img.id)
            self.add_human_annotations(img.id)
            addLabelsToFeatures.delay(img.id)

        # Create a robot.
        result = trainRobot.delay(self.source_id)
        self.assertTrue(result.successful())


        # Upload a new image.
        img_id = self.upload_image('006_2012-06-28_color-grid-006.png')[0]

        # Preprocess and feature extract.
        PreprocessImages.delay(img_id)
        MakeFeatures.delay(img_id)

        # Add annotations.
        source = Source.objects.get(pk=self.source_id)
        img = Image.objects.get(pk=img_id)
        points = Point.objects.filter(image=img)
        labels = source.labelset.labels.all()

        # For odd-numbered points, make an annotation by picking a
        # label randomly from the source's labelset.
        # Leave the even-numbered points alone.
        # (Assumption: the test source has at least 2 points per image)
        for pt in points:

            if pt.point_number % 2 == 0:
                continue

            label = random.choice(labels)
            anno = Annotation(
                point=pt,
                image=img,
                source=source,
                user=annotator_user,
                label=label,
            )
            anno.save()

        img.status.save()


        # Get those annotations (again, only odd-numbered points).
        num_points = Point.objects.filter(image__pk=img_id).count()
        manual_annotations = dict()

        for point_num in range(1, num_points+1, 2):

            label_id = Annotation.objects.get(image__pk=img_id, point__point_number=point_num).label.id
            manual_annotations[point_num] = label_id


        # Try to Classify.
        result = Classify.delay(img_id)

        # Shouldn't throw exception.
        self.assertTrue(result.successful())
        self.assertEqual(Image.objects.get(pk=img_id).status.annotatedByRobot, True)


        # Check the Annotations.
        for point_num in range(1, num_points+1):

            anno = Annotation.objects.get(image__pk=img_id, point__point_number=point_num)
            label_id = anno.label.id

            if point_num % 2 == 0:
                # Even; should be robot
                self.assertEqual(anno.user.id, get_robot_user().id)
            else:
                # Odd; should be manual (and same as before)
                self.assertEqual(label_id, manual_annotations[point_num])
                self.assertEqual(anno.user.id, annotator_user.id)

            if settings.UNIT_TEST_VERBOSITY >= 1:
                print "Point {num} | {username} | {label_id}".format(
                    num=point_num,
                    username=anno.user.username,
                    label_id=label_id,
                )


    def test_classify_does_not_overwrite_human_user_annotations(self):
        """
        Tests that when an image is partially annotated by a non-robot
        CoralNet user, automatic classification doesn't overwrite any
        of that user's points.
        """
        self.helper_classify_does_not_overwrite_manual_annotations(
            User.objects.get(username=self.username)
        )


    def test_classify_does_not_overwrite_imported_annotations(self):
        """
        Tests that when an image is partially annotated by imported data,
        automatic classification doesn't overwrite any of the imported
        points.
        """
        self.helper_classify_does_not_overwrite_manual_annotations(
            get_imported_user()
        )


    def test_classify_with_multiple_points_on_same_pixel(self):
        """
        Tests that classification still works as expected when the classified
        image has more than one point on a single pixel (row/col) location.
        """
        # TODO
        pass