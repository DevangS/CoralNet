function labelSetBarPlot(labelSet, count)

b = bar(count);
bb = get(b, 'Parent');
set(bb, 'XTick', 1:length(count));
set(bb, 'XTickLabel', labelSet);

xticklabel_rotate();
xlabel('label');
ylabel('count');
title('Label count');

end