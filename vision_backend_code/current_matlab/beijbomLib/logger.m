function logger(varargin)
% function logger(varargin)
% appends a date and time stamp to each log message.
% Also prints message to console.
% use global parameter logfid.

global logfid;

message = sprintf(varargin{1}, varargin{2:end});

callingFcn = dbstack(1);

if (isempty(callingFcn))
    callingFcn(1).file = 'script';
end

logStr = sprintf('[%s] <%s> %s', datestr(clock, 31), callingFcn(1).file, message);

fprintf(logfid, '%s\n', logStr);

if (logfid ~= 1)
    fprintf(1, '%s\n', logStr);
end

end