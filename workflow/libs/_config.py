'''
This script holds general meta data & configuration paths required for pipeline operation 
'''
import os 
import numpy as np

# comment out the next line to use in an experiment
#assert False, 'you are importing the template config.py file, import your local experiment specific file'

####################################################################################
############################## experiment details ##################################
####################################################################################

## path parameters -- These MUST be adjusted to your specific dataset 
myloc=       '/mnt/e/CycIF_analysis/registration_outputs/6-Dhivya/D4'            # location of this script (WSL file structure) 
data_dir=    '../../test_de-dusted/'#'/mnt/z/Marilyne/Axioscan/6-Dhivya/split/No_Scene/'  # location of the unregistered images 

# Specify the experiment here
slide_name=  'D1'
scene_name=  'None'                                                              # use 'None' to specify no scene name (cap sensitive)

# These paths probably don't need to be adjusted
lib_dir=     '/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/libs'
script_dir=  '/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/scripts'
output_dir=   '/mnt/e/CycIF_analysis/registration_outputs/test_core_reg'

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
padding = 25

# segmentation params 
# larger values will create more blur 
# rational range is 1e-2 to 1e-4
# default ~ 3.5e-3
gaussian_blur_variance = 1

# core matching clustering method
# options: 'k-means-constrained', 'dbscan' 
# note: k-means-constrained has issues if later rounds have more identified cores 
# default ~ dbscan
clustering_method = 'dbscan'

# IF DBSCAN
# minimum distance between points to be considered within the same neighborhood 
# NOTE: this is dependent on the downsample_proportion
# default ~ 500
eps = 0.12
min_samples = 2

feats = ['center_x', 'center_y']
feat_importance = np.array([1,1])

####################################################################################
################################### GENERAL ########################################
####################################################################################
# this isn't used anywhere - YET - SimpleITK does use spacing, but I haven't changed it yet - worried how it might change results

pixel_width = 0.65 # microns
pixel_height = 0.65 # microns 

####################################################################################
############################## REGISTRATION ########################################
####################################################################################

num_hist_bins = 256
learning_rate = 1
min_step = 1e-10
iterations = 500
sampling_percentage = 1.0

####################################################################################
############################## QUALITY CONTROL #####################################
####################################################################################

QC_dice_coef = 0.4    # this is the one uesd in `generate_QC_file.py` 12/30/2020
FPR_threshold = 0.5
FNR_threshold = 0.5
hausdorff_distance_threshold = 0.2

####################################################################################
##############################  DEDUST PARAMS  #####################################
####################################################################################

dedust_gaussian_var = 1e-1
dust_thresh_quantile = 0.999


