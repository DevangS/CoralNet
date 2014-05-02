function number = get_number_at_end_of_string(str)
% number = getnumberatendofstring(str) 
% returns the digits at the end of a string until first non-digit character is
% encountered.

pos = length(str);
if ~isdigit(str(pos))
    error('str must end with a digit (0-9).');
end
j = pos;
while isdigit(str(j - 1))
    j = j - 1;
end
number = num2str(str(j:end));