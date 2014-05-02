function [labelGroups, LGcount] = mapLabelsToGroups(mapping, labelSet, count)

labelGroups = {};
LGcount = [];
for i = 1 : length(mapping)
    
    ind = strcmp(mapping(i).label, labelSet);
    if(sum(ind) == 0)
        continue;
    end
   
    fgInd = strcmp(mapping(i).fg, labelGroups);
    
    if(sum(fgInd) == 0)
        labelGroups = [labelGroups, {mapping(i).fg}];
        LGcount = [LGcount count(ind)];
    else
        LGcount(fgInd) = LGcount(fgInd) + count(ind);
    end
    
end

[~, ind] = sort(LGcount, 'descend');
LGcount = LGcount(ind);
labelGroups = labelGroups(ind);


end