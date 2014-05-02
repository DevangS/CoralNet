function mappedX = visualizeDataWithTSNE(data, labels)
% function visualizeDataWithTSNE(data, labels)

mappedX = tsne(data, []);

gscatter(mappedX(:,1), mappedX(:,2), labels, [], 'o');


end