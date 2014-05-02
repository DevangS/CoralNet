function Y = sqrt_fi(X,fip)
% SQRT_FI Square root calculations for fixed point.
%
% Synopsis:
%  Y = sqrt_fi(X,fip)
%
% Description:
%  This function implements a integer square root function
%  for fixed point valued data. The algorithm used is
%  described in Li, Y. & Chu, W., "A New Non-Restoring
%  Square Root Algorithm and Itäs VLSI Implementation."
%
% Input:
%  X [nbrOfVals x 1]: Values whose integer square
%  roots are to be found.
%  fip: parameters determining the fixed point type.
%
% Output:
%  Y [nbrOfVals x 1]: Integer square roots for X,
%  i.e. values such that y^2 <= x <= (y+1)^2.
%  By using the remainder from x - y^2, the output
%  integer is the integer closest to the values y or y+1.
%
% 2009-02-13, Henrik Blidh
%----------------------------------------------------------

if ~isfi(X)
    Y = sqrt(X);
else
    [m,n] = size(X);

    if ((min([m n]) ~= 1) || (min(X.double) < 0))
        error('The input to sqrt_fi is required to be a vector of non-negtive values.');
    end
    if (nargin < 2)
        fip.F = X.fimath;
        fip.T = X.numerictype;
    end
    
    % Makes call to MEX-function intsqrt.
    Y = intsqrt(X.double);
    Y = fi(Y, fip.T, fip.F);
    
end

end





