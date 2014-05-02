function [labelCount, allLabels] = coralLabelStats(dataDir, content)

%%% crawl annotations
allLabels = {};
labelCount = [];

c = content;
fprintf(1, 'Checking fileNbr:');
for fileNbr = 1 : length(c);
    fprintf(1, '%d, ', fileNbr);
    if (mod(fileNbr, 30) == 0)
        fprintf(1, '\n');
    end
    fid = fopen(fullfile(dataDir, c(fileNbr).labelFile), 'r');
    line = fgetl(fid);
    while(line ~= -1)
        
        if(~strcmp(strtrim(line(1)), '#'))
            [~, ~, type] = strread(line, '%d%d%s', 'delimiter', ';');
            comp = strcmp(allLabels, type{1});
            if (sum(comp) == 0)
                allLabels = [allLabels type];
                labelCount = [labelCount 1];
            else
                labelCount(comp) = labelCount(comp) + 1;
            end
        end
        line = fgetl(fid);
        
    end
    fclose(fid);
end
fprintf(1, '\n');

%%% visualize annotations
[~, ind] = sort(labelCount, 'descend');
labelCount = labelCount(ind);
allLabels = allLabels(ind);
bar(labelCount);

for i = 1:length(labelCount)
    
    fprintf(1, '%s: %.4f\n', allLabels{i}, labelCount(i) / sum(labelCount));
    
end



