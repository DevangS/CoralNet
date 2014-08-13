function coralnet_trainRobot(modelPath, oldModelPath, pointInfoPath, fileNamesPath, workDir, logFile, errorLogfile)

global logfid

%%% HARD CODED PARAMS, KIND OF BUGGY, BUT COULDNT BOTHER WITH YET ANOTHER
%%% PARAM FILE
targetNbrSamplesPerClass.final = 7500;
targetNbrSamplesPerClass.HP = 5000;
labelRatio = 0.005;
maxNbrTestImages = 500;
gridParams.start = [0 2];
gridParams.range.min = [-5 -5];
gridParams.range.max = [5 5];
gridParams.stepsize = [1 1];
gridParams.edgeLength = 3;


solverOptions.libsvm.gamma = -2;
solverOptions.libsvm.C = -1;
solverOptions.libsvm.prob = 0;
solverOptions.libsvm.quiet = 1;
solverOptions.type = 'libsvm';


try
    
    logfid = fopen(logFile, 'a');
    %%% IMPORT FROM DISK %%%
    
    startTime = clock;
    
    tmp = dlmread(pointInfoPath);
    allData.fromfile = tmp(:,1);
    allData.pointNbr = tmp(:,2);
    allData.labels = tmp(:,3);
    
    fileNames = importdata(fileNamesPath);

    %%% PREPARE HP DATA SPLIT AND SET UP PATHS %%%
    testIdsBinary = false(numel(fileNames), 1);
    testIdsBinary(1:5:end) = true; % 1/5 of the data is test data
    trainIds = find(~testIdsBinary);
    testIds = find(testIdsBinary);
    logger('nTrainIds = %d, nTestIds = %d', numel(trainIds), numel(testIds));
    HPtrainPath = fullfile(workDir, 'train');
    HPtestPath = fullfile(workDir, 'test');
    finalTrainPath = fullfile(workDir, 'trainFinal');
    labelPath = fullfile(workDir, 'label');
    labelMap = unique(allData.labels);
    
    %%% FIND A THRESHHOLD FOR NBR SAMPLES REQUIRED FOR TRAINING %%%
    labelThreshhold = findNbrLabelsThreshhold(allData.labels, labelRatio);
    
    %%% HP - TRAINDATA %%%
    logger('Making HP train data')
    hp.trainData = makeTrainData(allData, fileNames, trainIds, HPtrainPath, targetNbrSamplesPerClass.HP, labelThreshhold, labelMap);
    
    %%% HP - TESTDATA %%%
    logger('Making HP test data')
    [hp.testData gtLabels] = makeTestData(allData, fileNames, testIds, HPtestPath, maxNbrTestImages);
    
    %%% RUN HP %%%
    logger('Running HP calibration');
    [hp.optValues, hp.estPrecision, hp.gridStats] = coralnet_runHPcalibration(HPtrainPath, HPtestPath, modelPath, labelPath, gtLabels, gridParams, solverOptions, hp.trainData.ssfactor, labelMap);
    
    %%% MAKE FINAL TRAIN DATA %%%
    logger('Making final train data')
    final.trainData = makeTrainData(allData, fileNames, [trainIds; testIds], finalTrainPath, targetNbrSamplesPerClass.final, labelThreshhold, labelMap);
    
    
    %%% TRAIN MODEL %%%
    logger('Training final model');
    solverOptions.libsvm.prob = 1; % this one uses probability outputs.
    solverOptions = setSolverCommonOptions(solverOptions, hp.optValues);
    final.optStr = makeSolverOptionString(solverOptions, final.trainData.ssfactor, labelMap);
    tic; system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-train %s %s %s;\n', final.optStr, finalTrainPath, modelPath));
    final.time.train = toc;
    
    %%% STORE IN MEAT DATA STRUCTURE %%%
    logger('Storing metadata');
    meta.gridParams = gridParams;
    meta.solverOptions = solverOptions;
    meta.hp = hp;
    meta.final = final;
    meta.labelMap = labelMap;
    meta.totalRuntime = etime(clock, startTime);
    meta.labelThreshhold = labelThreshhold;
    meta.targetNbrSamplesPerClass = targetNbrSamplesPerClass;
    meta.maxNbrTestImages = maxNbrTestImages;
    
    %%% SAVE %%%
    save(strcat(modelPath, '.meta.mat'), 'meta');
    
    ff = fopen(strcat(modelPath, '.meta.json'), 'w');
    fprintf(ff, '%s', savejson('' , meta, []));
    fclose(ff);
    
    logger('Done.');
    fclose(logfid);
    
catch me
    
    fid = fopen(errorLogfile, 'a');
    fprintf(fid, '[%s] Error executing coralnet_trainRobot: %s, %s, %s, %d \n', datestr(clock, 31), me.identifier, me.message, me.stack(1).file, me.stack(1).line);
    logger('[%s] Error executing coralnet_trainRobot: %s, %s, %s, %d \n', datestr(clock, 31), me.identifier, me.message, me.stack(1).file, me.stack(1).line);
    fclose(fid);
    fclose(logfid);
    
end


end

function labelThreshhold = findNbrLabelsThreshhold(labels, ratio)

labelMap = unique(labels);

counts = hist(labels, labelMap);

% we need each class to have at leat 'ratio' of the amount of
% annotated points as the most common class, else we won't consider
% it in training.
labelThreshhold = floor(max(counts) * ratio);


end



function stats = makeTrainData(allData, fileNames, trainIds, trainPath, targetNbrSamplesPerClass, labelThreshhold, labelMap)

% select the ids.
trainData = splitData(allData, trainIds);
stats.labelhist.org = hist(trainData.labels, labelMap);

% Subsamples to not have too much data
ssfactor = getSVMssfactor(trainData, targetNbrSamplesPerClass);
trainData = subsampleDataStruct(trainData, ssfactor);

% Filter out the most rare labels
trainData = removeRareLabels(trainData, labelThreshhold);
stats.labelhist.pruned = hist(trainData.labels, labelMap);

% Merge the train data
tic; concatSelect(trainPath, [], trainData, 0, 1, fileNames);
stats.runtime = toc;
stats.ssfactor = ssfactor;

end

function [stats, gtLabels] = makeTestData(allData, fileNames, testIds, testPath, maxNbrTestImages)

stats.ids.org = testIds;
% Use only a subset of the test files; it suffice.
testIds = testIds(unique(round(linspace(1, numel(testIds), maxNbrTestImages))));

stats.ids.mod = testIds;
% Split the test data
testData = splitData(allData, testIds);
tic; concatSelect(testPath, [], testData, 1, 1, fileNames);
stats.runtime = toc;
gtLabels = testData.labels;

end

function dataOut = removeRareLabels(dataIn, labelThreshhold)


classes = unique(dataIn.labels);
nbrClasses = length(classes);

keepInd = true(numel(dataIn.labels), 1);
removedLabelsStr = [];
for itt = 1 : nbrClasses
    thisClass = classes(itt);
    theseSamples = (dataIn.labels == thisClass);
    nbrTotalSamples = nnz(theseSamples);
    if (nbrTotalSamples < labelThreshhold)
        removedLabelsStr = sprintf('%s %d,', removedLabelsStr, thisClass);
        keepInd(theseSamples) = false;
    end
end
logger('Removed labels: %s', removedLabelsStr);

dataOut = dataIn;
for thisField = rowVector(fieldnames(dataOut))
    dataOut.(thisField{1}) = dataIn.(thisField{1})(keepInd, :);
end


end


function [optValues, estPrecision, stats] = coralnet_runHPcalibration(trainPath, testPath, modelPath, labelPath, gtLabels, gridParams, solverOptions, ssfactor, labelMap)
np = gridCrawler([], [], gridParams);
mainItt = 0;
fval = [];
vp = [];
while (~isempty(np))
    mainItt = mainItt + 1;
    thisFval = zeros(size(np, 1), 1);
    cm = cell(size(np, 1), 1);
    
    logger('Running new grid of points.');
    % Plant jobs.
    tic
    for thisPoint = 1 : size(np, 1)
        
        solverOptions = setSolverCommonOptions(solverOptions, np(thisPoint, :));
        optStr = makeSolverOptionString(solverOptions, ssfactor, labelMap);
        
        logger(sprintf('Running job, gamma:%.3g, C:%.3g', np(thisPoint, 1), np(thisPoint, 2)));
        
        system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-train %s %s %s;\n', optStr, trainPath, modelPath));
        
        system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-predict %s %s %s;\n', testPath, modelPath, labelPath));
        
        estLabels = dlmread(labelPath);
        
        thisFval(thisPoint) = 1 - (nnz(gtLabels == estLabels) / nnz(gtLabels));
        
        % now make the confusion matrix
        cm{thisPoint} = confMatrix(mapLabels(gtLabels, labelMap), mapLabels(estLabels, labelMap), numel(labelMap));
        
    end
    
    vp = [vp ; np]; %#ok<AGROW>
    fval = [fval; mean(thisFval, 2)]; %#ok<AGROW>
    
    % do bookkeeping.
    stats(mainItt).runtime = toc;
    stats(mainItt).np  = np;
    stats(mainItt).fvalAll = thisFval;
    stats(mainItt).fvalMean = mean(thisFval, 2);
    stats(mainItt).cm = cm;
    stats(mainItt).minIndex = find(stats(mainItt).fvalMean == min(stats(mainItt).fvalMean), 1);
    stats(mainItt).gammaCOpt = stats(mainItt).np(stats(mainItt).minIndex, :);
    stats(mainItt).fvalOpt = stats(mainItt).fvalMean(stats(mainItt).minIndex);
    stats(mainItt).cmOpt = cm{stats(mainItt).minIndex};
    
    %create new points.
    np = gridCrawler(vp, fval, gridParams);
    
end

optValues = stats(end).gammaCOpt;
estPrecision = stats(end).fvalOpt;

end


function labelsOut = mapLabels(labelsIn, labelMap)

labelsOut = zeros(size(labelsIn));

for i = 1 : numel(labelMap)
    
    labelsOut(labelsIn == labelMap(i)) = i;
    
end

end
