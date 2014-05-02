function [rVal p1] = plotCorr(estCov, gtCov, forceZero)

Y = estCov;
X = gtCov;

plot(X, Y, '*', 'markersize', 10, 'color', 'yellow');
mm = min(1.1 * max([X;Y]), 1);

n = length(X);
rVal = sum((X - mean(X)).*(Y-mean(Y))) / (sqrt(n * var(X)) * sqrt(n * var(Y)));
if (forceZero)
    c = [Y'/X', 0];
else
    c = polyfit(X, Y, 1);
end

x = linspace(0, mm, 1000);
y = polyval(c, x);
hold on
plot(x,y, 'r', 'linewidth', 2);

ylabel('est. cov');
xlabel('gt. cov');
p1 = c(1);
axis([0 mm 0 mm]);

end