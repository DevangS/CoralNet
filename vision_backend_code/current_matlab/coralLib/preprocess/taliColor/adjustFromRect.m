
function im_cor=adjustFromRect(im,rect,gamma,percen)

if (nargin == 2)
    gamma=1;
    percen=[0.001 0.999];
end

if (nargin == 3)
    percen=[0.001 0.999];
end

im=im/max(im(:));
tempIm=fromrect(im,rect);
lim=stretchlim(tempIm,percen);
im_cor=imadjust(im,lim,[],gamma);

