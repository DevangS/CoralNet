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
                image.after_height_cm_change() # this resets the image
                continue
            preprocessedImageFile = os.path.join(PREPROCESS_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".mat")
            featureFile = os.path.join(FEATURES_DIR, str(image.id) + "_" + image.get_process_date_short_str() + ".dat")
            if not(os.path.isfile(preprocessedImageFile)) or not(os.path.isfile(featureFile)):
                image.after_height_cm_change() # this resets the image
                img_counter += 1
        print "Reset the status for " + str(img_counter) + " images in: " + this_source.name


"""
This script exports all images from a source.
"""
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


"""
Takes in prefix like Taiwan, directory of labels, directory of images,
output annotation filename, pickled label mapping file location
Note: automatically renames the images and require the custom_listdir above
"""
def importCPCImage(prefix, dirName, imagesLoc, outputFilename, pickledLabelDictLoc):
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


"""
Takes in prefix like Taiwan, directory of labels, directory of images,
output annotation filename, pickled label mapping file location,
and total images to
pick(put 0 if want all images)
Note: automatically renames the images and require the custom_listdir above
"""
def importPhotoGridImage(prefix, dirName, imagesLoc, targetImgDir, outputFilename, pickledLabelDictLoc):
    
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

"""
This is legacy code from the inter operator study. Not sure exactly what it does
"""
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
"""
This is legacy code from the inter operator study. Not sure exactly what it does
"""
def renameAllTheImages(prefix, dirName, destDirName, errorArray):
    count = 1
    for filename in custom_listdir(dirName):
        if errorArray.count(filename.replace(".jpg", "")):
            newname = "404"+filename
        else:
            newname = prefix + "_" + str(count) + "_" + filename
        count += 1
        os.rename(dirName+filename, destDirName+newname)

"""
This is legacy code from the inter operator study. Not sure exactly what it does
"""
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

"""
This is legacy code from when we cleaned the database for corrupt images
"""
def verifyImage(image):
    try:
        fp = open(ORIGINALIMAGES_DIR + "/" + str(image.original_file), "rb")
        im = PILImage.open(fp) # open from file object
        im.load() # make sure PIL has read the data
        fp.close()
        return True
    except IOError:
        return False

"""
This is legacy code from when we cleaned the database for corrupt images
"""
def verifyAllImages():
    errorImages = []
    for image in Image.objects.all():
        if not verifyImage(image):
            errorImages.append(image)
    return errorImages

"""
This is legacy code from when we cleaned the database for corrupt images
"""
def verifyAllAndPrint():
    for errorFile in verifyAllImages():
        print errorFile.original_file.name
