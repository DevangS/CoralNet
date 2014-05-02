function labels = parseTxtFile(filepath, scale)

fid = fopen(filepath);
str = fgetl(fid);
fclose(fid);

k = strfind(str, ';');
k = [0 k];
fields = {'type', 'cat', 'col', 'row'};

labels = struct('cat', [], 'type', [], 'row', [], 'col', []);
for i = 1 : length(k) - 1
    thisStr = str(k(i)+1:k(i+1)-1);
    kk = strfind(thisStr, ',');
    kk = [0 kk length(thisStr) + 1];
    for j = 1:4
       labels(i).(fields{j}) = thisStr(kk(j) + 1:kk(j+1)-1);
    end
    labels(i).row = round(str2double(labels(i).row)/scale);
    labels(i).col = round(str2double(labels(i).col)/scale);
end

end
