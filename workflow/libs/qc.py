'''
'''
import SimpleITK as sitk
from matplotlib import pyplot as plt
import utils
import numpy as np
import os

from ipywidgets import interact, interactive, fixed, interact_manual
import ipywidgets as widgets
from IPython.display import display, clear_output

def plot_core_reg(core, output_dir='/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output', slide='S3', scene='Scene-1', _round=['R0','R1','R2'], channel=['c1']*3):
    
    print('plotting core image, this may take a moment...')
    core_dir = f'{output_dir}/{slide}/{scene}/{core}'
    
    try:
        _temp = []
        for name,r,c in zip(['Red','Blue','Green'],_round, channel): 
            status = 'registered' if r!='R0' else 'unregistered'
            img_path = core_dir + f'/{status}_core={int(core[-3:])}_round={r}_color={c}.tif'
            print(f'{name} channel --> {img_path}')
            img = sitk.ReadImage(img_path)
            _temp.append(img) 
            
        round0, round1, round2 = _temp

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
        #raise
        
        
def restitch_image(dat, _round, _channel, output_dir, config=None, qc=None, save=True, verbose=True, pbar=None): 
    '''
    restitch a set of images. The core locations are maintained relative to R0-dapi original core locations. 
    
    input 
        dat         <dataframe>      the results dataframe (aggregated_results.csv), and must include only one experiment (slide_name, scene)
        _round      <str>            round to use for restitching 
        _channel    <str>            color channel to use for restitching
        qc          <str or list>    qc method to employ, can be [None, 'auto', List]. If None, no qc is done. If 'auto', the hardcoded thresholds are used to remove poorly registered cores. If List<of int>, core ID's included in the list will be removed.  
        save        <bool>           option to save to file, will save in `output_dir` and use the original image name appended with '-registered.tif'
        pbar        <generator>      atpbar generator
    output 
        joined_image   <sitk Image>  Restitched image with all cores, excluding qc 
    '''

    assert (qc in [None, 'auto']) | (type(qc) == type([])), f'Invalid value: qc can be None, "auto" or a List object, got: {qc} [{type(qc)}]'
    
    # we'll use the R0 dapi core positions as the core mapping 
    c1R0_res = dat[lambda x: (x['round'] == 'R0') & (x['color_channel'] == 'c1')][['core','center_x','center_y','width', 'height']].drop_duplicates().set_index('core')
    
    #! DELETE THIS WHEN DONE VVV
    #import pandas as pd
    #pd.set_option("display.max_rows", None, "display.max_columns", None)
    #print(c1R0_res[c1R0_res['core'] == 0].head())
    #! DELETE THIS WHEN DONE ^^^

    # calculate the necessary size of the restitched image
    # TODO: this needs to be the same size as the R0 image
    full_size_x = int(c1R0_res.center_x.max() + c1R0_res.width.max())*config.downsample_proportion  # ensures our final image is large enough to include all the cores
    full_size_y = int(c1R0_res.center_y.max() + c1R0_res.height.max())*config.downsample_proportion # 

    # filter to round and core; this is what we can use for hard path ref
    imDat = dat[lambda x: (x['round'] == _round) & (x['color_channel'] == _channel)]
    
    # the dataframe has missingness: rows where the color_channel=/=c1 don't have an 'original' image path name
    # so we'll need to grab to RX-c1 path name and then change the cX as appropriate 
    Rxc1_name =  dat[lambda x: (x['round'] == _round) & (x['color_channel'] == 'c1')].img_name.unique() 
    assert Rxc1_name.shape[0] == 1, f'expected 1 original pathname, got {Rxc1_name.shape[0]}'
    Rxc1_name = Rxc1_name[0]
    
    # create an empty image of the proper size 
    joined_image = sitk.Image(full_size_x, full_size_y, sitk.sitkUInt8)
    joined_image.SetSpacing((config.pixel_width, config.pixel_height))
    
    ###########################################################################
    ############################# Quality Control #############################
    ###########################################################################
    if qc == 'auto': 
        # filter all cores with registration metrics that don't pass QC 
        imDat = imDat[lambda x: \
                      (x.false_pos_err < config.FPR_threshold) & \
                      (x.false_neg_err < config.FNR_threshold) & \
                      (x.hausdorff_dist < config.hausdorff_distance_threshold)]
        
    elif (type(qc) == type([])): 
        # filter all cores listed in qc 
        imDat = imDat[lambda x: ~x.core.isin(qc)]
        
    else: 
        pass
        #print('No QC performed')
    ###########################################################################
    
    # resample each core of size `joined_image` then combine by addition 
    for i, row in imDat.sort_values('core').iterrows(): 

        #if verbose: print(f'\t\tresampling core {(_round, _channel)}: {row.core}', end='\r')

        # get core position [in microns]
        cx = c1R0_res.loc[row.core].center_x * config.downsample_proportion * config.pixel_width
        cy = c1R0_res.loc[row.core].center_y * config.downsample_proportion * config.pixel_height

        #print(cx)
        #print(cy)
        #print(type(cx))
        #print(type(cy))

        cx = int(cx.item())
        cy = int(cy.item())

        # read registered core into memory (UNLESS ITS R0-then unregistered)
        # TODO: compare `restitiched` R0 against original R0 - there should be minimal changes! check for image quality loss, etc.. 
        _im = sitk.ReadImage(row.registered_path, sitk.sitkUInt8)
        _im.SetSpacing((config.pixel_width, config.pixel_height))

        _im.SetOrigin((cx, cy))

        # resample using linear interpolator 
        _im = sitk.Resample(_im,
                            joined_image.GetSize(),
                            sitk.Transform(),
                            sitk.sitkLinear,
                            joined_image.GetOrigin(),
                            joined_image.GetSpacing(),
                            joined_image.GetDirection(),
                            0,
                            joined_image.GetPixelID())

        # combine image by addition
        joined_image = joined_image + _im
        
    # save file 
    if save: 
        # 'R0_AF488.AF555.AF647.AF750_S3_2020_01_21__13471-Scene-1_c1_ORG.tif'
        #                                                         | |   |
        #                                                       -10-8  -4  
        fname = output_dir + Rxc1_name[:-10] + _channel + Rxc1_name[-8:-4] + '.tif'
        #print('\n\tsaving re-stitched image to:', fname)
        sitk.WriteImage(joined_image, fname)

    next(pbar)
    
    #return joined_image


def choose_and_viz(config): 
    '''
    '''
    data_dir=config.data_dir

    opt = np.sort([x for x in os.listdir(data_dir) if x[-4:]=='.tif'])

    R = widgets.Dropdown(
        options=opt,
        value=opt[0],
        description='Channel 1:',
        disabled=False,
    )

    G = widgets.Dropdown(
        options=opt,
        value=opt[1],
        description='Channel 2:',
        disabled=False,
    )

    B = widgets.Dropdown(
        options=opt,
        value=opt[2],
        description='Channel 3:',
        disabled=False,
    )

    GO = widgets.Button(
        description='Generate Image',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltip='Click me',
        icon='' # (FontAwesome names without the `fa-` prefix)
    )

    def on_button_clicked(b):
        clear_output()
        choose_and_viz(data_dir=data_dir)
        
        print('this can take a few moments...')

        print('loading images...')
        im1=sitk.ReadImage(data_dir + R.value)
        im2=sitk.ReadImage(data_dir + G.value)
        im3=sitk.ReadImage(data_dir + B.value)
        
        print('rescaling images...')
        sigm1 = sitk.Cast(sitk.RescaleIntensity(im1), sitk.sitkUInt8) # imshow clips integers to 255 
        sigm2 = sitk.Cast(sitk.RescaleIntensity(im2), sitk.sitkUInt8)
        sigm3 = sitk.Cast(sitk.RescaleIntensity(im3), sitk.sitkUInt8)
        
        if (sigm1.GetSize() != sigm2.GetSize()) | (sigm1.GetSize() != sigm3.GetSize()): 
            print('warning: images are different sizes')
            min_x = min([x.GetSize()[0] for x in [sigm1, sigm2, sigm3]])
            min_y = min([x.GetSize()[1] for x in [sigm1, sigm2, sigm3]])
            print('cropping to:', (min_x, min_y)) 
            
            sigm1,sigm2,sigm3 = [x[:min_x, :min_y] for x in [sigm1, sigm2, sigm3]]
        
        cimg = sitk.Compose(sigm1, sigm2, sigm3)
        
        print('plotting images...')
        print('\tchannel 1 (R): ', R.value)
        print('\tchannel 2 (B): ', B.value)
        print('\tchannel 3 (G): ', G.value)
        utils.myshow(cimg, title='registered re-stitched image overlay', figsize=(15,15))

    GO.on_click(on_button_clicked)

    display(R,G,B,GO)
    
    
def choose_and_plot_core(config): 
    '''
    '''
    output_dir = config.output_dir

    slide_opt = sorted([x for x in os.listdir(output_dir) if os.path.isdir(output_dir + '/' + x)]) + ['None']
    
    def on_change1(change):
        if change['type'] == 'change' and change['name'] == 'value': 
            slide = change["new"]
            
            scene_opt=sorted([x for x in os.listdir(output_dir + '/' + slide) if os.path.isdir(output_dir +'/' + slide + '/' + x)]) + ['None']
            
            sceneW = widgets.Dropdown(
                options=scene_opt,
                value='None',
                description='scene:',
                disabled=False
                )
            
            def on_change2(change):
                if change['type'] == 'change' and change['name'] == 'value': 
                    scene = change["new"]
                    
                    core_opt=sorted([x for x in os.listdir(output_dir + '/' + slide + '/' + scene) if os.path.isdir(output_dir + '/' + slide + '/' + scene + '/' + x)]) + ['None']

                    coreW = widgets.Dropdown(
                        options=core_opt,
                        value='None',
                        description='core:',
                        disabled=False
                        )

                    def on_change3(change):
                        if change['type'] == 'change' and change['name'] == 'value': 
                            core = change["new"]
                            
                            print('#'*50)
                            # choose channels for RGB
                            
                            img_paths = [x for x in os.listdir(output_dir + '/' + slide + '/' + scene + '/' + core) if x[-4:] == '.tif']
                            nrounds = int((len(img_paths)-5)/10) + 1
                            
                            r_opt = [f'R{x}' for x in range(nrounds)]
                            c_opt = [f'c{x}' for x in range(1,6)]
                            
                            Rr = widgets.Dropdown(
                                options=r_opt,
                                value='R0',
                                description='Red - Round:',
                                disabled=False,
                            )

                            Gr = widgets.Dropdown(
                                options=r_opt,
                                value='R1',
                                description='Blue - Round:',
                                disabled=False,
                            )

                            Br = widgets.Dropdown(
                                options=r_opt,
                                value='R2',
                                description='Green - Round:',
                                disabled=False,
                            )
                            
                            Rc = widgets.Dropdown(
                                options=c_opt,
                                value='c1',
                                description='Red - color:',
                                disabled=False,
                            )

                            Gc = widgets.Dropdown(
                                options=c_opt,
                                value='c1',
                                description='Blue - color:',
                                disabled=False,
                            )

                            Bc = widgets.Dropdown(
                                options=c_opt,
                                value='c1',
                                description='Green - color:',
                                disabled=False,
                            )
                            
                            GO = widgets.Button(
                                description='Generate Image',
                                disabled=False,
                                button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                tooltip='Click me',
                                icon='' # (FontAwesome names without the `fa-` prefix)
                            )
                            
                            # def plot_core_reg(core, output_dir='/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output', slide='S3', scene='Scene-1', _round=['R0','R1','R2'], channel=['c1']*3):
                            def on_button_clicked(b):
                                plot_core_reg(core, output_dir=output_dir, slide=slide, scene=scene, _round=[Rr.value, Br.value, Gr.value], channel=[Rc.value, Bc.value, Gc.value])
                                
                            
                            GO.on_click(on_button_clicked)
                            
                            # display choices 
                            display(Rr, Rc, Br, Bc, Gr, Gc, GO)

                    coreW.observe(on_change3)
                    display(coreW)     
                    
            sceneW.observe(on_change2)
            display(sceneW)

    slideW = widgets.Dropdown(
        options=slide_opt,
        value='None',
        description='slide name:',
        disabled=False
        )
    
    slideW.observe(on_change1)
    display(slideW)