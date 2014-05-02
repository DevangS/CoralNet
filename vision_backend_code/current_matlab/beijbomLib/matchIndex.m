function ind = matchIndex(vector, entries)

ind = false(size(vector));
for i = 1:length(entries)
    ind = ind | vector == entries(i);
end
      
end