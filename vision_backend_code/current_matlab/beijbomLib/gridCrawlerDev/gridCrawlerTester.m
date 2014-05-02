function gridCrawlerTester

gridParams.range.min = [-5 -2 ];
gridParams.range.max = [55 212];
gridParams.start = [10 0];
gridParams.stepsize = [1 1];
gridParams.edgeLength = 5;
gridParams.maxNbrMinPoints = 2;
gridParams.plausibleInfPointsRemoval = true;

for i = 1:1000
 [vp fval] = gridCrawlerTesterOne(gridParams);
end

end


function [vp fval] = gridCrawlerTesterOne(gridParams)



np = 'dummy';
fval = [];
vp = [];
itt = 0;
while (~isempty(np))
    itt = itt + 1;
    np = gridCrawler(vp, fval, gridParams);
    nfval = zeros(size(np,1), 1);
    for i = 1:size(np,1)
        nfval(i) = gridCrawlerTestObjFnc(np(i,:));
    end
    vp = [vp ; np];
    fval = [fval ; nfval];
    
    fprintf(1, '%d np generated in itteration %d \n', size(np,1), itt);
    
end
% index = find(fval == min(fval),1);
% xmin = vp(index,:);
% xmin



end



function err = gridCrawlerTestObjFnc(xval)


% err = rand(1);
err = sum(xval);
%if (xval(2) == 1)
 %   err = inf;
%end

end