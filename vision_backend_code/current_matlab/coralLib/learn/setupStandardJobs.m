function jobs = setupStandardJobs(data, trainSettings, rootDir, localDataDir)

nJobs = length(trainSettings);

for jn = 1 : nJobs
    logger(sprintf('Setting up job %d.', jn));
    jobDir = fullfile(rootDir, sprintf('job%d', jn));
    mkdir(jobDir);
    job = standardSolverJob(jobDir);
    job.ts = trainSettings(jn);
    
    %%% CREATE TRAIN AND TEST DATA %%%
    job.trainData = splitData(data, job.ts.trainIds);
    job.testData = splitData(data, job.ts.testIds);
    [job.trainingWeights job.ssStats] = getSVMssfactor(job.trainData, job.ts.svmParams.targetNbrSamplesPerClass);
    job.trainData = subsampleDataStruct(job.trainData, job.trainingWeights);
    
    %%% SET PARAMS %%%
    job.fwtoolSolverParams(1).optStr = makeSolverOptionString(job.ts.svmParams.options, job.trainingWeights);
    job.commitoptions = job.ts.svmParams.commitoptions;
    job.maxRuntime = job.ts.svmParams.maxRuntime;
    job.fwtoolSolverParams(1).plantHandle = job.ts.svmParams.plantHandle;
    job.fwtoolSolverParams(2).plantHandle = job.ts.svmParams.plantHandle;
    
    tempTargetFile = fullfile('/home/beijbom/.concatscripts/', datestr(now, 30), 'targettemp.txt');
    concatSelect(tempTargetFile, localDataDir, job.trainData, job.ts.svmParams.targetNbrSamplesPerClass == inf, 1);
    system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(1).trainPath));
    [~, job.gtlabels] = concatSelect(tempTargetFile, localDataDir, job.testData, 1, 1);
    system(sprintf('cp %s %s', tempTargetFile, job.fwtoolSolverParams(2).testPath));

    jobs(jn) = job;
end

jobs = fwtool_makeScripts(jobs);

logger('Committing jobs');
for jn = 1 : nJobs
    jobs(jn).jobId = fwtool_commitJob(jobs(jn).script, jobs(jn).commitoptions); %#ok<AGROW>
end


end
