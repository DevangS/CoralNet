import os
from django.conf import settings

try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

def generate_patch_if_doesnt_exist(patchPath, annotation):
    patchFullPath = os.path.join(settings.MEDIA_ROOT, patchPath)
    PATCH_X = 150 #x size of patch (after scaling)
    PATCH_Y = 150 #y size of patch (after scaling)
    REDUCE_SIZE = 1.0/5.0 #patch covers this proportion of the original image's greater dimension
    
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
        #careful; x is the column, y is the row
        x = annotation.point.column
        y = annotation.point.row

        patchSize = int(max(max_x,max_y)*REDUCE_SIZE)
        patchSize = (patchSize/2)*2  #force patch size to be even
        halfPatchSize = patchSize/2
        scaledPatchSize = (PATCH_X, PATCH_Y)

        # If a patch centered on (x,y) would be too far off to the left,
        # then just take a patch on the left edge of the image.
        if x - halfPatchSize < 0:
            left = 0
            right = patchSize
        # If too far to the right, take a patch on the right edge
        elif x + halfPatchSize > max_x:
            left = max_x - patchSize
            right = max_x
        else:
            left = x - halfPatchSize
            right = x + halfPatchSize

        # If too far toward the top, take a patch on the top edge
        if y - halfPatchSize < 0:
            upper = 0
            lower = patchSize
        # If too far toward the bottom, take a patch on the bottom edge
        elif y + halfPatchSize > max_y:
            upper = max_y - patchSize
            lower = max_y
        else:
            upper = y - halfPatchSize
            lower = y + halfPatchSize

        box = (left,upper,right,lower)

        #crop the image and save it
        region = image.crop(box)
        region = region.resize(scaledPatchSize)
        region.save(patchFullPath)
