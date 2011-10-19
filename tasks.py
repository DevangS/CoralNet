from datetime import datetime
from subprocess import call
from celery.decorators import task
import os
from django.contrib.auth.models import User
from accounts.utils import get_robot_user
from annotations.models import Label, Annotation
from images.models import Point, Image, Source

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
    print("dummy task output")

@task()
def PreprocessImages(image):
    print 'Start pre-processing image id {}'.format(image.id)

    #gets current date to append to file name
    now = datetime.now()
    #matlab will output image.id_YearMonthDay.mat file
    preprocessedImageFile = PREPROCESS_DIR + str(image.id) + "_" + str(now.year) + str(now.month) + str(now.day) + ".mat"

    matlabCallString = '/usr/bin/matlab/bin/matlab -nosplash -nodesktop -nojvm -r "cd /home/beijbom/e/Code/MATLAB; startup; warning off; coralnet_preprocessImage(\'' + ORIGINALIMAGES_DIR + str(image.original_file) + '\', \'' + preprocessedImageFile + '\', \'' + PREPROCESS_PARAM_FILE + '\', \'' + PREPROCESS_ERROR_LOG + '\'); exit;"'

    #call coralnet_preprocessImage(matlab script) to process a single image
    os.system(matlabCallString);

    #error occurred in matlab
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing this image, halting!")
    #everything went okay with matlab
    else:
        image.status = '1'
        image.save()
        print 'Finished pre-processing image id {}'.format(image.id)

@task()
def MakeFeatures(image):
    print 'Start feature extraction for  image id {}'.format(image.id)
    
    #if error had occurred in preprocess, don't let them go further
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing, halting feature extraction!")
    else:
        #builds args for matlab script
        now = datetime.now()

        preprocessedImageFile = PREPROCESS_DIR + str(image.id) + "_" + str(now.year) + str(now.month) + str(now.day) + ".mat"
        featureFile = FEATURES_DIR + str(image.id) + "_" + str(now.year) + str(now.month) + str(now.day) + ".dat"
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
            image.status = '2'
            image.save()
            print 'Finished feature extraction for image id {}'.format(image.id)
        
@task()
def Classify(image):
    print 'Start classify image id {}'.format(image.id)

    #if error occurred in feature extraction, don't let them go further
    if os.path.isfile(FEATURE_ERROR_LOG):
        print("Sorry error detected in feature extraction, halting classification!")
    else:
        #builds args for matlab script
        now = datetime.now()
        featureFile = FEATURES_DIR + str(image.id) + "_" + str(now.year) + str(now.month) + str(now.day) + ".dat"
	#get the source id for this file
        modelFile = MODEL_DIR + str(image.source.labelset.id) + "_model.txt"
        labelFile = CLASSIFY_DIR + str(image.id) + "_" + str(now.year) + str(now.month) + str(now.day) + ".txt"
        
        matlabCallString = '/usr/bin/matlab/bin/matlab -nosplash -nodesktop -nojvm -r "cd /home/beijbom/e/Code/MATLAB; startup; warning off; coralnet_classify(\'' + featureFile + '\', \'' + modelFile + '\', \'' + labelFile + '\', \'' + CLASSIFY_ERROR_LOG + '\'); exit;"'

        #call matlab script coralnet_classify
        os.system(matlabCallString);
	if os.path.isfile(CLASSIFY_ERROR_LOG):
            print("Sorry error detected in classification!")
        else:
            #get algorithm user object
            user = get_robot_user()

            #open the labelFile and rowColFile to process labels
            rowColFile = FEATURES_DIR + str(image.id) + "_rowCol.txt"
            label_file = open(labelFile, 'r')
            row_file = open(rowColFile, 'r')

            for line in row_file:
                #words[0] is row, words[1] is column
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
            image.status = '3'
            image.save()
            print 'Finished classification of image id {}'.format(image.id)

