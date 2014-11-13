from images.models import Point, Image, Source, Robot
import os
from django.conf import settings

join_processing_root = lambda *p: os.path.join(settings.PROCESSING_ROOT, *p)
PREPROCESS_DIR = join_processing_root("images/preprocess/")
FEATURES_DIR = join_processing_root("images/features/")

"""
This is a script to remove all inactive robot models. 
The current semantic is that the robot model file is 
removed once a new is trained. Previously, however
this was not the case, and we kept them all on disk. 
This was filling up the drive, since models for large
sources can be quite large (hundreds of MB). So we 
changed the semantics, and created this script to clean
up. Note that meatdata, and database entries are kept.

"""
def removeOldRobots():
    for mysource in Source.objects.filter(enable_robot_classifier=True):
        print "Processing source id:" + str(mysource.id)
        latest_robot = mysource.get_latest_robot()
        valid_robots = mysource.get_valid_robots()
        for this_robot in valid_robots:
            if not latest_robot == this_robot:
                try:
                    os.remove(this_robot.path_to_model)
                    print "removed " + this_robot.path_to_model
                except:
                    print this_robot.path_to_model + "is already removed"
    
"""
This script was created after a week of MATLAB not starting. This created a bunch of images with the wrong status. For example, the database updated status.featuresExtracted = true, and then called MATLAB. MATLAB then didn't start (and didn't tell the system), so the status was never changed back. The remedy is to go through all images and check that the MATLAB output files are on the disk.
"""
    
def resetImageStatus():
    source_querry = Source.objects.filter()
    for this_source in source_querry:
        imgquerry = Image.objects.filter(source = this_source)
        img_counter = 0
        for image in imgquerry:
            if image.process_date is None:
                img_counter += 1
                continue
            preprocessedImageFile = os.path.join(PREPROCESS_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".mat")
            featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
            if not(os.path.isfile(preprocessedImageFile)) or not(os.path.isfile(featureFile)):
                # i.after_height_cm_change() # this resets the image
                img_counter += 1
        print this_source.name + "has " + str(img_counter) + " images with bad status"




