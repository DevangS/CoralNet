function [cs ok] = featureWrapper(cs, rootDir, fileNbrs)
% cs = featureWrapper(cs, rootDir, fileNbrs)

logger('Creating features using fwgrid.');

system(sprintf('cp ~/e/Data/testdata/%s/%s/data.mat %s', cs.fileinfo.date, cs.fileinfo.dir, fullfile(rootDir, 'data.mat')));

nbrFilesPerCommit = cs.params.featureParams.nbrFilesPerCommit;
startFileNumbers = 1 : nbrFilesPerCommit : numel(fileNbrs);
nJobs = numel(startFileNumbers);

jobs = struct('script', cell(nJobs, 1), ...
    'jobId', [], ...
    'jobLog', [], ...
    'commitoptions', '-l matlab=1 -cwd', ...
    'maxRuntime', cs.params.featureParams.maxRuntime, ...
    'fwtoolSolverParams', struct(...
    'solverPath', cs.params.featureParams.handle,...
    'csStructPath', fullfile(rootDir, 'data.mat'), ...
    'fileNbr', cell(nbrFilesPerCommit), ...
    'outputPath', [], ...
    'plantHandle', @plantForCoralFeatures) );

for itt = 1 : numel(startFileNumbers)
    jobs(itt).script = fullfile(rootDir, sprintf('IPT%d', itt));
    for i = 1 : min(numel(fileNbrs) - (nbrFilesPerCommit * (itt - 1)), nbrFilesPerCommit)
        jobs(itt).fwtoolSolverParams(i).fileNbr = fileNbrs((itt - 1) * nbrFilesPerCommit + i);
        jobs(itt).fwtoolSolverParams(i).dataPath = fullfile(rootDir, sprintf('file%d.dat', jobs(itt).fwtoolSolverParams(i).fileNbr));
        jobs(itt).fwtoolSolverParams(i).metaPath = fullfile(rootDir, sprintf('meta%d.mat', jobs(itt).fwtoolSolverParams(i).fileNbr));
        if(exist(jobs(itt).fwtoolSolverParams(i).metaPath, 'file'))
            jobs(itt).fwtoolSolverParams(i).plantHandle = @nojob;
        end
    end
    jobs(itt).fwtoolSolverParams = jobs(itt).fwtoolSolverParams(1:i);
end

logger('Running jobs');
jobs = fwtool_runJobs(fwtool_makeScripts(jobs));

logger('Collecting jobs');
[cs.data ok] = collectFeatureMetadata(jobs);

cs = saveDataStruct(cs);

end

function [all_features ok] = collectFeatureMetadata(jobs)

ok = true;
temp = robustLoad(jobs(1).fwtoolSolverParams(1).metaPath);

F = rowVector(fields(temp.data));

nSamplesPerFile = numel(temp.data.labels) * 1.5; %hedge a bit if the first file is super small.
nFiles = length(jobs) * length(jobs(1).fwtoolSolverParams);
all_features.labels = zeros(nSamplesPerFile * nFiles, 1, 'single');
all_features.fromfile = zeros(nSamplesPerFile * nFiles, 1, 'single');
all_features.rowCol = zeros(nSamplesPerFile * nFiles, 2, 'single');
all_features.pointNbr = zeros(nSamplesPerFile * nFiles, 1, 'single');

pos = 0;

startTime = clock;
for itt = 1 : length(jobs)
    
    for j = 1 : length(jobs(itt).fwtoolSolverParams);
        
        
        
        filepath = jobs(itt).fwtoolSolverParams(j).metaPath;
        logger(sprintf('Collecting file %s', filepath));
        
        [temp success] = robustLoad(filepath, 'nbrTries', 5);
        
        if (~success)
            logger(sprintf('Failed to load [%s], aborting.', filepath));
            ok = false;
        end
        
        if(~ok)
            return
        end
        
        these_features = temp.data;
        nbrSamples = length(these_features.labels);
        if(nbrSamples == 0)
			continue
		end  
        for f = F
            all_features.(f{1})(pos + 1: pos + nbrSamples, :) = these_features.(f{1});
        end
        pos = pos + nbrSamples;
    end
    estimateRemainingTime(startTime, clock, length(jobs), itt, 1);
    
end

F = rowVector(fields(all_features));
for f = F
    all_features.(f{1}) = all_features.(f{1})(1 : pos, :);
end

end
