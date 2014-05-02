function dataOut = subsampleDataStruct(dataIn, ssfactor)

classes = unique(dataIn.labels);
nbrClasses = length(classes);

% subsample dataOut and labels
dataOut = dataIn;
for thisField = rowVector(fieldnames(dataOut))
   dataOut.(thisField{1}) = []; 
end

for itt = 1 : nbrClasses
    thisClass = classes(itt);
    for thisField = rowVector(fieldnames(dataOut))
        temp.(thisField{1}) = dataIn.(thisField{1})(dataIn.labels == thisClass, :);
        indexes = round(1 : ssfactor(itt) : size(temp.(thisField{1}), 1));
        dataOut.(thisField{1}) = [dataOut.(thisField{1}); temp.(thisField{1})(indexes, :)];
    end
end

end