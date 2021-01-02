import SimpleITK as sitk

def get_registration_transform(fixed, moving, config=None, verbose=True): 
    '''
    '''
    assert config is not None, 'config is none, pass config object'
    
    # make sure imgs are Float32's 
    fixed =  sitk.Cast(fixed, sitk.sitkFloat32)
    moving = sitk.Cast(moving, sitk.sitkFloat32)

    # do we need to rescale the data ?
    fixed = sitk.RescaleIntensity(fixed, 0)
    
    # normalize values? - should this be done?
    fixed = sitk.Normalize(fixed)
    moving = sitk.Normalize(moving)
    
    # define registration parameters 
    R = sitk.ImageRegistrationMethod()
    
    #R.SetMetricAsMeanSquares()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=config.num_hist_bins)
    
    #R.SetOptimizerAsConjugateGradientLineSearch(learningRate=config.learning_rate, numberOfIterations=config.iterations)
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=config.learning_rate, 
                                               minStep=config.min_step, 
                                               numberOfIterations=config.iterations)
    
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