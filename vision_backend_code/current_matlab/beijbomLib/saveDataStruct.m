function thisStruct = saveDataStruct(thisStruct)

if nargin < 2
    useHovdingTestDataDir = 0;
end

%check for neccesary fileinfo.
if ~isfield(thisStruct, 'fileinfo')
    error('Cant find field "fileinfo".');
end

if ~isfield(thisStruct.fileinfo, 'name')
    error('Cant find field "fileinfo.name".');
end

try
    
    %get directories.
    dataDir = getdirs('testdatadir');
    
    if ~isfield(thisStruct.fileinfo, 'date')
        thisStruct.fileinfo.date = datestr(date,29);
        disp(['Date set to todays date [' num2str(datestr(date,29)) '].'])
    end
    
    dateDir = strcat(dataDir, thisStruct.fileinfo.date);
    
    if ~exist(dateDir, 'dir')
        mkdir(dateDir);
        fprintf(1, 'Directory %s created.\n', dateDir);
    end
    
    if ~isfield(thisStruct.fileinfo, 'number')
        thisStruct.fileinfo.number = findnextfilenumber(dateDir, thisStruct.fileinfo.name, '', 1);
        fprintf(1, 'Filenumber set to %d.\n', thisStruct.fileinfo.number);
    end
    
    thisDir = strcat(dateDir, filesep, thisStruct.fileinfo.name, num2str(thisStruct.fileinfo.number));
    
    if ~exist(thisDir, 'dir')
        mkdir(thisDir);
        fprintf(1, 'Directory %s created.\n', thisDir);
    end
    
    %crete filename from info
    thisStruct.fileinfo.dir = strcat(thisStruct.fileinfo.name, num2str(thisStruct.fileinfo.number));
    thisStruct.fileinfo.filename = strcat(thisStruct.fileinfo.date, '_', num2str(thisStruct.fileinfo.dir));
    thisStruct.fileinfo.shortId = strcat(thisStruct.fileinfo.date(6:7), thisStruct.fileinfo.date(9:10), thisStruct.fileinfo.dir);
    thisStruct.fileinfo.DD = fullfile(thisStruct.fileinfo.date, thisStruct.fileinfo.dir);
    
    % keep a log over when this file has been saved
    if (~(isfield(thisStruct.fileinfo, 'savelog')))
        thisStruct.fileinfo.savelog = clock;
    else
        thisStruct.fileinfo.savelog = [thisStruct.fileinfo.savelog ; clock];
    end
    
    %order fields
    thisStruct.fileinfo = orderfields(thisStruct.fileinfo);
    thisStruct = orderfields(thisStruct);
    
    %rename structure to thisstruct.fileinfo.name.
    eval([thisStruct.fileinfo.name ' = thisStruct;'])
    
    %save file
    fprintf('[Saving file: %s%sdata.mat...', thisDir, filesep);
    
    inf = whos(thisStruct.fileinfo.name);
    
    if inf.bytes < 100000000
        save(strcat(thisDir, filesep, 'data.mat'), thisStruct.fileinfo.name);
    else
        save(strcat(thisDir, filesep, 'data.mat'), thisStruct.fileinfo.name, '-v7.3');
    end
    fprintf('done.]\n');
    
    
catch me
    
    disp('Could not save file. Error message:')
    disp(me.message);
    
end



end