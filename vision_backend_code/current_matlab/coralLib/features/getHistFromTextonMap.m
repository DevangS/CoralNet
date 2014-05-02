function features = getHistFromTextonMap(textonMap, rowCol, patchSize, nbrTextons, framecrop)
% function features = getHistFromTextonMap(textonMap, rowCol, patchSize,
% nbrTextons, framecrop)

if nargin < 5
    framecrop.do = false;
end

nbrPoints = size(rowCol, 1);
features = [];
[maxRow maxCol] = size(textonMap);
for point = 1 : nbrPoints
    
    for psInd = 1 : length(patchSize)
        
        thisPatchSize = patchSize(psInd);
        
        rows = (rowCol(point, 1) - thisPatchSize) : (rowCol(point, 1) + thisPatchSize);
        cols = (rowCol(point, 2) - thisPatchSize) : (rowCol(point, 2) + thisPatchSize);
        
        if framecrop.do
            
            thisMinRow = max(min(framecrop.size, rowCol(point, 1) - 10), 0); %larger than 0 and at least 10 rows from the point.
            thisMinCol = max(min(framecrop.size, rowCol(point, 2) - 10), 0); 
            thisMaxRow = min(max(maxRow - framecrop.size, rowCol(point, 1) + 10), maxRow);
            thisMaxCol = min(max(maxCol - framecrop.size, rowCol(point, 2) + 10), maxCol);
            
            rows = rows(rows > thisMinRow & rows <= thisMaxRow);
            cols = cols(cols > thisMinCol & cols <= thisMaxCol);
            
        else
            
            rows = rows(rows > 0 & rows <= maxRow);
            cols = cols(cols > 0 & cols <= maxCol);
            
        end
        patch = textonMap(rows, cols);
        
        featVector = hist(patch(:), 1 : nbrTextons);
        
        features(point, (psInd - 1) * nbrTextons + 1 : psInd * nbrTextons) = featVector ./ sum(featVector);
        
    end
    
end

end