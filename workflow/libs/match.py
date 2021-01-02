import pandas as pd 
import SimpleITK as sitk 
from scipy.stats import zscore

# config is depreccated, this must be passed as config object 
# import config
 
import segment
#from k_means_constrained import KMeansConstrained # need to cite - https://github.com/joshlk/k-means-constrained
import numpy as np
from sklearn.cluster import DBSCAN

def get_all_rounds_core_statistics(info, imgs, config=None, verbose=True, return_R0_dapi=False):
    '''
    info             dataframe          general full round image information, `parsed_names3` in tutorial
    imgs             dict               dict matching round image file name to image, `imgs` in tutorial 
    verbose          boolean            print msgs 
    return_R0_dapi   boolean            whether to return the downsampled R0-c1 (dapi) image 
    '''
    assert config is not None, 'config is none, pass a config object'
    
    # select dapi channel only
    dapi_names = info[(info.color_channel == 'c1')]

    _res = []
    R0_dapi = None 
    for name in dapi_names.original.values: 

        if verbose: print('processing: ', name)
            
        dapi = imgs[name][::config.downsample_proportion,::config.downsample_proportion]
        dapi_stats, shape_stats = segment.segment_dapi_round(dapi, config=config, verbose=verbose, plot=False)

        dapi_stats = dapi_stats.assign(img_name = name)

        assert dapi_stats.shape[0] > 0, f'empty dapi_stats dataframe - error in {name}'

        _res.append(dapi_stats)
        
        if 'R0_' in name:
            assert R0_dapi is None, 'multiple assignments to R0_dapi when there should only be one - check image naming convention'
            R0_dapi = dapi

    if verbose: print('concatenating...')
    res = pd.concat(_res, axis=0)

    if verbose: print('merging...')
    res = res.merge(info, left_on='img_name', right_on='original', how='left')
    
    if return_R0_dapi: 
        if verbose: print('returning res, R0_dapi')
        assert R0_dapi is not None, 'could not identify R0 dapi in `match.get_all_rounds_core_statistics`' 
        return res, R0_dapi
    else: 
        return res 

def match_cores_across_rounds(info, verbose=True, config=None, eps=None): 
    '''
    info    dataframe 
    
    returns ndarray matching each observation in `info` with it's assigned cluster. 
    '''
    assert config is not None, 'config is none, pass config object'
    
    method = config.clustering_method
    # number of labels in R0_dapi - use this for the # of clusters (k)
    num_R0_components = info[info['round'] == 'R0'].component.unique().shape[0]
    
    # maximum number of components allowed in a cluster 
    num_of_rounds = info['round'].unique().shape[0]

    # data to fit 
    X = info[config.feats].values
    
    # zscore the data 
    _mean = X.mean(axis=0)
    _std = X.std(axis=0) 
    X = (X - _mean)/_std
    
    # scale feature importance 
    X = X * config.feat_importance

    # initial cluster seeds will be R0 centers 
    seeds = ((info[info['round'] == 'R0'][config.feats].values - _mean)/_std) * config.feat_importance
    
    if verbose: print('using clustering method:', method)
        
    if method == 'k-means-constrained': 
        print('this method is deprecated, use method "dbscan"')
        # https://github.com/joshlk/k-means-constrained
        #clus = KMeansConstrained(n_clusters=num_R0_components, init=seeds, size_max=num_of_rounds, n_init=1, tol=1e-8, max_iter=1000)
        #_ = clus.fit(X)
        raise ValueError('invalid clustering method- use dbscan')

    elif method == 'dbscan':
        if eps is not None: 
            clus = DBSCAN(eps=eps, min_samples=config.min_samples).fit(X)
        else: 
            clus = DBSCAN(eps=config.eps, min_samples=config.min_samples).fit(X)
        
    else: 
        raise ValueError('choose an appropriate clustering method from: "dbscan", "k-means-constrained"')
        
    # TODO: check that every cluster has a R0 [and not doubles from any round]
    
    return clus.labels_ + 1

    
    
    
