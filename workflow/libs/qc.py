'''
'''
import SimpleITK as sitk
from matplotlib import pyplot as plt

import utils

def plot_core_reg(core):
    core_dir = f'/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/S3/Scene-1/core-{"0"*(3-len(str(core)))}{core}'
    try:
        round0 = sitk.ReadImage(core_dir + f'/unregistered_core={core}_round=R0_color=c1.tif')
        round1 = sitk.ReadImage(core_dir + f'/registered_core={core}_round=R1_color=c1.tif')
        round2 = sitk.ReadImage(core_dir + f'/registered_core={core}_round=R2_color=c1.tif')

        sigm1 = sitk.Cast(sitk.RescaleIntensity(round0), sitk.sitkUInt8)
        sigm2 = sitk.Cast(sitk.RescaleIntensity(round1), sitk.sitkUInt8)
        sigm3 = sitk.Cast(sitk.RescaleIntensity(round2), sitk.sitkUInt8)

        cimg = sitk.Compose(sigm1, sigm2, sigm3)

        #utils.myshow(cimg, figsize=(10,10))

        wsize = 100
        x,y = cimg.GetSize()
        #utils.myshow(cimg[int(x/2-wsize):int(x/2+wsize), int(y/2-wsize):int(y/2+wsize)], figsize=(10,10))

        f,axes = plt.subplots(1,2, figsize=(15,12))
        utils.myshow(cimg, ax=axes[0], title=f'full core registration- {core}')
        utils.myshow(cimg[int(x/2-wsize):int(x/2+wsize), int(y/2-wsize):int(y/2+wsize)], ax=axes[1], title=f'zoom- {core}')
    except:
        print('error loading images - there may be one missing?')