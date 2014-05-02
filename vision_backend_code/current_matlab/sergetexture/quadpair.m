function [F1,F2]=quadpair(sig,lam,th,N);
% [F1,F2]=quadpair(sig,lam,th,N);
%
% For Thomas' ECCV98 filters, use sig=sqrt(2), lam=4.

%N=31;
[x,y]=meshgrid(-(N/2)+1/2:(N/2)-1/2,-(N/2)+1/2:(N/2)-1/2);


F1=(4*(y.^2)/(sig^4)-2/(sig^2)).*exp(-(y.^2)/(sig^2)-(x.^2)/(lam^2*sig^2));
F2=imag(hilbert(F1));

F1=imrotate(F1,th,'bil','crop');
F2=imrotate(F2,th,'bil','crop');

F1=F1-mean(F1(:));
F2=F2-mean(F2(:));

F1=F1/norm(F1(:),1);
F2=F2/norm(F2(:),1);