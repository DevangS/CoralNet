function out = sprod(x,y)
%function out = sprod(x,y)
% Calculates scalar product between x and y.

nx = length(x);
ny = length(y);

if nx~=ny
    error('input vectors must have the same length');
end

out = x.*y;
out = sum(out,2);
