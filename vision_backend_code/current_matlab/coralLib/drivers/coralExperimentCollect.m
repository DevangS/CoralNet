function jobs = coralExperimentCollect(jobs, force)
% jobs = coralExperimentCollect(jobs, force)
%
%  coralExperimentCollect collects the results from INPUT jobs
%  it reads nbrClasses and gtlabels from the jobs structure
%  it calls getStatsWrapper to create result statistics

nbrJobs = numel(jobs);

if nargin < 2
    force = false;
end

logger('Collect job');
for jn = 1 : nbrJobs
    
    
    if (isfield(jobs(jn), 'res') && ~isempty(jobs(jn).res) && ~force)
        logger('Already collected job %d', jn);
        continue
    end
    nbrClasses = numel(unique(jobs(jn).trainData));
    gtlabels = jobs(jn).gtlabels;
    
    [labelOk estLabels] = loadLabelfileSecure(jobs(jn).ts.svmParams.collectHandle, jobs(jn).fwtoolSolverParams(2).labelPath, gtlabels, nbrClasses);
    if (labelOk)
        [jobs(jn).res.CM jobs(jn).res.fScore jobs(jn).res.simpleScore] = getStatsWrapper(gtlabels, estLabels);
        jobs(jn).estLabels = estLabels;
    end
end

end
