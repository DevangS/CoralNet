
%% SETUP PATHS
workDir = '/home/beijbom/cnhome/images/models/debug_testDir/';
modelPath = fullfile(workDir, 'robot');
oldModelPath = '';
pointInfoPath = fullfile(workDir, 'points');
fileNamesPath = fullfile(workDir, 'fileNames');

logFile = fullfile(workDir, 'log');
errorLogfile = fullfile(workDir, 'errorLog');
labelFile = fullfile(workDir, 'labels');
ppfile = fullfile(workDir, 'pp');
featfile = fullfile(workDir, 'features');
imageFile = '/home/beijbom/e/Data/Coral/LTER-MCR/organised/mcr_lter1_fringingreef_pole1-2_qu1_20080415.JPG';
rowCol = fullfile(workDir, '100_rowCol.txt');
ssFile = fullfile(workDir, 'ssFile');

%%
coralnet_preprocessImage(imageFile, ppfile, './preProcessParameters.mat', ssFile, logFile, errorLogfile);
%%
coralnet_makeFeatures(ppfile, featfile, rowCol, ssFile, './preProcessParameters.mat', logFile, errorLogfile)
%%
coralnet_trainRobot(modelPath, oldModelPath, pointInfoPath, fileNamesPath, workDir, logFile, errorLogfile);
%%
coralnet_classify(featfile, modelPath, labelFile, errorLogfile)
load(strcat(modelPath, '.meta.mat'))

%%
addpath(genpath('~/e/Code/gitProjects/CoralNet/vision_backend_code/current_matlab'))
workdir = 'home/beijbom/e/Code/gitProjects/CoralNet/images/models/robot27.workdir';
coralnet_trainRobot('~/Desktop/modeltmp.dat', '', fullfile(workdir, 'points'), fullfile(workdir, 'fileNames'), fullfile(workdir), '~/Desktop/log.txt', '~/Desktop/err.log');