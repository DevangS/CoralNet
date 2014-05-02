function FIC = coralApplyFilters(I, filterMeta)

F = filterMeta.F;
Fids = filterMeta.Fids;
nbrOriented = filterMeta.nbrOriented * 2;
nbrCircular = filterMeta.nbrCircular * 2;
nbrFilters = nbrOriented + nbrCircular;

FI = fft_filt_2(I, F, 1);

FIC = zeros(size(FI, 1), size(FI, 2), nbrFilters);
pos = 0;
for r = rowVector(unique(Fids))
       ind = Fids == r;
     if (sum(ind) > 1) 
         thisFI = abs(FI(:,:,ind));
         FIC(:,:,r) = max(thisFI, [], 3);
     else
         FIC(:,:,r) = FI(:,:,ind);       
     end
end

% normalize according to Fowles.
L = sqrt(sum(FIC.^2, 3));
FIC = FIC.*repmat(log(1 + L./.03) ./ L, [1 1 size(FIC, 3)]);

end


