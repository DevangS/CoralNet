import time
import csv
from shutil import copyfile
from datetime import datetime
import pickle
from random import random
import shutil
from celery.task import task
import operator
import os, copy
from django.conf import settings
from django.core.mail import send_mail
import json, csv, os.path, time
from django.shortcuts import render_to_response, get_object_or_404

try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

from django.db import transaction
import reversion
from accounts.utils import get_robot_user
from accounts.utils import is_robot_user
from annotations.models import Label, Annotation, LabelGroup
from images import task_helpers, task_utils
from images.models import Point, Image, Source, Robot
from numpy import array, zeros, sum, float32, newaxis
import numpy as np
import math

# Revision objects will not be saved during Celery tasks unless
# the Celery worker hooks up Reversion's signal handlers.
# To do this, import admin modules so that
# the admin registration statements are run.
from django.contrib import admin
admin.autodiscover()


join_processing_root = lambda *p: os.path.join(settings.PROCESSING_ROOT, *p)

# In most cases you'll join from the image-processing root directory, not
# from the project root directory.  Uncomment this if needed though.
# - Stephen
#join_project_root = lambda *p: os.path.join(settings.PROJECT_ROOT, *p)

PREPROCESS_ERROR_LOG = join_processing_root("logs/preprocess_error.txt")
FEATURE_ERROR_LOG = join_processing_root("logs/features_error.txt")
CLASSIFY_ERROR_LOG = join_processing_root("logs/classify_error.txt")
TRAIN_ERROR_LOG = join_processing_root("logs/train_error.txt")
CV_LOG = join_processing_root("logs/cvlog.txt")

ORIGINALIMAGES_DIR = settings.MEDIA_ROOT
PREPROCESS_DIR = join_processing_root("images/preprocess/")
FEATURES_DIR = join_processing_root("images/features/")
CLASSIFY_DIR = join_processing_root("images/classify/")
MODEL_DIR = join_processing_root("images/models/")
TARGET_PIXEL_CM_RATIO = 17.2

PREPROCESS_PARAM_FILE = join_processing_root("images/preprocess/preProcessParameters.mat")

#Tasks that get processed by Celery
#Possible future problems include that each task relies on it being the same day to continue processing an image,
#a solution would be to store the date that you preprocess the iamge and then update it if you run a newer version of
#the algorithm against it

@task()
def dummyTask():
    print("This is a dummy task console output")
    return 1

@task()
def dummyTaskLong(s):
    print("This is a dummy task that can sleep")
    time.sleep(s)

# this task is depleated!!!
def processAllSources():
	keyfilepath = join_processing_root("images/robot_running_flag")
	if os.path.exists(keyfilepath):
		return 1
	open(keyfilepath, 'w')
	for source in Source.objects.filter(enable_robot_classifier=True):
		processSourceCompleate(source.id)
	os.remove(keyfilepath)

# this is the new MAIN TASK called by the CRONJOB once per day. It parallellize on the source level. This allows for two calls to svmtrain concurrently. Which might hog a ton of memory, but it will be faster.
def processAllSourcesConcurrent():
    keyfilepath = join_processing_root("images/robot_running_flag")
    if os.path.exists(keyfilepath):
        return 1
    open(keyfilepath, 'w')
    for source in Source.objects.filter(enable_robot_classifier=True):
        result = processSingleSource.delay(source.id)
    while not result.ready(): #NOTE, implement with callback
        time.sleep(5)
    os.remove(keyfilepath)

# this task is depleated!!!
@task()
def processSourceCompleate(source_id):
    source = Source.objects.get(pk = source_id)
    
    if not source.get_all_images():
        return 1

    print "==== Processing source: " + source.name + " ===="
    # == For each image, do all preprocessing ==
    for image in source.get_all_images():
        result = prepareImage.delay(image.id)
    while not result.ready(): #NOTE, implement with callback
        time.sleep(5)

    # == Train robot for this source ==
    result = trainRobot.delay(source.id)
    while not result.ready():
        time.sleep(5)

    # == Classify all images with the new robot ==
    for image in source.get_all_images():
        result = Classify.delay(image.id)
    while not result.ready():
        time.sleep(5)
    print "==== Source: " + source.name + " done ===="


# this function is used by the main CRONJOB task. But is can also be called from the command line. 
@task()
def processSingleSource(source_id):
    source = Source.objects.get(pk = source_id)
    
    if not source.get_all_images():
        return 1

    print "==== Processing source: " + source.name + " ===="
    # == For each image, do all preprocessing ==
    for image in source.get_all_images():
        prepareImage(image.id)

    # == Train robot for this source ==
    trainRobot(source.id)

    # == Classify all images with the new robot ==
    for image in source.get_all_images():
        Classify(image.id)
    print "==== Source: " + source.name + " done ===="
    return 1


@task()
def prepareImage(image_id):
    PreprocessImages(image_id)
    MakeFeatures(image_id)
    addLabelsToFeatures(image_id)
    return 1

@task()
@transaction.commit_on_success()
def PreprocessImages(image_id):
    image = Image.objects.get(pk=image_id)

    # check if already preprocessed
    if image.status.preprocessed:
        print 'PreprocessImages: Image {id} is already preprocessed'.format(id = image_id)
        return 1

    if not (image.metadata.height_in_cm or image.source.image_height_in_cm):
        print "PreprocessImages: Can't get a cm height for image {id}. Can not preprocess".format(id = image_id)
        return 1

    ####### EVERYTHING OK: START THE IMAGE PREPROCESSING ##########
    image.status.preprocessed = True # Update database
    image.status.save()
    print 'Start pre-processing image id {id}'.format(id = image_id)

    thisPixelCmRatio = image.original_height / float(image.height_cm())
    subSampleRate = thisPixelCmRatio / TARGET_PIXEL_CM_RATIO
    if(subSampleRate < 1):
        print 'Changed ssrate from {ssold} to 1 for id {id}'.format(ssold = subSampleRate, id = image_id)
        subSampleRate = 1

    #creates ssRate file
    ssFile = os.path.join(PREPROCESS_DIR, str(image_id) + "_ssRate.txt")
    file = open(ssFile, 'w')
    file.write(str(subSampleRate) + "\n");
    file.close()

    # set the process_date to todays date
    image.process_date = datetime.now()
    image.save()

    #matlab will output image.id_YearMonthDay.mat file
    preprocessedImageFile = os.path.join(PREPROCESS_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".mat")

    task_helpers.coralnet_preprocessImage(
        imageFile=os.path.join(ORIGINALIMAGES_DIR, str(image.original_file)),
        preprocessedImageFile=preprocessedImageFile,
        preprocessParameterFile=PREPROCESS_PARAM_FILE,
        ssFile = ssFile,
        logFile = CV_LOG,
        errorLogfile=PREPROCESS_ERROR_LOG,
    )

    #error occurred in matlab
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        image.status.preprocessed = False # roll back data base changes
        image.status.save()
        print("Sorry error detected in preprocessing this image, halting!")
        send_mail('CoralNet Backend Error', 'in PreprocessImages', 'noreply@coralnet.ucsd.edu', ['oscar.beijbom@gmail.com'])
    #everything went okay with matlab
    else:
        print 'Finished pre-processing image id {id}'.format(id = image_id)
    return 1

@task()
def MakeFeatures(image_id):
    image = Image.objects.get(pk=image_id)

    #if error had occurred in preprocess, don't let them go further
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("MakeFeatures: Sorry error detected in preprocessing, halting feature extraction!")
        return
    if not image.status.preprocessed:
        print 'MakeFeatures: Image id {id} is not preprocessed. Can not make features'.format(id = image_id)
        return
    if not image.status.hasRandomPoints:
        print 'MakeFeatures: Image id {id} doesnt have random points. Can not make features'.format(id = image_id)
        return
    if image.status.featuresExtracted:
        print 'MakeFeatures: Features already extracted for image id {id}'.format(id = image_id)
        return

    ####### EVERYTHING OK: START THE FEATURE EXTRACTION ##########
    print 'Start feature extraction for image id {id}'.format(id = image_id)
    image.status.featuresExtracted = True;
    image.status.save()

    #builds args for matlab script
    preprocessedImageFile = os.path.join(PREPROCESS_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".mat")
    featureFile = os.path.join(FEATURES_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".dat")
    #creates rowColFile
    rowColFile = os.path.join(FEATURES_DIR, str(image_id) + "_rowCol.txt")
    file = open(rowColFile, 'w')
    points = Point.objects.filter(image=image)
    for point in points:
        #points get stored in the file in this format, one of these per line: row,column\n
        file.write(str(point.row) + "," + str(point.column) + "\n")
    file.close()

    ssFile = os.path.join(PREPROCESS_DIR, str(image_id) + "_ssRate.txt")
    task_helpers.coralnet_makeFeatures(
        preprocessedImageFile=preprocessedImageFile,
        featureFile=featureFile,
        rowColFile=rowColFile,
        ssFile = ssFile,
        featureExtractionParameterFile=PREPROCESS_PARAM_FILE,
        logFile = CV_LOG,
        errorLogfile=FEATURE_ERROR_LOG,
    )

    if os.path.isfile(FEATURE_ERROR_LOG):
        image.status.featuresExtracted = False;
        image.status.save()
        print("Sorry error detected in feature extraction!")
        send_mail('CoralNet Backend Error', 'in MakeFeatures', 'noreply@coralnet.ucsd.edu', ['oscar.beijbom@gmail.com'])
    else:
        print 'Finished feature extraction for image id {id}'.format(id = image_id)

@task()
@transaction.commit_on_success()
@reversion.create_revision()
def Classify(image_id):
    image = Image.objects.get(pk=image_id)

    # if annotated by Human, no need to re-classify
    if image.status.annotatedByHuman:
        print 'Classify: Image nr ' + str(image_id) + ' is annotated by the human operator, aborting'
        return

    # make sure that the previous step is complete
    if not image.status.featuresExtracted:
        print 'Classify: Features not extracted for image id {id}, can not proceed'.format(id = image_id)
        return

    # Get all robots for this source
    latestRobot = image.source.get_latest_robot()

    if latestRobot == None:
        print 'Classify: No robots exist for the source, {src}, of image id {id}. Aborting.'.format(src=image.source, id=image_id)
        return

    # Check if this image has been previously annotated by a robot.
    if (image.status.annotatedByRobot):
        # now, compare this version number to the latest_robot_annotator field for image.
        if (not (latestRobot.version > image.latest_robot_annotator.version)):
            print 'Image {id} is already annotated by the latest robot version, {ver}, for source, {src}'.format(id = image_id,  ver=latestRobot.version, src=image.source)
            return

    ####### EVERYTHING OK: START THE CLASSIFICATION ##########
    print 'Start classify image id {id}'.format(id = image_id)
    #builds args for matlab script
    featureFile = os.path.join(FEATURES_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".dat")
    #get the source id for this file
    labelFile = os.path.join(CLASSIFY_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".txt")

    task_helpers.coralnet_classify(
        featureFile=featureFile,
        modelFile=latestRobot.path_to_model,
        labelFile=labelFile,
        logFile=CV_LOG,
        errorLogfile=CLASSIFY_ERROR_LOG,
    )

    if os.path.isfile(CLASSIFY_ERROR_LOG):
        print("Error detected in image classification.")
        send_mail('CoralNet Backend Error', 'in Classify', 'noreply@coralnet.ucsd.edu', ['oscar.beijbom@gmail.com'])
        return 0
    else:
        #update image status
        image.status.annotatedByRobot = True
        image.status.save()
        image.latest_robot_annotator = latestRobot
        image.save()


    #get algorithm user object
    user = get_robot_user()

    # Get the label probabilities that we just generated
    label_probabilities = task_utils.get_label_probabilities_for_image(image_id)

    # Go through each point and update/create the annotation as appropriate
    for point_number, probs in label_probabilities.iteritems():
        pt = Point.objects.get(image=image, point_number=point_number)

        probs_descending_order = sorted(probs, key=operator.itemgetter('score'), reverse=True)
        top_prob_label_code = probs_descending_order[0]['label']
        label = Label.objects.get(code=top_prob_label_code)

        # If there's an existing annotation for this point, get it.
        # Otherwise, create a new annotation.
        #
        # (Assumption: there's at most 1 Annotation per Point, never multiple.
        # If there are multiple, we'll get a MultipleObjectsReturned exception.)
        try:
            anno = Annotation.objects.get(image=image, point=pt)

        except Annotation.DoesNotExist:
            # No existing annotation. Create a new one.
            new_anno = Annotation(
                image=image, label=label, point=pt,
                user=user, robot_version=latestRobot, source=image.source
            )
            new_anno.save()

        else:
            # Got an existing annotation.
            if is_robot_user(anno.user):
                # It's an existing robot annotation. Update it as necessary.
                if anno.label.id != label.id:
                    anno.label = label
                    anno.robot_version = latestRobot
                    anno.save()

            # Else, it's an existing confirmed annotation, and we don't want
            # to overwrite it. So do nothing in this case.

    print 'Finished classification of image id {id}'.format(id = image_id)


# This task modifies the feature file so that is contains the correct labels, as provided by the human operator.
@task()
def addLabelsToFeatures(image_id):

    image = Image.objects.get(pk=image_id)
    if not image.status.annotatedByHuman:
        print 'addLabelsToFeatures: Image id {id} is not annoated by human. Can not make add labels to feature file'.format(id = image_id)
        return 0
    if not image.status.featuresExtracted:
        print 'addLabelsToFeatures: Image id {id} has not yet gone through feature extraction. Can not add labels to feature file'.format(id = image_id)
        return 0
    if image.status.featureFileHasHumanLabels:
        print 'addLabelsToFeatuers: Image id ' + str(image_id) + ' already has human label attached to the feature file'
        return 1


    ############### EVERYTHING OK, START THE PROCEDURE ###########
    # update status first to ensure concurrency
    image.status.featureFileHasHumanLabels = True
    image.status.save()

    featureFileIn = os.path.join(FEATURES_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".dat")
    featureFileOut = os.path.join(FEATURES_DIR, str(image_id) + "_temp_" + image.get_process_date_short_str() + ".dat")	#temp file
    inputFF = open(featureFileIn, 'r')
    outputFF = open(featureFileOut, 'w')

    points = Point.objects.filter(image=image)
    itt = -1;
    for line in inputFF:
        itt = itt + 1
        label = line.split(None, 1)
        # find the annotation associated with this point, and then write the label.id
        # associated with this annotaiton
        Ann = Annotation.objects.filter(point=points[itt], image=image)
        outputFF.write(str(Ann[0].label.id) + " " + label[1]) #label[1] contains the rest of the row, excluding the first number (the old dummy label)

    outputFF.close()
    inputFF.close()

    copyfile(featureFileOut, featureFileIn)
    os.remove(featureFileOut)
@task()
def trainRobot(source_id):

    # first, see if we should train a new robot
    hasNewImagesToTrainOn = False
    nbrAnnotatedImages = 0
    source = Source.objects.get(pk = source_id)
    allImages = Image.objects.filter(source = source)
    for image in allImages:
        if (image.status.featureFileHasHumanLabels and not image.status.usedInCurrentModel):
            hasNewImagesToTrainOn = True
        if image.status.featureFileHasHumanLabels:
            nbrAnnotatedImages = nbrAnnotatedImages + 1;

    if ( not hasNewImagesToTrainOn or ( nbrAnnotatedImages < 5 ) ) : #TODO, add field to souce object that specify this threshold.
        print 'Source ' + str(source_id) + ' has no new images to train on, aborting'
        return 1

    ################### EVERYTHING OK, START TRAINING NEW MODEL ################

    # create the new Robot object
    if Robot.objects.all().count() == 0:
        version = 1
    else:
        version = Robot.objects.all().order_by('-version')[0].version + 1

    newRobot = Robot(source=source, version = version, time_to_train = 1)
    newRobot.path_to_model = os.path.join(MODEL_DIR, "robot"+str(newRobot.version))
    newRobot.save();
    print 'new robot version:' + str(newRobot.version)
    # update the data base.
    for image in allImages: # mark that these images are used in the current model.
        if image.status.featureFileHasHumanLabels:
            image.status.usedInCurrentModel = True;
            image.status.save()

    # grab the last robot
    previousRobot = source.get_latest_robot()
    if previousRobot == None:
        oldModelPath = '';
    else:
        oldModelPath = previousRobot.path_to_model
        print 'previous robot version:' + str(previousRobot.version)

    # now, loop through the images and create some meta data files that MATLAB needs
    workingDir = newRobot.path_to_model + '.workdir/'
    pointInfoPath = os.path.join(workingDir + 'points')
    fileNamesPath = os.path.join(workingDir, 'fileNames')

    try:
        os.mkdir(workingDir)
    except OSError as e:
        print "Error creating workingDir: {error}".format(error=e.strerror)
        raise

    fItt = 0 #image iterator
    pointFile = open(pointInfoPath, 'w')
    fileNameFile = open(fileNamesPath, 'w')
    for image in allImages:
        if not image.status.featureFileHasHumanLabels:
            continue
        fItt = fItt + 1 #note that we start at 1, MATLAB style
        featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
        fileNameFile.write(featureFile + "\n") # write all file names in a file, so that mablat can find them
        points = Point.objects.filter(image=image)
        pItt = 0
        for point in points:
            pItt = pItt + 1 #note that we start at 1, MATLAB style
            Ann = Annotation.objects.filter(point=point, image=image)
            pointFile.write(str(fItt) + ', ' + str(pItt) + ', ' + str(Ann[0].label.id) + '\n')

    pointFile.close()
    fileNameFile.close()

    # call the matlab function
    task_helpers.coralnet_trainRobot(
        modelPath = newRobot.path_to_model,
        oldModelPath = oldModelPath,
        pointInfoPath = pointInfoPath,
        fileNamesPath = fileNamesPath,
        workDir = workingDir,
        logFile = CV_LOG,
        errorLogfile = TRAIN_ERROR_LOG,
    )

    # clean up
    shutil.rmtree(workingDir)
    if os.path.isfile(TRAIN_ERROR_LOG):
        for image in allImages: # roll back changes.
            if image.status.featureFileHasHumanLabels:
                image.status.usedInCurrentModel = False
                image.status.save()
        print("Sorry error detected in robot training!")
        send_mail('CoralNet Backend Error', 'in trainRobot', 'noreply@coralnet.ucsd.edu', ['oscar.beijbom@gmail.com'])
        newRobot.delete()
    else:
        #if not (previousRobot == None):
            #os.remove(oldModelPath) # remove old model, but keep the meta data files.
        print 'Finished training new robot(' + str(newRobot.version) + ') for source id: ' + str(source_id)

def export_images(source_id, outDir):
    mysource = Source.objects.filter(id = source_id)
    images = Image.objects.filter(source = mysource[0])
    for i in images:
        m = i.metadata
        fname = str(m.value1) + '_' + str(m.value2) + '_' + \
        str(m.value3) + '_' + str(m.value4) + '_' + str(m.value5) + \
        '_' + m.photo_date.isoformat() + '.jpg'
        copyfile(os.path.join(ORIGINALIMAGES_DIR, str(i.original_file)), 
        os.path.join(outDir, fname))


def custom_listdir(path):
    """
    Returns the content of a directory by showing directories first
    and then files by ordering the names alphabetically
    """
    dirs = sorted([d for d in os.listdir(path) if os.path.isdir(path + os.path.sep + d)])
    dirs.extend(sorted([f for f in os.listdir(path) if os.path.isfile(path + os.path.sep + f)]))

    return dirs

def importCPCImage(prefix, dirName, imagesLoc, outputFilename, pickledLabelDictLoc):
    """
    Takes in prefix like Taiwan, directory of labels, directory of images,
    output annotation filename, pickled label mapping file location
    Note: automatically renames the images and require the custom_listdir above
    """
    LabelDict = pickle.load(open(pickledLabelDictLoc, 'r'))
    outputFile = open(outputFilename, 'wb') #opens output file for writing
    errors = []
    image_errors = []
    coords = []
    labels = []
    count = 0
    counts = [] 
    currImage = ""
    imagesDirList = custom_listdir(imagesLoc)
    for dataFilename in custom_listdir(dirName):
        dataFile = open(dirName+dataFilename, 'rb') #opens the file for reading
        imageName = dataFilename.replace('.cpc', '.JPG')
        if not imagesDirList.count(imageName):
            if not image_errors.count(imageName):
                image_errors.append(imageName)
                os.rename(imagesLoc+imageName, "404"+filename)
                continue
        if imageName != currImage:
            count += 1
            currImage = imageName
            newname = prefix + "_" + str(count) + "_2012-02-29_" + imageName
            os.rename(imagesLoc+imageName, imagesLoc+newname)
        if str(dataFile).count(".cpc") == 1:
            for index,words in enumerate(dataFile):
                if index > 5:
                    if words.count(",") == 1:
                        coords.append(str(words))
                    elif words.count(",") == 3:
                        words = words.split(',')
                        labelName = words[1].replace('"', '')
                        name = LabelDict.get(labelName.strip())
                        if name:
                            #add label
                            labels.append(name)
                            counts.append(count)
                            #rename file
                        else:
                            if not errors.count(labelName):
                                errors.append(labelName)
        dataFile.close()

    if not errors:
        for index,coord in enumerate(coords):
            coord = coord.split(',')
            row = str(int(coord[1])/15) #todo automatically scale
            col = str(int(coord[0])/15)
            name = labels[index]
            output = prefix + ";" + str(counts[index]) + ";2012-02-29;" + row.strip() + ";" + col.strip() + ";" + name + "\n"
            outputFile.write(str(output))

    outputFile.close()
    print errors
    print image_errors



def importPhotoGridImage(prefix, dirName, imagesLoc, targetImgDir, outputFilename, pickledLabelDictLoc):
    """
    Takes in prefix like Taiwan, directory of labels, directory of images,
    output annotation filename, pickled label mapping file location,
    and total images to
    pick(put 0 if want all images)
    Note: automatically renames the images and require the custom_listdir above
    """
    LabelDict = pickle.load(open(pickledLabelDictLoc, 'r'))
    outputFile = open(outputFilename, 'wb') #opens output file for writing
    count = 0
    errors = []
    valid_labels = []
    image_errors = []
    imagesDirList = custom_listdir(imagesLoc)
    for dataFilename in custom_listdir(dirName):
        dataFile = open(dirName+dataFilename, 'rb') #opens the file for reading
        reader = csv.reader(dataFile)
        currImage = ""
        for index,words in enumerate(reader):
            #skip table header line
            if index and len(words) > 1:
                #parse line and store needed data
                imageName = str(words[0]).strip() + ".jpg"
                #if image not found, skip it
                if not imagesDirList.count(imageName):
                    if not image_errors.count(imageName):
                        image_errors.append(imageName)
                    continue

                if imageName != currImage:
                    count += 1
                    currImage = imageName
                    newname = prefix + "_" + str(count) + "_" + "2012-02-29_" + imageName
                    shutil.copyfile(imagesLoc+imageName, targetImgDir+newname)
                x_coord = words[9]
                y_coord = words[10]
                labelName = str(words[11]).strip()
                name = LabelDict.get(labelName)
                if name:
                    output = prefix + ";" + str(count) + ";2012-02-29;" + y_coord + ";" + x_coord + ";" + name + "\n"
                    outputFile.write(str(output))
                    if not valid_labels.count(labelName):
                        valid_labels.append(labelName)
                else:
                    output = prefix + ";" + str(count) + ";2012-02-29;" + y_coord + ";" + x_coord + "; error" + labelName + "\n"
                    outputFile.write(str(output))
                    if not errors.count(labelName):
                        errors.append(labelName)

        dataFile.close()
    outputFile.close()
    print sorted(image_errors)

def randomSampleImages(origImagesLoc, dirName, destImagesLoc, total):
    list = []
    imagesDirList = custom_listdir(origImagesLoc)
    for dataFilename in custom_listdir(dirName):
        dataFile = open(dirName+dataFilename, 'rb') #opens the file for reading
        reader = csv.reader(dataFile)
        for index,words in enumerate(reader):
        #skip table header line
            if index and len(words) > 1:
                #parse line and store needed data
                imageName = str(words[0]).strip() + ".jpg"
                #if image not found, skip it
                if imagesDirList.count(imageName) and not list.count(imageName):
                    list.append(imageName)
        dataFile.close()
    list = random.sample(list, total)
    for image in list:
        shutil.move(origImagesLoc+image, destImagesLoc+image)

def renameAllTheImages(prefix, dirName, destDirName, errorArray):
    count = 1
    for filename in custom_listdir(dirName):
        if errorArray.count(filename.replace(".jpg", "")):
            newname = "404"+filename
        else:
            newname = prefix + "_" + str(count) + "_" + filename
        count += 1
        os.rename(dirName+filename, destDirName+newname)

def pickle_labels(inputFileLoc, outputFileLoc):
    dataFile = open(inputFileLoc, 'r') #opens the file for reading
    outputFile = open(outputFileLoc, 'w') #opens output file for writing
    dict = {}
    new_name = ""

    #goes through the input file and outputs a pickled dictionary with each
    #label name being the key to the value of the consensus label set name
    for line in dataFile:
        if line.count(':'):
            words = line.split(':')
            new_name = words[0].strip()
        else:
            words = line.split(',')
            old_name = words[0].strip()
            dict[old_name] = new_name
    pickle.dump(dict, outputFile )
    #can be unpickled by doing dict = pickle.load(outputFile)
    dataFile.close()
    outputFile.close()

def image_status_overview():
    sources = Source.objects.filter()
    for s in sources:
        nAnnotated = 0
        nTotal = 0
        images = Image.objects.filter(source = s)
        for i in images:
            nTotal = nTotal + 1
            if i.status.annotatedByHuman:
                nAnnotated = nAnnotated + 1


        print s.name + ". Num annotated images: " + str(nAnnotated) + ", num total images: " + str(nTotal) + "."

def verifyImage(image):
    try:
        fp = open(ORIGINALIMAGES_DIR + "/" + str(image.original_file), "rb")
        im = PILImage.open(fp) # open from file object
        im.load() # make sure PIL has read the data
        fp.close()
        return True
    except IOError:
        return False

def verifyAllImages():
    errorImages = []
    for image in Image.objects.all():
        if not verifyImage(image):
            errorImages.append(image)
    return errorImages

def verifyAllAndPrint():
    for errorFile in verifyAllImages():
        print errorFile.original_file.name

#
# (cm, labelIds) = get_full_confusion_matrix(source_id) 
# reads the confusion matrix form the vision .json file. 
# it also returns a list of the labelIds corresponding to each row (and column) of the matrix.
#
def get_current_confusion_matrix(source_id):

    source = Source.objects.get(id = source_id)
    latestRobot = source.get_latest_robot()
    if latestRobot == None:
        return None
    (cm, labelIds) = get_confusion_matrix(latestRobot)
    return (cm, labelIds)

def get_confusion_matrix(robot):

    f = open(robot.path_to_model + '.meta.json')
    meta=json.loads(f.read())
    f.close()
        
    # get raw confusion matrix from json file
    if 'cmOpt' in meta['hp']['gridStats']:
        cmraw = meta['hp']['gridStats']['cmOpt']
    else:
        cmraw = meta['hp']['gridStats'][-1]['cmOpt']

    # read labelId's from the metadata
    labelIds = meta['labelMap'] # this lists the labelIds in order.


    # convert to numpy matrix.
    nlabels = len(labelIds)
    cm = zeros( ( nlabels, nlabels ), dtype = int )
    for x in range(len(cmraw)):
        cm[x/nlabels, x%nlabels] = cmraw[x]

    return (cm, labelIds)

#
# (cm_func, fdict, funcIds) = collapse_confusion_matrix(cm, labelIds)
# OUTPUT cm_func. a numpy matrix of functional group confusion matrix
# OUTPUT fdict a dictionary that maps the functional group id to the row (and column) number in the confusion matrix
# OUTPUT funcIds is a list that maps the row (or column) to the functional group id. ("inverse" or the fdict).
#
def collapse_confusion_matrix(cm, labelIds):

    nlabels = len(labelIds)

    # create a labelmap that maps the labels to functional groups. 
    # The thing is that we can't rely on the functional group id field, 
    # since this may not start on one, nor be consecutive.
    funcgroups = LabelGroup.objects.filter().order_by('id') # get all groups
    nfuncgroups = len(funcgroups)
    fdict = {} # this will map group_id to a counter from 0 to (number of functional groups - 1).
    for itt, group in enumerate(funcgroups):
        fdict[group.id] = itt

    # create the 'inverse' of the dictionary, namely a list of the functional groups. Same as the labelIds list but for functional groups. This is not used in this file, but is useful for other situations
    funcIds = []    
    for itt, group in enumerate(funcgroups):
        funcIds.append(int(group.id))

    # create a map from labelid to the functional group consecutive id. Needed for the matrix collapse.
    funcMap = zeros( (nlabels, 1), dtype = int )
    for labelItt in range(nlabels):
        funcMap[labelItt] = fdict[Label.objects.get(id=labelIds[labelItt]).group_id]

    ## collapse columns
    
    # create an intermediate confusion matrix to facilitate the collapse
    cm_int = zeros( ( nlabels, nfuncgroups ), dtype = int )
        
    # do the collapse
    for rowlabelitt in range(nlabels):
        for collabelitt in range(nlabels):
            cm_int[rowlabelitt, funcMap[collabelitt]] += cm[rowlabelitt, collabelitt]
    
    ## collapse rows
    # create the final confusion matrix for functional groups
    cm_func = zeros( ( nfuncgroups, nfuncgroups ), dtype = int )
        
    # do the collapse
    for rowlabelitt in range(nlabels):
        for funclabelitt in range(nfuncgroups):
            cm_func[funcMap[rowlabelitt], funclabelitt] += cm_int[rowlabelitt, funclabelitt]

    return (cm_func, fdict, funcIds)

# (cm, row_sums) = confusion_matrix_normalize(cm)
# OUTPUT cm is row-normalized confusion matrix. Exception. if row sums to zero, it will not be normalized.
# OUTPUT row_sums is the row sums of the input cm
def confusion_matrix_normalize(cm):

    # row-normalize
    row_sums = cm.sum(axis=1)
    cm = float32(cm)

    row_sums_corr = copy.deepcopy(row_sums)
    for i, item in enumerate(row_sums):
        if (item == 0):
            row_sums_corr[i] = 1

    cm_normalized = cm / row_sums_corr[:, newaxis]

    return (cm_normalized, row_sums)


#
# This function takes a cm, and labels, and formats it for display on screen. 
# OUTPUT cm_str is a list of strings.
#
def format_cm_for_display(cm, row_sums, labelobjects, labelIds):

    nlabels = len(labelIds)
    cm_str = ['']
    for thisid in labelIds:
        cm_str.append(str(labelobjects.get(id = thisid).name))
    cm_str.append('Count')
    for row in range(nlabels):
        cm_str.append(str(labelobjects.get(id = labelIds[row]).name)) #the first entry is the name of the funcgroup.
        for col in range(nlabels):
            cm_str.append("%.2f" % cm[row][col])
        cm_str.append("%.0f" % row_sums[row]) # add the count for this row

    return cm_str



#
#
#
def accuracy_from_cm(cm):
    cm = float32(cm)
    acc = sum(np.diagonal(cm))/sum(cm)

    pgt = cm.sum(axis=1) / sum(cm) #probability of the ground truth to predict each class

    pest = cm.sum(axis=0) / sum(cm) #probability of the estimates to predict each class

    pe = sum(pgt * pest) #probaility of randomly guessing the same thing!

    if (pe == 1):
        cok = 1
    else:
        cok = (acc - pe) / (1 - pe) #cohens kappa!

    return (acc, cok)


