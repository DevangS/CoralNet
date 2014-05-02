function adj=taliAdjust(work,val,flag,percen)

%flag 1 to use stretchlim

if (nargin == 2)
    flag=1;
    percen=[0.01 0.99];
elseif (nargin == 3)
    percen=[0.01 0.99];
end

minn=min(work(:));
work=work-minn;
work=work./max(work(:));
minw=min(min(work));
minw=minw(:);
maxw=max(max(work));
maxw=maxw(:);
if (flag==1)
    adj=imadjust(work,stretchlim(work,percen),[],val);
elseif(flag==2)
    if(size(work,3)==3)
        adj=imadjust(work,[minw'; maxw'],[0 0 0;1 1 1],val);
    else
        adj=imadjust(work,[minw'; maxw'],[0 ; 1],val);
    end
end
