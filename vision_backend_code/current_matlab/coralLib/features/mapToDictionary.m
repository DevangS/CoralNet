function map = mapToDictionary(I, dictionary)
% I is column stacked images, basically foramtted to work with pdist2

map = zeros(size(I, 1), 1);
% divide in 100 parts
P = round(linspace(0, size(I,1), 100));

for i = 2 : length(P)
    thisChunk = I(P(i-1) + 1 : P(i), :);
    dist = pdist2(thisChunk, dictionary, 'sqeuclidean' );
    [~, map(P(i-1) + 1 : P(i), :)] = min(dist, [], 2);
end

end