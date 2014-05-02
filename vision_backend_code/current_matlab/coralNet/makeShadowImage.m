%% make content

dataDir = fullfile(getdirs('datadir'), '/Coral/LTER-MCR/organised');
locationKeys = {'database', 'lter', 'habitat', 'pole', 'qu', 'date'};
content = makeCoralContent(dataDir, locationKeys);

%% load images and resize them
n = 10; %number of image to overlay, no need to use all of them
targetsize = 1000; % choose this to be e.g. the dims of the first image.
ind = randsample(numel(content), n); %choose n images randomly form all availible images.
Isum = zeros(targetsize, targetsize, 3); % target image.
for i = 1 : numel(ind) % for each image
   
    I = double(imread(fullfile(dataDir, content(ind(i)).imgFile))); % load image
    for channel = 1:3 % for each channel
        Ic = I(:,:,channel) ./ max(max(I(:,:,channel))); %normalize each channel to max = 1
        Isum(:,:,channel) = Isum(:,:,channel) + (imresize(Ic, [targetsize targetsize])); % add it to the target image
    end
    
end

Isum = Isum ./ n; %re-normalize the target image.
%%
imagesc(Isum)
axis image
% colormap(gray)

% export_fig('./shadowimage', '-jpg');