function optStr = makeSolverOptionString(options, weights, labelIndex)

if nargin == 2
    labelIndex = 1 : length(weights);
end

switch options.type
    
    case 'pegasos'
        optStr = sprintf('-lambda %.20f -k %d', exp(options.lambda), exp(options.k));
    case 'libsvm'
        optStr = makeLibsvmOptionString(options.libsvm, weights, labelIndex);
        
    case 'joah'
        optStr = sprintf('-c %.8f', exp(options.joah.C));
        
    case 'steve'
        options.steve.Regularization_0x20__0x28_C_0x29_ = exp(options.steve.Regularization_0x20__0x28_C_0x29_);
        options.steve.Feature_0x20_Scale = exp(options.steve.Feature_0x20_Scale);
        optStr = savejson(' ', options.steve);
        
    case 'liblin'
        optStr = sprintf('-c %.20f -s %d -e %.20f -a %f -b %f', options.C, options.solver, options.epsilon, options.outputTempModels(1), options.outputTempModels(2));
        
    case 'svmmulti'
        optStr = sprintf('-c %.20f -w %d -e %.10f -l %d -i %f -j %f', options.C, options.solver, options.epsilon, options.loss, options.outputTempModels(1), options.outputTempModels(2));
        
    case 'imp'
        optStr = sprintf('-L %.20f -e %.20f -m %s -w %f %f', options.lambda, options.epsilon, options.stepper, options.outputTempModels(1), options.outputTempModels(2));
        
    case 'pegasos_ova'
        optStr = sprintf('-lambda %.20f -a %f -b %f', options.lambda, options.outputTempModels(1), options.outputTempModels(2));
        if(isfield(options, 'niter'))
            optStr = sprintf('%s -iter %f', optStr, options.niter);
        end
    case 'pegasos_multi'
        optStr = sprintf('-lambda %.20f -a %f -b %f', options.lambda, options.outputTempModels(1), options.outputTempModels(2));
        if(isfield(options, 'niter'))
            optStr = sprintf('%s -iter %f', optStr, options.niter);
        end
        
end

end

function optStr = makeLibsvmOptionString(options, weights, labelIndex)

% set weight string
weightstr = [];
for thisClass = 1 : length(weights)
    weightstr = [weightstr '-w', num2str(labelIndex(thisClass)), ' ', num2str(weights(thisClass)), ' ']; %#ok<AGROW>
end

if ~isfield(options, 'type')
    options.type = 2;
end
if ~isfield(options, 'degree')
    options.degree = 2;
end
if ~isfield(options, 'coef0')
    options.coef0 = 0;
end
if ~isfield(options, 'quiet')
    options.quiet = 0;
end

% merge to options string.
optStr = sprintf('-t %d -d %d -g %.4f -r %.4f -c %.4f -b %d %s', options.type, options.degree, exp(options.gamma), options.coef0, exp(options.C), options.prob, weightstr);

if (options.quiet)
    optStr = [optStr '-q '];
end


end
