function [CM fscore simpleScore] = getStatsWrapper(trueLabels, estLabels)

nbrClasses = max(trueLabels);

CM = confMatrix(trueLabels, estLabels, nbrClasses);

p.type = 'fscore';
fscore = 1 - coralErrorFcn(CM, p);

p.type = 'simple';
simpleScore = 1 - coralErrorFcn(CM, p);

end