function coralnet_trainRobot(modelPath, oldModelPath, pointInfoPath, fileNamesPath, workDir, logFile, errorLogfile, varargin)

global logfid

gridParams.start = [0 2];
gridParams.range.min = [-5 -5];
gridParams.range.max = [5 5];
gridParams.stepsize = [1 1];
gridParams.edgeLength = 3;

targetNbrSamplesPerClass.final = 7500;
targetNbrSamplesPerClass.HP = 5000;

[varnames, varvals] = var2varvallist(gridParams, targetNbrSamplesPerClass);
[gridParams, targetNbrSamplesPerClass] = varargin_helper(varnames, varvals, varargin{:});


%%% HARD CODED PARAMS, KIND OF BUGGY, BUT COULDNT BOTHER WITH YET ANOTHER
%%% PARAM FILE
labelRatio = 0.005;
maxNbrTestImages = 500;

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
    labelMap = unique(allData.labels); %this is a list of all the label ids
    
    %%% FIND A THRESHHOLD FOR NBR SAMPLES REQUIRED FOR TRAINING %%%
    labelThreshhold = findNbrLabelsThreshhold(allData.labels, labelRatio);
    
    %%% HP - TRAINDATA %%%
    logger('Making HP train data')
    [hp.trainData, keepClasses] = makeTrainData(allData, fileNames, trainIds, HPtrainPath, targetNbrSamplesPerClass.HP, labelThreshhold, labelMap);
    
    %%% HP - TESTDATA %%%
    logger('Making HP test data')
    [hp.testData, gtLabels] = makeTestData(allData, fileNames, testIds, HPtestPath, maxNbrTestImages);
    
    %%% RUN HP %%%
    logger('Running HP calibration');
    [hp.optValues, hp.estPrecision, hp.gridStats] = coralnet_runHPcalibration(HPtrainPath, HPtestPath, modelPath, labelPath, gtLabels, gridParams, solverOptions, hp.trainData.ssfactor, labelMap, keepClasses);
    
    %%% SET FINAL PARAMS %%%
    solverOptions.libsvm.prob = 1; % this one uses probability outputs.
    solverOptions = setSolverCommonOptions(solverOptions, hp.optValues);
    
    
    %%% RERUN WITH OPTIMAL PARAMETERS TO GENEARTE DECISION VALUES %%%
    logger('Training model for making decision values');
    hp.decvals.optStr = makeSolverOptionString(solverOptions, hp.trainData.ssfactor(keepClasses), labelMap(keepClasses));
    system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-train %s %s %s;\n', hp.decvals.optStr, HPtrainPath, modelPath));
    system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-predict -b 1 %s %s %s', HPtestPath,  modelPath,  labelPath));
    coralnet_alleviatecurves(gtLabels, labelPath, fullfile(workDir, 'labelmap'), strcat(modelPath, '.meta_all'));
    
    
    %%% MAKE FINAL TRAIN DATA %%%
    logger('Making final train data')
    [final.trainData, keepClasses] = makeTrainData(allData, fileNames, [trainIds; testIds], finalTrainPath, targetNbrSamplesPerClass.final, labelThreshhold, labelMap);
    
    %%% TRAIN MODEL %%%
    logger('Training final model');
    final.optStr = makeSolverOptionString(solverOptions, final.trainData.ssfactor(keepClasses), labelMap(keepClasses));
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



function [stats keepClasses] = makeTrainData(allData, fileNames, trainIds, trainPath, targetNbrSamplesPerClass, labelThreshhold, labelMap)

% select the ids.
trainData = splitData(allData, trainIds);
stats.labelhist.org = hist(trainData.labels, labelMap);

% Subsamples to not have too much data
ssfactor = getSVMssfactor(trainData, targetNbrSamplesPerClass, labelMap);
trainData = subsampleDataStruct(trainData, ssfactor);

% Filter out the most rare labels
[trainData, keepClasses] = removeRareLabels(trainData, labelThreshhold, labelMap);
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

function [dataOut keepClasses] = removeRareLabels(dataIn, labelThreshhold, labelMap)


nbrClasses = length(labelMap);

keepInd = true(numel(dataIn.labels), 1);
keepClasses = true(size(labelMap));
removedLabelsStr = [];
for itt = 1 : nbrClasses
    thisClass = labelMap(itt);
    theseSamples = (dataIn.labels == thisClass);
    if (nnz(theseSamples) < labelThreshhold)
        removedLabelsStr = sprintf('%s %d,', removedLabelsStr, thisClass);
        keepInd(theseSamples) = false;
        keepClasses(itt) = false;
    end
end
logger('Removed labels: %s', removedLabelsStr);

dataOut = dataIn;
for thisField = rowVector(fieldnames(dataOut))
    dataOut.(thisField{1}) = dataIn.(thisField{1})(keepInd, :);
end


end


function [optValues, estPrecision, stats] = coralnet_runHPcalibration(trainPath, testPath, modelPath, labelPath, gtLabels, gridParams, solverOptions, ssfactor, labelMap, keepInd)
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
        optStr = makeSolverOptionString(solverOptions, ssfactor(keepInd), labelMap(keepInd));
        
        logger(sprintf('Running job, gamma:%.3g, C:%.3g', np(thisPoint, 1), np(thisPoint, 2)));
        
        system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-train %s %s %s;\n', optStr, trainPath, modelPath));
        
        system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-predict %s %s %s;\n', testPath, modelPath, labelPath));
        
        estLabels = dlmread(labelPath);
        
        thisFval(thisPoint) = 1 - (nnz(gtLabels == estLabels) / numel(gtLabels));
        
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


function coralnet_alleviatecurves(gtLabels, decvalPath, labelMapPath, outputmetapath)
% this function does the whole alleviate thing. 

% read decision values (probabilities)
decvals = dlmread(decvalPath, ' ', 1, 1);
estLabels = dlmread(decvalPath, ' ', [1 0 size(decvals, 1) 0]);

% read label order
estLabelorder = dlmread(decvalPath, ' ', [0 1 0 size(decvals, 2)]);

allLabels = union(unique(gtLabels), estLabelorder);

% read the func group map
[funcmap, funcnames] = coralnet_readlabelmap(labelMapPath);

% pick all possible threholds
thresholds = unique(decvals(:));

% now subsample so we only consider max 10000 threholds
thresholds = thresholds(round(linspace(1, numel(thresholds), min(10000, numel(thresholds)))));
thresholds = sort(thresholds, 'descend');
alleviateLabels = gtLabels;

activeFuncGroups = unique(funcmap(allLabels));
acc = zeros(numel(thresholds), numel(activeFuncGroups));
keepRatio = zeros(numel(thresholds), 1);
for tItt = 1 : numel(thresholds)
    keepInd = any(decvals > thresholds(tItt), 2);
    keepRatio(tItt) = nnz(keepInd) ./ numel(keepInd);
    alleviateLabels(keepInd) = estLabels(keepInd);
    alleviateLabels(~keepInd) = gtLabels(~keepInd);
    cm = confMatrix(gtLabels, alleviateLabels, numel(funcmap));
    
    for fItt = 1 : numel(activeFuncGroups)
        maptmp = (funcmap == activeFuncGroups(fItt));
        maptmp = maptmp + 1; % 2 will now be the active func group. The rest will be 1.
        acc(tItt, fItt) = cohensKappa(confMatrixCollapse(cm, maptmp));
    end
end


clf;
plot(keepRatio, acc,'LineWidth',3);
legend(funcnames(activeFuncGroups))
ylabel('Cohens kappa')
xlabel('Ratio of points classified by machine');

if sum(ismember('Hard coral', funcnames(activeFuncGroups))) > 0
    coralAcc = acc(:, strcmp(funcnames(activeFuncGroups), 'Hard coral'));
    allLevel = find(coralAcc<0.95, 1);
    line([keepRatio(allLevel) keepRatio(allLevel)], [0 1], 'LineStyle', '-.', 'color', 'red', 'LineWidth', 1.5)
    line([0 1], [coralAcc(allLevel) coralAcc(allLevel)], 'LineStyle', '-.', 'color', 'red', 'LineWidth', 1.5)
    grid
    set(gcf, 'color', [1 1 1]);
    set(gcf, 'position', [100 100 500 300]);
    
    meta_all.keepRatio = round(keepRatio(allLevel) * 100);
    meta_all.ok = 1;
    % find the threholds that correspond to each integer alleviation level
    for intkeep = rowVector(1 : 100)
        [~, ind] = min(abs(keepRatio*100 - intkeep));
        meta_all.thout(intkeep) = thresholds(ind);
    end
    
else
    meta_all.ok = 0; % no hard coral label, can't do anything.
end

export_fig([outputmetapath, '.png']);
save([outputmetapath, '.mat'], 'meta_all');

ff = fopen(strcat(outputmetapath, '.json'), 'w');
fprintf(ff, '%s', savejson('' , meta_all, []));
fclose(ff);


end

function [funcmap, funcnames] = coralnet_readlabelmap(labelMapPath)
fid = fopen(labelMapPath, 'r');
line = fgetl(fid);
while ~strcmp(line, '===')
    parts = regexp(line, ',', 'split');
    funcnames{str2double(parts{2})} = parts{1};
    line = fgetl(fid);
end

line = fgetl(fid);
while ~(line == -1)
    parts = regexp(line, ',', 'split');
    funcmap(str2double(parts{1})) = str2double(parts{2});
    line = fgetl(fid);
end
fclose(fid);


end