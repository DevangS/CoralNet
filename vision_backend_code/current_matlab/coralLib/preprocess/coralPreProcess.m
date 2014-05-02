function Iout = coralPreProcess(I, params)
% function Iout = coralPreProcess(I, params)
% INPUT I is rgb image.

Iout = I;
switch params.type
    case 'none'
        
    case 'globalHistStretch'
        Iout = reshape(imadjust(I(:), stretchlim(I(:),[params.low params.high])), size(I));
    case 'eachColorchannelStretch'
        for i = 1:3
            Iout(:,:,i) = imadjust(I(:,:,i), stretchlim(I(:,:,i),[params.low params.high]));
        end
    case 'intensitystretch'
        I = applycform(I, makecform('srgb2lab'));
        I(:,:,1) = imadjust(I(:,:,1), stretchlim(I(:,:,1),[params.low params.high]));
        Iout = applycform(I, makecform('lab2srgb'));
    case 'intensitystretchRGB'
        I = double(I);
        I = I ./ 255;
        lowHigh = stretchlim(I(:), [params.low params.high]);
        I(I > lowHigh(2)) = lowHigh(2);
        I = I - lowHigh(1);
        I(I<0) = 0;
        Iout = I / max(I(:));
    case 'taliAdjust'
        Iout = adjust(double(I), 1, 1, [params.low params.high]);
        
    case 'colormodLAB'
        params.type = 'intensitystretchRGB';
        I = coralPreProcess(I, params); %stretch intensity
        I = uint8(round(I * 255));
        I = applycform(I, makecform('srgb2lab'));
        
        I = double(I);
        I(:,:,2) = I(:,:,2) .* params.aMod;
        I(:,:,3) = I(:,:,3) .* params.bMod;
        Iout = applycform(uint8(round(I)), makecform('lab2srgb'));
        
    case 'colormodRGB'
        params.type = 'intensitystretchRGB';
        I = coralPreProcess(I, params);
        for c = 1:3
            I(:, :, c) = I(:, :, c) .* params.rgbMod(c);
        end
        I = I ./ max(I(:));
        Iout = I;
        
    case 'trueColor'
        if (params.removeNans)
            params.ccVals(isnan(params.ccVals)) = 255;
        end
        params.ccVals = params.ccVals/255;
        
        Iout = runCC(double(I), params.trueColorMethod, params.ccVals, params.ccValsGT, params.ccType);
        
end
end

function adj = adjust(work,val,flag,percen)

%flag 1 to use stretchlim

if (nargin == 2)
    flag=1;
    percen=[0.01 0.99];
elseif (nargin == 3)
    percen=[0.01 0.99];
end

minn=min(work(:));
work=work-minn;
work=work./max(work(:));
minw=min(min(work));
minw=minw(:);
maxw=max(max(work));
maxw=maxw(:);
if (flag==1)
    adj=imadjust(work,stretchlim(work, percen),[],val);
elseif(flag==2)
    if(size(work,3)==3)
        adj=imadjust(work,[minw'; maxw'],[0 0 0;1 1 1],val);
    else
        adj=imadjust(work,[minw'; maxw'],[0 ; 1],val);
    end
end
end

