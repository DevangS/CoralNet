from accounts.utils import get_robot_user
from annotations.models import Annotation
from images.models import Image, Point

def image_annotation_all_done(image_id):

    image = Image.objects.get(id=image_id)
    annotations = Annotation.objects.filter(image=image)

    # If every point has an annotation, and all annotations are by humans,
    # then we're all done
    return (annotations.count() == Point.objects.filter(image=image).count()
            and annotations.filter(user=get_robot_user()).count() == 0)