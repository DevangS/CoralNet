function coralnet_classify(featureFile, modelFile, labelFile, logFile, errorLogfile)

try
    
    system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-predict %s %s %s', featureFile,  modelFile,  labelFile));
    system(sprintf('/home/beijbom/e/Code/apps/libsvm/svm-predict -b 1 %s %s %s', featureFile,  modelFile,  strcat(labelFile, '.prob')));
    
catch me
    
    fid = fopen(errorLogfile, 'a');
    fprintf(fid, '[%s] Error executing coralnet_classify: %s, %s \n', datestr(clock, 31), me.identifier, me.message);
    fclose(fid);
    
end

end