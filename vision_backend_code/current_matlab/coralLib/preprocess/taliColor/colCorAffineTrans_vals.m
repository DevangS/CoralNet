
function trans_im=colCorAffineTrans_vals(im,vals,base_v,method,SD_flag)

switch(SD_flag)
    case 1
        estimate_func=@estimateAffineSD;
        apply_func=@applyAffine;
        sign=0;
    case 0
        estimate_func=@estimateAffine;
        apply_func=@applyAffine;
        sign=0;
    otherwise
        estimate_func=@estimateAffine_Poly;
        apply_func=@applyAffine_Poly;
        sign=SD_flag;
end

if (findstr(method,'diag'))
    estimate_func=@estimateDiag;
    apply_func=@applyAffine;
    sign=0;
end


% C = makecform('srgb2xyz', 'AdaptedWhitePoint', whitepoint('D65'));
% C_rev = makecform('xyz2srgb', 'AdaptedWhitePoint', whitepoint('D65'));
% keyboard;

[vals good_rows]=removeNans(vals);
base_v=base_v(good_rows,:);
base_v_ch=rgb2ch(base_v);

% keyboard;
% smallValTh=0.01;
% [tempVals good_rows]=removeSmallVals(vals/max(vals(:)),smallValTh,[1]); % th is relative to 1
% vals=vals(good_rows,:);
% base_v=base_v(good_rows,:);


cs_method=method;

if (findstr(method,'YCB'))
    im=rgb2ycbcr(im);
    vals=rgb2ycbcr(vals);
    base_v=rgb2ycbcr(base_v);
    
    method='RGB';
end

if (findstr(method,'HSV'))
    im=rgb2hsv(im);
    vals=rgb2hsv(vals);
    base_v=rgb2hsv(base_v);
    
    method='RGB';
end

if (findstr(method,'LAB'))
    im=rgb2lab(im);
    vals=rgb2lab(vals);
    base_v_ch=rgb2lab(base_v);
    method='ch';
end


if (findstr(method,'neg'))
    sign=-1;
elseif (findstr(method,'pos'))
    sign=1;
end

if (findstr(method,'RGB'))
    channels=1:3;
        
    
    
    if (findstr(method,'linear'))
        
        if (~SD_flag)
            M=estimateLinear(vals,base_v);
        else
            M=estimateLinearSD(vals,base_v);
        end
        %         M=vals\base_v;
    elseif (findstr(method,'diagonal'))
        
%         M=diag(mean(vals.\base_v));

        M=estimate_func(vals,base_v,sign);
        
    elseif (findstr(method,'ROT'))
        
        M=estimateRotation(vals,base_v);
        
    else
        
        M=estimate_func(vals,base_v,sign);
        
    end
    v=vals;
    im_vec=reshape((im),[],3);
    
elseif (findstr(method,'ch'))
    channels=2:3;
    if (findstr(cs_method,'LAB'))
        v=(vals);
        im_vec=reshape(rgb2lab(im),[],3);
    else
        v=rgb2ch(vals);
        im_vec=reshape(rgb2ch(im),[],3);
    end
    v=v(:,channels);
    M=estimate_func(v,base_v_ch(:,channels),sign);
    im_vec=im_vec(:,channels);
    
elseif (findstr(method,'XYZ'))
    channels=1:3;
    v=applycform(vals,C);
    base_v=applycform(base_v,C);
    im_vec=applycform(im,C);
    im_vec=reshape((im_vec),[],3);
    if (findstr(method,'norm'))
        v=bsxfun(@rdivide,v,v(:,2));
        base_v=bsxfun(@rdivide,base_v,base_v(:,2));
        im_y=im_vec(:,2);
        im_vec=bsxfun(@rdivide,im_vec,im_vec(:,2));
    end
    M=estimate_func(v,base_v,sign);
end

if (findstr(method,'XYZ'))
    d=0.92;
    trans_im_vec=d*apply_func(im_vec,M)+(1-d)*im_vec;
elseif ( ~isempty(findstr(method,'linear')) )
    trans_im_vec=im_vec*M;
    trans_vals=vals*M;
else
    d=1;
    trans_im_vec=d*apply_func(im_vec,M)+(1-d)*im_vec;
    trans_vals=apply_func(v,M);
end

if (findstr(method,'norm'))
    trans_im_vec=bsxfun(@times,trans_im_vec,im_y);
end

trans_im=reshape(trans_im_vec,[size(im,1) size(im,2) length(channels)]);

if (strcmp(method,'XYZ') || strcmp(method,'XYZ_norm'))
    trans_im(isnan(trans_im))=0;
    trans_im = applycform(trans_im,C_rev);
end


if (findstr(cs_method,'YCB'))
    trans_im=ycbcr2rgb(trans_im);
end

if (findstr(cs_method,'HSV'))
    trans_im=hsv2rgb(trans_im);
end

if (findstr(cs_method,'LAB'))
    temp(:,:,1)=im(:,:,1);
    temp(:,:,2:3)=trans_im;
    trans_im=lab2rgb(temp);
    method='RGB';
end

% if (findstr(method,'RGB') || findstr(method,'XYZ') || findstr(method,'XYZ_norm'))
%     if (min(trans_im(:))<0)
%         trans_im(trans_im<0)=0;
%     else
%         trans_im=trans_im-min(trans_im(:));
%     end
%     trans_im=trans_im/max(trans_im(:));
% end

if(findstr(method,'ch'))
    temp=zeros(size(im));
    temp(:,:,channels)=trans_im;
    temp(:,:,setdiff(1:3,channels))=1-sum(trans_im,3);
    trans_im=temp;
    trans_im=bsxfun(@times,trans_im,sum(im,3));
end


