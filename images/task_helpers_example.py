# Here's an example of what task_helpers.py would look like.
#
# task_helpers.py contains SYSTEM SPECIFIC helper functions for tasks.
# For production environments, these are typically calls to an
# outside program like Matlab.  For development environments,
# these are typically light scripts that do the minimum file manipulations
# required by the task.
#
# Because task_helpers.py is system specific, it should not be added
# to the Git repository.  Only this file (which is not imported by
# anything, but merely serves as an example) should be in the Git
# repository.
#
# If you add a function to task_helpers.py, add it to this example file
# too, so other team members know what needs to go in their task_helpers.py.


def coralnet_preprocessImage(imageFile, preprocessedImageFile, preprocessParameterFile, errorLogfile):
    # The Preprocessing step prepares the image for feature making.
    pass


def coralnet_makeFeatures(preprocessedImageFile, featureFile, rowColFile, featureExtractionParameterFile, errorLogfile):
    # The Feature file encodes the visual features around each point.
    pass


def coralnet_classify(featureFile, modelFile, labelFile, errorLogfile):
    # The label file is the result of classification: what each point is labelled as.
    # From the feature file, we get information about the points.
    # From the model file, we figure out how to label a point given its features.
    #
    # The model file needs to be made manually or by a separate program; it is not
    # made by any tasks.  The model file also needs to be set as the path_to_model of
    # the Robot that's being used.
    pass
