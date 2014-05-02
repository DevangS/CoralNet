load('/home/beijbom/cnhome/images/models/r.meta.mat', '-mat')


m = loadjson(savejson('' , meta));

m2 = loadjson(savejson('' , m));



m3 = loadjson(savejson('' , m2));



%%
works = struct('root', struct('root2', struct('root3', [1 2]')));
works_out = loadjson(savejson('' , works));

doesnt_work = struct('root', struct('root2', struct('root3', [1 2])));
doesnt_work_out = loadjson(savejson('' , doesnt_work));


% s = , []);
% 
% f = fopen('./jsonlab', 'w');
% fprintf(f, '%s', s);
% fclose(f);
