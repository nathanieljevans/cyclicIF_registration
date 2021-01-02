import SimpleITK as sitk
from matplotlib import pyplot as plt 
from matplotlib import patches as patches
import pandas as pd
import numpy as np
import utils
import warnings


def segment_dapi_round(img, config=None, plot=False, verbose=False): 
    '''
    This includes gaussian blur 
    
    plot = verbose and plotting
    '''
    assert config is not None, 'config is none, pass config object'

    if verbose: print('rescaling img..')
    img = sitk.RescaleIntensity(img)

    img = sitk.Cast(img, sitk.sitkUInt8)

    # add a blur to eliminate small componentns
    # variance of ~ 1e-6 = almost no effect
    # ~1e-4 is appropriate <- no downsampling
    # ~1e-3 with 10x downsamping 
    
    if verbose: print('applying gaussing blur...')
    gaussian = sitk.DiscreteGaussianImageFilter()
    gaussian.SetVariance( (config.gaussian_blur_variance, config.gaussian_blur_variance) )
    gaussian.SetMaximumKernelWidth(1000)
    img_blur = gaussian.Execute ( img )

    #if plot: print('otsu thresholding...')
    #otsu_filter = sitk.OtsuThresholdImageFilter()
    #otsu_filter.SetInsideValue(0)
    #otsu_filter.SetOutsideValue(1)
    #seg = otsu_filter.Execute(img_blur)
    
    seg_thresh = np.quantile(sitk.GetArrayViewFromImage(img_blur).ravel(), config.core_seg_quantile)
    seg = img_blur > seg_thresh
    
    if plot:
        plt.figure()
        plt.title('pixel intensity histogram')
        plt.hist(sitk.GetArrayViewFromImage(img_blur).ravel(), bins=100)
        plt.axvline(seg_thresh, c='r', label='threshold')
        plt.legend()
        plt.show()

        utils.myshow(seg)

    #if plot: print('watershed threshold...')
    #stats = sitk.LabelShapeStatisticsImageFilter()
    #stats.Execute(sitk.ConnectedComponent(seg))
    
    # get connected components
    cc = sitk.ConnectedComponent(seg)
    
    # remove small components 
    cc = sitk.RelabelComponent(cc, minimumObjectSize = config.min_obj_size)
    
    # THIS DOESN'T WORK HERE - need to apply the mask on the original image in select_core() - but can't use a downsampled mask ... 
    # set non-segmented regions to zero in order to avoid artifacts included in padding
    #mask = cc > 0 
    #if plot: utils.myshow(mask)
    #maskFilter = sitk.MaskImageFilter()
    #cc = maskFilter.Execute(cc, mask) 
    
    if plot: utils.myshow(cc, title='filtered connected components') 
    
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(cc)
    
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



def select_core(img, label, stats, config=None, scale=1): 
    '''
    takes full round image, and retrieves the label region of interest, as specified by shape stats. Optional scaling if using downsampled image for segmentation. 
    '''
    assert config is not None, 'config is none, pass config object'

    _max_x, _max_y = img.GetSize()
    
    stats = stats[stats.component == label]
    
    if stats[['center_x','center_y','width','height']].drop_duplicates().shape[0] > 1: 
        
        if len(label) > 1:
            #warnings.warn('Two or more core components from the same round were assigned to the one cluster. Only the first component will be used. Consider tuning the segmentation parameters to prevent this in the future.')
            stats = stats[stats.component == label.values[0]]
        else: 
            raise ValueError(f'`select_core` got an ambiguous number of bounding box stats, try filtering dataframe to a single round prior to selecting cores')
            
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
    

def plot_cores(img, stats, config): 
    '''
    '''
    ncomp = len(stats.component.unique())
    rowsize = 10 if ncomp > 10 else ncomp
    nrows = int(ncomp / 10 + 1)
    f,axes = plt.subplots(nrows, rowsize, figsize=(15,15))

    for i,(label,ax) in enumerate(zip(stats.component.unique(), axes.flat)): 
        print(f'progress: {i}/{len(stats.component.unique())}', end='\r')
        roi = select_core(img, label, stats, config=config)
        
        ax.imshow(sitk.GetArrayViewFromImage(roi))
        ax.set_title(label)
        ax.set_axis_off()

    #plt.tight_layout()
    plt.show()
    
    
def perform_otsu_threshold(img): 
    '''
    This generates a core segmentation used for evaluating registration success metrics. 
    '''
    #img = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt16)

    otsu_filter = sitk.OtsuThresholdImageFilter()
    otsu_filter.SetInsideValue(0)
    otsu_filter.SetOutsideValue(1)
    seg = otsu_filter.Execute(img)

    return seg

def generate_core_id_map(img, stats, config=None, plot=True): 
    '''
    Generate a downsampled image of R0-C1 (dapi) image where each core bounding box is labeled with it's corresponding identifier. 
    
    inputs: 
    img            <sitk.image>       should be the downsampled image of R0-C1 (dapi) from which shape statistics were calculated. 
    stats          <pd.dataframe>     shape statistics calculated during image segmentation
    
    outputs: 
    shape statistic results [, downsampled R0-c1 (dapi) image] 
    '''
    assert config is not None, 'config is none, pass config object'

    out = config.output_dir + '/' + config.slide_name + '/' + config.scene_name

    img = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)
    
    img_arr = sitk.GetArrayViewFromImage(img)
        
    # Create figure and axes
    fig,ax = plt.subplots(1, figsize=(15,15))

    # Display the image
    ax.imshow(img_arr)
    
    for i, row in stats.iterrows(): 
        
        rect = patches.Rectangle((row.center_x, row.center_y), row.width, row.height, linewidth=2, edgecolor='r', facecolor='none')
        ax.add_patch(rect)
        plt.text(row.center_x, row.center_y - 10, f'core-{int(row.component)}', c='w')

    plt.axis('off')
    
    if out is not None: 
        print('saving to:', out)
        fig.savefig(out + '/core_id_mapping.png')
        
    if plot: 
        print('plotting')
        plt.show()
        
    plt.close('all')


