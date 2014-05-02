function [h,det] = plotRoc( D, varargin )
% Function for display of rocs (receiver operator characteristic curves).
%
% Displays nice clearly visible curves. Consistent usage ensures uniform
% look for rocs. The input D should have n rows, each of which is of the
% form [false-positive rate true-positive rate]. D is generated, for
% example, by scanning a detection threshold over n values from 0 (so first
% entry in D is [1 1]) to 1 (so last entry is [0 0]). Alternatively D can
% be a cell vector of rocs, in which case an average ROC will be shown with
% error bars.
%
% USAGE
%  [h,det] = plotRoc( D, prm )
%
% INPUTS
%  D    - [nx2] n data points along roc (falsePos/truePos)
%  prm  - [] param struct
%   .color    - ['g'] color for curve
%   .lineSt   - ['-'] linestyle (see LineSpec)
%   .lineWd   - [4] curve width
%   .logx     - [0] use logarithmic scale for x-axis
%   .logy     - [0] use logarithmic scale for y-axis
%   .marker   - [''] marker type (see LineSpec)
%   .mrkrSiz  - [12] marker size
%   .nMarker  - [5] number of markers (regularly spaced) to display
%   .lims     - [0 1 0 1] axes limits
%   .smooth   - [0] if T compute lower envelop of roc to smooth staircase
%   .fpTarget - [-1] if>0 plot line and return detection rate at given fp
%
% OUTPUTS
%  h    - plot handle for use in legend only
%  det  - detection rate at fpTarget (if fpTar specified)
%
% EXAMPLE
%  k=2; x=0:.0001:1; data1 = [1-x; (1-x.^k).^(1/k)]';
%  k=3; x=0:.0001:1; data2 = [1-x; (1-x.^k).^(1/k)]';
%  hs(1)=plotRoc(data1,struct('color','g','marker','s'));
%  hs(2)=plotRoc(data2,struct('color','b','lineSt','--'));
%  legend( hs, {'roc1','roc2'} ); xlabel('fp'); ylabel('fn');
%
% See also
%
% Piotr's Image&Video Toolbox      Version 2.41
% Copyright 2009 Piotr Dollar.  [pdollar-at-caltech.edu]
% Please email me if you find bugs, or have suggestions or questions!
% Licensed under the Lesser GPL [see external/lgpl.txt]

% get params
[ color lineSt lineWd logx logy marker mrkrSiz nMarker lims smooth  ...
  fpTarget] = getPrmDflt( varargin, {'color' 'g' 'lineSt' '-' ...
  'lineWd' 4 'logx' 0 'logy' 0 'marker' '' 'mrkrSiz' 12 'nMarker' 5 ...
  'lims' [] 'smooth' 0 'fpTarget', -1} );
if( isempty(lims) ); lims=[logx*1e-5 1 logy*1e-5 1]; end

% flip to plot miss rate, optionally 'nicefy' roc
if(~iscell(D)), D={D}; end; nD=length(D);
for j=1:nD, D{j}(:,2)=max(eps,1-D{j}(:,2))+.001; end
if(smooth); for j=1:nD, D{j}=smoothRoc(D{j}); end; end

% plot: (1) h for legend only, (2) roc curves, (3) markers, (4) error bars
hold on; axis(lims);
prmMrkr = {'MarkerSize',mrkrSiz,'MarkerFaceColor',color};
prmClr={'Color',color}; prmPlot = [prmClr,{'LineWidth',lineWd}];
h = plot( 2, 0, [lineSt marker], prmMrkr{:}, prmPlot{:} ); %(1)
if(nD==1), D1=D{1}; else D1=mean(quantizeRoc(D,100,logx,lims),3); end
plot( D1(:,1), D1(:,2), lineSt, prmPlot{:} ); %(2)
DQ = quantizeRoc( D, nMarker, logx, lims ); DQm=mean(DQ,3);
if(~isempty(marker))
  plot(DQm(:,1),DQm(:,2),marker,prmClr{:},prmMrkr{:} ); end %(3)
if(nD>1), DQs=std(squeeze(DQ(:,2,:)),0,2);
  errorbar(DQm(:,1),DQm(:,2),DQs,'.',prmClr{:}); end %(4)

% plot line at given fp rate
if(fpTarget<=0), det=-1; else
  if(D1(1,2)>D1(end,2)), D1=flipud(D1); end
  [d,i]=max(D1(:,1)<fpTarget); det=D1(i,2);
  plot([fpTarget fpTarget],[lims(3) lims(4)],'b-');
end

% set log axes
if( logx==1 )
  ticks=10.^(-8:0);
  set(gca,'XScale','log','XTick',ticks);
end
if( logy==1 )
  ticks=[.001 .002 .005 .01 .02 .05 .1 .2 .5 1];
  set(gca,'YScale','log','YTick',ticks);
end
if( logx==1 || logy==1 )
  set(gca,'XMinorGrid','off','XMinorTic','off');
  set(gca,'YMinorGrid','off','YMinorTic','off');
end

end

function DQ = quantizeRoc( D, nPnts, logx, lims )
if(iscell(D))
  nD=length(D); DQ=zeros(nPnts,2,nD);
  for j=1:nD, DQ(:,:,j)=quantizeRoc(D{j},nPnts,logx,lims); end
  return;
end

if( logx==1 )
  locs = logspace(log10(lims(1)),log10(lims(2)),nPnts);
else
  locs = linspace(lims(1),lims(2),nPnts);
end
DQ = [locs' ones(length(locs),1)];

loc=1; D=[1 0; D; 0 1]; D=max(0,min(D,1));
for i=length(locs):-1:1
  fpCur = DQ(i,1);
  while( loc<size(D,1) && D(loc,1)>=fpCur ), loc=loc+1; end
  dN=D(loc,:); if(loc==1); dP=D(loc,:); else dP=D(loc-1,:); end
  distP=dP(1)-fpCur; distN=fpCur-dN(1); r=distN/(distP+distN);
  DQ(i,2) = r*dP(2) + (1-r)*dN(2);
end
DQ = flipud(DQ);
end

function D1 = smoothRoc( D )
D1 = zeros(size(D));
n = size(D,1); cnt=0;
for i=1:n
  isAnkle = (i==1) || (i==n);
  if( ~isAnkle )
    dP=D1(cnt,:); dC=D(i,:); dN=D(i+1,:);
    isAnkle = (dC(1)~=dP(1)) && (dC(2)~=dN(2));
  end
  if(isAnkle); cnt=cnt+1; D1(cnt,:)=D(i,:); end
end
D1=D1(1:cnt,:);
end
