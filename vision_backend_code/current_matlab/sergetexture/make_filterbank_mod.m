function [FB,M1,M2,N3]=make_filterbank_mod(params, resizeFactor)
% multi-scale even and odd filters

scales = params.sigmaScales ./ resizeFactor;

nbrPixels = round(max(scales) * 9);

if(mod(nbrPixels, 2) == 0)
    nbrPixels = nbrPixels + 1;
end


M1 = nbrPixels;	% size in pixels
M2 = M1;
num_ori=6;
num_scales=3;
num_phases=2;
N3=num_ori*num_scales*num_phases;
FB=zeros(M1,M2,N3);

counter=1;

for m = scales
   for n=1:num_ori
      [F1,F2]=quadpair(sqrt(2)^m,2,180*(n-1)/num_ori,M1);
      FB(:,:,counter)=F1;
      counter=counter+1;
      FB(:,:,counter)=F2;
      counter=counter+1;
   end
end

FB=cat(3,FB,dog2(1,M1),dog2(sqrt(2),M1),dog2(2,M1),dog2(2*sqrt(2),M1));

N3=size(FB,3);

% stuff for visualizing spectra of filters:
if 0
FBF=zeros(size(FB));

for n=1:36
   FBF(:,:,n)=abs(fftshift(fft2(FB(:,:,n))));
end

montage2(FBF)

im(sum(FBF,3))

end
