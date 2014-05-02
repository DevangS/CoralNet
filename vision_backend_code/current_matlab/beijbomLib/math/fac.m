function faculty = fac(n)
% faculty = fac(n) calculates n!

if n ~= 0
    t = cumprod(1:n);
    faculty = t(end);
else
    faculty = 1;

end