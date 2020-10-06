import SimpleITK as sitk 
import segment
from matplotlib import pyplot as plt


def plot_registration(fixed, moving, fixed_seg=None, moving_seg=None, figsize=(10,15)):
    '''
    '''
    if fixed_seg is None: 
        fixed_seg  = segment.perform_otsu_threshold(fixed)
    
    if moving_seg is None: 
        moving_seg = segment.perform_otsu_threshold(moving)
    
    # make sure not unsigned, we want to allow negative values 
    fixed_seg_show = sitk.Cast(sitk.RescaleIntensity(fixed_seg), sitk.sitkInt8)
    moving_seg_show = sitk.Cast(sitk.RescaleIntensity(moving_seg), sitk.sitkInt8)

    f, axes = plt.subplots(1,3, figsize=figsize)
    axes[0].imshow(sitk.GetArrayViewFromImage(fixed_seg_show))
    axes[0].set_title('fixed segmentation')
    axes[1].imshow(sitk.GetArrayViewFromImage(moving_seg_show))
    axes[1].set_title('moving segmentation')
    diff = fixed_seg_show - moving_seg_show
    axes[2].imshow(sitk.GetArrayViewFromImage(diff))
    axes[2].set_title('difference')
    plt.tight_layout()
    plt.show()
    

def eval_registration(fixed, moving, name, plot=True): 
    '''
    
    '''
    
    overlap_measures_filter = sitk.LabelOverlapMeasuresImageFilter()
    hausdorff_distance_filter = sitk.HausdorffDistanceImageFilter()

    reg_eval = {'name':name}
    
    fixed_seg  = segment.perform_otsu_threshold(fixed)
    moving_seg = segment.perform_otsu_threshold(moving)
        
    if plot: 
        print('review the segmentations to make sure the look appropriate for comparison...')
        plot_registration(fixed, moving, fixed_seg=fixed_seg, moving_seg=moving_seg)

    overlap_measures_filter.Execute(fixed_seg, moving_seg)
    reg_eval['jacaard_coef'] = overlap_measures_filter.GetJaccardCoefficient()
    reg_eval['dice_coef'] = overlap_measures_filter.GetDiceCoefficient()
    reg_eval['volume_similarity'] = overlap_measures_filter.GetVolumeSimilarity()
    reg_eval['false_neg_err'] = overlap_measures_filter.GetFalseNegativeError()
    reg_eval['false_pos_err'] = overlap_measures_filter.GetFalsePositiveError()

    # Hausdorff distance
    hausdorff_distance_filter.Execute(fixed_seg, moving_seg)
    reg_eval['hausdorff_dist'] = hausdorff_distance_filter.GetHausdorffDistance()
    
    return reg_eval