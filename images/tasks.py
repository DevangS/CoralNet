import time, os, copy, csv, pickle, shutil, operator, json, reversion, math, logging
import numpy as np
from shutil import copyfile
from datetime import datetime
from random import random
from celery.task import task
from django.conf import settings
from django.core.mail import mail_admins
from django.shortcuts import render_to_response, get_object_or_404
from accounts.utils import get_robot_user
from accounts.utils import is_robot_user
from annotations.models import Label, Annotation, LabelGroup
from images import task_helpers, task_utils
from images.models import Point, Image, Source, Robot
from images.utils import source_robot_status
from numpy import array, zeros, sum, float32, newaxis
from django.db import transaction
# Revision objects will not be saved during Celery tasks unless
# the Celery worker hooks up Reversion's signal handlers.
# To do this, import admin modules so that
# the admin registration statements are run.
from django.contrib import admin
try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

logging.basicConfig(filename=os.path.join(settings.PROCESSING_ROOT, 'logs/tasks.log'), level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
admin.autodiscover()

PREPROCESS_ERROR_LOG = os.path.join(settings.PROCESSING_ROOT, "logs/preprocess_error.txt")
FEATURE_ERROR_LOG = os.path.join(settings.PROCESSING_ROOT, "logs/features_error.txt")
CLASSIFY_ERROR_LOG = os.path.join(settings.PROCESSING_ROOT, "logs/classify_error.txt")
TRAIN_ERROR_LOG = os.path.join(settings.PROCESSING_ROOT, "logs/train_error.txt")
CV_LOG = os.path.join(settings.PROCESSING_ROOT, "logs/cvlog.txt")

ALLEVIATE_IMAGE_DIR = os.path.join(settings.MEDIA_ROOT, "vision_backend/alleviate_plots")
ALLEVIATE_IMAGE_URL = os.path.join(settings.MEDIA_URL, "vision_backend/alleviate_plots")
PREPROCESS_DIR = os.path.join(settings.PROCESSING_ROOT, "images/preprocess/")
FEATURES_DIR = os.path.join(settings.PROCESSING_ROOT, "images/features/")
CLASSIFY_DIR = os.path.join(settings.PROCESSING_ROOT, "images/classify/")
MODEL_DIR = os.path.join(settings.PROCESSING_ROOT, "images/models/")
PREPROCESS_PARAM_FILE = os.path.join(settings.PROCESSING_ROOT, "images/preprocess/preProcessParameters.mat")

TARGET_PIXEL_CM_RATIO = 17.2



#Tasks that get processed by Celery
#Possible future problems include that each task relies on it being the same day to continue processing an image,
#a solution would be to store the date that you preprocess the iamge and then update it if you run a newer version of
#the algorithm against it

@task()
def dummy_task():
    print("This is a dummy task console output")
    return 1

@task()
def dummy_task_sleep(s):
    print("This is a dummy task that can sleep")
    time.sleep(s)


# This is the main tasks for classification. This does not use the task manager, but does everything in serial. Nice and slow.
def classify_wrapper():
    keyfilepath = os.path.join(settings.PROCESSING_ROOT, "logs/classify_flag")

    if os.path.exists(keyfilepath):
        return 1
    open(keyfilepath, 'w')
    logging.info("==== Start classifying all images ====")
    for source in Source.objects.filter(enable_robot_classifier=True).order_by('id'):
        for image in source.get_all_images():
            preprocess_image(image.id)
            make_features(image.id)
            classify_image(image.id)
    logging.info("==== Done classifying all images ====")
    os.remove(keyfilepath)

# This is the main tasks for learning. This does not use the task manager, but does everything in serial. Nice and slow.
def train_wrapper():
    keyfilepath = os.path.join(settings.PROCESSING_ROOT, "logs/learning_flag")

    if os.path.exists(keyfilepath):
        return 1
    open(keyfilepath, 'w')
    logging.info("==== Start training new batch of robots ====")
    for source in Source.objects.filter(enable_robot_classifier=True).order_by('id'):
        for image in source.get_all_images():
            add_labels_to_features(image.id)
        train_robot(source.id)
    logging.info("==== Done training robots ====")
    os.remove(keyfilepath)


# This is the new master function
def nrs_robot_wrapper():

    # check if thread is already running
    keyfilepath = os.path.join(settings.PROCESSING_ROOT, "logs/nrs_running_flag")
    if os.path.exists(keyfilepath):
        return 1
    open(keyfilepath, 'w')

    # make laundry list for the sources
    laundry_list = []
    for source in Source.objects.filter():
        laundry_list.append(source_robot_status(source.id))
    laundry_list = [l for l in laundry_list if l['need_attention']]
    logging.info("==== NRS MAIN WRAPPER start processing {} sources ====".format(len(laundry_list)))
    pickle.dump(laundry_list, open(os.path.join(settings.PROCESSING_ROOT, "logs/laundry_list.pkl"), "wb"))


    for item in laundry_list:
        # check break flag:
        if os.path.exists(os.path.join(settings.PROCESSING_ROOT, "logs/break_flag")):
            logging.info("==== NRS Aborting due to break flag raised ====")
            return 1

        if item['need_robot']:
            nrs_train_wrapper(item['id'])
        if item['nbr_unclassified_images'] > 0:
            nrs_classify_wrapper(item['id'])
    logging.info("==== NRS MAIN WRAPPER done processing {} sources ====".format(len(laundry_list)))

    os.remove(keyfilepath)
        


def nrs_train_wrapper(source_id):

    # we begin by extracting features for all verified images
    source = Source.objects.get(id = source_id)
    imglist = Image.objects.filter(source=source, status__annotatedByHuman=True, status__featuresExtracted=False)
    logging.info("==== NRS Making features for {nbr} images in preparation for robot training of source{sid}: {sname} ====".format(nbr = len(imglist), sid = source.id, sname = source.name))
    for img in imglist:
        preprocess_image(img.id)
        make_features(img.id)

    imglist = Image.objects.filter(source=source, status__annotatedByHuman=True, status__featuresExtracted=True)
    for img in imglist:
        add_labels_to_features(img.id)

    # then we train a new robot
    train_robot(source_id)

    # now we re-classify all images that were classified by an older version of the robot.
    imglist = Image.objects.filter(source=source, status__annotatedByRobot=True)
    logging.info("==== NRS Re-classifier {nbr} images after robot training of source{sid}: {sname}".format(nbr = len(imglist), sid = source.id, sname = source.name))
    for img in imglist:
        classify_image(img.id)
    logging.info("==== NRS Done train wrapper for source{sid}: {sname}".format(sid = source.id, sname = source.name))

def nrs_classify_wrapper(source_id):

    source = Source.objects.get(id = source_id)
    imglist = Image.objects.filter(source = source, status__annotatedByRobot = False, status__annotatedByHuman = False)[:settings.NBR_IMAGES_PER_LOOP]
    logging.info("==== NRS Extracting features and classifying {nbr} images from source{sid}: {sname} ====".format(nbr = len(imglist), sid = source.id, sname = source.name))
    for img in imglist:
        preprocess_image(img.id)
        make_features(img.id)
        classify_image(img.id)
    logging.info("==== NRS Done extracting features and classifying {nbr} images from source{sid}: {sname} ====".format(nbr = len(imglist), sid = source.id, sname = source.name))



@task()
@transaction.commit_on_success()
def preprocess_image(image_id):
    image = Image.objects.get(pk=image_id)

    if image.status.preprocessed:
        return 1

    if not (image.metadata.height_in_cm or image.source.image_height_in_cm): #missing critical info. return.
        return 1

    ####### EVERYTHING OK: START THE IMAGE PREPROCESSING ##########
    image.status.preprocessed = True # Update database
    image.status.save()
    logging.info('Pre-processing image{id} from source{sid}: {sname}'.format(id = image_id, sid = image.source_id, sname = image.source.name))

    thisPixelCmRatio = image.original_height / float(image.height_cm())
    subSampleRate = thisPixelCmRatio / TARGET_PIXEL_CM_RATIO
    if(subSampleRate < 1):
        logging.info('Changed ssrate from {ssold} to 1 for image{id}'.format(ssold = subSampleRate, id = image_id))
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
        imageFile=os.path.join(settings.MEDIA_ROOT, str(image.original_file)),
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
        logging.info('ERROR pre-processing [image {id}] from [source{sid}: {sname}]'.format(id = image_id, sid = image.source_id, sname = image.source.name))
        mail_admins('CoralNet Backend Error', 'in PreprocessImages')
        return 0
    
    return 1

@task()
def make_features(image_id):
    image = Image.objects.get(pk=image_id)

    # Do some checks
    if os.path.isfile(PREPROCESS_ERROR_LOG) or not image.status.preprocessed or not image.status.hasRandomPoints or image.status.featuresExtracted:
        return 1
    
    ####### EVERYTHING OK: START THE FEATURE EXTRACTION ##########
    logging.info('Extracting features image{id} from source{sid}: {sname}'.format(id = image_id, sid = image.source_id, sname = image.source.name))
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
        logging.info('ERROR extracting features image{id} from source{sid}: {sname}'.format(id = image_id, sid = image.source_id, sname = image.source.name))
        mail_admins('CoralNet Backend Error', 'in MakeFeatures')
        return 0

    return 1
    
@task()
@transaction.commit_on_success()
@reversion.create_revision()
def classify_image(image_id):
    image = Image.objects.get(pk=image_id)

    # if annotated by Human, or if the previous step is not complete
    if image.status.annotatedByHuman or not image.status.featuresExtracted:
        return 1

    # Get last robot for this source
    latestRobot = image.source.get_latest_robot()

    if latestRobot == None:
        return

    # Check if this image has been previously annotated by a robot.
    if (image.status.annotatedByRobot):
        # now, compare this version number to the latest_robot_annotator field for image.
        if (not (latestRobot.version > image.latest_robot_annotator.version)):
            return 1

    ####### EVERYTHING OK: START THE CLASSIFICATION ##########
    logging.info('Classifying image{id} from source{sid}: {sname}'.format(id = image_id, sid = image.source_id, sname = image.source.name))
    
    #builds args for matlab script
    featureFile = os.path.join(FEATURES_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".dat")
    labelFile = os.path.join(CLASSIFY_DIR, str(image_id) + "_" + image.get_process_date_short_str() + ".txt")

    task_helpers.coralnet_classify(
        featureFile=featureFile,
        modelFile=latestRobot.path_to_model,
        labelFile=labelFile,
        logFile=CV_LOG,
        errorLogfile=CLASSIFY_ERROR_LOG,
    )

    if os.path.isfile(CLASSIFY_ERROR_LOG):
        logging.info('ERROR classifying image{id} from source{sid}: {sname}'.format(id = image_id, sid = image.source_id, sname = image.source.name))
        mail_admins('CoralNet Backend Error', 'in Classify')
        return 0
    else:
        #update image status
        image.status.annotatedByRobot = True
        image.status.save()
        image.latest_robot_annotator = latestRobot
        image.save()

    ####### IMPORT CLASSIFICATION RESULT TO DATABASE ##########
    user = get_robot_user()

    # Get the label probabilities that we just generated
    label_probabilities = task_utils.get_label_probabilities_for_image(image_id)

    if len(label_probabilities) == 0:
        mail_admins('Classify error', 'Classification output for image{id} from source{sid}: {sname} was empty.'.format(id = image_id, sid = image.source_id, sname = image.source.name))

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

    logging.info('Classified {npts} points in image{id} from source{sid}: {sname}'.format(npts = len(label_probabilities), id = image_id, sid = image.source_id, sname = image.source.name))
    return 1


# This task modifies the feature file so that is contains the correct labels, as provided by the human operator.
@task()
def add_labels_to_features(image_id):

    image = Image.objects.get(pk=image_id)
    if not image.status.annotatedByHuman or not image.status.featuresExtracted:
        return 1

    ############### EVERYTHING OK, START THE PROCEDURE ###########
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
    return 1

@task()
def train_robot(source_id):

    source = Source.objects.get(id = source_id)
    if not source.need_new_robot():
        return 1
    
    allImages = Image.objects.filter(source = source, status__annotatedByHuman = True, status__featuresExtracted = True)

    ################### EVERYTHING OK, START TRAINING NEW MODEL ################

    # create the new Robot object
    if Robot.objects.all().count() == 0:
        version = 1
    else:
        version = Robot.objects.all().order_by('-version')[0].version + 1

    newRobot = Robot(source = source, version = version, time_to_train = 1)
    newRobot.path_to_model = os.path.join(MODEL_DIR, "robot" + str(newRobot.version))
    newRobot.save();
    
    # update the data base.
    for image in allImages: # mark that these images are used in the current model.
        if not image.status.usedInCurrentModel:
            image.status.usedInCurrentModel = True;
            image.status.save()

    # grab the last robot
    previousRobot = source.get_latest_robot()
    if previousRobot == None:
        oldModelPath = '';
        logging.info('Training first robot{id} for source{sid}: {sname}'.format(id = newRobot.version, sid = image.source_id, sname = image.source.name))
    else:
        oldModelPath = previousRobot.path_to_model
        logging.info('Training robot{id} for source{sid}: {sname}. Previous was robot{pid}'.format(id = newRobot.version, sid = image.source_id, sname = image.source.name, pid = previousRobot.version))

    # now, loop through the images and create some meta data files that MATLAB needs
    workingDir = newRobot.path_to_model + '.workdir/'
    pointInfoPath = os.path.join(workingDir + 'points')
    fileNamesPath = os.path.join(workingDir + 'fileNames')

    try:
        os.mkdir(workingDir)
    except OSError as e:
        logging.info("Error creating workingDir: {error}".format(error=e.strerror))
        raise

    fItt = 0 #image iterator
    pointFile = open(pointInfoPath, 'w')
    fileNameFile = open(fileNamesPath, 'w')
    for image in allImages:
        fItt = fItt + 1 #note that we start at 1, MATLAB style
        featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
        fileNameFile.write(featureFile + "\n") # write all file names in a file, so that MATLAB can find them
        points = Point.objects.filter(image=image)
        pItt = 0
        for point in points:
            pItt = pItt + 1 #note that we start at 1, MATLAB style
            Ann = Annotation.objects.filter(point=point, image=image)
            pointFile.write(str(fItt) + ', ' + str(pItt) + ', ' + str(Ann[0].label.id) + '\n')

    pointFile.close()
    fileNameFile.close()

    # write the label map function
    labelMapPath = os.path.join(workingDir + 'labelmap')
    mapFile = open(labelMapPath, 'w')
    for labelgroup in LabelGroup.objects.filter():
        mapFile.write(str(labelgroup.name) + ',' + str(labelgroup.id) + '\n')
    mapFile.write('===\n')
    for label in Label.objects.filter():
        mapFile.write(str(label.id) + ',' + str(label.group_id) + '\n')    
    mapFile.close()

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
  
    if os.path.isfile(TRAIN_ERROR_LOG):
        for image in allImages: # roll back changes.
            image.status.usedInCurrentModel = False
            image.status.save()
        logging.info('ERROR training robot{id} for source{sid}: {sname}'.format(id = newRobot.version, sid = image.source_id, sname = image.source.name))
        mail_admins('CoralNet Backend Error', 'in trainRobot')
        os.rename(TRAIN_ERROR_LOG, TRAIN_ERROR_LOG + '.' + str(source_id)) # change the name so it won't interfere with other sources.
        # newRobot.delete() Don't delete the model. It won't bother us anyays since it lacks the needed metadata.
        return 0
    else:
        copyfile(newRobot.path_to_model + '.meta_all.png', os.path.join(ALLEVIATE_IMAGE_DIR, str(newRobot.version) + '.png')) #copy to the media folder where it can be viewed
        if not (previousRobot == None):
            os.remove(oldModelPath) # remove old model, but keep the meta data files.
        shutil.rmtree(workingDir) # only remove temp files if everything worked. Else keep it for debugging purposes.
        logging.info('Done training robot{id} for source{sid}: {sname}'.format(id = newRobot.version, sid = image.source_id, sname = image.source.name))
        return 1


def custom_listdir(path):
    """
    Returns the content of a directory by showing directories first
    and then files by ordering the names alphabetically
    """
    dirs = sorted([d for d in os.listdir(path) if os.path.isdir(path + os.path.sep + d)])
    dirs.extend(sorted([f for f in os.listdir(path) if os.path.isfile(path + os.path.sep + f)]))

    return dirs

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

"""
(cm, labelIds) = get_full_confusion_matrix(source_id) 
reads the confusion matrix form the vision .json file. 
it also returns a list of the labelIds corresponding to each row (and column) of the matrix.
"""
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
# This function calculates accuracy and cohens kappa from a confusion matrix
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


#
# Reads the alleviate stats
#
def get_alleviate_meta(robot):
    alleviate_meta_file  = robot.path_to_model + '.meta_all.json'
    if not os.path.exists(alleviate_meta_file):
        ok = 0
    else:
        f = open(alleviate_meta_file)
        meta=json.loads(f.read())
        f.close()
        ok = meta['ok']

    if (ok == 1):
        alleviate_meta = dict(        
            suggestion = meta['keepRatio'],
            score_translate = meta['thout'],
            plot_path = os.path.join(ALLEVIATE_IMAGE_DIR, str(robot.version) + '.png'),
            plot_url = os.path.join(ALLEVIATE_IMAGE_URL, str(robot.version) + '.png'),
            ok = True,
        )
    else:
        alleviate_meta = dict(        
            ok = False,
        )
    return (alleviate_meta)


