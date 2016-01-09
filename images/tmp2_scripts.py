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
This script exports all imges and annotations for the purpose of building a deep super-classifier
"""
def export_images_and_annotations(source_idlist, outdir):

    for source_id in source_idlist:
        this_dir = os.path.join(outdir, 's{}'.format(source_id))
        os.mkdir(this_dir)
        os.mkdir(os.path.join(this_dir, 'imgs'))
        imdict = {} 
        source = Source.objects.get(id = source_id)
        for im in source.get_all_images():
            
            # Special check for MLC. Do not want the imgs from 2008!!!!
            if source_id == 16 and im.metadata.photo_date.year == 2008:
            	continue
            if not im.status.annotatedByHuman:
            	continue
            
            annlist = []
            for a in im.annotation_set.filter():
                annlist.append((a.label.name, a.point.row, a.point.column))
            imdict[im.metadata.name] = (annlist, im.height_cm())
            copyfile(os.path.join('/cnhome/media', str(im.original_file)), os.path.join(this_dir, 'imgs', im.metadata.name))
        pickle.dump(imdict, open(os.path.join(this_dir, 'imdict.p'), 'wb'))
