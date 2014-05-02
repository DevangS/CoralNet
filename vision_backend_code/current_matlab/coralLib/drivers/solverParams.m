function svmParams = solverParams(type)

svmParams.crossVal.nbrFolds = 2;
svmParams.crossVal.stepSize = 4;
svmParams.crossVal.maxRuntime = 6 * 60 * 60;

switch type
    
    case 'libsvm'
        svmParams.targetNbrSamplesPerClass = 7500;
        
        svmParams.gridParams.start = [-2 -1];
        svmParams.gridParams.range.min = [-5 -5];
        svmParams.gridParams.range.max = [5 5];
        svmParams.gridParams.stepsize = [1 1];
        svmParams.gridParams.edgeLength = 3;

        svmParams.plantHandle = @libsvmStandardPlant;
        svmParams.collectHandle = @libsvmStandardCollect;
        
        svmParams.commitoptions = '-l exclusive=2,mem_free=3G ';
        svmParams.maxRuntime = 10 * 60 * 60;
        
        svmParams.options.libsvm.gamma = -2;
        svmParams.options.libsvm.C = -1;
        svmParams.options.libsvm.prob = 0;
        
    case 'pegasos'
        svmParams.targetNbrSamplesPerClass = inf;
        
        svmParams.gridParams.start = [-12 0];
        svmParams.gridParams.range.min = [-25 0];
        svmParams.gridParams.range.max = [-3 0];
        svmParams.gridParams.stepsize = [1 0];
        svmParams.gridParams.edgeLength = 25;
        svmParams.plantHandle = @pegasosOvaPlant;
        svmParams.collectHandle = @pegasosOvaCollect;
        
        svmParams.commitoptions = '-l exclusive=2,mem_free=3G ';
        svmParams.maxRuntime = 10 * 60 * 60; % 10 hours
    case 'joah'
        svmParams.targetNbrSamplesPerClass = inf;
        
        svmParams.gridParams.start = [10 0];
        svmParams.gridParams.range.min = [-20 0];
        svmParams.gridParams.range.max = [20 0];
        svmParams.gridParams.stepsize = [1 0];
        svmParams.gridParams.edgeLength = 5;
        svmParams.plantHandle = @joahPlant;
        svmParams.collectHandle = @joahCollect;
        
        svmParams.commitoptions = '-l exclusive=2,mem_free=7G ';
        svmParams.maxRuntime = 10 * 60 * 60; % 10 hours
    case 'steve'
        svmParams.targetNbrSamplesPerClass = inf;
        
        svmParams.gridParams.start = [10 0];
        svmParams.gridParams.range.min = [-20 0];
        svmParams.gridParams.range.max = [20 0];
        svmParams.gridParams.stepsize = [1 0];
        svmParams.gridParams.edgeLength = 9;
        svmParams.plantHandle = @stevePlant;
        svmParams.collectHandle = @steveCollect;
        
        svmParams.commitoptions = '-l exclusive=2,mem_free=3G ';
        svmParams.maxRuntime = 60 * 60; % 1 hour.
        svmParams.crossVal.maxRuntime = 60 *30; % 30 mins.
end

svmParams.options.type = type;

end




