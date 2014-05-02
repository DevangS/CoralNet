function [labels decisionvalues metaData] = svmclassifyFast(samples, model)
%[labels decisionvalues metaData] = svmclassify(samples, model)
% -1 is accident
% 1 is non accident

metaData = 0;
if isfi(samples)
    [labels decisionvalues metaData] = svmClassifyFi(samples, model);
else

    SVs = full(model.SVs);

    if size(SVs,2)~=size(samples,2)
        error('dimension of Support vectors does not match sampel data dimension.');
    end

    if ~(model.Parameters(1) == 0)
        error('Wrong SVM-type. Only C-svm type problems allowed.');
    end
    if ~ ((model.Parameters(2) == 0) ||(model.Parameters(2) == 1) || (model.Parameters(2) == 2))
        error('Kernel type not allowed. Only linear, polynomial and RBF kernels allowed.');
    end

    nbrsamples = size(samples,1);

    degree = model.Parameters(3);
    gamma = model.Parameters(4);
    coeff = model.Parameters(5);
    b = model.rho;
    alphay = model.sv_coef;
    nbrsvs = model.totalSV;

    %     metaData.beforeGammaExp = zeros(nbrsamples, nbrsvs);
    %     metaData.afterGammaExp = zeros(nbrsamples, nbrsvs);

    if model.Parameters(2) == 0
        gamma = 1;
        coeff = 0;
        degree = 1;
    end

    if ((model.Parameters(2) == 1) || (model.Parameters(2) == 0))
        %         metaData = zeros(nbrsamples, nbrsvs);
        m = samples * SVs';

        m = (m * gamma + coeff).^degree;
        m = m .* repmat(alphay',nbrsamples,1);
        m = sum(m,2);
        decisionvalues = m - b;
    else
        decisionvalues = zeros(nbrsamples,1);

        %evaluate kernel!
        for i = 1 : size(samples,1)

            temp = SVs - repmat(samples(i,:), nbrsvs, 1);

            temp = sum(temp.^2,2) .* -gamma;
            %             metaData.beforeGammaExp(i, :) = temp';
            temp = exp(temp);

            temp = temp.*alphay;
            %             metaData.afterGammaExp(i, :) = temp';
            decisionvalues(i) = sum(temp);

        end

        decisionvalues = decisionvalues - b;
    end
    labels = sign(decisionvalues);
end

end


function [labels decisionvalues metaData] = svmClassifyFi(samples, model)
% [labels decisionvalues metaData] = svmClassifyFi(samples, model)
%
% 2009-02-13 Oscar. Works only for rbf kernels.
%
metaData = 0;
if (model.Parameters(2) == 2)

    fip.F = samples.fimath;
    fip.T = samples.numerictype;

    model = model.fi;

    bias = model.rho;
    SVs = model.SVs;
    alphaY = model.sv_coef;
    nbrsvs = model.totalSV;
    nbrsamples = size(samples,1);

    labels = fi(zeros(nbrsamples,1), fip.T, fip.F);

    decisionvalues = fi(zeros(nbrsamples,1), fip.T, fip.F);
    %     metaData = struct('v', cell(size(samples,1),1),'u', [],'w',[]);
    %     metaData.beforeGammaExp = fi(zeros(nbrsamples, nbrsvs), fip.T, fip.F);
    %     metaData.afterGammaExp = fi(zeros(nbrsamples, nbrsvs), fip.T, fip.F);

    for i = 1:size(samples,1)

        % performs first steps in double precision. Equivelent since no
        % divisions.
        svSmall = SVs.double(:,1:18);
        samplesSmall = samples.double(i,1:18);
        %         metaData(i).v18 = svSmall - repmat(samplesSmall, nbrsvs, 1);
        %         metaData(i).v18 = sum((metaData(i).v18).^2,2);

        tD = SVs.double - repmat(samples.double(i,:), nbrsvs, 1);
        tD = sum(tD.^2,2);
        %         metaData(i).v = tD;
        tD = fi(tD, fip.T, fip.F);
        %         metaData.beforeGammaExp(i, :) = tD';
        % looks result in table
        temp = lookupFiGammaTable(model.table, tD);
        %         metaData(i).u = temp.double;
        % finish in 64 bit precision.
        fip64 = setfi(64,0);

        %         temp64 = fi(temp, fip64.T, fip64.F);
        %         alphaY64 = fi(alphaY, fip64.T, fip64.F);
        %         temp = sum(temp64.*alphaY64);
        %         bias64 = fi(bias, fip64.T, fip64.F);
        %         temp = temp - bias64;

        decisionvalues(i) = fi(sum(temp.double.*alphaY.double) - bias.double, fip64.T, fip64.F);
        %         metaData(i).w = sum(temp.double.*alphaY.double);
        labels(i) = sign(decisionvalues(i));

    end
    %     fprintf(1, '\n');
else
    error('Only RBF kernels supported');
end




end

function out = lookupFiGammaTable(table, in)

fip.F = in.fimath;
fip.T = in.numerictype;

% nbitsTable = table.nbitsTable;
% nbitsMaxIn = table.nbitsMaxIn;
% nbitsOut = table.nbitsOut;


% slå i tabellen!
pos = bitshift(in, -table.lookupShift);
pos(pos == 0 ) = 1;

% this is because the table in cut off. Everything larger than this should
% return a zero!
pos(pos > length(table.tableOut)) = length(table.tableOut);

% interpolation
% diff = in - pos * table.lookupShift;

%samplar ner resten
% linRegPrec = fi(2 ^ (nbitsOut - nbitsTable), fip.T, fip.F);
% diff = diff * linRegPrec;
% diff = divide(fip.T, diff, table.lookupShift);

out1 = table.tableOut(pos.double);
% out2 = table.tableOut(pos.double + 1);

% out = (out1 .* (linRegPrec - diff) + out2 .* diff);
out = out1;
end
