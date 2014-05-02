function printstructure(s)
% printstructure(s) prints structure s in consolewindow
printsrec(s,0)

end

function printsrec(s,n)
indention = 5;
if isstruct(s)
    temp = fieldnames(s);
    for i = 1:length(temp)
        eval(['t = s.' temp{i} ';']);
        l = length(temp{i});
        formatstring = strcat('%', num2str(l+indention*n), 's');
        if isstruct(t)
            fprintf(1, [formatstring '\n'], temp{i})
            printsrec(t, n+1)
        elseif iscell(t)
            nbrcells = length(t);
            fprintf(1, [formatstring '%s%d%s\n'], temp{i}, '{', nbrcells, '}')
            printsrec(t{1}, n+1);
        else
            fprintf(1, [formatstring '\n'], temp{i})
        end
    end
end


end