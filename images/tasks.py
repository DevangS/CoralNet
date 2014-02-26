import time
import csv
from shutil import copyfile
from datetime import datetime
import pickle
from random import random
import shutil
from celery.task import task
import os
from django.conf import settings

try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

from django.db import transaction
import reversion
from accounts.utils import get_robot_user
from accounts.utils import is_robot_user
from annotations.models import Label, Annotation
from images import task_helpers
from images.models import Point, Image, Source, Robot

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

@task()
# this function is depleated. Not in use anymore.
def schedulerInfLoop():
    time.sleep(10) # sleep 10 secs to allow the scheduler to start
    while True:
        for source in Source.objects.filter(enable_robot_classifier=True): # grab all sources, on at the time
            processSourceCompleate(source.id)
        time.sleep(settings.SLEEP_TIME_BETWEEN_IMAGE_PROCESSING) #sleep

def processAllSources():
	keyfilepath = join_processing_root("images/robot_running_flag")
	if os.path.exists(keyfilepath):
		return 1
	open(keyfilepath, 'w')
	for source in Source.objects.filter(enable_robot_classifier=True):
			processSourceCompleate(source.id)
	os.remove(keyfilepath)


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

@task()
def prepareImage(image_id):
    PreprocessImages(image_id)
    MakeFeatures(image_id)
    addLabelsToFeatures(image_id)

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
    #everything went okay with matlab
    else:
        print 'Finished pre-processing image id {id}'.format(id = image_id)

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
    #update image status
    image.status.annotatedByRobot = True
    image.status.save()
    image.latest_robot_annotator = latestRobot
    image.save()

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

    #get algorithm user object
    user = get_robot_user()

    #open the labelFile and rowColFile to process labels
    rowColFile = os.path.join(FEATURES_DIR, str(image_id) + "_rowCol.txt")
    label_file = open(labelFile, 'r')
    row_file = open(rowColFile, 'r')

    for line in row_file:
        row, column = line.split(',')

        #gets the label object based on the label id the algorithm specified
        label_id = label_file.readline()
        label_id.replace('\n', '')
        label = Label.objects.get(id=label_id)

        #gets the point object(s) that have that row and column.
        #if there's more than one such point, add annotations to all of
        #these points.
        points_at_this_row_col = Point.objects.filter(image=image, row=row, column=column)

        for point in points_at_this_row_col:

            existing_annotations = Annotation.objects.filter(point=point, image=image)

            if (len(existing_annotations) > 0):
                # there's an existing Annotation object for this point.
                # (assumption: this means there's only one Annotation object
                # for this point, never multiple.)
                existing_annotation = existing_annotations[0]

                # if this is an imported or human, we don't want to overwrite it, so continue
                if not is_robot_user(existing_annotation.user):
                    continue

                # we have an annotation that was annotated by a previous
                # robot version.  if the current robot's label is different
                # from the previous robot's label, update the annotation.
                if existing_annotation.label.id != label.id:
                    existing_annotation.label = label
                    existing_annotation.robot_version = latestRobot
                    existing_annotation.save()

            else:
                # there's no existing Annotation object for this point.
                # create a new annotation object and save it.
                new_annotation = Annotation(image=image, label=label, point=point, user=user, robot_version=latestRobot, source=image.source)
                new_annotation.save()

    print 'Finished classification of image id {id}'.format(id = image_id)

    label_file.close()
    row_file.close()


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
    # rmtree(workingDir)
    if os.path.isfile(TRAIN_ERROR_LOG):
        for image in allImages: # roll back changes.
            if image.status.featureFileHasHumanLabels:
                image.status.usedInCurrentModel = False
                image.status.save()
        print("Sorry error detected in robot training!")
        newRobot.delete()
    else:
        #if not (previousRobot == None):
            #os.remove(oldModelPath) # remove old model, but keep the meta data files.
        print 'Finished training new robot(' + str(newRobot.version) + ') for source id: ' + str(source_id)


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
