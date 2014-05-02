function dataOut = mergeData(dataOne, dataTwo)
% dataOut = mergeData(dataOne, dataTwo)
% takes two data structs and stack all fields.

for thisField = rowVector(fieldnames(dataOne))
    dataOut.(thisField{1}) = [dataOne.(thisField{1}) ; dataTwo.(thisField{1})];
end



end