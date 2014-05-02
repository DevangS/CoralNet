function res = trainWithBootstrap(allData, trainSettings, rootDir, localDataDir)

nJobs = length(trainSettings);

%%% DO FIRST ROUND, WITH A SMALL TRAIN DATA %%%
for jn = 1 : nJobs
    clear job
    logger(sprintf('Setting up job %d.', jn));
    jobDir = fullfile(rootDir, 'first', sprintf('job%d', jn));
    mkdir(jobDir);
    job = standardSolverJob(jobDir);
    job.ts = trainSettings(jn);

    
    %%% CREATE TRAIN AND TEST DATA %%%
    trainData = splitData(allData, job.ts.trainIds);
    [job.trainingWeights job.ssStats] = getSVMssfactor(trainData, round(job.ts.svmParams.targetNbrSamplesPerClass / 2));
    [job.trainData job.testData] = subsampleDataStructKeppTheRest(trainData, job.trainingWeights);
    
    
    %%% SET PARAMS %%%
    job.fwtoolSolverParams(1).optStr = makeSolverOptionString(job.ts.svmParams.options, job.trainingWeights);
    job.commitoptions = job.ts.svmParams.commitoptions;
    job.maxRuntime = job.ts.svmParams.maxRuntime;
    job.fwtoolSolverParams(1).plantHandle = job.ts.svmParams.plantHandle;
    job.fwtoolSolverParams(2).plantHandle = job.ts.svmParams.plantHandle;
    
%     tempTargetFile = fullfile('/home/beijbom/.concatscripts/', datestr(now, 30), 'targettemp.txt');
%     concatSelect(tempTargetFile, localDataDir, job.trainData, 0, 1);
%     system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(1).trainPath));
%     concatSelect(tempTargetFile, localDataDir, job.testData, 0, 1);
%     system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(2).testPath));

    jobs(jn) = job;
end

%%% RUN JOBS AND WAIT FOR THEM %%%
% res.first = fwtool_runJobs(fwtool_makeScripts(jobs));
res.first = jobs;
clear jobs;
%%% DO SECOND ROUND, WITH A SMALL TRAIN DATA %%%
for jn = 1 : nJobs
    clear job
    logger(sprintf('Setting up job %d.', jn));
    jobDir = fullfile(rootDir, 'second', sprintf('job%d', jn));
    mkdir(jobDir);
    job = standardSolverJob(jobDir);
    job.ts = trainSettings(jn);

    
    %%% CREATE TRAIN AND TEST DATA %%%
    estLabels = dlmread(res.first(jn).fwtoolSolverParams(2).labelPath);
    [dataHard job.selectHardStats] = selectHardSamples(res.first(jn).testData, estLabels, round(job.ts.svmParams.targetNbrSamplesPerClass / 2));
    job.trainData = mergeData(res.first(jn).trainData, dataHard);
    job.trainingWeights = findWeights(job.trainData, splitData(allData, job.ts.trainIds));
    job.testData = splitData(allData, job.ts.testIds);
    
    %%% SET PARAMS %%%
    job.fwtoolSolverParams(1).optStr = makeSolverOptionString(job.ts.svmParams.options, job.trainingWeights);
    job.commitoptions = job.ts.svmParams.commitoptions;
    job.maxRuntime = job.ts.svmParams.maxRuntime;
    job.fwtoolSolverParams(1).plantHandle = job.ts.svmParams.plantHandle;
    job.fwtoolSolverParams(2).plantHandle = job.ts.svmParams.plantHandle;
    
%     tempTargetFile = fullfile('/home/beijbom/.concatscripts/', datestr(now, 30), 'targettemp.txt');
%     concatSelect(tempTargetFile, localDataDir, job.trainData, 0, 1);
%     system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(1).trainPath));
%     concatSelect(tempTargetFile, localDataDir, job.testData, 0, 1);
%     system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(2).testPath));

    jobs(jn) = job;
end

%%% RUN SECOND BATCH %%%
jobs = fwtool_makeScripts(jobs);

for jn = 1 : nJobs
%     jobs(jn).jobId = fwtool_commitJob(jobs(jn).script, jobs(jn).commitoptions); %#ok<AGROW>
end
res.second = jobs;


end

function weights = findWeights(dataSS, dataAll)

classes = unique(dataAll.labels);
nbrClasses = length(classes);
for itt = 1 : nbrClasses
    thisClass = classes(itt);
    weights(itt) = nnz(dataAll.labels == thisClass) / nnz(dataSS.labels == thisClass);
end

end

function [dataOut stats] = selectHardSamples(dataIn, estLabels, targetNbrSamplesPerClass)


dataOut = dataIn;
for thisField = rowVector(fieldnames(dataIn))
    dataOut.(thisField{1}) = [];
end

classes = unique(dataIn.labels);
nbrClasses = length(classes);
for itt = 1 : nbrClasses
    thisClass = classes(itt);
    
    classIndex = find(dataIn.labels == thisClass);
    if (isempty(classIndex))
        continue
    end
    theseEstLabels = estLabels(classIndex);
    theseGtLabels = dataIn.labels(classIndex);
    
    falseInd = classIndex(theseEstLabels ~= theseGtLabels);
    nfalse = numel(falseInd);
    if (nfalse > 0)
        falseIndMod = falseInd(unique(round(linspace(1, nfalse, targetNbrSamplesPerClass))));
    end
    
    trueInd = classIndex(theseEstLabels == theseGtLabels);
    
    nTrue = numel(trueInd);
    nLeft = targetNbrSamplesPerClass - numel(falseIndMod);
    if (nTrue > 0 && nLeft > 0)
        trueIndMod = trueInd(unique(round(linspace(1, nTrue, nLeft))));
    else
        trueIndMod = [];
    end
    
    indexes = [falseIndMod; trueIndMod];
    
    for thisField = rowVector(fieldnames(dataOut))
        dataOut.(thisField{1}) = [dataOut.(thisField{1}); dataIn.(thisField{1})(indexes, :)];
    end
    
    ss.theseEstLabels = theseEstLabels;
    ss.theseGtLabels = theseGtLabels;
    ss.falseInd = falseInd;
    ss.falseIndMod = falseIndMod;
    ss.trueInd = trueInd;
    ss.trueIndMod = trueIndMod;
    ss.nfalse = nfalse;
    ss.nTrue = nTrue;
    ss.nLeft = nLeft;
    ss.indexes = indexes;
    ss.thisClass = thisClass;
    stats(itt) = ss;
    
end

end


function [dataOut dataRest] = subsampleDataStructKeppTheRest(dataIn, ssfactor)

classes = unique(dataIn.labels);
nbrClasses = length(classes);

% subsample dataOut and labels
dataOut = dataIn;
for thisField = rowVector(fieldnames(dataOut))
    dataOut.(thisField{1}) = [];
    dataRest.(thisField{1}) = [];
end

for itt = 1 : nbrClasses
    thisClass = classes(itt);
    for thisField = rowVector(fieldnames(dataOut))
        temp.(thisField{1}) = dataIn.(thisField{1})(dataIn.labels == thisClass, :);
        indexes = round(1 : ssfactor(itt) : size(temp.(thisField{1}), 1));
        
        logind = true(size(temp.(thisField{1}), 1), 1);
        logind(indexes) = false;
        
        dataOut.(thisField{1}) = [dataOut.(thisField{1}); temp.(thisField{1})(indexes, :)];
        dataRest.(thisField{1}) = [dataRest.(thisField{1}); temp.(thisField{1})(logind, :)];
        
    end
end

end