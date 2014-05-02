function nextnumber = findnextfilenumber(directory, fileNameCore, suffix, isDir)
%
% nextnumber = findNextFileNumber(directory, filenamecore, suffix, (optional) isDir)
%
% Finds next filenumber in the given directory, with the given filenamecore
% and the given suffix (without the dot!). If no such file exist, nextnumber is set to 1.
% Can be used to find the next directory as well. In this case use '' as
% suffix and isDir = 1.

if (nargin < 4)
    isDir = false;
end

largestnumber = 0;
FNCLength = length(fileNameCore);
filelist=dir(directory);
for i = 3:length(filelist)
    
    if  (~filelist(i).isdir && ~isDir) || (filelist(i).isdir && isDir)
        thisFile = filelist(i).name;
        thisFileWithoutFilesuffix = remove_filesuffix(thisFile);
        thisFileCore = thisFile(1 : min(length(thisFileWithoutFilesuffix), FNCLength));

        thisFileSuffix = get_filesuffix(thisFile);
        % fprintf(1, '\nNew File.\n');
        % fprintf(1, 'file: %s\n', thisFile)
        % fprintf(1, 'fileCore: %s\n', thisFileCore)
        % fprintf(1, 'filesuffix: %s\n', thisFileSuffix)


        if ( ( strcmp(thisFileSuffix, suffix) && strcmp(thisFileCore, fileNameCore) ) || ( strcmp(thisFileCore, fileNameCore) && isempty(suffix) && isempty(thisFileSuffix)))
            % fprintf(1, 'match found!!!\n');

            numberStr = thisFileWithoutFilesuffix(FNCLength + 1 : end);
            if (length(numberStr) == sum(isdigit(numberStr)))
                
                number = str2double(thisFileWithoutFilesuffix(FNCLength + 1 : end));
                % fprintf(1, 'filewithoutsuffix: %s\n', thisFileWithoutFilesuffix)
                % fprintf(1, 'thisfilenumber: %.3f\n', number)
                if number > largestnumber;
                    largestnumber = number;
                end
            end
        end
    end
end

nextnumber=largestnumber+1;
end



