function FIallChannels = coralApplyFilterWrapper(I, featureParams, filterMeta, totalNbrChannels)

if (nargin < 4)
    totalNbrChannels = 1;
end

% preprosess
I = coralPreProcess(I, featureParams.preprocess);

% change colorspace
switch featureParams.color.cspace
    case 'hsv'
        I = rgb2hsv(I);
    case 'lab'
        I = applycform(I, makecform('srgb2lab'));
    case 'rgb'
        
    case 'gray'
        I = rgb2gray(I);
end

% apply filters
FIallChannels = zeros(size(I, 1), size(I,2), totalNbrChannels);

for channelNbr = 1 : length(featureParams.color.channels)

    thisChannel = featureParams.color.channels(channelNbr);
    FI = coralApplyFilters(I(:,:, thisChannel), filterMeta);
    FIallChannels(:,:, (channelNbr - 1) * size(FI, 3) + 1 : channelNbr * size(FI, 3)) = FI;
    
end

end