function cs = coralExperimentWrapper(cs, varargin)
% cs = multiYearStandardExpDistributed(cs, svmParams, varargin)
%
%
% varargin:
% testRun = 0;
% makeDictionary = 1;
% extractFeatures = 1;
% cvSettings.do = 0;
% trainSettings.do = 0;

testRun = 0;
makeDictionary = 1;
extractFeatures = 1;
cvSettings.do = 0;
trainSettings.do = 0;


[varnames, varvals] = var2varvallist(testRun, makeDictionary, extractFeatures, cvSettings, trainSettings);
[testRun, makeDictionary, extractFeatures, cvSettings, trainSettings] = varargin_helper(varnames, varvals, varargin{:});

global logfid
logfid = fopen(fullfile(getdirs('testdatadir'), cs.fileinfo.date, cs.fileinfo.dir, 'log.txt'), 'a');
localDataDir = fullfile('/home/beijbom/e/Data/testdata/', cs.fileinfo.DD, 'feat');
rootDir = fullfile('~/runs', cs.fileinfo.shortId);
featureDir = fullfile(rootDir, 'features');
mkdir(featureDir);
mkdir(rootDir);
mkdir(localDataDir);
mkdir(fullfile(rootDir, 'dictionary'));


%%% IF TESTRUN %%%
if (testRun)
    cs.params.featureParams.prep.nbrFilesPerCommit = 2;
    cs.params.featureParams.nbrFilesPerCommit =  2;
    cs.params.featureParams.prep.fileIndex = cs.params.featureParams.prep.fileIndex(1:10:end);
    cs.params.fileNbrs = cs.params.fileNbrs(1:10:end);
    cvSettings = cvSettings(1);
    cvSettings.svmParams.targetNbrSamplesPerClass = 200;
    cvSettings.svmParams.gridParams.start = [-2 -1];
    cvSettings.svmParams.gridParams.range.min = [-3 -2];
    cvSettings.svmParams.gridParams.range.max = [-1 0];
    cvSettings.svmParams.crossVal.nbrFolds = 1;
    cvSettings.svmParams.crossVal.stepSize = 2;
    for jn = 1 : numel(trainSettings)
        trainSettings(jn).svmParams.targetNbrSamplesPerClass = 200;
        trainSettings(jn).cvIds = 1;
    end
end

%%% CREATE DICTIONARY %%%
if (makeDictionary)
    ok = false;
    while(~ok)
        [cs ok] = dictionaryWrapper(cs, fullfile(rootDir, 'dictionary'), cs.params.featureParams.prep.fileIndex);
    end
end

%%% EXTRACT FEATURES %%%
if (extractFeatures)
    ok = false;
    while(~ok)
        [cs ok] = featureWrapper(cs, featureDir, cs.params.fileNbrs);
    end
end

nDims = size(mergeCellContent(cs.featurePrep{1}.textons(1, :)), 1) * length(cs.params.featureParams.patchSize);

%%% COPY FROM CLUSTER AND NORMALIZE FEATURES %%%
cs.normalizer = getFeatureNormalizationFromDisk(featureDir, localDataDir, cs.params.featureParams.prep.fileIndex, cs.params.nPointsPerFile, nDims);
normalizeFeaturefiles(featureDir, localDataDir, cs.params.fileNbrs, cs.data.fromfile);
cs = saveDataStruct(cs);


%%% DO CROSSVALIDATION %%%
for itt = 1 : length(cvSettings)
    if (cvSettings(itt).do)
        cvDir = fullfile(rootDir, sprintf('svmCV_%d', itt));
        logger(sprintf('Finding optimal hyper parameters for set %d.', itt));
        trainData = splitData(cs.data, cvSettings{itt}.trainIds);
        cvNbr = findnextcellnumber(cs, 'cv');
        [cs.cv(cvNbr).gammaCOpt cs.cv(cvNbr).stats] = calibrateGammaCCluster(cvDir, cvSettings(itt).svmParams, cs.params.errorParams, trainData, localDataDir);
        cs.cv(cvNbr).settings.trainIds = cvSettings(itt).trainIds;
        cs = saveDataStruct(cs);
    end
end

%%% RUN STANDARD JOBS %%%
if (trainSettings(1).do)
    
    for jn = 1 : numel(trainSettings)
        if(trainSettings(jn).cvid > 0)
            trainSettings(jn).svmParams.options = setSolverCommonOptions(trainSettings(jn).svmParams.options, cs.cv(trainSettings(jn).cvid).gammaCOpt);
        end
    end
    
    cs.standard.jobs = setupStandardJobs(cs.data, trainSettings, fullfile(rootDir, 'standardjobs'), localDataDir);
    cs = saveDataStruct(cs);
end
fclose(logfid);
end





