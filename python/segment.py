import SimpleITK as sitk
from matplotlib import pyplot as plt 
import config
import pandas as pd

def segment_dapi_round(img, plot=False): 
    '''
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
    gaussian.SetVariance( 1e-2)
    img_blur = gaussian.Execute ( img )

    if plot: print('otsu thresholding...')
    otsu_filter = sitk.OtsuThresholdImageFilter()
    otsu_filter.SetInsideValue(0)
    otsu_filter.SetOutsideValue(1)
    seg = otsu_filter.Execute(img_blur)

    if plot:
        plt.figure(figsize=(7,7))
        plt.imshow(sitk.GetArrayViewFromImage(seg))
        plt.show()

    if plot: print('watershed threshold...')
    stats = sitk.LabelShapeStatisticsImageFilter()
    stats.Execute(sitk.ConnectedComponent(seg))
    
    dist_img = sitk.SignedMaurerDistanceMap(seg != 0, insideIsPositive=False, squaredDistance=False, useImageSpacing=False)

    seeds = sitk.ConnectedComponent(dist_img < -config.radius)
    # Relabel the seed objects using consecutive object labels while removing all objects with less than 15 pixels.
    seeds = sitk.RelabelComponent(seeds, minimumObjectSize= config.min_obj_size)

    # Run the watershed segmentation using the distance map and seeds.
    ws = sitk.MorphologicalWatershedFromMarkers(dist_img, seeds, markWatershedLine=True)
    ws = sitk.Mask(ws, sitk.Cast(seg, ws.GetPixelID()))
    
    if plot: 
        plt.figure(figsize=(7,7))
        plt.imshow(sitk.GetArrayViewFromImage(ws))
        plt.show()
        
    if plot: 'calculating stats...'
    shape_stats = sitk.LabelShapeStatisticsImageFilter()
    shape_stats.ComputeOrientedBoundingBoxOn()
    shape_stats.Execute(ws)

    intensity_stats = sitk.LabelIntensityStatisticsImageFilter()
    intensity_stats.Execute(ws, img)

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
    
    return stats, shape_stats

def select_core(img, label, shape_stats, scale=1): 
    '''
    takes full round image, and retrieves the label region of interest, as specified by shape stats. Optional scaling if using downsampled image for segmentation. 
    '''
    R0_max_x, R0_max_y = img.GetSize()
    
    bbox = shape_stats.GetBoundingBox(label)

    index = (scale * max(0, bbox[0] - int(config.padding / 2))       , scale * max(0, bbox[1] - int(config.padding / 2)))
    size =  (scale * min(R0_max_x-index[0], bbox[2] + config.padding), scale * min(R0_max_x-index[1], bbox[3] + config.padding ))
    
    roi = sitk.RegionOfInterest(img, size, index)
    
    return roi
    

def plot_cores(img, shape_stats): 
    '''
    '''
    nrows = int(len(shape_stats.GetLabels()) / 10 + 1)
    f,axes = plt.subplots(nrows,10, figsize=(15,15))

    for i,(label,ax) in enumerate(zip(shape_stats.GetLabels(), axes.flat)): 
        print(f'progress: {i}/{len(shape_stats.GetLabels())}', end='\r')
        roi = select_core(img, label, shape_stats)
        
        ax.imshow(sitk.GetArrayViewFromImage(roi))
        ax.set_title(label)
        ax.set_axis_off()

    #plt.tight_layout()
    plt.show()


