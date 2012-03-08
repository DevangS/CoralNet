from images.tasks import *


dirName = 'temp/labels/'
imagesLoc = 'temp/images/'
destImagesLoc = 'temp/sampled/'
outputFilename = 'temp/tony_annotations.txt'
pickledLabelDictLoc = 'import/tony_pickled_labels.txt'
prefix = 'Taiwan'
#okayArray = ['FAN1-1', 'FAN1-10-', 'FAN1-2', 'FAN1-20', 'FAN1-3', 'FAN1-4', 'FAN1-5', 'FAN1-6', 'FAN1-7', 'FAN1-8', 'FAN10-1', 'FAN10-10', 'FAN10-11', 'FAN10-12', 'FAN10-13', 'FAN10-14', 'FAN10-15', 'FAN10-16', 'FAN10-17', 'FAN10-18', 'FAN10-19', 'FAN10-2', 'FAN10-20', 'FAN10-21', 'FAN10-3', 'FAN10-4', 'FAN10-5', 'FAN10-6', 'FAN10-7', 'FAN10-8', 'FAN10-9', 'FAN2-1', 'FAN2-10', 'FAN2-11', 'FAN2-12', 'FAN2-13', 'FAN2-14', 'FAN2-15', 'FAN2-16', 'FAN2-17', 'FAN2-18', 'FAN2-19', 'FAN2-2', 'FAN2-20', 'FAN2-3', 'FAN2-4', 'FAN2-5', 'FAN2-6', 'FAN2-7', 'FAN2-8', 'FAN2-9', 'FAN3-1', 'FAN3-10', 'FAN3-11', 'FAN3-12', 'FAN3-13', 'FAN3-14', 'FAN3-15', 'FAN3-16', 'FAN3-17', 'FAN3-18', 'FAN3-19', 'FAN3-2', 'FAN3-20', 'FAN3-3', 'FAN3-4', 'FAN3-5', 'FAN3-6', 'FAN3-7', 'FAN3-8', 'FAN3-9', 'FAN4-1', 'FAN4-10', 'FAN4-11', 'FAN4-12', 'FAN4-13', 'FAN4-14', 'FAN4-15', 'FAN4-16', 'FAN4-17', 'FAN4-19', 'FAN4-2', 'FAN4-20', 'FAN4-3', 'FAN4-4', 'FAN4-5', 'FAN4-6', 'FAN4-7', 'FAN4-8', 'FAN4-9', 'FAN5-1', 'FAN5-10', 'FAN5-11', 'FAN5-12', 'FAN5-13', 'FAN5-14', 'FAN5-15', 'FAN5-16', 'FAN5-17', 'FAN5-18', 'FAN5-19', 'FAN5-2', 'FAN5-20', 'FAN5-21', 'FAN5-3', 'FAN5-4', 'FAN5-5', 'FAN5-6', 'FAN5-7', 'FAN5-8', 'FAN5-9', 'FAN6-1', 'FAN6-10', 'FAN6-11', 'FAN6-12', 'FAN6-13', 'FAN6-14', 'FAN6-15', 'FAN6-16', 'FAN6-17', 'FAN6-18', 'FAN6-19', 'FAN6-2', 'FAN6-20', 'FAN6-21', 'FAN6-22', 'FAN6-3', 'FAN6-4', 'FAN6-5', 'FAN6-6', 'FAN6-7', 'FAN6-8', 'FAN6-9', 'FAN7-1', 'FAN7-10', 'FAN7-11', 'FAN7-12', 'FAN7-13', 'FAN7-14', 'FAN7-15', 'FAN7-16', 'FAN7-17', 'FAN7-18', 'FAN7-19', 'FAN7-2', 'FAN7-20', 'FAN7-3', 'FAN7-4', 'FAN7-5', 'FAN7-6', 'FAN7-7', 'FAN7-8', 'FAN7-9', 'FAN8-1', 'FAN8-10', 'FAN8-11', 'FAN8-12', 'FAN8-13', 'FAN8-14', 'FAN8-15', 'FAN8-16', 'FAN8-17', 'FAN8-18', 'FAN8-19', 'FAN8-2', 'FAN8-20', 'FAN8-3', 'FAN8-4', 'FAN8-5', 'FAN8-6', 'FAN8-7', 'FAN8-8', 'FAN8-9', 'FAN9-1', 'FAN9-10', 'FAN9-11', 'FAN9-12', 'FAN9-13', 'FAN9-14', 'FAN9-15', 'FAN9-16', 'FAN9-17', 'FAN9-18', 'FAN9-19', 'FAN9-2', 'FAN9-20', 'FAN9-3', 'FAN9-4', 'FAN9-5', 'FAN9-6', 'FAN9-7', 'FAN9-8', 'FAN9-9', 'KIN1-1', 'KIN1-10', 'KIN1-11', 'KIN1-12', 'KIN1-13', 'KIN1-14', 'KIN1-15', 'KIN1-16', 'KIN1-17', 'KIN1-18', 'KIN1-19', 'KIN1-2', 'KIN1-20', 'KIN1-3', 'KIN1-4', 'KIN1-5', 'KIN1-6', 'KIN1-7', 'KIN1-8', 'KIN1-9', 'KIN2-1', 'KIN2-10', 'KIN2-11', 'KIN2-12', 'KIN2-13', 'KIN2-14', 'KIN2-15', 'KIN2-16', 'KIN2-17', 'KIN2-18', 'KIN2-19', 'KIN2-2', 'KIN2-20', 'KIN2-3', 'KIN2-4', 'KIN2-5', 'KIN2-6', 'KIN2-7', 'KIN2-8', 'KIN2-9', 'KING10-1', 'KING10-10', 'KING10-11', 'KING10-12', 'KING10-13', 'KING10-14', 'KING10-15', 'KING10-16', 'KING10-17', 'KING10-18', 'KING10-19', 'KING10-2', 'KING10-20', 'KING10-3', 'KING10-4', 'KING10-5', 'KING10-6', 'KING10-7', 'KING10-8', 'KING10-9', 'KING3-1', 'KING3-10', 'KING3-11', 'KING3-12', 'KING3-13', 'KING3-14', 'KING3-15', 'KING3-16', 'KING3-17', 'KING3-18', 'KING3-19', 'KING3-2', 'KING3-20', 'KING3-3', 'KING3-4', 'KING3-5', 'KING3-6', 'KING3-7', 'KING3-8', 'KING3-9', 'KING4-1', 'KING4-10', 'KING4-11', 'KING4-12', 'KING4-13', 'KING4-14', 'KING4-15', 'KING4-16', 'KING4-17', 'KING4-18', 'KING4-19', 'KING4-2', 'KING4-20', 'KING4-3', 'KING4-4', 'KING4-5', 'KING4-6', 'KING4-7', 'KING4-8', 'KING4-9', 'KING6-1', 'KING6-10', 'KING6-11', 'KING6-12', 'KING6-13', 'KING6-14', 'KING6-15', 'KING6-16', 'KING6-17', 'KING6-18-WITH', 'KING6-19', 'KING6-2', 'KING6-20', 'KING6-3', 'KING6-4', 'KING6-5', 'KING6-6', 'KING6-7', 'KING6-8', 'KING6-9', 'KING7-1', 'KING7-10', 'KING7-11', 'KING7-12', 'KING7-13', 'KING7-14', 'KING7-15', 'KING7-16', 'KING7-17', 'KING7-18', 'KING7-19', 'KING7-20', 'KING7-3', 'KING7-4', 'KING7-5', 'KING7-6', 'KING7-8', 'KING7-9', 'KING8-1', 'KING8-10', 'KING8-11', 'KING8-12', 'KING8-13', 'KING8-14', 'KING8-15', 'KING8-16', 'KING8-17', 'KING8-2', 'KING8-3', 'KING8-4', 'KING8-5', 'KING8-7', 'KING8-8', 'KING8-9', 'KING9-1', 'KING9-11', 'KING9-12', 'KING9-13', 'KING9-14', 'KING9-15', 'KING9-16', 'KING9-17', 'KING9-18', 'KING9-2', 'KING9-20', 'KING9-3', 'KING9-6', 'KING9-7', 'KING9-8', 'KING9-9', 'KIR1-1', 'KIR1-10', 'KIR1-11', 'KIR1-12', 'KIR1-13', 'KIR1-14', 'KIR1-15', 'KIR1-16', 'KIR1-17', 'KIR1-18', 'KIR1-19', 'KIR1-2', 'KIR1-20', 'KIR1-3', 'KIR1-4', 'KIR1-5', 'KIR1-6', 'KIR1-7', 'KIR1-8', 'KIR1-9', 'KIR10-1', 'KIR10-10', 'KIR10-11', 'KIR10-12', 'KIR10-13', 'KIR10-14', 'KIR10-15', 'KIR10-16', 'KIR10-17', 'KIR10-18', 'KIR10-19', 'KIR10-2', 'KIR10-20', 'KIR10-3', 'KIR10-4', 'KIR10-5', 'KIR10-6', 'KIR10-7', 'KIR10-8', 'KIR10-9', 'KIR11-1', 'KIR11-10', 'KIR11-11', 'KIR11-12', 'KIR11-13', 'KIR11-14', 'KIR11-2', 'KIR11-20 with', 'KIR11-3', 'KIR11-4', 'KIR11-5', 'KIR11-6', 'KIR11-7', 'KIR11-8', 'KIR11-9', 'KIR2-1', 'KIR2-10', 'KIR2-11', 'KIR2-12', 'KIR2-13', 'KIR2-14', 'KIR2-15', 'KIR2-16', 'KIR2-18', 'KIR2-19', 'KIR2-2', 'KIR2-20', 'KIR2-3', 'KIR2-4', 'KIR2-5', 'KIR2-6', 'KIR2-7', 'KIR2-8', 'KIR2-9', 'KIR3-1', 'KIR3-10', 'KIR3-11', 'KIR3-12', 'KIR3-13', 'KIR3-14', 'KIR3-15', 'KIR3-16', 'KIR3-17', 'KIR3-18', 'KIR3-19', 'KIR3-2', 'KIR3-20', 'KIR3-3', 'KIR3-4', 'KIR3-5', 'KIR3-6', 'KIR3-7', 'KIR3-8', 'KIR3-9', 'KIR4-1', 'KIR4-10', 'KIR4-11', 'KIR4-12', 'KIR4-13', 'KIR4-14', 'KIR4-15', 'KIR4-16', 'KIR4-17', 'KIR4-18', 'KIR4-19', 'KIR4-2', 'KIR4-20with', 'KIR4-3', 'KIR4-4', 'KIR4-5', 'KIR4-6', 'KIR4-7', 'KIR4-8', 'KIR4-9', 'KIR7-1', 'KIR7-10', 'KIR7-11-WITH', 'KIR7-12', 'KIR7-13', 'KIR7-14', 'KIR7-15', 'KIR7-16', 'KIR7-17', 'KIR7-18', 'KIR7-19-WITH', 'KIR7-2', 'KIR7-20-WITH', 'KIR7-3', 'KIR7-4', 'KIR7-5', 'KIR7-6', 'KIR7-7', 'KIR7-8', 'KIR7-9', 'KIR8-1', 'KIR8-10', 'KIR8-11', 'KIR8-12', 'KIR8-13', 'KIR8-14', 'KIR8-15', 'KIR8-16', 'KIR8-17', 'KIR8-18', 'KIR8-19-WITH', 'KIR8-2', 'KIR8-20-WITH', 'KIR8-3', 'KIR8-4', 'KIR8-5', 'KIR8-6', 'KIR8-7', 'KIR8-8', 'KIR8-9', 'KIR9-1', 'KIR9-10', 'KIR9-11', 'KIR9-12', 'KIR9-13', 'KIR9-14', 'KIR9-15', 'KIR9-16', 'KIR9-17', 'KIR9-18-WITH', 'KIR9-19-WITH', 'KIR9-2', 'KIR9-20-WITH', 'KIR9-3', 'KIR9-4', 'KIR9-5', 'KIR9-6', 'KIR9-7', 'KIR9-8', 'KIR9-9', 'PAL1-1', 'PAL1-10', 'PAL1-11', 'PAL1-12', 'PAL1-13', 'PAL1-14', 'PAL1-15', 'PAL1-16', 'PAL1-17', 'PAL1-18', 'PAL1-19', 'PAL1-2', 'PAL1-3', 'PAL1-4', 'PAL1-5', 'PAL1-6', 'PAL1-7', 'PAL1-8', 'PAL1-9', 'PAL10-1', 'PAL10-10', 'PAL10-11', 'PAL10-12', 'PAL10-13', 'PAL10-14', 'PAL10-15', 'PAL10-16', 'PAL10-17', 'PAL10-18', 'PAL10-19', 'PAL10-2', 'PAL10-20', 'PAL10-3', 'PAL10-4', 'PAL10-5', 'PAL10-6', 'PAL10-7', 'PAL10-8', 'PAL10-9', 'PAL12-1', 'PAL12-10', 'PAL12-11', 'PAL12-12', 'PAL12-13', 'PAL12-14', 'PAL12-15', 'PAL12-16', 'PAL12-17', 'PAL12-18', 'PAL12-19', 'PAL12-2', 'PAL12-20', 'PAL12-3', 'PAL12-4', 'PAL12-5', 'PAL12-6', 'PAL12-7', 'PAL12-8', 'PAL12-9', 'PAL2-1', 'PAL2-10', 'PAL2-11', 'PAL2-12', 'PAL2-13', 'PAL2-14', 'PAL2-15', 'PAL2-16', 'PAL2-17', 'PAL2-18', 'PAL2-19', 'PAL2-2', 'PAL2-20-WITH', 'PAL2-3', 'PAL2-4', 'PAL2-5', 'PAL2-6', 'PAL2-7', 'PAL2-8', 'PAL2-9', 'PAL3-1', 'PAL3-10', 'PAL3-11', 'PAL3-12', 'PAL3-13', 'PAL3-14', 'PAL3-15', 'PAL3-16', 'PAL3-17', 'PAL3-18 WITH', 'PAL3-19 WITH', 'PAL3-2', 'PAL3-20', 'PAL3-3', 'PAL3-4', 'PAL3-5', 'PAL3-6', 'PAL3-7', 'PAL3-8', 'PAL3-9', 'PAL4-1', 'PAL4-10', 'PAL4-11', 'PAL4-12', 'PAL4-13', 'PAL4-14', 'PAL4-15', 'PAL4-16', 'PAL4-17', 'PAL4-18', 'PAL4-19', 'PAL4-2', 'PAL4-20', 'PAL4-3', 'PAL4-4', 'PAL4-5', 'PAL4-6', 'PAL4-7', 'PAL4-8', 'PAL4-9', 'PAL5-1', 'PAL5-10', 'PAL5-11', 'PAL5-12', 'PAL5-13', 'PAL5-14', 'PAL5-15', 'PAL5-16', 'PAL5-17', 'PAL5-18', 'PAL5-19WITH', 'PAL5-2', 'PAL5-20 WITH', 'PAL5-3', 'PAL5-4', 'PAL5-5', 'PAL5-6', 'PAL5-7', 'PAL5-8', 'PAL5-9', 'PAL6-1', 'PAL6-10', 'PAL6-11', 'PAL6-12', 'PAL6-13', 'PAL6-14', 'PAL6-15', 'PAL6-16', 'PAL6-17', 'PAL6-18', 'PAL6-19', 'PAL6-2', 'PAL6-20', 'PAL6-3', 'PAL6-4', 'PAL6-5', 'PAL6-6', 'PAL6-7', 'PAL6-8', 'PAL6-9', 'PAL7-1', 'PAL7-10', 'PAL7-11', 'PAL7-12', 'PAL7-13', 'PAL7-14', 'PAL7-15', 'PAL7-16', 'PAL7-17', 'PAL7-18', 'PAL7-19', 'PAL7-2', 'PAL7-3', 'PAL7-4', 'PAL7-5', 'PAL7-6', 'PAL7-7', 'PAL7-8', 'PAL7-9', 'PAL8-1', 'PAL8-10', 'PAL8-11', 'PAL8-12', 'PAL8-13', 'PAL8-14', 'PAL8-15', 'PAL8-16', 'PAL8-17', 'PAL8-18', 'PAL8-19', 'PAL8-2', 'PAL8-3', 'PAL8-4', 'PAL8-5', 'PAL8-6', 'PAL8-7', 'PAL8-8', 'PAL8-9', 'king8-6', 'king9-10']
#importPhotoGridImage(prefix, dirName, imagesLoc, outputFilename, pickledLabelDictLoc)
#renameAllTheImages(prefix, imagesLoc, imagesLoc, okayArray )
#importCPCImage(prefix, dirName, imagesLoc, outputFilename, pickledLabelDictLoc)
#randomSampleImages(imagesLoc, dirName, destImagesLoc, 200)