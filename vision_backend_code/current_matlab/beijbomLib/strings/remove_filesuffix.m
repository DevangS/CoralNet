function outstr = remove_filesuffix(str)
%str = removefilesuffix(str) removes filesuffix including the dot and
%returns the rest of the string. Returns whole string if no dot is
%encountered.

pos = length(str);
while pos ~= 0 && ~strcmp(str(pos), '.')
   pos = pos - 1; 
end
if pos == 0;
    outstr = str;
else
    outstr = str(1:pos - 1);
end
