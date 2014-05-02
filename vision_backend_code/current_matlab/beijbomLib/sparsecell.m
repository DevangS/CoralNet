function csparse = sparsecell(c)


cpm = zeros(size(c));
for i = 1:size(c,1)
    for j = 1:size(c,2)
        if isempty(c{i,j})
            cpm(i,j) = 0;
        else
            cpm(i,j) = length(c{i,j});
        end
    end
end

csparse.data = cell(1,sum(sum(cpm > 0)));
csparse.indexes = zeros(length(csparse.data),2);
csparse.size = size(c);
pos = 1;

for i = 1:size(c,1)
    for j = find(cpm(i,:) > 0)
        if cpm(i,j) > 0
            csparse.indexes(pos,1) = i;
            csparse.indexes(pos,2) = j;
            csparse.data(pos) = c(i,j);
            pos = pos + 1;
        end
    end
end

