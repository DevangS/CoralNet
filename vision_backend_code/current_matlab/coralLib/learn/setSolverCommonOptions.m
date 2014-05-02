function solverOptions = setSolverCommonOptions(solverOptions, newVals)


switch solverOptions.type
    
    case 'pegasos'
        fields = {'lambda', 'k'};
    case 'libsvm'
        fields = {'gamma', 'C'};
    case 'joah'
        fields = {'C', 'd'};
    case 'steve'
        fields = {'Regularization_0x20__0x28_C_0x29_', 'Feature_0x20_Scale'};
        
end

for fitt = 1 : length(fields)
    solverOptions.(solverOptions.type).(fields{fitt}) = newVals(fitt);
end


end