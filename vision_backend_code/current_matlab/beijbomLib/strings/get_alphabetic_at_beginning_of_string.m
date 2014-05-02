function n = get_alphabetic_at_beginning_of_string(name)
%keeps the beginning of NAME until first nonalphabetic character is
%encountered.

pos=1;
while pos <= length(name) && isletter(name(pos))
    pos=pos+1;
end
n=name(1:pos-1);
end