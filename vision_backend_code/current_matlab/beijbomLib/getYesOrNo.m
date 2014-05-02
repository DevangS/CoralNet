function answer = getYesOrNo(question)
% function answer = getYesOrNo(question)
% input string question
% output logical answer.
answer = [];
while ~(strcmp(answer, 'y') || strcmp(answer, 'n'))
    answer = input([question ' [y/n] (y default): '],'s');   %input detector
    if isempty(answer)
        answer = 'y';
    end
end

if strcmp(answer, 'y')
    answer = true;
else
    answer = false;
end

end