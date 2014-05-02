function showCoralImg(fileNbr, content, varargin)
%
% VARARGIN:
%
% plotParams.colors = 'bcgrrgbcm';
% plotParams.markers = '^^^^ooooo';
% plotParams.sizes = [5 5 5 5 5 5 5 5 5];
% plotParams.predSizes = [15 15 15 15 15 15 15 15 15];
% labelParams.cats = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit'};
% labelParams.id = [1 2 3 4 5 6 7 8 9 9 9 9];
% labelParams.catsOrg = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit', 'P. Irr', 'P. Rus', 'P mass'};
%
% ppParams.type = 'intensitystretchRGB';
% ppParams.low = 0.01;
% ppParams.high = 0.99;
%
% showLegend = 0;
% nbrClasses = 9;
% ssFactor = 1/2;
%
% rowCol = [];
% gtLabels = [];
% estLabels = [];
%
% dataDir = '~/e/Data/Coral/LTER-MCR/organised';


plotParams.colors = 'bcgrrgbcm';
plotParams.markers = '^^^^ooooo';
plotParams.sizes = [5 5 5 5 5 5 5 5 5];
plotParams.predSizes = [15 15 15 15 15 15 15 15 15];

labelParams.cats = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit'};
labelParams.id = [1 2 3 4 5 6 7 8 9 9 9 9];
labelParams.catsOrg = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit', 'P. Irr', 'P. Rus', 'P mass'};

ppParams.type = 'intensitystretchRGB';
ppParams.low = 0.01;
ppParams.high = 0.99;

showLegend = 1;
nbrClasses = 9;
ssFactor = 1/2;

rowCol = [];
gtLabels = [];
estLabels = [];

dataDir = '~/e/Data/Coral/LTER-MCR/organised';


[varnames, varvals] = var2varvallist(ppParams, labelParams, plotParams, showLegend, gtLabels, rowCol, ssFactor, estLabels, nbrClasses, dataDir);
[ppParams, labelParams, plotParams, showLegend, gtLabels, rowCol, ssFactor, estLabels, nbrClasses, dataDir] = varargin_helper(varnames, varvals, varargin{:});


labelMatrix = readCoralLabelFile(fullfile(dataDir, content(fileNbr).labelFile), labelParams);

if (isempty(rowCol))
    rowCol = labelMatrix(:, 1:2);
end
if (isempty(gtLabels))
    gtLabels = labelMatrix(:, 3);
end

I = imread(fullfile(dataDir, content(fileNbr).imgFile));

rowCol = round(rowCol * ssFactor);

imagesc(coralPreProcess(imresize(I, ssFactor), ppParams));
axis off;
axis image;
hold on;

if(showLegend)
    % plot dummy stuff for the legend to work...
    for tt = 1: nbrClasses
        plot(1,1, plotParams.markers(tt), 'MarkerEdgeColor', plotParams.colors(tt));
    end
    legend(labelParams.cats);
end

% plot the actual markers.
for ii = 1 : size(rowCol, 1)
    plot(rowCol(ii, 2), rowCol(ii, 1), plotParams.markers(gtLabels(ii)), 'Markersize', plotParams.sizes(gtLabels(ii)), 'MarkerEdgeColor', plotParams.colors(gtLabels(ii)), 'LineWidth', 3);
end

if (~isempty(estLabels))
    for ii = 1 : size(rowCol, 1)
        plot(rowCol(ii, 2), rowCol(ii, 1), plotParams.markers(estLabels(ii)), 'Markersize', plotParams.predSizes(estLabels(ii)), 'MarkerEdgeColor', plotParams.colors(estLabels(ii)),'LineWidth', 3);
    end
end


end