function index = struct_strcmp(struct, field, string)
% function index = struct_strcmp(struct, field, string)
%
% [string] field determines which field that should be compared to [string]
% string. Field can be used with .notation e.g
% struct_strcmp(myStruct, 'field.subfiled', 'myString').
% struct_strcmp then loops through the field.subfield vector and returns
% true for those instances that the field matches 'myString'.
%

index = false(length(struct),1);
w = strread(field, '%s', 'delimiter', '.');
for i = 1:length(struct)

    thisstruct = struct(i);
    for j = 1 : length(w) - 1
        thisstruct = thisstruct.(w{j});
    end
    index(i) = strcmp(thisstruct.(w{end}), string);
end
end