function G=dog2(sig,N);
% G=dog2(sig,N);

% by Serge Belongie

no_pts=N;  % no. of points in x,y grid

[x,y]=meshgrid(-(N/2)+1/2:(N/2)-1/2,-(N/2)+1/2:(N/2)-1/2);

sigi=0.62*sig;
sigo=1.6*sig;
C=diag([sig,sig]);
Ci=diag([sigi,sigi]);
Co=diag([sigo,sigo]);

X=[x(:) y(:)];

Ga=gaussian(X,[0 0]',Ci);
Ga=reshape(Ga,N,N);
Gb=gaussian(X,[0 0]',C);
Gb=reshape(Gb,N,N);
Gc=gaussian(X,[0 0]',Co);
Gc=reshape(Gc,N,N);

a=-1;
b=2;
c=-1;

G = a*Ga + b*Gb + c*Gc;

G=G-mean(G(:));

G=G/norm(G(:),1);
