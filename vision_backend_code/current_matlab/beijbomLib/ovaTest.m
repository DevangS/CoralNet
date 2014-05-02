function [labels decMatrix] = ovaTest(modelStruct, testData, rootDir)

nbrClasses = length(modelStruct);
nbrSamples = size(testData.models, 1);
decMatrix = zeros(nbrSamples, nbrClasses);
logger('Writing test data');
writeLibsvmDatafile(testData.models, testData.labels, fullfile(rootDir, 'test.txt'));

for i = 1 : nbrClasses
    logger(sprintf('Classifying class %d', i));

    system(sprintf('~/e/Code/apps/libsvm/svm-predict-decval -b %d %s %s %s', 0, fullfile(rootDir, 'test.txt'),  modelStruct(i).modelFile,  fullfile(rootDir, 'testDecvals.txt')));
    delete(modelStruct(i).modelFile);
    decMatrix(:,i) = load(fullfile(rootDir, 'testDecvals.txt'));
    
end

[~, labels] = max(decMatrix, [], 2);

delete(fullfile(rootDir, 'test.txt'));
delete(fullfile(rootDir, 'testDecvals.txt'));

end



%     [dummy, decMatrix(:,i)] = feval(handle, testData.models,
%     modelStruct(i).model);