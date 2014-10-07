from images.models import Point, Image, Source, Robot
import os




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
    
    
