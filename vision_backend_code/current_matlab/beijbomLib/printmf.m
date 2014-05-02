function printmf(fids, varargin)
% printmf(fids, varargin)
% input a vector with fids and printmf will print to all fids, using normal
% fprintf format syntax. Printmf stands for print multiple fids.

for i = 1:length(fids)
    if ~(fids(i) == 0)
        fprintf(fids(i), varargin{:});
    end
end

end