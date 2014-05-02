function str = remove_blanks_at_beginning_of_file(str)
% strout = remove_blanks_at_beginning_of_file(str) removes all non-alphabetic or non-digits at
% the beginning of string str.

l = length(str);
pos = 1;
while pos <= l && ~isdigit(str(pos)) && ~isletter(str(pos))
    pos = pos + 1;
end

str = str(pos:end);
    

