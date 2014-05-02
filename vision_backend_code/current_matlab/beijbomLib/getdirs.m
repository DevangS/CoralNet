function dirPath = getdirs(dirname)

d = readHovdingInputFile('directories.txt');

if(sum(struct_strcmp(d, 'identifier', dirname)) == 0)
    error('input string not found in directories.txt')
elseif sum(struct_strcmp(d, 'identifier', dirname)) > 1
    error('more than one match in directories.txt')
end
    
dirPath = d(struct_strcmp(d, 'identifier', dirname)).value;

if dirPath(end) ~= filesep
    dirPath = strcat(dirPath, filesep);
end

end