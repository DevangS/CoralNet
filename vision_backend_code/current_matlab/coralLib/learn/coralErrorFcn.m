function [error meta] = coralErrorFcn(CM, params)
% returnes the average of the precision and recall scores,
% which themselves are normalized over all classes.



% in case there are classes missing, remove those.
keepInd = true(size(CM, 1), 1);
for i = 1:size(CM, 1)
    if (sum(CM(i, :)) == 0 && sum(CM(:, i)) == 0)
        keepInd(i) = false;
    end
    
end
CM = CM(keepInd, :);
CM = CM(:, keepInd);

switch(params.type)
    
    case('fscore')
        
        normalizer = sum(CM, 2);
        normalizer(normalizer == 0) = 1;
        CM1 = CM./repmat(normalizer, 1, size(CM, 2));
        
        normalizer = sum(CM, 1);
        normalizer(normalizer == 0) = 1;
        CM2 = CM./repmat(normalizer, size(CM, 1), 1);
        
        recall = sum(diag(CM1))./size(CM1,1);
        precision =  sum(diag(CM2))./size(CM2,1);
        
        fscore = 2 * precision * recall / (precision + recall);
        
        % output 1 - fscore, because we need a minimizer
        error = 1 - fscore;
        meta.recall = diag(CM1);
        meta.precision = diag(CM2);
        
    case('simple')
        
        meta = [];
        error = 1 - sum(diag(CM)) ./ sum(CM(:));
        
end

end