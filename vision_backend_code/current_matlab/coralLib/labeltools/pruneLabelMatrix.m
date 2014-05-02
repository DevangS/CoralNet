function labelMatrix = pruneLabelMatrix(labelMatrix, imgSize, pruneSize)

% prune the labelMatrix
maxRow = imgSize(1) - pruneSize;
maxCol = imgSize(2) - pruneSize;
minRow = 1 + pruneSize;
minCol = 1 + pruneSize;

% remove samples to close to the edge.
edgeIndexes = (labelMatrix(:,1) <= minRow | ...
    labelMatrix(:,2) <= minCol | ...
    labelMatrix(:,1) > maxRow | ...
    labelMatrix(:,2) > maxCol);
labelMatrix = labelMatrix(~edgeIndexes, :);

end