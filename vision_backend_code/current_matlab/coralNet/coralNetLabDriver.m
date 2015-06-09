%% DEBUGGING SOME TRAINING
workDir = '/home/beijbom/robot/robot823.workdir';
modelPath = '/home/beijbom/robot/robot823';

testPath = fullfile(workDir, 'test');
labelPath = fullfile(workDir, 'label2');

system(sprintf('/home/beijbom/apps/libsvm/svm-predict %s %s %s;\n', testPath, modelPath, labelPath));

%%

estLabels = dlmread(fullfile(workDir, 'label'));
d1 = unique(estLabels);

tmp = dlmread(fullfile(workDir, 'points'));
allData.fromfile = tmp(:,1);
allData.pointNbr = tmp(:,2);
allData.labels = tmp(:,3);
labelMap = unique(allData.labels); %this is a list of all the label ids

[gtLabels, testfeatures] = libsvmread(fullfile(workDir, 'test'));

cm{thisPoint} = confMatrix(mapLabels(gtLabels, labelMap), mapLabels(estLabels, labelMap), numel(labelMap));

% 
% d2 = unique(gtlabels);
% setdiff(d1, dd)
% setdiff(dd, d1)
% setdiff(dd, d2)
% setdiff(d2, d1)
% setdiff(d1, d2)



%% SETUP PATHS
workDir = '/home/beijbom/robot/robot823.workdir';
modelPath = '/home/beijbom/robot/robot823';
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
workdir = '/home/beijbom/e/Code/gitProjects/CoralNet/images/models/robot31.workdir';

gridParams.start = [0 2];
gridParams.range.min = [-5 -5];
gridParams.range.max = [5 5];
gridParams.stepsize = [1 1];
gridParams.edgeLength = 1;

targetNbrSamplesPerClass.final = 200;
targetNbrSamplesPerClass.HP = 100;


coralnet_trainRobot('~/Desktop/modeltmp.dat', '', fullfile(workdir, 'points'), ...
    fullfile(workdir, 'fileNames'), fullfile(workdir), '~/Desktop/log.txt', ...
    '~/Desktop/err.log', 'gridParams', gridParams, 'targetNbrSamplesPerClass', targetNbrSamplesPerClass);


%%
addpath(genpath('/cnhome/vision_backend_code/current_matlab'))
workdir = '/home/beijbom/tmp/robot695.workdir';

gridParams.start = [0 2];
gridParams.range.min = [-5 -5];
gridParams.range.max = [5 5];
gridParams.stepsize = [1 1];
gridParams.edgeLength = 1;

targetNbrSamplesPerClass.final = 200;
targetNbrSamplesPerClass.HP = 100;


coralnet_trainRobot('~/modeltmp.dat', '', fullfile(workdir, 'points'), ...
    fullfile(workdir, 'fileNames'), fullfile(workdir), '~/log.txt', ...
    '~/err.log', 'gridParams', gridParams, 'targetNbrSamplesPerClass', targetNbrSamplesPerClass);