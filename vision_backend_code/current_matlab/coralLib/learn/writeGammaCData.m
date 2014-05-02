function [testLabelsTrue, ssStats] = writeGammaCData(svmParams, localDataDir, targetDir, allData)

fileNbrs = unique(allData.fromfile);
nbrFiles = length(fileNbrs);

tempTargetFileDir = fullfile('/home/beijbom/.concatscripts/', datestr(now, 30));
mkdir(tempTargetFileDir);
tempTargetFile = fullfile(tempTargetFileDir, 'target.txt');

% generate and write data.
for cvNbr = 1 : svmParams.crossVal.nbrFolds
    
    trainIds = true(nbrFiles, 1);
    trainIds(cvNbr : svmParams.crossVal.stepSize : end) = false;
    trainData = splitData(allData, fileNbrs(trainIds));
    testData = splitData(allData, fileNbrs(~trainIds));
    
    % subsample trainData and write to disk.
	[ssfactor ssStats{cvNbr}] = getSVMssfactor(trainData, svmParams.targetNbrSamplesPerClass);
    trainData = subsampleDataStruct(trainData, ssfactor);
    logger(sprintf('Writing CV:%d trainData', cvNbr));
    
    targetFile = fullfile(targetDir, sprintf('CV%d_train', cvNbr));
    concatSelect(tempTargetFile , localDataDir, trainData, svmParams.targetNbrSamplesPerClass == inf, 1);
    
    logger(sprintf('Copying CV:%d trainData', cvNbr));
    system(sprintf('cp %s %s', tempTargetFile, targetFile));
    
    % Write testData to disk.
    logger(sprintf('Writing CV:%d testData', cvNbr));

    targetFile = fullfile(targetDir, sprintf('CV%d_test', cvNbr));
    concatSelect(tempTargetFile , localDataDir, testData, 1, 1);
    
    logger(sprintf('Copying CV:%d testData', cvNbr));
    system(sprintf('cp %s %s', tempTargetFile, targetFile));
    system(sprintf('rm %s', tempTargetFile));
    % output the ground truth labels.
    testLabelsTrue{cvNbr} = testData.labels; %#ok<AGROW>
    
end

end
