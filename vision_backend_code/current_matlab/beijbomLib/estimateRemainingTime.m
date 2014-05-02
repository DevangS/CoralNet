function remainingtime = estimateRemainingTime(starttime, thistime, nbriterations, thisiteration, doPrint)
% remainingtime = estimateRemainingTime(starttime, thistime, nbriterations,
% thisiteration, doPrint)
% Times should be entered in the format obtained by function CLOCK.

remainingtime = zeros(1,6);
elapsedtime = zeros(1,6);

elapsedTotal = thistime - starttime;
%g�r om till sekunder!

elapsedSeconds = elapsedTotal(6) + elapsedTotal(5) * 60 + elapsedTotal(4) * 3600 + elapsedTotal(3) * 3600 * 24 + elapsedTotal(2) * 3600 * 24 * 30;

secondsPerIteration = elapsedSeconds / thisiteration;

remainingSeconds = round(secondsPerIteration * (nbriterations - thisiteration));

mods = [365*30*24*60*60 30*24*60*60 24*60*60 60*60 60 1];

for i = 1:6

    remainingtime(i) = floor ( remainingSeconds / (mods(i)) );
    remainingSeconds = mod ( remainingSeconds, mods(i) );

end

for i = 1:6

    elapsedtime(i) = floor(elapsedSeconds / (mods(i)));
    elapsedSeconds = mod(elapsedSeconds,mods(i));

end

if doPrint

    fprintf(1, 'Current time: %s. ', datestr(clock, 31));
    
    fprintf(1, '%s', '[');
    printTime(elapsedtime, 'ymdhms', 'elapsed, ');

    printTime(remainingtime, 'ymdhms', 'remaining');
    fprintf(1, '%s\n', ']');
    
end
end


function printTime(e, labels, info)
for i = 1:6
    if ~(e(i) == 0)
        fprintf(1,'%d%s', e(i), labels(i));
        if i ~= 6
            fprintf(1,'%s', ', ')
        else
            fprintf(1,'%s', ' ')
        end
    end
end
fprintf(1, info);

end