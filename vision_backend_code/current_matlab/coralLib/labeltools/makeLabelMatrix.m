function labels = makeLabelMatrix(labelStruct, labelParams)

cats = labelParams.names; %we use the 'name' field here, the 'cats' field refers to the actual categories.
field = labelParams.field;
id = labelParams.id;
labels = zeros(length(labelStruct), 3);
pos = 0;
for i = 1:length(labelStruct)
    
    ind = strcmpi(labelStruct(i).(field), cats);
    if (sum(ind) ~= 0)
        pos = pos + 1;
        labels(pos, 3) = id(strcmpi(labelStruct(i).(field), cats));
        labels(pos, 1) = labelStruct(i).row;
        labels(pos, 2) = labelStruct(i).col;
    end
    
    
end

labels = labels(1:pos, :);

end