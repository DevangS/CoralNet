function t = isdigit(c)

    t = ischar(c) & ('0' <= c) & (c <= '9');
    
end