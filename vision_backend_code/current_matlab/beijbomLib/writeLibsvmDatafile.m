function writeLibsvmDatafile(data, labels, filepath)
% function writeLibsvmDatafile(data, labels, filepath)

fid = fopen(filepath, 'w');

for row = 1:size(data, 1)
    
    if(~(isempty(labels)))
        thisStr = sprintf('%.3g ', labels(row));
    else
        thisStr = '';
    end
    
    for col = 1:size(data, 2)
        if ~(data(row,col) == 0)
            thisStr = sprintf('%s%d:%.6g ', thisStr, col, data(row, col));
        end
    end
    fprintf(fid, '%s\n', thisStr);
    
end
fclose(fid);

end