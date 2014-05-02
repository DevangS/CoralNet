function normalizer = getFeatureNormalizationFromDisk(inputDir, outputDir, files, nFeatPerFile, nDims)

global logfid;
logfid = fopen(fullfile(outputDir, 'log'), 'w');

if(exist(fullfile(outputDir, 'normalizer.mat'), 'file'))
    fclose(logfid);
    load(fullfile(outputDir, 'normalizer.mat'));
    return
end

allFeatures = zeros(nFeatPerFile * length(files), nDims);
pos = 0;

for f = files
    inputFile = fullfile(inputDir, sprintf('file%d.dat', f));
    fprintf(logfid, 'Processing file: %s\n', inputFile);
    [~, features] = libsvmread(GetFullPath(inputFile));
    ffull = full(features);
    nFeat = size(ffull, 1);
    allFeatures(pos + 1: pos + nFeat, 1 : size(ffull, 2)) = ffull;
    pos = pos + nFeat;

end

allFeatures = allFeatures(1:pos, :);

normalizer = max(allFeatures);
save(fullfile(outputDir, 'normalizer'), 'normalizer');
fclose(logfid);
end