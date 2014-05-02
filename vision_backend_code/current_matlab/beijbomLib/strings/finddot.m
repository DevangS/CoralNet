function [dotpos] = finddot(string)
% [dotpos] = finddot(string) finds position of dot in string string. If
% nbrdots = 0 or > 1 an error message is printed.
nbrdots = 0;
for j=1:length(string)
    if string(j)=='.'
        dotpos = j;
        nbrdots = nbrdots + 1;
    end
end

if nbrdots == 0
    dotpos = length(string)  + 1;
end
if nbrdots > 1
    error('more then on dot in string')
end 
    
end