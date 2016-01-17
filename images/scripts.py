"""
This file contains scripts that are not part of the main production server. But that reads/exports/manipulates things on a one-to-one basis.
"""

from images.models import Point, Image, Source, Robot
from annotations.models import Annotation
import os
import numpy as np
from django.conf import settings
from datetime import datetime
from images.tasks import *
from images.scripts_helper import RobotStats
from django.core.exceptions import ValidationError, MultipleObjectsReturned
join_processing_root = lambda *p: os.path.join(settings.PROCESSING_ROOT, *p)
PREPROCESS_DIR = join_processing_root("images/preprocess/")
FEATURES_DIR = join_processing_root("images/features/")






"""
This script process a source in serial. Useful for debugging the vision backend
"""

def process_source_complete_debug(source_id, force_retrain = False):
  
    print "==== Start processing source ===="
    source = Source.objects.get(pk = source_id)

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
This script runs to robot for all "small" sources.

"""
def train_small_robots(th = 50):
    for source in Source.objects.filter(enable_robot_classifier=True).order_by('id'):
        if len(source.get_all_images()) < th:
            print 'Adding labels for ' + source.name + '.'
            for image in source.get_all_images():
                add_labels_to_features(image.id)
            print 'Done adding labels. Training robot for ' + source.name + '.'
            train_robot(source.id)


"""
This script goes through all point and check if there are duplicate annotations. We had some problems with this so are trying to debug.
"""
def find_duplicate_annotations():
    n = len(Point.objects.filter())
    for itt, p in enumerate(Point.objects.filter()):
        if(itt % 500000 == 0):
            print 'Processed ' + str(itt) + ' out of ' + str(n) + 'annotations.'
        try:
            a = Annotation.objects.get(point = p)
        except MultipleObjectsReturned:
            print 'Multiple annotation objects for Imageid:' + str(p.image_id) + ', pointid:' + str(p.id)
        except Annotation.DoesNotExist:
            d = 1
    print "done."


"""
This script exports all imges and annotations for the purpose of building a deep super-classifier
"""
def export_imgage_and_annotations(source_idlist, outdir):

    for source_id in source_idlist:
        this_dir = os.path.join(outdir, 's{}'.format(source_id))
        os.mkdir(this_dir)
        os.mkdir(os.path.join(this_dir, 'imgs'))
        imdict = []
        source = Source.objects.get(id = source_id)
        for im in source.get_all_images:

            # Special check for MLC. Do not want the imgs from 2008!!!!
            if source_id == 16 and im.metadata.photo_date.year == 2008:
                continue
            if not im.status.annotatedByHuman:
                continue
            
            annlist = []
            for a in im.annotation_set.filter():
                annlist.append((a.label.name, a.point.row, a.point.column))
            imdict[im.metadata.name] = (annlist, im.height_cm())
            copyfile(os.path.join('/cnhome/media', str(i.original_file)), os.path.join(this_dir, 'imgs', im.metadata.name))
        pickle.dump(imdict, os.path.join(this_dir, 'imdict.p'))


"""
This script organizes some key stats of all the source, and puts it in a nice list.
"""
def get_source_stats():
    nlabels = Label.objects.order_by('-id')[0].id #highest label id on the site
    labelname = {}
    labelfunc = {}
    funcname = {}
    for label in Label.objects.filter():
        labelname[label.id] = label.name
        labelfunc[label.id] = label.group_id
    for fg in LabelGroup.objects.filter():
        funcname[fg.id] = fg.name
    ss = []
    for s in Source.objects.filter():
        annlist = [a.label_id for a in s.annotation_set.exclude(user=get_robot_user())]
        if not annlist:
            continue
        print s.name
        sp = {}
        sp['name'] = s.name
        sp['lat'] = s.latitude
        sp['long'] = s.longitude
        sp['id'] = s.id
        sp['labelids'] = [l.id for l in s.labelset.labels.all()]
        sp['nlabels'] = s.labelset.labels.count()
        sp['nimgs'] = s.get_all_images().filter(status__annotatedByHuman=True).count()
        sp['nanns'] = len(annlist)
        sp['anncount'] = np.bincount(annlist, minlength = nlabels)
        ss.append(sp)
    return ss, labelname, labelfunc, funcname






"""
This script exports a bunch of robots stats to a data structure. This is then saved to disk (for now). 
TODO: automatically generate scripts to read this data structure and display plots on the website.
"""

def export_robot_stats():
   
    sources = Source.objects.filter()
    all_stats = []
    for source in sources:
        robots = source.get_valid_robots()
        latest_robot = source.get_latest_robot()
        for robot in robots:
            print robot
            ts = RobotStats(robot.version)

            # basic stats
            ts.source_id = source.id
            ts.active = robot == latest_robot
            ts.date = '%s' %  datetime.fromtimestamp(os.path.getctime(robot.path_to_model + '.meta.json')).date()

            # read accuracy of the full confusion matrix
            (fullcm, labelIds) = get_confusion_matrix(robot)
            fullacc = accuracy_from_cm(fullcm)
            ts.fullacc = fullacc[0]
            ts.fullkappa = fullacc[1]

            # read accuracy of the functional groups
            (funccm, placeholder, groupIds) = collapse_confusion_matrix(fullcm, labelIds)
            funcacc = accuracy_from_cm(funccm)
            ts.funcacc = funcacc[0]
            ts.funckappa = funcacc[1]

            # read other stuff
            f = open(robot.path_to_model + '.meta.json')
            meta=json.loads(f.read())
            f.close()

            ts.nsamples_org = sum(meta['final']['trainData']['labelhist']['org'])
            ts.nsamples_pruned = sum(meta['final']['trainData']['labelhist']['pruned'])
            ts.train_time = int(round(meta['totalRuntime']))
            ts.target_nbr_samples_hp = meta['targetNbrSamplesPerClass']['HP']
            ts.target_nbr_samples_final = meta['targetNbrSamplesPerClass']['final']
            ts.nlabels = len(meta['labelMap'])
            ts.label_threshold = meta['labelThreshhold']
            gs = meta['hp']['gridStats']
            if(isinstance(gs, list)):
                gs = gs[-1]
            ts.gamma_opt = gs['gammaCOpt'][0]
            ts.c_opt = gs['gammaCOpt'][1]

            # alleviation meta
            all_meta = get_alleviate_meta(robot)
            if all_meta['ok']:
                ts.allevation_level = all_meta['suggestion']
            else:
                ts.allevation_level = None
            all_stats.append(ts)

    return all_stats



"""
This scripts set the level of alleviation to 0 for all sources
"""
def set_alleviate_to_zero():
    for source in Source.objects.filter(enable_robot_classifier=True):
        print "Processing source id:" + str(source.id)
        source.alleviate_threshold = 0
        source.save()

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
def export_images(source_id, outDir, original_file_name = True):
    mysource = Source.objects.filter(id = source_id)
    images = Image.objects.filter(source = mysource[0])
    for i in images:
        m = i.metadata
        if original_file_name:
            fname = m.name
        else:
            fname = str(m.value1) + '_' + str(m.value2) + '_' + \
            str(m.value3) + '_' + str(m.value4) + '_' + str(m.value5) + \
            '_' + m.photo_date.isoformat() + '.jpg'
        copyfile(os.path.join('/cnhome/media', str(i.original_file)), 
        os.path.join(outDir, fname))


"""
This checks for duplicates among image names.
"""
def find_duplicate_imagenames():
    for source in Source.objects.filter():
        if not source.all_image_names_are_unique():
            print '==== Source {}[{}] ===='.format(source.name, source.id)
            for image in source.get_all_images().filter(metadata__name__in = source.get_nonunique_image_names()):
                print image.id, image.metadata.name




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
