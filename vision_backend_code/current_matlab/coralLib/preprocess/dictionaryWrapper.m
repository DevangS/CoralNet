function [cs ok] = dictionaryWrapper(cs, rootDir, fileNbrs)
% [cs ok] = dictionaryWrapper(cs, rootDir, fileNbrs)
logger('Creating dictionary using fwgrid.');

system(sprintf('cp ~/e/Data/testdata/%s/%s/data.mat %s', cs.fileinfo.date, cs.fileinfo.dir, fullfile(rootDir, 'data.mat')));

nbrFilesPerCommit = cs.params.featureParams.prep.nbrFilesPerCommit;
startFileNumbers = 1 : nbrFilesPerCommit : numel(fileNbrs);
nJobs = numel(startFileNumbers);

jobs = struct('script', cell(nJobs, 1), ...
    'jobId', [], ...
    'jobLog', [], ...
    'commitoptions', '-l matlab=1 -cwd', ...
    'maxRuntime', cs.params.featureParams.prep.maxRuntime, ...
    'fwtoolSolverParams', struct(...
    'solverPath', cs.params.featureParams.prep.handle,...
    'csStructPath', fullfile(rootDir, 'data.mat'), ...
    'fileNbr', cell(nbrFilesPerCommit), ...
    'outputPath', [], ...
    'plantHandle', @plantForDictionary) );

for itt = 1 : numel(startFileNumbers)
    jobs(itt).script = fullfile(rootDir, sprintf('IPT%d', itt));
    for i = 1 : min(numel(fileNbrs) - (nbrFilesPerCommit * (itt - 1)), nbrFilesPerCommit)
        jobs(itt).fwtoolSolverParams(i).fileNbr = fileNbrs((itt - 1) * nbrFilesPerCommit + i);
        jobs(itt).fwtoolSolverParams(i).outputPath = fullfile(rootDir, sprintf('filterReponse%d.mat', jobs(itt).fwtoolSolverParams(i).fileNbr));
        if(exist(jobs(itt).fwtoolSolverParams(i).outputPath, 'file'))
            jobs(itt).fwtoolSolverParams(i).plantHandle = @nojob;
        end
    end
    jobs(itt).fwtoolSolverParams = jobs(itt).fwtoolSolverParams(1:i);
end

logger('Running jobs');
jobs = fwtool_runJobs(fwtool_makeScripts(jobs));

logger('Collecting jobs');
[samples, cs.stats.featurePrep.nbrSamplesAcc ok] = fwtool_collectFilterSamples(jobs, cs.params.featureParams(1).prep.maxNbrSamples, cs.params.featureParams.filterOutputDim, cs.stats.nbrClasses);

if(~ok)
    return
end

logger('Creating dictionary');

if (isfield(cs.params.featureParams, 'whiten') && cs.params.featureParams.whiten.do)
    
    allSamples = mergeCellContent(samples);
    [~, mu, ~, whMat] = whiten(allSamples);
    cs.featurePrep{1}.whiten.mu = mu;
    cs.featurePrep{1}.whiten.whMat = whMat;
    
end

textons = cell(1, cs.stats.nbrClasses);
for thisClass = 1 : cs.stats.nbrClasses
    if ~isempty(samples{thisClass})
        
        %%% if whiten boolean is set, perform whitening.
        if (isfield(cs.params.featureParams, 'whiten') && cs.params.featureParams.whiten.do)
            samples{thisClass} = bsxfun(@minus, samples{thisClass}, mu);
            theseSamples = samples{thisClass} * whMat;
        else
            theseSamples = samples{thisClass};
        end
        
        
        [~, textons{thisClass}, ~] = kmeans2(theseSamples, cs.params.featureParams(1).nbrTextons);
    end
end
cs.featurePrep{1}.textons = textons;
cs.featurePrep{1}.jobs = jobs;

cs = saveDataStruct(cs);

end

function [samples, nbrSamplesAcc, ok] = fwtool_collectFilterSamples(jobs, maxNbrSamplesPerClass, filterOutputDim, nbrClasses)

ok = true;
samples = cell(1, nbrClasses);
nbrSamplesAcc = zeros(1, nbrClasses);

for i = 1 : nbrClasses
    samples{i} = zeros(200 * length(jobs) * length(jobs(1).fwtoolSolverParams), filterOutputDim);
end

for jobItt = 1 : numel(jobs)
    
    for taskItt = 1 : numel(jobs(jobItt).fwtoolSolverParams)
        
        filepath = jobs(jobItt).fwtoolSolverParams(taskItt).outputPath;
        logger('Collecting file %s', filepath);
        [data success] = robustLoad(filepath, 'nbrTries', 5);
        
        if (~success)
            logger(sprintf('Failed to load [%s], aborting.', filepath));
            ok = false;
            return
        end
        
        for i = 1 : nbrClasses
            nbrSamplesInThisClass = size(data.samples{i}, 1);
            samples{i}(nbrSamplesAcc(i) + 1 : nbrSamplesAcc(i) + nbrSamplesInThisClass, :) = data.samples{i};
            nbrSamplesAcc(i) = nbrSamplesAcc(i) + nbrSamplesInThisClass;
        end
    end
end

% remove samples from classes with too many in them.
for i = 1 : nbrClasses
    if (nbrSamplesAcc(i) > maxNbrSamplesPerClass)
        useIndexes = randperm(nbrSamplesAcc(i));
        samples{i} = samples{i}(useIndexes(1:maxNbrSamplesPerClass), :);
    else
        samples{i} = samples{i}(1 : nbrSamplesAcc(i), :);
    end
end

end