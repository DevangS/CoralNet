
function im_cor=diagWhite_vals(im,greyVals)

im_cor=im;

[L] = fitline3d(greyVals');

vector=L(:,2)'-L(:,1)';

 for c=1:3
        im_cor(:,:,c)=im_cor(:,:,c)/(vector(c)+eps);
 end
 
im_cor=im_cor/max(im_cor(:));
