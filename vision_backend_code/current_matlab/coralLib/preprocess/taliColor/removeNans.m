
function [new_vals good_rows]=removeNans(vals)

[m n]=find(isnan(vals));
bad_rows=unique(m);
good_rows= setdiff(1:size(vals,1), bad_rows);

if (isempty(good_rows))
    new_vals=[];
else
    new_vals=vals(good_rows,:);
end