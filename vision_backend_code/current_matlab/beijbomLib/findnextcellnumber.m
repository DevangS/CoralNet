function nbr = findnextcellnumber(thisstruct, thiscell)

if isfield(thisstruct, thiscell)
    temp = thisstruct.(thiscell);

    nbr = length(temp) + 1;

else
    nbr = 1;
end