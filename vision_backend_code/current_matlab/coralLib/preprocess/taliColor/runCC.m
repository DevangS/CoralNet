
% Write a function that takes one image, the meta data associated with the color card/Homography,
% and one method and returns the color corrected image.


function im_cor=runCC(im,method_name,vals,groundTruth_vals,colorCardType) %H,scale,groundTruth_vals,queryCoords,param,expectedGrey)

im=im/max(im(:));


switch(colorCardType)
    case 1
        color_squares=[1:6 13:18];
        grey_squares=[8:12];
end
% groundTruth_vals=groundTruth_vals([color_squares grey_squares],:);
colorGroup=str2num(method_name(end));

if (~isempty(colorGroup))
    method_name=method_name(1:end-1);
    switch(colorGroup)
        case 1
            vals(7:end,:)=NaN;
        case 2
            vals([1:6 13:end],:)=NaN;
    end
end

if (strcmp(method_name,'raw'))
    
    im_cor=im;
    
elseif (strcmp(method_name,'taliAdjust'))
    [ im_cor]=taliAdjust(im,1,1);% no gamma
    
elseif (strcmp(method_name,'adjustInside'))
    
    %[ im_cor]=adjust(im,1,1);% no gamma
    insideRect=round([40         40        160        160] * 4);
    im_cor=adjustFromRect(im,insideRect);
    
elseif (strcmp(method_name, 'eachColorchannelStretch'))
    for i = 1:3
        im_cor(:,:,i) = imadjust(im(:,:,i), stretchlim(im(:,:,i),[0.01 0.99]));
    end
    
    
elseif (strcmp(method_name,'diag_white'))
    
    [im_cor]=diagWhite_vals(im,vals(grey_squares,:));
    
elseif (findstr(method_name,'card_inter'))
    
    [ im_cor]=colCorInterp_vals(im,vals,groundTruth_vals);
    
elseif (findstr(method_name,'rot_white'))
    
   
    vals(isnan(vals)) = 1;

    
    [im_cor]=colCorRotWhite_vals(im,vals(grey_squares,:));
    
elseif (findstr(method_name,'affine'))
    
    SD_flag=~isempty(findstr(method_name,'SD'));
    
    t=findstr(method_name,'_');
    t=[t length(method_name)+1];
    method_cs_name=method_name(t(1)+1:t(2)-1);
    
    if (findstr(method_name,'linear'))
        method_name=[method_cs_name '_linear'];
    end
    
    if (findstr(method_name,'diagonal'))
        method_name=[method_cs_name '_diagonal'];
    end
    
    
    if (findstr(method_name,'neg'))
        method_name=[method_cs_name '_neg'];
    end
    
    if (findstr(method_name,'pos'))
        method_name=[method_cs_name '_pos'];
    end
    
    [im_cor]=colCorAffineTrans_vals(im,vals,groundTruth_vals,method_name,SD_flag);
    
    
elseif (strcmp(method_name,'POLY_2'))
    im_cor=colCorAffineTrans_vals(im,groundTruth_vals,'RGB',2);
else
    'invalid method'
    error
end

if(~isempty(im_cor))
    im_cor(im_cor<0)=0;
    per=0.001;
    lim=stretchlim(im_cor,[per 1-per]);
    lim_min=min(lim(1,:));
    lim_max=max(lim(2,:));
    im_cor(im_cor>lim_max)=lim_max;
    im_cor=im_cor-lim_min;
    im_cor(im_cor<0)=0;
    im_cor=im_cor/max(im_cor(:));
end
