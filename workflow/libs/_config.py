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
myloc=        os.getcwd()   # location of this script (WSL file structure) 
data_dir=   './pre-registered_imgs/' # otherwise use this 
# data_dir =  '/mnt/z/Marilyne/Axioscan/6-Dhivya/New_folder/Test_D1/' # use this if examining images before pre-registration via tutorial.ipynb

# Specify the experiment here
slide_name=  'D1'
scene_name=  'None'                                                                  # use 'None' to specify no scene name (cap sensitive)

# These paths probably don't need to be adjusted
lib_dir=     '/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/libs'
script_dir=  '/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/scripts'
output_dir=  '/mnt/d/cyclicIF_outputs/6_Dhivya/D1/registered_imgs/'    # this is path to registered cores

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
min_obj_size = int( 4e4 / downsample_proportion )

# threshold value used to select core regions (after a gaussian blur) 
# default ~ 0.75
core_seg_quantile = 0.74 # (Dhiva D1) #0.785 (Pejovic)

# padding used when selecting a core, eg selects core bounding box + 2*padding
# default ~ 10
padding = 20

# segmentation params 
# larger values will create more blur 
gaussian_blur_variance = 4000

# core matching clustering method
# options: 'k-means-constrained', 'dbscan' 
# note: k-means-constrained has issues if later rounds have more identified cores 
# default ~ dbscan
clustering_method = 'dbscan'

# IF DBSCAN
# minimum distance between points to be considered within the same neighborhood 
eps = 0.12   # (pejovic~0.15)
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
learning_rate = 1e-1   # deprecated - not used in powell optimizer
min_step = 1e-10       # deprecated - not used in powell optimizer
iterations = 500
sampling_percentage = 1.0 # x100% 
stepLength=1
stepTolerance = 1e-7
valueTolerance = 1e-7

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


