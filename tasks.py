from datetime import datetime
from subprocess import call
from celery.decorators import task
import os
from django.contrib.auth.models import User
from annotations.models import Label, Annotation
from images.models import Point

PREPROCESS_ERROR_LOG = "preprocess_error.txt"
FEATURES_ERROR_LOG = "features_error.txt"
CLASSIFY_ERROR_LOG = "classify_error.txt"

PREPROCESS_DIR = "/images/preprocess/"
FEATURES_DIR = "/images/features/"
CLASSIFY_DIR = "/images/classify/"

PREPROCESS_PARAM_FILE = "/images/preprocess/preProcessParameters.mat"
FEATURE_PARAM_FILE = "/images/features/featuresExtractionParameters.mat"

ALGORITHM_USERID = '0' #TODO: create new user for this and put userid here

#Tasks that get processed by Celery
#Possible future problems include that each task relies on it being the same day to continue processing an image,
#a solution would be to store the date that you preprocess the iamge and then update it if you run a newer version of
#the algorithm against it

@task()
def PreprocessImages(image):
    print("Start pre-processing image id %r", image.id)

    #gets current date to append to file name
    now = datetime.datetime.now()
    #matlab will output image.id_YearMonthDay.mat file
    preprocessedImageFile = PREPROCESS_DIR + image.id + "_" + now.year + now.month + now.day + ".mat"

    #call coralnet_preprocessImage(matlab script) to process a single image
    call(['coralnet_preprocessImage', "/" + str(image.original_file),   preprocessedImageFile, PREPROCESS_PARAM_FILE,
          PREPROCESS_ERROR_LOG])

    #error occurred in matlab
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing this image, halting!")
    #everything went okay with matlab
    else:
        image.status = '1'
        image.save()
        print("Finished pre-processing image id %r", image.id)

@task()
def MakeFeatures(image):
    print("Start feature extraction for  image id %r", image.id)
    
    #if error had occurred in preprocess, don't let them go further
    if os.path.isfile(PREPROCESS_ERROR_LOG):
        print("Sorry error detected in preprocessing, halting feature extraction!")
    else:
        #builds args for matlab script
        now = datetime.datetime.now()
        preProcessedImageFile = PREPROCESS_DIR + image.id + "_" + now.year + now.month + now.day + ".mat"
        featureFile = FEATURES_DIR + image.id + "_" + now.year + now.month + now.day + ".dat"

        #creates rowColFile
        rowColFile = FEATURES_DIR + image.id + "_rowCol.txt"
        file = open(rowColFile, 'w')
        points = Point.objects.filter(image=image)
        for point in points:
            #points get stored in the file in this format, one of these per line: row,column\n
            file.write(str(point.row) + "," + str(point.column) + "\n")
        file.close()
        
        #call matlab script coralnet_makeFeatures
        call(['coralnet_makeFeatures', preProcessedImageFile, featureFile, rowColFile, FEATURE_PARAM_FILE,
              FEATURES_ERROR_LOG])

        if os.path.isfile(FEATURES_ERROR_LOG):
            print("Sorry error detected in feature extraction!")
        else:
            image.status = '2'
            image.save()
            print("Finished feature extraction for  image id %r", image.id)
        
@task()
def Classify(image):
    print("Start classify image id %r", image.id)

    #if error occurred in feature extraction, don't let them go further
    if os.path.isfile(FEATURES_ERROR_LOG):
        print("Sorry error detected in feature extraction, halting classification!")
    else:
        #builds args for matlab script
        now = datetime.datetime.now()
        featureFile = FEATURES_DIR + image.id + "_" + now.year + now.month + now.day + ".dat"
        modelFile = #TODO: ask Oscar about where to get coralnet_train's output
        labelFile = CLASSIFY_DIR + image.id + "_" + now.year + now.month + now.day + ".txt"

        #call matlab script coralnet_classify
        call(['coralnet_classify', featureFile, modelFile, labelFile])
        if os.path.isfile(CLASSIFY_ERROR_LOG):
            print("Sorry error detected in classification!")
        else:
            #get algorithm user object
            user = User.objects.get(id=ALGORITHM_USERID)

            #open the labelFile and rowColFile to process labels
            rowColFile = FEATURES_DIR + image.id + "_rowCol.txt"
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
                annotation = Annotation(image=image, label=label, point=point, user=user, source=image.source)
                annotation.save()

            #update image status
            image.status = '3'
            image.save()
            print("Finished classification for  image id %r", image.id)

