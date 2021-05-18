'''
This script removes dust from dapi images by creating a mask of values greater than a user specified value. 

Values greater than this value are set to zero. 

All 'c1' images will be processsed. 
'''

from atpbar import atpbar
from mantichora import mantichora
import numpy as np
import pandas as pd 
import SimpleITK as sitk
import os 
import shutil
import argparse

import sys, os
sys.path.append('../libs/')
import utils

def dedust(info, args, pbar, config): 
    '''

    '''

    # load image 
    im = utils.myload(args.input[0] + '/' + info.original, sitk.sitkUInt16)

    # gaussian blur to avoid grabbing random high intesnity pixels 
    gaussian = sitk.DiscreteGaussianImageFilter()
    gaussian.SetVariance( (config.dedust_gaussian_var, config.dedust_gaussian_var) )
    im_blur  = gaussian.Execute ( im )

    # create mask image
    # should really use quantile or something... 
    mask = im_blur > np.quantile(sitk.GetArrayFromImage(im_blur).flatten(), config.dust_thresh_quantile) #100

    # create mask filter 
    filt = sitk.MaskImageFilter()
    filt.SetMaskingValue(1)
    filt.SetOutsideValue(0)

    # modify image
    im2 = filt.Execute(image=im, maskImage=mask) 

    # rescale image 
    im2 = sitk.RescaleIntensity(im2)

    # save image
    sitk.WriteImage(im2, args.output[0] + '/' + info.original)


if __name__ == '__main__': 

    # parse command line arguments
    parser = argparse.ArgumentParser(description='CyclicIF registration of a full slide')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='directory of input files (.tif slide scenes)')
    parser.add_argument('--output', metavar='out', type=str, nargs=1,
                        help='directory of output files (registered cores)')
    parser.add_argument('--slide', metavar='slide', type=str, nargs=1,
                        help='slide name (identifier)')
    parser.add_argument('--scene', 
                        metavar='scene', 
                        type=str, 
                        nargs=1,
                        help='scene name (identifier)',
                        default=['None']) # necessary if there is no scene name provided
    parser.add_argument('--config', 
                        dest='config_path', 
                        type=str, 
                        nargs=1,
                        default='None',
                        help='path to the directory where local config.py file is stored')
                
    args = parser.parse_args()

    print('#'*100)
    print('#'*100)
    print('input directory:', args.input[0])
    print('output directory:', args.output[0])
    print()

    config = utils.load_config(args.config_path[0])

    img_file_names = [x for x in os.listdir(args.input[0]) if x[-4:] == '.tif']
    parsed_names = pd.DataFrame([utils.parse_file_name(x) for x in img_file_names])

    # filter to only slide/scene
    parsed_names = parsed_names[lambda x: (x.slide_name == args.slide[0]) & (x.scene == args.scene[0])]

    # multithreading
    with mantichora(mode='threading', nworkers=16) as mcore:
        info = parsed_names[lambda x: (x.color_channel == 'c1')].reset_index(drop=True)
        pbar = iter(atpbar(range(info.shape[0] + 1), 'dedusting dapi images'))
        next(pbar)
        for i, row in info.iterrows():  
            mcore.run(dedust, row, args, pbar, config)
        returns = mcore.returns()
        for i in pbar:
            pass

    # move all other images into output folder
    if args.input[0] != args.output[0]:
        other = parsed_names[lambda x: (x.color_channel != 'c1')]
        for _path in atpbar(other.original.values, 'copying c2+ channels to output folder'):
            shutil.copyfile(args.input[0] + '/' + _path, args.output[0] + '/' + _path)

    print('#'*100)
    print('#'*100)