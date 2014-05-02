function out = splitData(data, fileIds)
% out = splitData(data, fileIds)

allFields = rowVector(fields(data));
out = data;
for f = allFields
    out.(f{1}) = out.(f{1})(1,:);
end
pos = 0;
for i = 1 : length(fileIds)
    id = fileIds(i);
    ids = (data.fromfile == id);
    nbrSamples = sum(ids);
    
    for f = allFields
        out.(f{1})(pos + 1: pos + nbrSamples, :) = data.(f{1})(ids, :);
    end
    pos = pos + nbrSamples;
    
end
for f = allFields
    out.(f{1}) = out.(f{1})(1 : pos, :);
end

end