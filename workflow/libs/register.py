import SimpleITK as sitk
import config

def get_registration_transform(fixed, moving, verbose=True): 
    '''
    '''
    
    # make sure imgs are Float32's 
    fixed =  sitk.Cast(fixed, sitk.sitkFloat32)
    moving = sitk.Cast(moving, sitk.sitkFloat32)
    
    # normalize values?
    fixed = sitk.Normalize(fixed)
    moving = sitk.Normalize(moving)
    
    # define registration parameters 
    R = sitk.ImageRegistrationMethod()
    
    #R.SetMetricAsMeanSquares()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=config.num_hist_bins)
    
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=config.learning_rate, minStep=config.min_step, numberOfIterations=config.iterations)
    R.SetInitialTransform(sitk.TranslationTransform(fixed.GetDimension()))
    R.SetInterpolator(sitk.sitkLinear)
    
    # preform registration 
    outTx = R.Execute(fixed, moving)
    
    # report fitting results
    if verbose: 
        print("-------")
        print(outTx)
        print("Optimizer stop condition: {0}"
              .format(R.GetOptimizerStopConditionDescription()))
        print(" Iteration: {0}".format(R.GetOptimizerIteration()))
        print(" Metric value: {0}".format(R.GetMetricValue()))
    
    return outTx 

def preform_transformation(fixed, moving, Tx): 
    '''
    '''
    resampler = sitk.ResampleImageFilter()
    resampler.SetReferenceImage(fixed)
    resampler.SetInterpolator(sitk.sitkLinear)
    resampler.SetDefaultPixelValue(0)
    resampler.SetTransform(Tx)

    out = resampler.Execute(moving)
    
    return out