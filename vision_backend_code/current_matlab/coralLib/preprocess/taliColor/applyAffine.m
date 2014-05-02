function V2=applyAffine(V1,M)


V11=[V1 ones(size(V1,1),1)]; % add ones for affine transformation

V2=V11*M; % M is 3X4 containing A*x+B

