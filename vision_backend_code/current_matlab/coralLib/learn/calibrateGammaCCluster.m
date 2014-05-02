function [gammaCOpt stats] = calibrateGammaCCluster(rootDir, svmParams, errorFuncParams, allData, sourceDatadir)

logger('Starting crossvalidation of svm hyper parameters');

if (exist(rootDir, 'dir'))
    rmdir(rootDir, 's')
end
mkdir(rootDir);


[gtLabels ssStats] = writeGammaCData(svmParams, sourceDatadir, rootDir, allData);

nbrClasses = max(allData.labels); % assumes the labels are sequential and starts at 1.
solverOptions = svmParams.options;

vp = [];
fval = [];
np = gridCrawler(vp, fval, svmParams.gridParams);
mainItt = 0;
while (~isempty(np))
    logger('Running new grid of points.');
    mainItt = mainItt + 1;
    
    thisFval = zeros(size(np, 1), svmParams.crossVal.nbrFolds);
    jobItt = 0;
    
    % Plant jobs.
    jobs = struct('script', cell(svmParams.crossVal.nbrFolds * size(np, 1), 1), ...
        'jobId', [], ...
        'jobLog', [], ...
        'commitoptions',  svmParams.commitoptions, ...
        'maxRuntime', svmParams.crossVal.maxRuntime, ...
        'fwtoolSolverParams', struct(...
        'plantHandle', svmParams.plantHandle, ...
        'trainPath', [], ...
        'testPath', [], ...
        'outputPath', [], ...
        'labelPath', [], ...
        'optStr', [], ...
        'modelPath', [], ...
        'type', cell(2, 1)), ...
        'cv', [], ...
        'pointNbr', []);
    
    
    for cvNbr = 1 : svmParams.crossVal.nbrFolds
        
        trainPath =  fullfile(rootDir, sprintf('CV%d_train', cvNbr));
        testPath =  fullfile(rootDir, sprintf('CV%d_test', cvNbr));
        
        for thisPoint = 1 : size(np, 1)
            logger('Creating job CV:%d, gamma:%.3g, C:%.3g', cvNbr, np(thisPoint, 1), np(thisPoint, 2));
            solverOptions = setSolverCommonOptions(solverOptions, np(thisPoint, :));
            optStr = makeSolverOptionString(solverOptions, ssStats{cvNbr}.ssfactor);
            
            jobItt = jobItt + 1;
            jobs(jobItt).script = fullfile(rootDir, sprintf('CV%d_%g_%g_script', cvNbr, 100 + np(thisPoint, 1), 100 + np(thisPoint, 2)));
            jobs(jobItt).fwtoolSolverParams(1).type = 'train';
            jobs(jobItt).fwtoolSolverParams(1).trainPath = trainPath;
            jobs(jobItt).fwtoolSolverParams(1).modelPath = fullfile(rootDir, sprintf('CV%d_%g_%g_model', cvNbr, 100 + np(thisPoint, 1), 100 + np(thisPoint, 2)));
            jobs(jobItt).fwtoolSolverParams(1).outputPath = fullfile(rootDir, sprintf('CV%d_%g_%g_output', cvNbr, 100 + np(thisPoint, 1), 100 + np(thisPoint, 2)));
            jobs(jobItt).fwtoolSolverParams(1).optStr = optStr;
            jobs(jobItt).fwtoolSolverParams(2).type = 'test';
            jobs(jobItt).fwtoolSolverParams(2).testPath = testPath;
            jobs(jobItt).fwtoolSolverParams(2).labelPath = fullfile(rootDir, sprintf('CV%d_%g_%g_labels', cvNbr, 100 + np(thisPoint, 1), 100 + np(thisPoint, 2)));
            jobs(jobItt).fwtoolSolverParams(2).modelPath = jobs(jobItt).fwtoolSolverParams(1).modelPath;
            jobs(jobItt).fwtoolSolverParams(2).outputPath = jobs(jobItt).fwtoolSolverParams(1).outputPath;
            jobs(jobItt).fwtoolSolverParams(2).optStr = '';
            jobs(jobItt).cv = cvNbr;
            jobs(jobItt).pointNbr = thisPoint;
            
        end
    end
    
    logger('Running jobs');
    jobs = fwtool_runJobs(fwtool_makeScripts(jobs));
    
    logger('Collect jobs');
    for jobItt = 1 : length(jobs)
        job = jobs(jobItt);
        logger('Collecting job: %s, id: %d, with job status: %d', job.script, job.jobId, job.jobLog);
        
        [labelOk labels] = loadLabelfileSecure(svmParams.collectHandle, job.fwtoolSolverParams(2).labelPath, gtLabels{job.cv}, nbrClasses);
        
        if (labelOk)
            thisFval(job.pointNbr, job.cv) = coralErrorFcn(confMatrix(gtLabels{job.cv}, labels, nbrClasses), errorFuncParams);
        else
            thisFval(job.pointNbr, job.cv) = inf;
        end
    end
    
    vp = [vp ; np]; %#ok<AGROW>
    fval = [fval; mean(thisFval, 2)]; %#ok<AGROW>
    
    % do bookkeeping.
    stats(mainItt).np  = np;
    stats(mainItt).fval = thisFval;
    stats(mainItt).minIndex = find(fval == min(fval), 1);
    stats(mainItt).gammaCOpt = vp(stats(mainItt).minIndex(1), :);
    stats(mainItt).jobs = jobs;
    stats(mainItt).ssStats = ssStats;
    
    %create new points.
    np = gridCrawler(vp, fval, svmParams.gridParams);
    
end
logger('Converged.');
minIndex = find(fval == min(fval), 1);
gammaCOpt = vp(minIndex(1), :);

end


function [labelOk estlabels] = loadLabelfileSecure(loadHandle, filePath, gtlabels, nbrClasses)

estlabels = [];
labelOk = true;
if ~exist(filePath, 'file')
    labelOk = false;
    logger(sprintf('Label file does not exist\n'));
end
if(labelOk)
    try
        estlabels = feval(loadHandle, filePath, nbrClasses);
    catch me
        logger(sprintf('Label file is corrupted (%s)\n', me.message));
        labelOk = false;
    end
end
if(labelOk)
    labelOk = (numel(estlabels) == numel(gtlabels));
end

if (~labelOk)
    logger(sprintf('Label file is not complete\n'));
end

end

