function labels = readCoralLabelFile(labelFile, labelParams)
% function labels = readCoralLabelFile(labelFile, labelParams)
%
% INPUT: labelFile. File containing the labels and coordinates.
% INPUT: labelParams[struct]. Fields:
%    labelParams.catsOrg is the names of the categories in the labelfiles
%    labelparams.id maps the catsOrg to an integer value. Note that
%    this can be a many-to one mapping.
%
labels = [];
lp = labelParams;
pos = 0;
fid = fopen(labelFile, 'r');

line = fgetl(fid);
while(line ~= -1)
    
    if(~strcmp(strtrim(line(1)), '#'))

        % parse string
        [row col label] = strread(line, '%d%d%s', 'delimiter', ';');
        
        % match against the wanted categories
        ind = strcmpi(label, lp.catsOrg);
        if (sum(ind) ~= 0) %if this is one of the label we want to use.
            pos = pos + 1;
            labels(pos, 1) = row;
            labels(pos, 2) = col;
            labels(pos, 3) = lp.id(ind); %set the label id.
        end
    end
    line = fgetl(fid);
end

fclose(fid);

end