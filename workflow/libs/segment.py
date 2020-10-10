import SimpleITK as sitk
from matplotlib import pyplot as plt 
import config
import pandas as pd
import numpy as np

def segment_dapi_round(img, plot=False): 
    '''
    This includes gaussian blur 
    
    plot = verbose and plotting
    '''
    if plot: print('rescaling img..')
    img = sitk.RescaleIntensity(img)
    img = sitk.Cast(img, sitk.sitkUInt8)

    # add a blur to eliminate small componentns
    # variance of ~ 1e-6 = almost no effect
    # ~1e-4 is appropriate <- no downsampling
    # ~1e-3 with 10x downsamping 
    
    if plot: print('applying gaussing blur...')
    gaussian = sitk.DiscreteGaussianImageFilter()
    gaussian.SetVariance( config.gaussian_blur_variance )
    img_blur = gaussian.Execute ( img )

    #if plot: print('otsu thresholding...')
    #otsu_filter = sitk.OtsuThresholdImageFilter()
    #otsu_filter.SetInsideValue(0)
    #otsu_filter.SetOutsideValue(1)
    #seg = otsu_filter.Execute(img_blur)
    
    seg_thresh = np.quantile(sitk.GetArrayViewFromImage(img_blur).ravel(), config.core_seg_quantile)
    seg = img_blur > seg_thresh
    
    plt.figure()

    if plot:
        plt.figure()
        plt.hist(sitk.GetArrayViewFromImage(img_blur).ravel(), bins=100)
        plt.axvline(seg_thresh, c='r')
        plt.show()
        
        plt.figure(figsize=(7,7))
        plt.imshow(sitk.GetArrayViewFromImage(seg))
        plt.show()

    #if plot: print('watershed threshold...')
    #stats = sitk.LabelShapeStatisticsImageFilter()
    #stats.Execute(sitk.ConnectedComponent(seg))
    
    # get connected components
    cc = sitk.ConnectedComponent(seg)
    
    # remove small components 
    cc = sitk.RelabelComponent(cc, minimumObjectSize = config.min_obj_size)
    
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(cc)
    
    if plot: 
        plt.figure(figsize=(7,7))
        plt.title('otsu connected components')
        plt.imshow(sitk.GetArrayViewFromImage(cc))
        plt.show()
        
    if plot: 'calculating stats...'
    shape_stats = sitk.LabelShapeStatisticsImageFilter()
    shape_stats.ComputeOrientedBoundingBoxOn()
    shape_stats.Execute(cc)

    intensity_stats = sitk.LabelIntensityStatisticsImageFilter()
    intensity_stats.Execute(cc, img)

    stats_list = [ (shape_stats.GetBoundingBox(i)[0],
                    shape_stats.GetBoundingBox(i)[1],
                    shape_stats.GetBoundingBox(i)[2],
                    shape_stats.GetBoundingBox(i)[3],
                    shape_stats.GetPhysicalSize(i),
                   shape_stats.GetElongation(i),
                   shape_stats.GetFlatness(i),
                   shape_stats.GetOrientedBoundingBoxSize(i)[0],
                   shape_stats.GetOrientedBoundingBoxSize(i)[1], # switched from 2->1, was getting tuple out of bounds issue
                   intensity_stats.GetMean(i),
                   intensity_stats.GetStandardDeviation(i),
                   intensity_stats.GetSkewness(i)) for i in shape_stats.GetLabels() ]

    cols=["center_x",
          "center_y",
          "width", 
          "height",
          "Volume (nm^3)",
          "Elongation",
          "Flatness",
          "Oriented Bounding Box Minimum Size(nm)",
          "Oriented Bounding Box Maximum Size(nm)",
         "Intensity Mean",
         "Intensity Standard Deviation",
         "Intensity Skewness"]

    # Create the pandas data frame and display descriptive statistics.
    stats = pd.DataFrame(data=stats_list, index=shape_stats.GetLabels(), columns=cols)
    
    stats = stats.assign(component=lambda x: x.index)
    
    return stats, shape_stats

def select_core(img, label, stats, scale=1): 
    '''
    takes full round image, and retrieves the label region of interest, as specified by shape stats. Optional scaling if using downsampled image for segmentation. 
    '''
    
    _max_x, _max_y = img.GetSize()
    
    stats = stats[stats.component == label]
        
    assert stats[['center_x','center_y','width','height']].drop_duplicates().shape[0] == 1, 'ambiguous number of bounding box stats, try filtering dataframe to a single round prior to selecting core' 
    
    x = stats.center_x.values[0]
    y = stats.center_y.values[0]
    width = stats.width.values[0]
    height = stats.height.values[0]

    index = (max(0, scale * (x - int(config.padding / 2)))       ,  max(0, scale *  (y - int(config.padding / 2))))
    size =  (min(_max_x-index[0], scale *  (width + config.padding)), min(_max_y-index[1], scale * (height + config.padding )))
    
    index = [int(x) for x in index]
    size =  [int(x) for x in size]
    
    roi = sitk.RegionOfInterest(img, size, index)
    
    return roi
    

def plot_cores(img, stats): 
    '''
    '''
    nrows = int(len(stats.component.unique()) / 10 + 1)
    f,axes = plt.subplots(nrows,10, figsize=(15,15))

    for i,(label,ax) in enumerate(zip(stats.component.unique(), axes.flat)): 
        print(f'progress: {i}/{len(stats.component.unique())}', end='\r')
        roi = select_core(img, label, stats)
        
        ax.imshow(sitk.GetArrayViewFromImage(roi))
        ax.set_title(label)
        ax.set_axis_off()

    #plt.tight_layout()
    plt.show()
    
    
def perform_otsu_threshold(img): 
    '''
    This generates a core segmentation used for evaluating registration success metrics. 
    '''
    img = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

    otsu_filter = sitk.OtsuThresholdImageFilter()
    otsu_filter.SetInsideValue(0)
    otsu_filter.SetOutsideValue(1)
    seg = otsu_filter.Execute(img)
    return seg


