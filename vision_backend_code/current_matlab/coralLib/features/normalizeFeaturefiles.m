function normalizeFeaturefiles(inputDir, outputDir, files, fromfile)
filelogPath = fullfile(outputDir, 'filelog.mat');
if(~exist(filelogPath, 'file'))
    filelog = zeros(max(files), 1);
    save(filelogPath, 'filelog');
end

load(filelogPath);
load(fullfile(outputDir, 'normalizer.mat'));
global logfid
logfid = fopen(fullfile(outputDir, 'log'), 'a');

logger('=============== new run ================');
normsparse = sparse(normalizer);

for f = files
    
    if(mod(f, 10) == 0)
        save(filelogPath, 'filelog');
    end
    
    if (filelog(f) == 1 || filelog(f) == 2 )
        continue
    end
    
    logger(sprintf('%d...', f));
    
    inputFile = fullfile(inputDir, sprintf('file%d.dat', f));
    if(~exist(inputFile, 'file'))
        filelog(f) = 2;
        logger(('Inputfile doesnt exist.'));
        continue;
    end
    copiedFile = fullfile(outputDir, sprintf('file%d.dat', f));
    copyok = copyfile(inputFile, copiedFile);
    if(~copyok)
        filelog(f) = 3;
        logger(('Error copying input file.'));
        continue
    end
    [labels features] = libsvmread(copiedFile);
    if (length(labels) ~= sum(fromfile == f))
        filelog(f) = 4;
        logger(('Inputfile does not contain all the data.'));
        continue
    end
    
    nDims = size(features, 2);
    
    outputFile = fullfile(outputDir, sprintf('file%dn.dat', f));
    features = features ./ repmat(normsparse(1:nDims), size(features, 1), 1);
    libsvmwrite(outputFile, labels, features);
    filelog(f) = 1;
    logger('Done');
    
    
    
end
save(filelogPath, 'filelog');
end
%
% function normalizeFeaturefiles(inputDir, rootDir, reds, greens, files, dataPath)
% filelogPath = fullfile(rootDir, 'filelog.mat');
% load(filelogPath);
% load(fullfile(rootDir, 'normalizer.mat'));
% load(dataPath);
% global logfid
% logfid = fopen(fullfile(rootDir, 'log'), 'a');
% fromfile = cs.data.fromfile;
% logger('=============== new run ================');
% normsparse = sparse(normalizer);
% for r = reds
%     for g = greens
%         outputDir = fullfile(rootDir, sprintf('r%d_g%d', r, g));
%         mkdir(outputDir);
%         for f = files
%             if (filelog(r,g,f) == 1 || filelog(r,g,f) == 2 )
%                 continue
%             end
%
%             logger(sprintf('%d, %d, %d...', r,g,f));
%
%             inputFile = fullfile(inputDir, sprintf('r%d_g%d', r, g), sprintf('file%d.dat', f));
%             if(~exist(inputFile, 'file'))
%                 filelog(r,g,f) = 2;
%                 logger(('Inputfile doesnt exist.'));
%                 continue;
%             end
%             copiedFile = fullfile(outputDir, sprintf('file%d.dat', f));
%             copyok = copyfile(inputFile, copiedFile);
%             if(~copyok)
%                 filelog(r,g,f) = 3;
%                 logger(('Error copying input file.'));
%                 continue
%             end
%             [labels features] = libsvmread(copiedFile);
%             if (length(labels) ~= sum(fromfile == f))
%                 filelog(r,g,f) = 4;
%                 logger(('Inputfile does not contain all the data.'));
%                 continue
%             end
%
%             nDims = size(features, 2);
%
%             outputFile = fullfile(outputDir, sprintf('file%dn.dat', f));
%             features = features ./ repmat(normsparse(1:nDims), size(features, 1), 1);
%             libsvmwrite(outputFile, labels, features);
%             filelog(r,g,f) = 1;
%             logger('Done');
%
%             if(mod(f, 10) == 0)
%                 save(filelogPath, 'filelog');
%             end
%
%         end
%         save(filelogPath, 'filelog');
%     end
% end
%
% end