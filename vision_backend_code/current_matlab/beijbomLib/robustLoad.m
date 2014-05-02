function [data success] = robustLoad(filePath, varargin)
% function data = robustLoad(filePath, nbrTries, pauseTime)
%
% INPUT filePath indicates file to load
%
% varargin with defaults
% nbrTries = 60 
% pauseTime = 60

nbrTries = 60;
pauseTime = 60;


[varnames, varvals] = var2varvallist(nbrTries, pauseTime);
[nbrTries, pauseTime] = varargin_helper(varnames, varvals, varargin{:});

tryNbr = 0;
success = 0;
data = [];
while ~success && tryNbr < nbrTries
    tryNbr = tryNbr + 1;
    try
        data = load(filePath);
        success = true;
    catch exception
        
        logger(sprintf('Failed to load [%s] on tryNbr: %d. Error:[ %s ]', filePath, tryNbr, exception.identifier));
        pause(pauseTime);
        
    end
    
end

end