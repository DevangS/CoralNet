import os
from django.conf import settings

try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

def generate_patch_if_doesnt_exist(patchPath, annotation):
    patchFullPath = os.path.join(settings.MEDIA_ROOT, patchPath)

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
        x = annotation.point.column
        y = annotation.point.row

        if x-75 > 0:
            left = x-75
        else:
            left = 0

        if x+75 < max_x:
            right = x+75
        else:
            right = max_x

        if y-75 > 0:
            upper = y-75
        else:
            upper = 0

        if y+75 < max_y:
            lower = y+75
        else:
            lower = max_y

        box = (left,upper,right,lower)

        #crop the image and save it
        region = image.crop(box)
        region.save(patchFullPath)
