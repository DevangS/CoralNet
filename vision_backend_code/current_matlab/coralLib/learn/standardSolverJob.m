function job = standardSolverJob(jobDir)

job.logPath = fullfile(jobDir, 'log');
job.script = fullfile(jobDir, 'solver');
job.fwtoolSolverParams(1).type = 'train';
job.fwtoolSolverParams(1).trainPath = fullfile(jobDir, 'train');
job.fwtoolSolverParams(1).modelPath = fullfile(jobDir, 'model');
job.fwtoolSolverParams(1).outputPath = fullfile(jobDir, 'output');
job.fwtoolSolverParams(1).optStr = '';

job.fwtoolSolverParams(2).type = 'test';
job.fwtoolSolverParams(2).testPath = fullfile(jobDir, 'test');
job.fwtoolSolverParams(2).labelPath = fullfile(jobDir, 'label');
job.fwtoolSolverParams(2).modelPath = fullfile(jobDir, 'model');
job.fwtoolSolverParams(2).outputPath = fullfile(jobDir, 'output');
job.fwtoolSolverParams(2).optStr = '';

end