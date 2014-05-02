function c_vals= rgb2ch(vals)

if (isempty(find(vals)))
    c_vals=vals;
    
else
    
    if (ndims(vals)==3) % Determine if input includes a 3-D array
        
        sum_vals=sum(vals,3);
        c_vals=bsxfun(@rdivide,vals,(sum_vals+eps));
        
    elseif (ndims(vals)==2)
        % rgb should be in columns
        sum_vals=sum(vals,2);
        c_vals=bsxfun(@rdivide,vals,(sum_vals+eps));
        
    end
end

