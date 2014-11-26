% [varnames, varvals] = var2varvallist(varargin)
%
% This function is kind of a strange one. First showing an example
% usage and its output.
% >> a = 1;
% >> b = 2;
% >> c = 3;
% >> [varnames, varvals] = var2varvallist(a,b,c)
% varnames = 
% 
%     'a'
%     'b'
%     'c'
% 
% 
% varvals = 
% 
%     [1]
%     [2]
%     [3]
% 
% As is shown, this function takes in a list of variables and
% returns the names of variables and the values of variables. If a
% primitie is passed in (like the scalar 1), then that cell of
% varnames will be empty, and but its value will exist in varvals.
%
% inputs:
%  varargin = any list of variables
% outputs:
%  varnames = a cellarray of the variable names in string form
%  varvals = the values for the variables.
% side effects:
%  none
%

% --------
% Sam Kwak
% Copyright 2011
function [varnames, varvals] = var2varvallist(varargin)

varnames = cell(length(varargin), 1);
varvals = cell(length(varargin), 1);
% loop over varargin. get its value and name and store them in the
% cell array.
for i_var = 1:length(varargin)
  % input name figures out the variable name in the calling space.
  varnames{i_var} = inputname(i_var);
  varvals{i_var} = varargin{i_var};
end % for i_var = 1:length(varargin)

end % var2varvallist(...)