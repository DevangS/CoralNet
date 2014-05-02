function [coverage fromfileOut] = getCoverageFromPoints(labels, fromfileIn, nbrClasses, fileNbrs)
% [coverage fromfileOut] = getCoverageFromPoints(labels, fromfileIn,
% nbrClasses)
if nargin<4
    fileNbrs = unique(fromfileIn);
end

nbrFiles = length(fileNbrs);
fromfileOut = zeros(nbrFiles, 1);
coverage = zeros(nbrFiles, nbrClasses);

for itt = 1 : nbrFiles
    fileNbr = fileNbrs(itt);
    fromfileOut(itt) = fileNbr;
    theseLabels = labels(fromfileIn == fileNbr);
    if isempty(theseLabels)
        coverage(itt, :) = ones(1, nbrClasses) / nbrClasses;
        warning('No annotations for file %d', fileNbr);
    else
        n = hist(labels(fromfileIn == fileNbr), 1 : nbrClasses);
        coverage(itt, :) = n ./ sum(n); %normalized histogram count!
    end
end

end