function [cok, acc] = cohensKappa(cm)
% [cok, acc] = cohensKappa(cm)

acc = sum(diag(cm)) ./ sum(cm(:)); % old fashioned accuracy

pgt = sum(cm, 2) ./ sum(cm(:)); %probability of the ground truth to predict each class

pest = sum(cm, 1)' ./ sum(cm(:)); %probability of the estimates to predict each class

pe = sum(pgt .* pest); %probaility of randomly guessing the same thing!

if (pe == 1)
    cok = 1;
else
    cok = (acc - pe) ./ (1 - pe); %cohens kappa!
end


end