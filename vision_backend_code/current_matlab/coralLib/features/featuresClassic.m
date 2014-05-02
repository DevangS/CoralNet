function dataOut = featuresClassic(cs, fileNbr)
% function dataOut = featuresClassic(cs, fileNbr)

dataOut.fromfile = [];
dataOut.features = [];
dataOut.labels = [];
dataOut.rowCol = [];
dataOut.pointNbr = [];

% load image
Iorg = imread(fullfile(cs.dataDir, cs.content(fileNbr).imgFile));
I = (imresize(Iorg, 1/cs.params.resizeFactor));

% load the labelMatrix
labelMatrix = readCoralLabelFile(fullfile(cs.dataDir, cs.content(fileNbr).labelFile), cs.params.labelParams);
if(isempty(labelMatrix))
    return
end
labelMatrix(:, 1:2) = round(labelMatrix(:,1:2)./cs.params.resizeFactor);
if (cs.params.crop.do)
    labelMatrix = pruneLabelMatrix(labelMatrix, size(I), max(cs.params.featureParams(1).patchSize) + cs.params.crop.nbrPixels);
end

rowCol = labelMatrix(:, 1:2);

if (strcmp(cs.params.featureParams.preprocess.type, 'trueColor'));
    
    ccvalsfile = fullfile(cs.dataDir, strcat(cs.content(fileNbr).labelFile(1:end-3), 'ccvals'));
    cs.params.featureParams.preprocess.ccVals = reshape(dlmread(ccvalsfile), 3,[])';
    
end

features = getMultiPatchFeatures(cs.params.featureParams, cs.featurePrep{1}, I, rowCol);

% add location key features
if (isfield(cs.params.featureParams, 'locationKeys') && cs.params.featureParams.locationKeys.do == 1)
    locFeatures = getLocFeatures(cs.content(fileNbr), cs.params.featureParams.locationKeys);
    features = [features repmat(locFeatures, size(labelMatrix, 1), 1)];
end

% store the results.
nfeatures = size(features, 1);
dataOut.fromfile = repmat(fileNbr, nfeatures, 1);
dataOut.features = features;
dataOut.labels = labelMatrix(:, 3);
dataOut.rowCol = rowCol;
dataOut.pointNbr = (1 : nfeatures)';

end

function locFeatures = getLocFeatures(c, locParams)

for i = 1 : length(locParams.key)
    locFeatures(i) = find(strcmp(c.(locParams.key(i).field), locParams.key(i).value)) ./ length(locParams.key(i).value);
end

end

function features = getMultiPatchFeatures(featureParams, featurePrep, I, rowCol)

% extract local features
textons = mergeCellContent(featurePrep.textons(1, :));
nbrTextons = size(textons, 1);
patchSize = [featureParams.patchSize];

% extract textonMap
textonMap = extractTextonMap(featureParams, featurePrep, I);

% pool textonMap to features.     
if (isfield(featureParams, 'framecrop'))
    features = getHistFromTextonMap(textonMap, rowCol, patchSize, nbrTextons, featureParams.framecrop);
else
    features = getHistFromTextonMap(textonMap, rowCol, patchSize, nbrTextons);
end
end