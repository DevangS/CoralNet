function samples = filterImageForDictionary(cs, fileNbr)

% load image
Iorg = imread(fullfile(cs.dataDir, cs.content(fileNbr).imgFile));
I = (imresize(Iorg, 1/cs.params.resizeFactor));

% load the labelMatrix
labelMatrix = readCoralLabelFile(fullfile(cs.dataDir, cs.content(fileNbr).labelFile), cs.params.labelParams);
labelMatrix(:, 1:2) = round(labelMatrix(:,1:2)./cs.params.resizeFactor);

labelMatrix = pruneLabelMatrix(labelMatrix, size(I), max(cs.params.featureParams(1).patchSize) + cs.params.crop.nbrPixels);

if (strcmp(cs.params.featureParams.preprocess.type, 'trueColor'));
    
    ccvalsfile = fullfile(cs.dataDir, strcat(cs.content(fileNbr).labelFile(1:end-3), 'ccvals'));
    cs.params.featureParams.preprocess.ccVals = reshape(dlmread(ccvalsfile), 3,[])';
    
end

FIallChannels = coralApplyFilterWrapper(I, cs.params.featureParams, cs.featurePrep{1}.filterMeta, cs.params.featureParams.filterOutputDim);

nbrSamplesAcc = zeros(1, cs.stats.nbrClasses);
samples = cell(1, cs.stats.nbrClasses);

for i = 1 : cs.stats.nbrClasses
    samples{i} = zeros(200, cs.params.featureParams.filterOutputDim);
end

for k = 1 : size(labelMatrix,1)
    
    nbrSamplesAcc(labelMatrix(k, 3)) = nbrSamplesAcc(labelMatrix(k, 3)) + 1;
    temp = FIallChannels(labelMatrix(k, 1), labelMatrix(k, 2), :);
    samples{labelMatrix(k, 3)}(nbrSamplesAcc(labelMatrix(k, 3)),:) = temp(:)';
    
end

for i = 1 : cs.stats.nbrClasses
    samples{i} = samples{i}(1 : nbrSamplesAcc(i), :);
end


end
