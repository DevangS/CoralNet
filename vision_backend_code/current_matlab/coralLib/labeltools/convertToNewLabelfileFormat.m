function convertToNewLabelfileFormat(infile, outfile)

if(exist(outfile, 'file'))
    error('Outfile exist');
end
out = fopen(outfile, 'w');
fprintf(out, '# Row; Col; Label\n');

labelStruct = parseTxtFile(infile, 15);

for i = 1 : length(labelStruct)
    fprintf(out, '%d; %d; %s\n', round(labelStruct(i).row), round(labelStruct(i).col), labelStruct(i).type);
end

fclose(out);

end