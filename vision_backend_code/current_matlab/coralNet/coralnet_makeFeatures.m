function coralnet_makeFeatures(preProcessedImageFile, featureFile, rowColFile, ssFile, preProcessParameterFile, logFile, errorLogfile)

global logfid

try
    
    logfid = fopen(logFile, 'a');
    
    subsampleRate = dlmread(ssFile);
    
    load(preProcessedImageFile);
    load(preProcessParameterFile);
    
    rowCol = load(rowColFile);
    rowCol = round(rowCol./subsampleRate);
    
    patchSize = coralnetPreprocessParams.featureParams.patchSize;
    nbrPoints = size(rowCol, 1);
    
    textons = mergeCellContent(coralnetPreprocessParams.featurePrep{1}.textons);
    nbrTextons = size(textons, 1);
    
    features = zeros(nbrPoints, nbrTextons * length(patchSize));
    [maxRow maxCol] = size(textonMap);
    imageNbrStr = rowColFile(regexp(rowColFile, '\d*_rowCol') : regexp(rowColFile, '_rowCol') -1 );
   
    logger('Image %s is [%d rows by %d cols] and has %d random points', imageNbrStr, maxRow, maxCol, nbrPoints);
    
    for point = 1 : nbrPoints
        
        for psInd = 1 : length(patchSize)
            
            thisPatchSize = patchSize(psInd);
            
            rows = (rowCol(point, 1) - thisPatchSize) : (rowCol(point, 1) + thisPatchSize);
            cols = (rowCol(point, 2) - thisPatchSize) : (rowCol(point, 2) + thisPatchSize);
            
            rows = rows(rows > 0 & rows <= maxRow);
            cols = cols(cols > 0 & cols <= maxCol);
            
            patch = textonMap(rows, cols);
            
            featVector = hist(patch(:), 1 : nbrTextons);
            
            features(point, (psInd - 1) * nbrTextons + 1 : psInd * nbrTextons) = featVector ./ sum(featVector);
            
        end
        
    end
    
    writeLibsvmDatafile(features, ones(nbrPoints, 1), featureFile);
    fclose(logfid);
    
catch me
    
    fid = fopen(errorLogfile, 'a');
    fprintf(fid, '[%s] Error executing coralnet_makeFeatures: %s, %s \n', datestr(clock, 31), me.identifier, me.message);
    fclose(fid);
    fclose(logfid);
    
end

end