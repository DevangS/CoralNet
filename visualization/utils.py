import os
from django.conf import settings

try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

def generate_patch_if_doesnt_exist(patchPath, annotation):
    patchFullPath = os.path.join(settings.MEDIA_ROOT, patchPath)
    PATCH_X = 150 #x size of patch
    PATCH_Y = 150 #y size of patch
    REDUCE_SIZE = 1/5 #proportion to select patch
    
    #check if patch exists for the annotation
    try:
        PILImage.open(patchFullPath)

    #otherwise generate the patch
    except IOError:

        originalPath = annotation.image.original_file
        image = PILImage.open(originalPath)

        #determine the crop box
        max_x = annotation.image.original_width
        max_y = annotation.image.original_height
        x = annotation.point.row
        y = annotation.point.column
        offset = int(max(x,y)*REDUCE_SIZE)
        size = (PATCH_X, PATCH_Y)
        if x-offset > 0:
            left = x-offset
        else:
            left = 0

        if x+offset < max_x:
            right = x+offset
        else:
            right = max_x

        if y-offset > 0:
            upper = y-offset
        else:
            upper = 0

        if y+offset < max_y:
            lower = y+offset
        else:
            lower = max_y

        box = (left,upper,right,lower)

        #crop the image and save it
        region = image.crop(box)
        region = region.resize(size)
        region.save(patchFullPath)
