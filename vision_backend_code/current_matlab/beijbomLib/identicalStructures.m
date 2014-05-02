function t = identicalStructures(s1, s2)
%------------------------------------------------------------------------
% IDENTICALSTRUCTURES Takes two structs as input and compares them.
%  Uses recursive calls to compare substructs.
%
% Synopsis:
%  t = identicalStructures(s1, s2)
%
% 2008-10-20, Oscar Beijbom
% 2009-03-10, Edited: Henrik Blidh
%------------------------------------------------------------------------

% Kollar först storleken på s1 och s2
s1size = size(s1);
s2size = size(s2);
if sum(s1size ~= s2size) > 0
    t = 0;
    return;
end
if length(s1size) > 2
    error('Can only handle 1d or 2d structures.');
end
t = 1;

% Går därefter igenom hela s1 och s2;
for i = 1:s1size(1)
    for j = 1:s1size(2)
        if (checkonestruct(s1(i,j), s2(i,j)) == 0)
            t = 0;
            return;
        end
    end
end

end

function t = checkonestruct(s1,s2)

t = 1;
f1 = fields(s1);
f2 = fields(s2);

% Kollar så att det är samma längd
if ( length(f1) ~= length(f2) )
    t = 0;
    return
end

% Kollar så att alla namnen finns i båda
for i = 1:length(f1)
    thisname = f1{i};
    temp = 0;
    for j = 1:length(f2)
        thatname = f2{j};
        if strcmp(thatname, thisname)
            temp = 1;
        end
    end
    t = temp && t;
end

% Kollar så att samma värden lagras i samma fältnamn.
for i = 1:length(f1)
    r1 = s1.(f1{i});
    r2 = s2.(f1{i});
    b1 = isstruct(r1);
    b2 = isstruct(r2);
    if ( b1 && b2 )
        t = identicalStructures(r1, r2);
        if ~t
            return;
        end
        continue;
    elseif ( b1 && ~ b2) || ( ~b1 && b2 )
        t = 0;
        return;
    end
    % Om de är celler måste element gås igenom en efter en.
    if iscell(r1)
        sizeCell1 = size(r1);
        sizeCell2 = size(r2);
        if ( sum(sizeCell1 - sizeCell2) ~= 0 )
            t = 0;
            return;
        end
        for k = 1:sizeCell1(1)
            for kk = 1:sizeCell1(2)
                % Måste först kolla om elementen i 
                % cellen är structar.
                bb1 = isstruct(r1{k,kk});
                bb2 = isstruct(r2{k,kk});
                if ( bb1 && bb2 )
                    t = identicalStructures(r1{k,kk}, r2{k,kk});
                    if ~t
                        return;
                    end
                    continue;
                elseif ( bb1 && ~ bb2) || ( ~bb1 && bb2 )
                    t = 0;
                    return;
                end
                if ~ischar(r1{k,kk})
                    if ( r1{k,kk} ~= r2{k,kk} )
                        t = 0;
                        return;
                    end
                else
                    if ( ~strcmp(r1{k,kk}, r2{k,kk}) )
                        t = 0;
                        return;
                    end
                end
            end
        end
    else
        % Kontrollera först om r är funktionshandles. Om så är 
        % fallet, kovertera till sträng och jämför.
        if isa(r1, 'function_handle')
            if ( ~strcmp(char(r1),char(r2)) )
                t = 0;
                return;
            end
        elseif ~ischar(r1)
            try
                if (sum(size(r1) - size(r2)) == 0)    
                    if ( r1 ~= r2 )
                        t = 0;
                        return;
                    end
                else
                    t = 0;
                    return;
                end
            catch
                1;
            end
        else
            if ( ~strcmp(r1, r2) )
                t = 0;
                return;
            end
        end
    end
end

end

