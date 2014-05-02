function fileContent = readHovdingInputFile(filepath)
% fileContent = readHovdingInputFile(filepath)
%
%
% Input:
% filepath should contain file path to a .txt file.
% readHovdingInputFile reads file specified by filepath. It will only
% extract rows that contain a '='.
%
% Output:
% fileContent.identifier is the string stored before the '='.
% fileContent.value is the string stored after the '='
%
% Exception: If the string after the '=' is initiated with a '[',
% readHovdingInputFile will convert the string to a double.
% readHovdingInputFile can handle these inputs also if they contain
% multiple rows. It will read until it encounters a ']'.
% The .value field will then be stored in a matrix, also with double
% precision


fileContent = struct('identifier', [], 'value', []);

fid = fopen(filepath, 'r');
if (fid == -1)
    return
end

fileContent = [];
thisoutput = 1;
while 1
    thisline = fgetl(fid);
    if thisline == -1
        break
    end
    if isempty(thisline)
        continue
    end
    if isempty(strfind(thisline, '='))
        continue
    end


    thisline = remove_blanks_at_beginning_of_file(thisline);
    w = strread(thisline, '%s', 'delimiter', '=');

    for i = 1:length(w)
        w{i} = strtrim(w{i});
    end
    identifier = w{1};
    
    if length(w) == 1
        value = [];
    else
        value = w{2};
    end

    if (~isempty(value) && value(1) == '[' && value(end) ~=']')

        value = []; lastchar = 'dummy';
        thisline = fgetl(fid);
        while lastchar ~= ']'
            thisline = strtrim(thisline);
            thisline = replacecommas(thisline);
            value = [value; str2num(thisline)]; %#ok<ST2NM,AGROW>
            thisline = fgetl(fid);
            lastchar = thisline(end);
        end

    else
        %kollar om den inl�sta raden �r en vektor. D� sparas identifier som
        %en double ist�llet f�r som en string.
        if (~isempty(value) && strcmp(value(1), '['))
            value = replacecommas(value);
            value = str2num(value); %#ok<ST2NM>
        end
    end

    fileContent(thisoutput).identifier = identifier; %#ok<AGROW>
    fileContent(thisoutput).value = value; %#ok<AGROW>
    thisoutput = thisoutput + 1;

end
fclose(fid);
end