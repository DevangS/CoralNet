function [cps cpm] = fullcell(csparse)

cps = cell(csparse.size);
cpm = zeros(csparse.size);

for i = 1:size(csparse.indexes,1)
    cps(csparse.indexes(i,1),csparse.indexes(i,2)) = csparse.data(i);
    cpm(csparse.indexes(i,1),csparse.indexes(i,2)) = length(csparse.data{i});
end

end