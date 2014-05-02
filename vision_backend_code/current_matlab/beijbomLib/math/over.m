function a = over(n, k)
a = zeros(size(k));
for i = 1:length(k)
    a(i) = fac(n) / (fac(k(i)) * fac(n-k(i)));
end

end