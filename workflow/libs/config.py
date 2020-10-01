'''
This script holds general meta data & configuration paths required for pipeline operation 
'''

## Tutorial config 

image_dir_path = '/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/data/' 
downsample_proportion = 10

# Seeds have a distance of "radius" or more to the object boundary, they are uniquely labelled.
radius = 0

# for watershed segmentation, remove connected components that are smaller than this 
min_obj_size = 1000

## General configs 

pixel_width = 0.65 # microns
pixel_height = 0.65 # microns 

# padding for selecting a core
padding = 100