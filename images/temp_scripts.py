"""
This file contains TEMP scripts that are not part of the main production server. But that reads/exports/manipulates things on a one-to-one basis.
"""
import logging
from images.models import Point, Image, Source, Robot
from annotations.models import Annotation
import os
from django.conf import settings
from datetime import datetime
from images.tasks import *
from images.scripts_helper import RobotStats
from django.core.exceptions import ValidationError, MultipleObjectsReturned
join_processing_root = lambda *p: os.path.join(settings.PROCESSING_ROOT, *p)
PREPROCESS_DIR = join_processing_root("images/preprocess/")
FEATURES_DIR = join_processing_root("images/features/")

logging.basicConfig(filename=os.path.join(settings.PROCESSING_ROOT, 'logs/tasks.log'), level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

"""
This script process a source in serial. Useful for debugging the vision backend
"""

def process_source_complete_debug(source_id, force_retrain = False):
  
    source = Source.objects.get(pk = source_id)
    print "==== Start processing source ====", source.id, source.name

    if force_retrain: #make sure the robot will re-train
        for image in Image.objects.filter(source = source):
            image.status.usedInCurrentModel = False
            image.status.save()
    
    for image in source.get_all_images():
        add_labels_to_features(image.id)
    train_robot(source.id)
    
    for image in source.get_all_images():
        preprocess_image(image.id)
        make_features(image.id)
        classify_image(image.id)
    
    print "==== Done processing source ===="



"""
This script process all "small" sources.

"""
def process_small_sources(th = 1000):
    for source in Source.objects.filter(enable_robot_classifier=True).order_by('id'):
        if len(source.get_all_images()) < th:
            logging.info('PSS Adding labels for ' + source.name + '[' + str(source.id) + '].')
            for image in source.get_all_images():
                image.status.featureFileHasHumanLabels = False
                image.status.save()
                add_labels_to_features(image.id)
            logging.info('PSS Done adding labels. Training robot for ' + source.name + '[' +str(source.id) + '].')
            train_robot(source.id)
            logging.info('PSS Done traing robot. Classifying all images in ' + source.name + '[' + str(source.id) + '].')
            for image in source.get_all_images():
                preprocess_image(image.id)
                make_features(image.id)
                classify_image(image.id)
            logging.info('PSS Done classifying all images in ' + source.name + '[' + str(source.id) + '].')
    




"""
This is a temp clssify wrapper since the NOAA CREP source is taking up so much power.
"""
def classify_wrapper_skip(skipid = 295):
    for source in Source.objects.filter(enable_robot_classifier=True).order_by('id'):
        if source.id == skipid:
            print "!!!!!!!!!!Skipping NOAA CREP!!!!!!!!!!!!!"
            continue
        print "Processing: " + source.name
        for image in source.get_all_images():
            preprocess_image(image.id)
            make_features(image.id)
            classify_image(image.id)
        print "Done processing: " + source.name


def write_workingdir(source_id, workingDir):

    source = Source.objects.get(pk = source_id)
    allImages = Image.objects.filter(source = source)
    
    # create the new Robot object
    if Robot.objects.all().count() == 0:
        version = 1
    else:
        version = Robot.objects.all().order_by('-version')[0].version + 1

    newRobot = Robot(source = source, version = version, time_to_train = 1)
    newRobot.path_to_model = os.path.join(MODEL_DIR, "robot" + str(newRobot.version))
    
    # now, loop through the images and create some meta data files that MATLAB needs
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
        if not image.status.featureFileHasHumanLabels:
            continue
        fItt = fItt + 1 #note that we start at 1, MATLAB style
        featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
        fileNameFile.write(featureFile + "\n") # write all file names in a file, so that MATLAB can find them
        points = Point.objects.filter(image=image)
        pItt = 0
        print image.id
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


def read_gtlabels(source_id, maxlength = 1):

    source = Source.objects.get(pk = source_id)
    allImages = Image.objects.filter(source = source)[:maxlength]
    
    fItt = 0 #image iterator
    gtlabels = []
    for image in allImages:
        if image.status.featureFileHasHumanLabels:
        	featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
        	with open(featureFile) as f:
    			lines = f.readlines()
    			for line in lines:
    				parts = line.split()
    				gtlabels.append(int(parts[0]))
    return gtlabels

        	
