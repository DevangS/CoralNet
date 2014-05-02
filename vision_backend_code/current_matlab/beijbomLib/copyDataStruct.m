function ds = copyDataStruct(ds)
% function ds = copyDataStruct(ds)
%
% copyDataStruct copies data struct ds (as created by saveDataStruct) into
% a new copy with the same content
%

name = ds.fileinfo.name;

ds = rmfield(ds, 'fileinfo');

ds.fileinfo.name = name;

ds = saveDataStruct(ds);

end