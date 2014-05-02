function t = totalNbrOfSubsets(N)
%--------------------------------------------------------------------------
% TOTALNBROFSUBSETS calculates the sum of the sizes of all 
%  possible subsets of a set with size N, for N < 1024.
%
% t = totalNbrOfSubsets(N)
%
% 2009-06-09, Henrik Blidh
%--------------------------------------------------------------------------

t = 0;
gln = gammaln(N+1);
for i = 1:N
    t = t + exp(gln - gammaln(i+1)-gammaln(N-i+1));
end
t = round(t);

end
