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