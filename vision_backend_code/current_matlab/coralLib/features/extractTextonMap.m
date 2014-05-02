function textonMap = extractTextonMap(featureParams, featurePrep, I)
% function textonMap = extractTextonMap(featureParams, featurePrep, I)

% set local structs.
textons = mergeCellContent(featurePrep.textons(1, :));
totalNbrChannels =  size(textons, 2);

% filter image
FIallChannels = coralApplyFilterWrapper(I, featureParams, featurePrep.filterMeta, totalNbrChannels);



% create texton map
[nbrRows nbrCols nbrDims] = size(FIallChannels);
FIallChannels = reshape(FIallChannels, nbrRows * nbrCols, nbrDims);

%%% if whiten boolean is set, perform whitening.
if (isfield(featureParams, 'whiten') && featureParams.whiten.do)
    samples = bsxfun(@minus, FIallChannels, featurePrep.whiten.mu);
    samples = samples*featurePrep.whiten.whMat;
else
    samples = FIallChannels;
end

textonMap = mapToDictionary(samples, textons);

textonMap = reshape(textonMap, nbrRows, nbrCols, 1);


end