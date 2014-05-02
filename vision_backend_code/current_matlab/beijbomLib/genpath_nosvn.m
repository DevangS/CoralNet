function pathstring = genpath_nosvn(rootdir)
    pathstring = rootdir;
    dirs = dir(rootdir);
    for i = 3:length(dirs)
        if ~strcmp(dirs(i).name, '.svn') && dirs(i).isdir
            thisdir = strcat(rootdir, filesep, dirs(i).name);
            pathstring = [pathstring ';' thisdir]; %#ok<AGROW>
            pathstring = genpath_nosvn_recursive(strcat(thisdir), pathstring); %#ok<AGROW>
        end
    end
end


function pathstring = genpath_nosvn_recursive(rootdir, pathstring)
    dirs = dir(rootdir);
    for i = 3:length(dirs)
        if ~strcmp(dirs(i).name, '.svn') && dirs(i).isdir
        thisdir = strcat(rootdir, filesep, dirs(i).name);
        pathstring = [pathstring ';' thisdir]; %#ok<AGROW>
        pathstring = genpath_nosvn_recursive(thisdir, pathstring); %#ok<AGROW>
        end
    end
end