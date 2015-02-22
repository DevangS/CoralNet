%%% THIS FILE READS ALL MODELS FROM INPUT DIRECTORY AND EXTRACT SOME STATS.
%indir = '~/e/Code/gitProjects/CoralNet/images/models';
indir = '~/far_robots';
logfid = 1;
files = rdirCell(fullfile(indir, '*.meta.mat'));

for i = 1 : numel(files)
    load(files{i})
    
    %     if (meta.totalRuntime/3600 < 10)
    %         continue
    %     end
    numvp = 0;
    for gsItt = 1 : numel(meta.hp.gridStats)
        numvp = numvp + numel(meta.hp.gridStats(gsItt).fvalAll);
    end
    r(i).id = str2double(regexp(files{i}, '\d+', 'match'));
    
    %fprintf(logfid, '[%3d] tt: %.0fh, nclass[%d => %d], nsamp[%d => %d], nvp: %d, opt: %d,%d\n', ...
    %   robot_id, meta.totalRuntime/3600, nnz(meta.hp.trainData.labelhist.org), ...
    %  nnz(meta.hp.trainData.labelhist.pruned), ...
    % sum(meta.hp.trainData.labelhist.org), ...
    %sum(meta.hp.trainData.labelhist.pruned), numvp, ...
    %meta.hp.gridStats(end).gammaCOpt(1), meta.hp.gridStats(end).gammaCOpt(2));
    
    r(i).tt = meta.totalRuntime/3600;
    r(i).nclassin = nnz(meta.hp.trainData.labelhist.org);
    r(i).nclassout = nnz(meta.hp.trainData.labelhist.pruned);
    r(i).nsamplesin = sum(meta.hp.trainData.labelhist.org);
    r(i).nsamplesout = sum(meta.hp.trainData.labelhist.pruned);
    r(i).opt = meta.hp.gridStats(end).gammaCOpt;
    i
end
%%
close all
d = [r.opt];
scatter([r.tt], d(2:2:end))