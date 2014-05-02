
function im_cor=colCorRotWhite_vals(im,greyVals)

im_cor=[];

if(nargin<7)
    white_vector=[1 1 1];
else
    greys=expectedGrey;
    greys=removeNans(greys);
    white_line = fitline3d(greys');
    white_vector=white_line(:,2)'-white_line(:,1)';
    white_vector=white_vector/norm(white_vector);
    
end

[L] = fitline3d(greyVals');
white_vector=white_vector/norm(white_vector);

vector=L(:,2)'-L(:,1)';

%intersection:
% x1 + a1 * t1 = x2 + a2 * t2
%  y1 + b1 * t1 = y2 + b2 * t2

% rotation matrix

rot_axis=cross(vector,white_vector);
rot_angle=1*acos(dot(vector/norm(vector),white_vector/norm(white_vector)));
R=rotationMatrix(rot_axis,rot_angle);

im_cor=R*reshape(im,[],3)';
im_cor=reshape(im_cor',size(im));

