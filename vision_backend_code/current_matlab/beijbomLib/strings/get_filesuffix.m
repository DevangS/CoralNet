function strout = get_filesuffix(strin)
g = remove_filesuffix(strin);
strout = strin(length(g) + 2: end);
end