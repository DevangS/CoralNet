
function M=estimateLinear(V1,V2)


% V1, V2 should be Xx3 = rows of RGB values from different patches

% To solve the matrix equation Ax = b, enter x=A\b
M=V1\V2; % M is 4X3 containing (A|B)'

m=size(V1,2);

cvx_begin quiet
variables A(m,m);
minimize( norm(A*V1' - V2','fro' ));
cvx_end

M=[A]';

