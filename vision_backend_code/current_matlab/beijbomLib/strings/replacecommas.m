function str = replacecommas(str)
%replaces commas with dots!

for i = 1:length(str)
    if strcmp(str(i),',')
        str(i) = '.';
    end
end

end