function coralnet_preprocessImage(imageFile, preProcessedImageFile, preProcessParameterFile, ssFile, logFile, errorLogfile)

global logfid

try
    
    logfid = fopen(logFile, 'a');
    
    % load parameter file
    load(preProcessParameterFile);
    
    % load image
    Iorg = imread(imageFile);
    
    % make sure the image has three channels
    if (size(Iorg, 3) == 1)
        Iorg = repmat(Iorg, [1 1 3]);
    end
    
    subsampleRate = dlmread(ssFile);
    
    imageNbrStr = ssFile(regexp(ssFile, '\d*_ssRate') : regexp(ssFile, '_ssRate') -1 );
    
    logger('Preprocessing image %s with SSrate %.3f', imageNbrStr, subsampleRate);
    
    % process image
    I = (imresize(Iorg, 1/subsampleRate));
    textonMap = extractTextonMap(coralnetPreprocessParams.featureParams, coralnetPreprocessParams.featurePrep{1}, I); %#ok<NASGU>
    
    save(preProcessedImageFile, 'textonMap');
    
    fclose(logfid);
    
catch me
    
    fid = fopen(errorLogfile, 'a');
    fprintf(fid, '[%s] Error executing coralnet_preprocessImage: %s, %s, %s, %d \n', datestr(clock, 31), me.identifier, me.message, me.stack(1).file, me.stack(1).line);
    logger('[%s] Error executing coralnet_preprocessImage: %s, %s, %s, %d \n', datestr(clock, 31), me.identifier, me.message, me.stack(1).file, me.stack(1).line);
    fclose(fid);
    fclose(logfid);
    
end

end

