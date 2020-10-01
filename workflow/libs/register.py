import SimpleITK as sitk

def get_registration_transform(fixed, moving, verbose=True): 
    '''
    '''
    
    # make sure imgs are Float32's 
    fixed =  sitk.Cast(fixed, sitk.sitkFloat32)
    moving = sitk.Cast(moving, sitk.sitkFloat32)
    
    # reset index - may not be necessary? 
    #fixed.SetOrigin((0,0))
    #moving.SetOrigin((0,0))
    
    # normalize values?
    fixed = sitk.Normalize(fixed)
    moving = sitk.Normalize(moving)
    
    # define registration parameters 
    R = sitk.ImageRegistrationMethod()
    
    #R.SetMetricAsMeanSquares()
    R.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
    
    R.SetOptimizerAsRegularStepGradientDescent(learningRate=1e-2, minStep=1e-9, numberOfIterations=50)
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