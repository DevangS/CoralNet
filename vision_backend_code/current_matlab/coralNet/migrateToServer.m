%% COPY ALL TOOLBOXES%%

system('scp -r ~/e/Code/MATLAB/toolboxes beijbom@coralnet:~/e/Code/MATLAB/')

system('scp -r ~/e/Code/MATLAB/not_on_path_toolboxes beijbom@coralnet:~/e/Code/MATLAB/')


%% CHECK OUT THE LATEST VERSION OF THE CODE

system('ssh beijbom@coralnet "cd ~/coralcode; svn update"')

system('ssh beijbom@coralnet "cd ~/e/Code/beijbom; svn update"')


%% COPY THE PARAMETER FILE

system('scp -r ~/coralcode/coralNet/preProcessParameters.mat beijbom@coralnet:~/cnhome/images/preprocess/preProcessParameters.mat')

%% COPY (IF OK) THE MATLAB STARTUP SCRIPT %%


% system('scp ~/e/Code/MATLAB/startup.m beijbom@coralnet:~/e/Code/MATLAB/startup.m')
