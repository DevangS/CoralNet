function modelStruct = ovaTrain(data, rootDir, targetNbrSamplesPerClass, libsvmoptions)


labelsIds = unique(data.labels);
nbrClasses = length(labelsIds);

modelStruct = struct('model', [], 'labelid', [], 'stats', []);
for i = 1 : nbrClasses
    logger(sprintf('Training classifier for class %d', i));
    labelid = labelsIds(i);
    this.labels = zeros(size(data.labels));
    this.models = data.models;
    this.labels(data.labels == labelid) = 1;
    this.labels(data.labels ~= labelid) = 2; 
    % The 1 - 2 labelling thing, is a technicality of libsvm. This way a 
    % positive dec value will correspond to the data.labels == labelid.
    
    %reorder labels and data
    trueIndex = (this.labels == 1);
    this.labels = [this.labels(trueIndex); this.labels(~trueIndex)];
    this.models = [this.models(trueIndex, :); this.models(~trueIndex, :)];
  
    %subsample
    [ssfactor, stats] = getSVMssfactor(this, targetNbrSamplesPerClass);
    this = subsampleDataStruct(this, ssfactor);
     
    optStr = makeLibsvmOptionString(libsvmoptions, ssfactor);
    
    logger('Writing train data to disk...');
    writeLibsvmDatafile(this.models, this.labels, fullfile(rootDir, 'train.txt'));
    logger('done.');
    modelFile = fullfile(rootDir, sprintf('modelOVA%d.txt', i));
    logger('Training SVM...')
    system(sprintf('~/e/Code/apps/libsvm/svm-train %s %s %s', optStr, fullfile(rootDir, 'train.txt'), modelFile));
    logger('done.')
    

    modelStruct(i).modelFile = modelFile;
    modelStruct(i).labelid = labelid;
    modelStruct(i).stats = stats;
    
end
delete(fullfile(rootDir, 'train.txt'));

end

