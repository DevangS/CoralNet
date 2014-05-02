function cs = setupCoralDetection(dataBase, varargin)

switch dataBase
    
    case('lter')
        labelParams.cats = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit'};
        labelParams.id = [1 2 3 4 5 6 7 8 9 9 9 9];
        labelParams.catsOrg = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit', 'P. Irr', 'P. Rus', 'P mass'};
        
        plotParams.colors = 'bcgrrgbcm';
        plotParams.markers = '^^^^ooooo';
        plotParams.sizes = [5 5 5 5 5 5 5 5 5];
        plotParams.predSizes = [15 15 15 15 15 15 15 15];
        
        dataDir = fullfile(getdirs('datadir'), '/Coral/LTER-MCR/organised');
        locationKeys = {'database', 'lter', 'habitat', 'pole', 'qu', 'date'};
        nPointsPerFile = 200;
        
        dictIndex = 1:3:671;
        resizeFactor = 2;
        content = makeCoralContent(dataDir, locationKeys);
        
        content = [content([content.year] == 2008); content([content.year] == 2009); content([content.year] == 2010); content([content.year] == 2011)];
        doCrop = 0;
        
    case('lter_color')
        labelParams.cats = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit'};
        labelParams.id = [1 2 3 4 5 6 7 8 9 9 9 9];
        labelParams.catsOrg = {'CCA', 'Turf', 'Macro', 'Sand', 'Acrop', 'Pavon', 'Monti', 'Pocill', 'Porit', 'P. Irr', 'P. Rus', 'P mass'};
        
        plotParams.colors = 'bcgrrgbcm';
        plotParams.markers = '^^^^ooooo';
        plotParams.sizes = [5 5 5 5 5 5 5 5 5];
        plotParams.predSizes = [15 15 15 15 15 15 15 15];
        
        dataDir = fullfile(getdirs('datadir'), '/Coral/LTER-MCR/organised');
        locationKeys = {'database', 'lter', 'habitat', 'pole', 'qu', 'date'};
        nPointsPerFile = 200;
        
        
        resizeFactor = 2;
        content = makeCoralContent(dataDir, locationKeys);
        
        content = content([content.year] == 2011);
        
        validCCids = false(numel(content), 1);
        for cItt = 1 : numel(content)
            validCCids(cItt) = exist(fullfile(dataDir, strcat(content(cItt).imgFile, '.ccvals')), 'file');
        end
        
        content = content(validCCids);
        
        dictIndex = 1 : 3 : numel(content);
        doCrop = 1;
        
    case('ams')
        
        labelParams.cats = {'ENC', 'BR', 'MASS', 'FOL', 'TAB', 'CCAH', 'TURFH', 'TURFR', 'HARD', 'EMA', 'UPMA', 'HAL', 'WAND', 'SAND', 'SHAD'};
        labelParams.field = 'type';
        labelParams.id = 1 : length(labelParams.cats);
        labelParams.names = {'ENC', 'BR', 'MASS', 'FOL', 'TAB', 'CCAH', 'TURFH', 'TURFR', 'HARD', 'EMA', 'UPMA', 'HAL', 'WAND', 'SAND', 'SHAD'};
        
        % ^ is algae, o is coral, > is wand shadow and sand
        plotParams.colors =  'rgbcmkrgbrgbrgb';
        plotParams.markers = 'ooooo<<<<>>>xxx';
        plotParams.sizes = 10 * ones(length(plotParams.colors), 1);
        plotParams.predSizes = 15 * ones(length(plotParams.colors), 1);
        
        nPointsPerFile = 10;
        resizeFactor = 2.3;
        
        % setup the content
        dataDir = fullfile(getdirs('datadir'), 'Coral/NOAA_CRED/american_samoa/organised');
        
        locationKeys = {'database', 'site', 'date', 'transect', 'qu'};
        content = makeCoralContent(dataDir, locationKeys);
        
        
        testFiles = (struct_strcmp(content, 'transect', 'T1') | struct_strcmp(content, 'transect', 'T2'));
        trainFiles = ~(struct_strcmp(content, 'transect', 'T1') | struct_strcmp(content, 'transect', 'T2'));
        content = [content(trainFiles); content(testFiles)];
        
        load('~/e/Data/Coral/NOAA_CRED/american_samoa/oddSizeInd.mat')
        
        content = content(~oddSizeInd);
        
        trainFiles = find(~(struct_strcmp(content, 'transect', 'T1') | struct_strcmp(content, 'transect', 'T2')));
        dictIndex = rowVector(trainFiles(1:10:end));
        doCrop = 0;
        
        
    case('line')
        
        labelParams.cats = {'Acrop', 'Monti', 'Pocill', 'Porit', 'Mille'};
        labelParams.id = 1 : length(labelParams.cats);
        labelParams.catsOrg = {'Acrop', 'Monti', 'Pocill', 'Porit', 'Mille'};
        
        % ^ is algae, o is coral, > is wand shadow and sand
        plotParams.colors =  'rgbcm';
        plotParams.markers = 'ooooo';
        plotParams.sizes = 10 * ones(length(plotParams.colors), 1);
        plotParams.predSizes = 15 * ones(length(plotParams.colors), 1);
        
        nPointsPerFile = 100;
        resizeFactor = 2;
        doCrop = 0;
        
        % setup the content
        dataDir = fullfile(getdirs('datadir'), 'Coral/inter_operator_study/Lineislands/organised');
        
        locationKeys = {'database', 'island', 'site', 'qu', 'date'};
        content = makeCoralContent(dataDir, locationKeys);
        dictIndex = 1 : 3 : numel(content);
        
    case('taiwan')
        
        labelParams.cats = {'Acrop', 'Monti', 'Pocill', 'Porit', 'Mille'};
        labelParams.id = 1 : length(labelParams.cats);
        labelParams.catsOrg = {'Acrop', 'Monti', 'Pocill', 'Porit', 'Mille'};
        
        nPointsPerFile = 50;
        resizeFactor = 2.44;
        doCrop = 0;
        plotParams = [];
        % setup the content
        dataDir = fullfile(getdirs('datadir'), 'Coral/inter_operator_study/Taiwan/organised');
        
        locationKeys = {'database', 'imgnbr', 'date', 'orgname'};
        content = makeCoralContent(dataDir, locationKeys);
        dictIndex = 1 : 3 : numel(content);
        
    otherwise
        error('unknown dataBase entry')
        
        
end

comment = '';

[varnames, varvals] = var2varvallist(labelParams, plotParams, content, dictIndex, comment);
[labelParams, plotParams, content, dictIndex, comment] = varargin_helper(varnames, varvals, varargin{:});

cs.params.nPointsPerFile = nPointsPerFile;
cs.content = content;
cs.params.plot = plotParams;
cs.params.labelParams = labelParams;
cs.dataDir = dataDir;
cs.params.resizeFactor = resizeFactor;
cs.params.fileNbrs = 1 : length(content);
cs.params.crop.do = doCrop;
cs.params.crop.nbrPixels = 0;

cs.params.featureParams.prep.handle = 'filterImageForDictionary';
cs.params.featureParams.prep.fileIndex = dictIndex;
cs.params.featureParams.prep.maxNbrSamples = 200000;
cs.params.featureParams.prep.maxRuntime = 60 * 60;
cs.params.featureParams.prep.nbrFilesPerCommit = 5;

load '~/e/Data/Coral/LTER-MCR/groundTruth_vals.mat';
groundTruth_vals = groundTruth_vals([13:24 1:6],:); %#ok<NODEF>
cs.params.featureParams.preprocess.type = 'eachColorchannelStretch';
cs.params.featureParams.preprocess.low = 0.01;
cs.params.featureParams.preprocess.high = 0.99;
cs.params.featureParams.preprocess.trueColorMethod = 'affine_RGB_linear';
cs.params.featureParams.preprocess.ccValsGT = groundTruth_vals;
cs.params.featureParams.preprocess.ccVals = [];
cs.params.featureParams.preprocess.ccType = 1;
cs.params.featureParams.preprocess.removeNans = 0;

cs.params.featureParams.framecrop.do = 0;
cs.params.featureParams.nbrTextons = 15;
cs.params.featureParams.uniTexton = 0;
cs.params.featureParams.color.cspace = 'lab';
cs.params.featureParams.color.channels = 1:3;
cs.params.featureParams.handle = 'featuresClassic';
cs.params.featureParams.filterParams.stds = [1 3 8 3];
cs.params.featureParams.filterParams.oriented = [1 1 1 0];
cs.params.featureParams.patchSize = [10 30 60 110];
cs.params.featureParams.maxRuntime = 60 * 60;
cs.params.featureParams.nbrFilesPerCommit = 10;


cs.params.errorParams.type = 'simple';

cs = setupFixedFields(cs);
cs.fileinfo.name = 'cs';
cs.comment = comment;
cs = saveDataStruct(cs);

end

function cs = setupFixedFields(cs)
% a kind of generic, setup file that sets standard values and creates
% dictionaries.


cs.params.featureParams(1).filterOutputDim = 2 * length(cs.params.featureParams(1).filterParams.stds) * length(cs.params.featureParams(1).color.channels);
cs.stats.nbrClasses = length(cs.params.labelParams.cats);
cs.stats.nbrDims = cs.stats.nbrClasses * cs.params.featureParams(1).nbrTextons;

featureParams = cs.params.featureParams(1);
filterMeta.F = makeRFSfilters(featureParams.filterParams.stds, featureParams.filterParams.oriented);

filterMeta.Fids = [];
for i = 1 : sum(featureParams.filterParams.oriented)  * 2
    filterMeta.Fids = [filterMeta.Fids ; ones(6,1) * i];
end
for i = sum(featureParams.filterParams.oriented)  * 2 + 1: length(featureParams.filterParams.oriented) * 2
    filterMeta.Fids = [filterMeta.Fids ; ones(1,1) * i];
end
filterMeta.nbrOriented = sum(featureParams.filterParams.oriented);
filterMeta.nbrCircular = sum(~featureParams.filterParams.oriented);

cs.featurePrep{1}.filterMeta = filterMeta;


end
