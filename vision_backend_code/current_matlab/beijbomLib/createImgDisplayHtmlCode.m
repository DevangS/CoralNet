function createImgDisplayHtmlCode(thisDir, imSize, nbrImgsPerPage, fontSize, doSortNat)
% createImgDisplayHtmlCode(thisDir, imSize, nbrImgsPerPage)
%
% INPUT thisDir specifies this directory
% imSize is a 1x2 vector specifying nbrPixels the images should be.
% valid img extenxions
% nbrImgsPerPage specifies how many images to display per page.
%
% [optionals] 
% fontSize. Default = 1.
% doSortNat. Default = 1.
% createImgDisplayHtmlCode supports images file extensions:
% {'jpg', 'png', 'gif', 'bmp', 'tiff', 'ppm', 'pnm', 'ppm', 'tif', 'eps'};
%
%
%
 
if nargin < 4
    fontSize = 1;
end

if nargin < 5
    doSortNat = true;
end

% make sure the directory is valid
if (~isdir(thisDir))
    disp('INPUT thisDir not a valid directory');
    return
end

% read images
imgFileExtensions = {'jpg', 'png', 'gif', 'bmp', 'tiff', 'ppm', 'pnm', 'ppm', 'tif', 'eps'};
images = [];
for i = 1:length(imgFileExtensions)
    images = [images; dir(fullfile(thisDir, strcat('*.', imgFileExtensions{i})))]; %#ok<AGROW>
end

if(isempty(images))
    return
end

% sort in natural order
temp = struct2cell(images);
if (doSortNat)
    imageNames = sort_nat(temp(1, :)); %sort_nat is availible at matlab file exchange.
else
    imageNames = temp(1, :); %sort_nat is availible at matlab file exchange.
end        

totalNbrImages = length(imageNames);
nbrPages = ceil(totalNbrImages / nbrImgsPerPage);

for imgNbr = 0 : length(imageNames) - 1
    
    if (mod(imgNbr, nbrImgsPerPage) == 0)
        if (imgNbr == 0)
            fid = fopen(fullfile(thisDir, 'index.html'), 'w');
            fprintf(fid, '<html><head>\n');
            fprintf(fid, '</head><body bgcolor="Black">\n');            
        else
            fprintf(fid, '</body></html>\n'); %end body and html.
            fclose(fid); %close the old fid
            fid = fopen(fullfile(thisDir, strcat(num2str(imgNbr/ nbrImgsPerPage), '.html')), 'w'); %open a new
            fprintf(fid, '<html><head>\n');
            fprintf(fid, '</head><body bgcolor="Black">\n');
        end
        % create menu bar
        fprintf(fid, '<p><FONT COLOR="White">Page: <a href="index.html"> 0 </a>');
        for thisPageNbr = 1 : nbrPages - 1
            fprintf(fid, '<FONT COLOR="White"> <a href="%d.html"> %d </a>', thisPageNbr, thisPageNbr);
        end
        fprintf(fid, '</p>');
    end
    
    %place the imageNames.
    fprintf(fid, '<table class="image" align="left" style="margin-left: 0.5em">');
    fprintf(fid, '<caption align="bottom"><FONT COLOR="White"><font size="%d">%s</font></caption><tr><td>', fontSize, imageNames{imgNbr + 1});
    fprintf(fid, '<img src = "./%s" width = "%d" height = "%d" border = "0"></a>', imageNames{imgNbr + 1}, imSize(1), imSize(2));
    fprintf(fid, '</td></tr></table>\n');
    
end
fprintf(fid, '<html><head>\n'); %end body and html.
fclose(fid); %close the old fid

end
