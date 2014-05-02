
function M=estimateAffineSD(V1,V2,sign)

% V1, V2 should be Xx3 = rows of RGB values from different patches
m=size(V1,2);

cvx_begin quiet
variables A(m,m) B(m,1);
BB=repmat(B,[1 size(V1,1)]);
minimize( norm(A*V1'+ BB - V2','fro'));
subject to
A == semidefinite(m);
sign*B>=0;
cvx_end

M=[A B]';

