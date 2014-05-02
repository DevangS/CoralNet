function matrixOut = mergeCellContent(cellIn)
% merge cell content to one matrix.
matrixOut = [];
for i = 1:length(cellIn)
    matrixOut  = [matrixOut ; cellIn{i}]; %#ok<AGROW>
end

end