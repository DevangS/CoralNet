function im=fromrect(im,rect)

im=im(rect(2):(rect(2)+rect(4)),rect(1):(rect(1)+rect(3)),:);