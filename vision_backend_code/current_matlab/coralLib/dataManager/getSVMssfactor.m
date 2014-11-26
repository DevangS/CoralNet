function [ssfactor stats] = getSVMssfactor(data, targetNbrSamplesPerClass, labelMap)

nbrClasses = length(labelMap);

% Prepare the train data and model weights.
% find subsamples factors for the train data.
for itt = 1 : nbrClasses
    thisClass = labelMap(itt);
    stats.nbrTotalSamples(itt) = sum(data.labels == thisClass);
    stats.ssfactor(itt) = max(1, stats.nbrTotalSamples(itt) / targetNbrSamplesPerClass);
    stats.nbrTrainSamples(itt) = stats.nbrTotalSamples(itt) / stats.ssfactor(itt);
end

ssfactor = stats.ssfactor;

end