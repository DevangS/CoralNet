from images.models import Image
from PIL import Image as PILImage

def verifyAllImages(): 
	for image in Image.objects.all():
		try:
			fp = open(image.original_file, "rb")
			im = PILImage.open(fp) # open from file object
			im.load() # make sure PIL has read the data
			fp.close()
			
		except IOError:
			yield image.original_file

def verifyAllAndPrint():
	for errorFile in verifyAllImages():
		print errorFile.name

