function [content M] = makeCoralContent(dataDir, keys)

logger('Making content-struct for %s\n', dataDir);

if(sum(strcmp(keys, 'date')) == 0)
    error('"keys" cell array must contain field "date"');
end

% Initialize content structure
content = struct('year', cell(length(dir(dataDir)), 1), 'imgFile', 0, 'labelFile', 0);
for i = 1 : length(keys)
    content(1).(keys{i}) = [];
end

% initialize hash map
M = java.util.HashMap;

nKeys = length(keys);

%%% GO THROUGH ALL TXT FILES AND PUT IN HASH MAP
txtfiles = dir(fullfile(dataDir, '*.txt'));

for i = 1 : length(txtfiles)
    
    %%% PARSE FILE NAME
    fname = txtfiles(i).name;
    k = strfind(fname, '_');
    if(length(k) ~= (nKeys - 1))
        continue
    end
    
    dotPos = strfind(fname, '.');
    k = [0 k dotPos(1)]; % pad with zero and end
    hashkey = [];
    for f = 1 : length(keys)
        if strcmp(keys{f}, 'date') % grab only the first four, the year.
            hashkey = [hashkey '-' fname(k(f)+1:k(f)+4)];
        else
            hashkey = [hashkey '-' fname(k(f)+1:k(f+1)-1)];
        end
    end
    
    %%% PUT IN HASH MAP
    if(~isempty(M.put(hashkey, fname)))
        error('hash map collision');
    end
end


%%% NOW GO THROUGH ALL IMAGES FILES AND MATCH TO TXT FILES
imgExtensions = {'jpg', 'JPG', 'png', 'PNG'};
imgfiles = [];
for i = 1 : length(imgExtensions)
   imgfiles = [imgfiles; dir(fullfile(dataDir, sprintf('*.%s', imgExtensions{i})))];
end

contPos = 0;

for i = 1 : length(imgfiles)
    
    %%% PARSE FILE NAME
    fname = imgfiles(i).name;
    k = strfind(fname, '_');
    if(length(k) ~= (nKeys - 1))
        continue
    end
        
    dotPos = strfind(fname, '.');
    k = [0 k dotPos(1)]; % pad with zero and end
    hashkey = [];
    for f = 1 : length(keys)
        if strcmp(keys{f}, 'date') % grab only the first four, the year.
            hashkey = [hashkey '-' fname(k(f)+1:k(f)+4)];
        else
            hashkey = [hashkey '-' fname(k(f)+1:k(f+1)-1)];
        end
    end
    
    %%% FIND CORRESPONDING TEXT FILE
    txtfile = M.put(hashkey, fname);
    if (isempty(txtfile))
        fprintf(1, 'Image file %s does not have an annotation file.\n', fname);
        continue
    end
    
    if (~strcmp(txtfile(end-2:end), 'txt'))
        fprintf(1, 'Keys for file %s already matched with different image file.\n', fname);
        figure(1)
        subplot(121);
        imagesc(imread(fullfile(dataDir, fname)));
        subplot(122);
        imagesc(imread(fullfile(dataDir, txtfile)));
        if(getYesOrNo('Do these look the same? Can I delete one?'))
            delete(fullfile(dataDir, fname));
        end
        continue
    end
    
    
    % Now we create the content entry.
    contPos = contPos + 1;
    for f = 1 : length(keys)
        content(contPos).(keys{f}) = fname(k(f)+1:k(f+1)-1);
    end
    content(contPos).year = str2double(content(contPos).date(1:4));
    content(contPos).labelFile = txtfile;
    content(contPos).imgFile = fname;
    
end

content = content(1:contPos);
logger('done!');
end
