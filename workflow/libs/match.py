import pandas as pd 
import SimpleITK as sitk 
import config 
import segment
from k_means_constrained import KMeansConstrained # need to cite - https://github.com/joshlk/k-means-constrained
import numpy as np
from sklearn.cluster import DBSCAN

def get_all_rounds_core_statistics(info, imgs, verbose=True):
    '''
    info    dataframe   general full round image information, `parsed_names3` in tutorial
    imgs    dict        dict matching round image file name to image, `imgs` in tutorial 
    '''
    
    dapi_names = info[(info.color_channel == 'c1')]

    res = []
    for name in dapi_names.original.values: 

        if verbose: print('processing: ', name)
            
        dapi = imgs[name][::config.downsample_proportion,::config.downsample_proportion]
        dapi_stats, shape_stats = segment.segment_dapi_round(dapi)

        dapi_stats = dapi_stats.assign(img_name = name)
        res.append(dapi_stats)

    res = pd.concat(res, axis=0)

    res = res.merge(info, left_on='img_name', right_on='original', how='left')
    res.head()
    
    return res 

def match_cores_across_rounds(info, verbose=True, method=config.clustering_method): 
    '''
    info    dataframe 
    
    returns ndarray matching each observation in `info` with it's assigned cluster. 
    '''
    
    # number of labels in R0_dapi - use this for the # of clusters (k)
    num_R0_components = info[info['round'] == 'R0'].component.unique().shape[0]
    
    # maximum number of components allowed in a cluster 
    num_of_rounds = info['round'].unique().shape[0]
    
    # features to use for clustering 
    feats = ['center_x', 'center_y'] #,'Intensity Mean', 'Volume (nm^3)'] # 'width', 'height', 
    
    # data to fit 
    X = info[feats].values
    
    # zscore the data 
    #_mean = X.mean(axis=0)
    #_std = X.std(axis=0) 
    #X = (X - _mean)/_std
    
    # scale feature importance 
    #X = X * np.array([10,10,1,1])

    # initial cluster seeds will be R0 centers 
    seeds = info[info['round'] == 'R0'][feats].values
    
    if verbose: print('using clustering method:', method)
        
    if method == 'k-means-constrained': 
        # https://github.com/joshlk/k-means-constrained
        clus = KMeansConstrained(n_clusters=num_R0_components, init=seeds, size_max=num_of_rounds, n_init=1, tol=1e-8, max_iter=1000)
        _ = clus.fit(X)
    
    elif method == 'dbscan':
        clus = DBSCAN(eps=config.eps, min_samples=config.min_samples).fit(X)
        
    else: 
        raise ValueError('choose an appropriate clustering method from: "dbscan", "k-means-constrained"')
        
    # TODO: check that every cluster has a R0 [and not doubles from any round]
    

    return clus.labels_ + 1

    
    
    