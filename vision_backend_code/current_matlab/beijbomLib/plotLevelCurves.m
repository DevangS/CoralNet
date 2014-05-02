function handles = plotLevelCurves(handles, visitedPoints, fValues, labels, refParam)
% handles = plotLevelCurves(handles, visitedPoints, fValues, labels,
% refParam)
% plots level curves for a three dimensional gridsearch. Can handle two dimensional
% inputs as well in which case it returns a single level curve
%
% input:
%
% visitedPoints: [n by 1, 2 or 3] matrix with visited points
% fValues: [n by 1] vector with function values
% labels: {n} cell structure with strings defining input labels.
% (optional) [scalar] refParam indicate for the three dimensional situation
% which dimension is to define the level curves. Default = 1.
%
% output:
%
% handles: handles to the created figures
%
% Created 27 february 2009 by Oscar Beijbom
%

if (nargin < 5)
    refParam = 1;
end

if (size(visitedPoints,1) ~= size(fValues,1))
    error('Nbr rows in visitedPoints not equal to nbr rows in fValues.')
end

if (size(visitedPoints,2) ~= length(labels))
    error('Nbr colums in visitedPoints not equal to nbr of labels.')
end

if (refParam > size(visitedPoints, 2))
    error('refParams is lager than nbr columns in visitedPoints')
end

ndims = length(labels);

%r�knar fram antal niv�er
levels = unique(visitedPoints(:,refParam));
nLevels = length(levels);

% l�gger till funktionsv�rdena i en extra kolumn.
visitedPoints = [visitedPoints fValues];

% tar bort kolumnen med den parameter som kommer bli niv�kurvorna.
visitedPointsRed = visitedPoints(:, 1 : ndims + 1 ~= refParam);

% plockar fram r�tt ettiketter.
if (ndims == 2)
    levelLabel = 'LevelCurves';
    nLevels = 1;
    visitedPointsRed = visitedPoints;
else
    levelLabel = labels{refParam};
    labels = labels(1:3 ~= refParam);
end
xLabel = labels{1};
yLabel = labels{2};


for i = 1 : nLevels

    handles(i) = figure(handles(i));
    if (ndims == 2)
        pointsIndexes = true(size(visitedPoints, 1),1);
    else
        pointsIndexes = visitedPoints(:,refParam) == levels(i);
    end
    thisPoints = visitedPointsRed(pointsIndexes,:);
    x = sort(unique(thisPoints(:,1)));
    y = sort(unique(thisPoints(:,2)));
    z = zeros(length(y), length(x));

    for j = 1:size(thisPoints,1)
        xpos = (x == thisPoints(j,1));
        ypos = (y == thisPoints(j,2));
        z(ypos,xpos) = thisPoints(j,3);
    end

    % fyller i z med interpolerade v�rden.
    for mm = 1:3
        for m = 1 : size(z,1)
            for n = 1 : size(z,2)
                if (z(m,n) == 0)
                    nbrs = getNeighbours(z,[m n]);
                    if (length(nbrs) > 2)
                        z(m,n) = mean(nbrs);
                    end
                end
            end
        end
    end

    [C,h] = contour(x,y,z);
    set(h,'ShowText','on','TextStep',get(h,'LevelStep')*1)
    grid
%     colormap(jet);
%     colorbar;
%     title([levelLabel ' = ' num2str(levels(i))]);
    xlabel(xLabel);
    ylabel(yLabel);
    hold on
    plot(thisPoints(:,1), thisPoints(:,2), 'bo');
    plot(thisPoints(:,1), thisPoints(:,2), 'r*');
end

end

function n = getNeighbours(z, coords)
pos = 1;
n = 1;
for i = coords(1) - 1 : 1 : coords(1) + 1
    for j = coords(2) - 1 : 1 : coords(2) + 1
        if (j < 1 ) || (j > size(z,2)) || (i < 1 ) || (i > size(z,1)) || (z(i,j) == 0)
            continue;
        end
        n(pos) = z(i,j); pos = pos + 1;
    end
end
end