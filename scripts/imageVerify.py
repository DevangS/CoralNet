from images.models import Image
try:
    from PIL import Image as PILImage
except ImportError:
    import Image as PILImage

def verifyAllImages(): 
	for image in Image.objects.all():
		try:
			PILImage.open(image.original_file)
		except IOError:
			yield image.original_file

def verifyAllAndPrint():
	for errorFile in verifyAllImages():
		print errorFile.name

