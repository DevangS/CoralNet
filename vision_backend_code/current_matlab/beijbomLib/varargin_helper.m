% varargout = varargin_helper(varnames, varvals, varargin)
%
% This function takes the output of var2varvallist and parameters
% that were passed into some function. The parameter list is
% assuemd to be of the form 'parameter', 'value' (ie matlab style).
%
% inputs:
%  varnames = the names of the variables.
%  varvals = the default values to the variables.
%  varargin = the parameters that were passed in to a function
% outputs:
%  varargout = the values of the parameters, in the order that they
%    were passed in to var2varvallist
% side effects:
%  none
%

% --------
% Sam Kwak
% Copyright 2011
function varargout = varargin_helper(varnames, varvals, varargin)

% first set the outputs to the "default" passed in values.
varargout = varvals;

% loop over the varargin, everyone entry in varargin is a parameter
% name, which is assumed to match a name in the varnames list.
for i_vars = 1:2:length(varargin)
  idx = strcmp(varargin{i_vars}, varnames);
  % make sure that parameter exists.
  if sum(idx) == 0
    error('Parameter "%s" not recognized.', varargin{i_vars});
  end % if sum(idx) == 0
  varargout{idx} = varargin{i_vars+1};
end % for i_vars = 1:2:length(varargin)


end % varargin_helper(...)