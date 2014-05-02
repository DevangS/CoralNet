
function M=estimateDiag(V1,V2,sign)

% V1, V2 should be Xx3 = rows of RGB values from different patches

% To solve the matrix equation Ax = b, enter x=A\b
V11=[V1 ones(size(V1,1),1)]; % add ones for affine transformation

M=V11\V2; % M is 4X3 containing (A|B)'

m=size(V1,2);

cvx_begin quiet
variable A(m,m) diagonal;
minimize( norm(A*V1' - V2','fro' ));
subject to
% A == diagonal(m);
A>=0;
cvx_end

B=zeros(m,1);
full(A);
M=[full(A) B]';

