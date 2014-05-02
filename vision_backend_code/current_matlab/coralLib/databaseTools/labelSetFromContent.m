function [labelSet count] = labelSetFromContent(content, dataDir)

labelSet = {};
count = [];
for fileItt = 1 : length(content)
    
    d = parseTxtFile(fullfile(dataDir, content(fileItt).labelFile), 15);
    
    for i = 1 : length(d)
        
        thisLabel = d(i).type;
        ind = strcmp(thisLabel, labelSet);
        if (sum(ind) == 0)
            labelSet = [labelSet {thisLabel}];
            count = [count 1];
        else
            count(ind) = count(ind) + 1;
        end
        
    end
    
    
end

[~, ind] = sort(count, 'descend');
count = count(ind);
labelSet = labelSet(ind);

end