function [scriptFilepath labels] = concatSelect(targetFile, rootDir, data, wholeFiles, runScript, fileNames)
% scriptFilepath = concatSelect(targetFile, rootDir, data, wholeFiles,
% runScript, fileNames)

if nargin < 6
    fileNames = [];
end
labels = [];
concatter= '/home/beijbom/e/Code/beijbom/projects/featureCat/featureCat';

%%% create a working directory %%%
localWorkDir = sprintf('/home/beijbom/.concatscripts/%s', datestr(now, 30));
if(~(exist(localWorkDir, 'dir')))
    mkdir(localWorkDir);
end

scriptFilepath = fullfile(localWorkDir, 'catscript.sh');

if(exist(targetFile, 'file'))
    delete(targetFile);
end
files = sort(unique(data.fromfile), 'ascend');

s_fid = fopen(scriptFilepath, 'w');

for fileItt = 1 : length(files)
    
    fileNbr = files(fileItt);
    
    if(isempty(fileNames))
    
        sourceFP = fullfile(rootDir, sprintf('file%dn.dat', fileNbr));
        
    else
        
        sourceFP = fileNames{fileNbr};
        
    end
    
    if(wholeFiles)
        
        fprintf(s_fid, 'cat %s >> %s\n', sourceFP, targetFile);
        theseSamples = splitData(data, fileNbr);
        
		labels = [labels; theseSamples.labels];
    else
        
        theseSamples = splitData(data, fileNbr);
        
        [sorted, ind] = sort(theseSamples.pointNbr, 'ascend');
        pointStr = sprintf('%d ', sorted);
        labels = [labels; theseSamples.labels(ind)];
        fprintf(s_fid, '%s %s %s %s\n', concatter, sourceFP, targetFile, pointStr);
        
    end
    
end
fclose(s_fid);

%%% run script %%%
if (runScript)
    system(sprintf('sh %s', scriptFilepath));
end

end
