import csv
from datetime import datetime
import pickle
from random import random
import shutil
from subprocess import call
from celery.decorators import task
import os
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from accounts.utils import get_robot_user
from annotations.models import Label, Annotation
from images.models import Point, Image, Source, Robot

PREPROCESS_ERROR_LOG = "/cnhome/errorlogs/preprocess_error.txt"
FEATURE_ERROR_LOG = "/cnhome/errorlogs/features_error.txt"
CLASSIFY_ERROR_LOG = "/cnhome/errorlogs/classify_error.txt"

ORIGINALIMAGES_DIR = "/cnhome/media/"
PREPROCESS_DIR = "/cnhome/images/preprocess/"
FEATURES_DIR = "/cnhome/images/features/"
CLASSIFY_DIR = "/cnhome/images/classify/"
MODEL_DIR = "/cnhome/images/models/"

PREPROCESS_PARAM_FILE = "/cnhome/images/preprocess/preProcessParameters.mat"
FEATURE_PARAM_FILE = "/cnhome/images/features/featureExtractionParameters.mat"


#Tasks that get processed by Celery
#Possible future problems include that each task relies on it being the same day to continue processing an image,
#a solution would be to store the date that you preprocess the iamge and then update it if you run a newer version of
#the algorithm against it

@task()
def dummyTask():
    print("This is a dummy task console output")
    return 1

@task()
def PreprocessImages(image):

    # check if already preprocessed
    if image.status.preprocessed:
	print 'Image {} is already preprocessed'.format(image.id)
	return 1

    # TODO: check if pixel-cm ratio field is set. If not return.

    print 'Start pre-processing image id {}'.format(image.id)

    # set the process_date to todays date
    image.process_date = datetime.now()
    image.save()

    #matlab will output image.id_YearMonthDay.mat file
    preprocessedImageFile = PREPROCESS_DIR + str(image.id) + "_" + str(image.process_date.year) + str(image.process_date.month) + str(image.process_date.day) + ".mat"

    matlabCallString = '/usr/bin/matlab/bin/matlab -nosplash -nodesktop -nojvm -r "cd /home/beijbom/e/Code/MATLAB; startup; warning off; coralnet_preprocessImage(\'' + ORIGINALIMAGES_DIR + str(image.original_file) + '\', \'' + preprocessedImageFile + '\', \'' + PREPROCESS_PARAM_FILE + '\', \'' + PREPROCESS_ERROR_LOG + '\'); exit;"'

    #call coralnet_preprocessImage(matlab script) to process a single image
    os.system(matlabCallString);

    #error occurred in matlab
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing this image, halting!")
    #everything went okay with matlab
    else:
        image.status.preprocessed = True
        image.status.save()
        print 'Finished pre-processing image id {}'.format(image.id)

@task()
def MakeFeatures(image):
    
    #if error had occurred in preprocess, don't let them go further
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing, halting feature extraction!")
        return
    if not image.status.preprocessed:
        print 'Image id {} is not preprocessed. Can not make features'.format(image.id)
        return
    if not image.status.hasRandomPoints:
        print 'Image id {} doesnt have random points. Can not make features'.format(image.id)
        return
    if image.status.featuresExtracted:
        print 'Features already extracted for image id {}'.format(image.id)
        return
 
    print 'Start feature extraction for  image id {}'.format(image.id)

    #builds args for matlab script
    preprocessedImageFile = PREPROCESS_DIR + str(image.id) + "_" + str(image.process_date.year) + str(image.process_date.month) + str(image.process_date.day) + ".mat"
    featureFile = FEATURES_DIR + str(image.id) + "_" + str(image.process_date.year) + str(image.process_date.month) + str(image.process_date.day) + ".dat"
    #creates rowColFile
    rowColFile = FEATURES_DIR + str(image.id) + "_rowCol.txt"
    file = open(rowColFile, 'w')
    points = Point.objects.filter(image=image)
    for point in points:
        #points get stored in the file in this format, one of these per line: row,column\n
        file.write(str(point.row) + "," + str(point.column) + "\n")
    file.close()
        
    matlabCallString = '/usr/bin/matlab/bin/matlab -nosplash -nodesktop -nojvm -r "cd /home/beijbom/e/Code/MATLAB; startup; warning off; coralnet_makeFeatures(\'' + preprocessedImageFile + '\', \'' + featureFile + '\', \'' + rowColFile + '\', \'' + FEATURE_PARAM_FILE+ '\', \'' + FEATURE_ERROR_LOG + '\'); exit;"'
    #call matlab script coralnet_makeFeatures
    os.system(matlabCallString);

    if os.path.isfile(FEATURE_ERROR_LOG):
        print("Sorry error detected in feature extraction!")
    else:
        image.status.featuresExtracted = True;
        image.status.save()
        print 'Finished feature extraction for image id {}'.format(image.id)
        
@task()
def Classify(image):

    #if error occurred in feature extraction, don't let them go further
    if os.path.isfile(FEATURE_ERROR_LOG):
        print("Sorry error detected in feature extraction, halting classification!")
        return

    # make sure that the previous step is complete
    if not image.status.featuresExtracted:
        print 'Features not extracted for image id {}, can not proceed'.format(image.id)
        return

    # Get all robots for this source
    allRobots = Robot.objects.filter(source = image.source)
 
    # if empty, return
    if len(allRobots) == 0:
        print 'No robots exist for the source, {}, of image id {}. Aborting.'.format(image.source, image.id)
        return
    
    # find the most recent robot
    latestRobot = allRobots[0]
    for thisRobot in allRobots:
        if thisRobot.version > latestRobot.version:
            latestRobot = thisRobot

    # Check if this image has been previously annotated by a robot.
    if (image.status.annotatedByRobot):
        # now, compare this version number to the latest_robot_annotator field for image.
        if (not (latestRobot.version > image.latest_robot_annotator.version)):
            print 'Image {} is already annotated by the latest robot version, {}, for source, {}'.format(image.id,  latestRobot.version, image.source)
            return
    
    print 'Start classify image id {}'.format(image.id)
    #builds args for matlab script
    featureFile = FEATURES_DIR + str(image.id) + "_" + str(image.process_date.year) + str(image.process_date.month) + str(image.process_date.day) + ".dat"
	#get the source id for this file
    labelFile = CLASSIFY_DIR + str(image.id) + "_" + str(image.process_date.year) + str(image.process_date.month) + str(image.process_date.day) + ".txt"
        
    matlabCallString = '/usr/bin/matlab/bin/matlab -nosplash -nodesktop -nojvm -r "cd /home/beijbom/e/Code/MATLAB; startup; warning off; coralnet_classify(\'' + featureFile + '\', \'' + latestRobot.path_to_model + '\', \'' + labelFile + '\', \'' + CLASSIFY_ERROR_LOG + '\'); exit;"'

    #call matlab script coralnet_classify
    os.system(matlabCallString)
    if os.path.isfile(CLASSIFY_ERROR_LOG):
        print("Sorry error detected in classification!")
    else:
        #get algorithm user object
        user = get_robot_user()

        #open the labelFile and rowColFile to process labels
        rowColFile = FEATURES_DIR + str(image.id) + "_rowCol.txt"
        label_file = open(labelFile, 'r')
        row_file = open(rowColFile, 'r')

        for line in row_file: #words[0] is row, words[1] is column 
            words = line.split(',') 
            #gets the point object for the image that has that row and column
            point = Point.objects.get(image=image, row=words[0], column=words[1])

            #gets the label object based on the label id the algorithm specified
            label_id = label_file.readline()
            label_id.replace('\n', '')
            label = Label.objects.filter(id=label_id)

            #create the annotation object and save it
            annotation = Annotation(image=image, label=label[0], point=point, user=user, source=image.source)
            annotation.save()

        #update image status
        image.status.annotatedByRobot = True
        image.status.save()
        image.latest_robot_annotator = latestRobot
        image.save()
        print 'Finished classification of image id {}'.format(image.id)

        label_file.close()
        row_file.close()


@task()
def processImageAll(image):
    PreprocessImages(image)
    MakeFeatures(image)
    Classify(image)

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
            newname = prefix + "_" + str(count) + "_" + imageName
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
                            #rename file
                        else:
                            if not errors.count(labelName):
                                errors.append(labelName)
        dataFile.close()

    if not errors:
        for index,coord in enumerate(coords):
            coord = coord.split(',')
            row = str(int(coord[0])/15) #todo automatically scale
            col = str(int(coord[1])/15)
            name = labels[index]
            output = prefix + ";" + str(index) + ";2012-02-29;" + row.strip() + ";" + col.strip() + ";" + name + "\n"
            outputFile.write(str(output))

    outputFile.close()
    print errors
    print image_errors

def importPhotoGridImage(prefix, dirName, imagesLoc, outputFilename, pickledLabelDictLoc):
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
                    newname = prefix + "_" + str(count) + "_" + imageName
                    os.rename(imagesLoc+imageName, imagesLoc+newname)
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
    print sorted(errors)
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