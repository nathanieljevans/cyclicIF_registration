'''
This script performs a full slide registration. To do this effectively, we follow three steps: 

1. general x-axis slide alighnment 
2. general y-axis slide alignment 
3. translation + rotation registration using mutual information and gradient descent

This attempts to ensure that the global alignment of cores is accurate. 
'''

from atpbar import atpbar
from mantichora import mantichora
import numpy as np
import pandas as pd 
import SimpleITK as sitk
import os 
import shutil
import argparse

import sys
sys.path.append('../libs/')
import utils


def parse_file_name(f): 
    '''
    given a directory of .tif cyclicIF files that follow Marilyne's naming convention - parse them

    input 
        f       str         path to .tif directory 
    
    output 
        dict                parsed file elements 
    '''
    try:
        multiscene = 'Scene' in f
        
        f2 = f.split('_')
        
        R, protein, slide = f2[:3]
        
        date = '-'.join(f2[3:6])
        
        scene='None'
        if multiscene: 
            scan, scene = f2[7].split('-', 1)
        else: 
            scan = f2[7]
            
        color = f2[8]
        note, ftype = f2[9].split('.')
        
        names = "round,protein,slide_name,date,scan_id,scene,color_channel,note,file_type,original".split(',')
        res = {n:v for n,v in zip(names, [R,protein,slide,date,scan,scene,color,note, ftype,f])}
        return res
    except: 
        print('PARSING FAILED - filename: ', f)


def alignment_1d(fixed, moving, axis='x'): 
    '''
    This method sums [x,y] 1 axis and transforms the data as zscore( log10(1+sum(axis)) ). 
    We then use cross correllation to test the optimal shift +/-. 
    The best shift is returned, previously non-existant pixels are introduced as zero values. 

    input
        fixed   sitk.image  the image to align to 
        moving  sitk.image  the image to align
        axis    str         the axis to align, can be 'x' or 'y'

    output 
        int                 optimal number of pxiels to shift 
    '''

    assert axis in ['x', 'y'], 'unrecognized axis type, can be either "x" or "y"'
    _axis={'x':0, 'y':1}

    def get_1d_arr(img):
        img_arr = sitk.GetArrayFromImage(img)
        arr1 = np.log10(np.sum(img_arr, axis=_axis[axis]) + 1) # take column sums - add one to avoid log10(0)
        arr1 = (arr1 - arr1.mean())/arr1.std() # zscore to try and normalize - adjust for differences in intensities
        return arr1

    fixed_arr = get_1d_arr(fixed)
    moving_arr = get_1d_arr(moving)

    cross_cor = np.correlate(fixed_arr,moving_arr, 'full')
    
    full_shift = np.concatenate((np.arange(-moving_arr.shape[0], -1, 1), np.arange(0,fixed_arr.shape[0],1)))
    _best_shift = full_shift[cross_cor == np.max(cross_cor)][0]

    return _best_shift

def shift_image(img, ref, x, y): 
    '''
    performs the resampling to shift the image properly. Can also be used to crop/expand to proper size. 

    input 
        img     sitk.Image      image to shift
        ref
        x       int             pixels to shift, can be negative or positive 
        y       int             pixels to shift, can be negative or positive 

    output 
        sitk.Image              shifted image
    '''
    translation = sitk.TranslationTransform(img.GetDimension())
    x,y = float(x), float(y)
    translation.SetOffset((-x,-y))
    return sitk.Resample(img,
                         ref, 
                         translation,
                         sitk.sitkLinear,
                         0)

def get_round_registration(fixed, moving): 
    '''
    performs the general x,y shift and then registers the round dapi image 
    
    input 
        fixed   sitk.Image      dapi R0 
        moving  sitk.Image      dapi R? 

    output 
        int                 x shift
        int                 y shift 
    '''
    # perform rough 1d transformation 
    x_shift = alignment_1d(fixed, moving, axis='x')
    y_shift = alignment_1d(fixed, moving, axis='y')

    return x_shift, y_shift

def transform_all_channels(fixed, channels, x, y): 
    '''
    perform the registration transforms on each channel c1-c5

    input 
        fixed           sitk.Image              reference image
        channels        dict {str:sitk.Image}   the images to be transformed - key is color e.g., 'c1':img
        x               int                     x shift 
        y               int                     y shift 
        Tx              sitk.Transform          dapi registration transform 

    output 
        dict {str:sitk.Image}                   images after being transformed 
    '''
    # general x,y alignment
    imgs2 = {}
    for _c in channels: 
        imgs2[_c] = shift_image(channels[_c], fixed, x, y)

    return imgs2

def sitk_registration(fixed, imgs, verbose=False): 
    '''
    '''

    def command_iteration(method):
        if (method.GetOptimizerIteration() == 0):
            print("Estimated Scales: ", method.GetOptimizerScales())
        print(f'iteration: {method.GetOptimizerIteration()} | metric={method.GetMetricValue()} | position={method.GetOptimizerPosition()}')
    
    num_hist_bins = 100
    max_iterations = 25
    sampling_percentage = 0.05 # x100% 
    stepLength=1
    stepTolerance = 1e-7
    valueTolerance = 1e-7


    moving = imgs['c1']

    # perform registration 

    # make sure imgs are Float32's 
    fixed =  sitk.Cast(fixed, sitk.sitkFloat32)
    moving = sitk.Cast(moving, sitk.sitkFloat32)
    
    # Normalize data - important for learning rate scaling
    fixed = sitk.Normalize(fixed)
    moving = sitk.Normalize(moving)
    
    # define registration parameters 
    R = sitk.ImageRegistrationMethod()
    
    #R.SetMetricAsMeanSquares()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=num_hist_bins)
    
    R.SetMetricSamplingStrategy(R.RANDOM)
    R.SetMetricSamplingPercentage(sampling_percentage)
    
    #R.SetOptimizerAsConjugateGradientLineSearch(learningRate=config.learning_rate, numberOfIterations=config.iterations)
    #R.SetOptimizerAsRegularStepGradientDescent(learningRate=config.learning_rate, 
    #                                           minStep=config.min_step, 
    #                                           numberOfIterations=config.iterations)
    #R.SetOptimizerAsGradientDescentLineSearch(learningRate=config.learning_rate, 
    #                                           numberOfIterations=config.iterations,
    #                                           convergenceMinimumValue=1e-8)
    R.SetOptimizerAsPowell(numberOfIterations=max_iterations,
                            maximumLineIterations=max_iterations,
                            stepLength=stepLength,
                            stepTolerance=stepTolerance,
                            valueTolerance=valueTolerance)

    #initial_transform = sitk.TranslationTransform(fixed.GetDimension())
    #initial_transform = sitk.Euler2DTransform()
    initial_transform = sitk.CenteredTransformInitializer(fixed, 
                                                      moving, 
                                                      sitk.Euler2DTransform(), 
                                                      sitk.CenteredTransformInitializerFilter.GEOMETRY)

    R.SetInitialTransform(initial_transform)
    R.SetInterpolator(sitk.sitkLinear)
    
    if verbose: R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))
    
    # preform registration 
    if verbose: print('training registration')
    outTx = R.Execute(fixed, moving)

    if verbose: 
        print("-------")
        print(outTx)
        print("Optimizer stop condition: {0}"
                .format(R.GetOptimizerStopConditionDescription()))
        print(" Iteration: {0}".format(R.GetOptimizerIteration()))
        print(" Metric value: {0}".format(R.GetMetricValue()))
        print('-------')
        
    # resample images 
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(0)
    resampler.SetTransform(outTx)

    return {channel:resampler.Execute(imgs[channel]) for channel in imgs}


def round_operation(fixed, moving_df, inp, out, rescale=False): 
    '''
    perform the all necessary operations for a given round:
    0. load data
    1. 1-d general registration 
    3. perform transformations on each channel 
    4. save registered images to given output directory 

    inputs
        fixed       sitk.Image          round 0 dapi image 
        moving_df   sitk.Image          dataframe with select round img data (e.g., path locations) 
        inp         str                 data directory path 
        out         str                 output directory path 
        rescale     bool                rescale 8-bit to 16bit 

    output
        None 
    '''
    # prepare progress bar - incrememnt with next()
    _round = moving_df['round'].unique().item()
    pbar = iter(atpbar(range(10), name=_round))
    next(pbar)

    # load images
    imgs = {} 
    for i, row in moving_df.iterrows(): 
        _im = utils.myload(inp + '/' + row.original)
        _im.SetSpacing((1,1))
        # rescale image 8-bit to 16-bit
        # check if values are les than 256 (8bit)
        if sitk.GetArrayFromImage(_im).max() < 256: 
            print()
            print(f'WARNING: "{row.original}" was read in as a 16-bit tiff file, but max value is less than 256.')
            print()
            if rescale: 
                raise DeprecationWarning('This feature is deprecated - and should not be used.')
                print('WARNING! Rescaling to 16-bit.')
                _im = _im * ((2**16 - 1) / (2**8 - 1))
                
        imgs[row.color_channel] = _im
        next(pbar)


    # get transformations
    x,y = get_round_registration(fixed, imgs['c1'])
    next(pbar)

    # perform transformations 
    reg_imgs = transform_all_channels(fixed, imgs, x, y)
    next(pbar)

    # perform fine + rotation transformations 
    reg_imgs = sitk_registration(fixed, reg_imgs)
    next(pbar)

    # save output s
    for _c in reg_imgs: 
        name = moving_df[lambda x: x['color_channel'] == _c].original.item()
        sitk.WriteImage(reg_imgs[_c], out + '/' + name)

    try: 
        for i in pbar: 
            #finish off the pbar
            pass
    except: 
        print('pbar for finish failed')


# make sure to use mantichora and the pretty terminal progress plotting
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
    parser.add_argument('--rescale', action='store_true')          
    args = parser.parse_args()

    print('#'*100)
    print('#'*100)
    print('input directory:', args.input[0])
    print('output directory:', args.output[0])
    print('slide name:', args.slide[0])
    print('scene name:', args.scene[0])
    print()

    if args.rescale: print('WARNING: the "--rescale" flag is deprecated and no long used.')

    img_file_names = [x for x in os.listdir(args.input[0]) if x[-4:] == '.tif']
    parsed_names = pd.DataFrame([parse_file_name(x) for x in img_file_names])

    # filter to slide/scene
    parsed_names = parsed_names[lambda x: (x.slide_name == args.slide[0]) & (x.scene == args.scene[0])]

    # load fixed image 
    print('loading fixed image')
    fixed_path = args.input[0] + '/' + parsed_names[lambda x: (x['round'] == 'R0') & (x['color_channel'] == 'c1')].original.item()
    fixed = utils.myload(fixed_path)
    fixed.SetSpacing((1,1))

    # check if values are les than 256 (8bit)
    if max(np.random.choice(sitk.GetArrayFromImage(fixed).flatten(), size=100000)) < 256: 
        print()
        print('WARNING: R0 was read in as a 16-bit tiff file, but max value is less than 256. Rescaling to 16-bit.')
        print()
        fixed = fixed * ((2**16 - 1) / (2**8 - 1))

    # for aesthetics 
    parsed_names = parsed_names.sort_values('round')

    # multithread registration 
    print('multithreading')
    with mantichora(mode='threading', nworkers=3) as mcore:
        for _round in parsed_names['round'].unique(): 
            if _round != 'R0':
                moving_df = parsed_names[lambda x: (x['round'] == _round)]
                mcore.run(round_operation, fixed, moving_df, args.input[0], args.output[0], args.rescale)
        returns = mcore.returns()

    # move R0 images over to output dire
    print('moving fixed image to output')
    R0_dat = parsed_names[lambda x: (x['round'] == 'R0')]
    for _path in R0_dat.original.values:
        shutil.copyfile(args.input[0] + '/' + _path, args.output[0] + '/' + _path)

    print('#'*100)
    print('#'*100)
