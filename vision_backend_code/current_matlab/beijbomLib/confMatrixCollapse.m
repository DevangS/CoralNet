function CMout = confMatrixCollapse(CM, classMap)
% CMout = confMatrixCollapse(CM, classMap)
%
% INPUT CM is a confusion matrix (with actual counts, not ratios)
% INPUT classMap is an int vector mapping each old class to a new class,
% e.g. [1 1 1 2 2 3 4], maps the first three classes to a first new class, the
% next two to a second new class and the last two each to new classes.
% 
% NOTE: BY setting clasmap indexes to 0, these classes are
% removed from the matrix.
%

nOldClasses = size(CM, 1);

if length(classMap) ~= nOldClasses
    error('length of INPUT classMap must be same a the number of input claaes(size of CM)');
end


nNewClasses = max(classMap);

CMint = zeros(nOldClasses, nNewClasses);
CMout = zeros(nNewClasses);
for i = 1 : nNewClasses
 
    CMint(:, i) = sum(CM(:, (classMap == i)), 2);
    
end


for i = 1 : nNewClasses
 
    CMout(i, :) = sum(CMint((classMap == i), :), 1);
    
end

end