'''
This script holds general meta data & configuration paths required for pipeline operation 
'''

## Tutorial config 

image_dir_path = '/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/data/' 

####################################################################################
############################## core segmentation ###################################
####################################################################################

# image downsampling for core segmentation 
# default ~10 
downsample_proportion = 10

# remove connected components that are smaller than this 
# REMEMBER THIS SCALES WITH `downsample_proportion`
# NOTE: this may need to be adjusted for different core sizes or types 
# default ~ 2000
min_obj_size = int( 5e4 / downsample_proportion )

# threshold value used to select core regions (after a gaussian blur) 
# default ~ 0.75
core_seg_quantile = 0.75

# padding used when selecting a core, eg selects core bounding box + 2*padding
# default ~ 10
padding = 10

# segmentation params 
# default ~ 3.5e-3
gaussian_blur_variance = 3.5e-3

# core matching clustering method
# options: 'k-means-constrained', 'dbscan' 
# note: k-means-constrained has issues if later rounds have more identified cores 
# default ~ dbscan
clustering_method = 'dbscan'

# IF DBSCAN
# minimum distance between points to be considered within the same neighborhood 
# NOTE: this is dependent on the downsample_proportion
# default ~ 500
eps = int( 500 / downsample_proportion )
min_samples = 2

####################################################################################
################################### GENERAL ########################################
####################################################################################
# this isn't used anywhere - YET - SimpleITK does use spacing, but I haven't changed it yet - worried how it might change results

pixel_width = 0.65 # microns
pixel_height = 0.65 # microns 

####################################################################################
############################## REGISTRATION ########################################
####################################################################################

num_hist_bins = 50
learning_rate = 1e-3
min_step = 1e-9
iterations = 100
sampling_percentage = 1.0

####################################################################################
############################## QUALITY CONTROL #####################################
####################################################################################

FPR_threshold = 0.5
FNR_threshold = 0.5
hausdorff_distance_threshold = 0.2





