'''
general utility functions 
'''

import SimpleITK as sitk
from matplotlib import pyplot as plt 
from mantichora import mantichora
from atpbar import atpbar
import time
import sys

def check_for_duplicates(df, cols): 
    return len(df[cols])-len(df[cols].drop_duplicates())

def load_imgs_mt(img_paths, base_path, _type=sitk.sitkUInt16): 
    '''
    threading to load images into memory faster 
    '''
    print('starting multithreaded image loading...')
    def load_image(path, tid, ntid):
        im = sitk.ReadImage(path, _type)
        im.SetSpacing((1,1))
        print(f'finished task: {tid}/{ntid}', end='\r')
        return (path.split('/')[-1], im)

    nimgs = len(img_paths)

    with mantichora(mode='threading', nworkers=16) as mcore: 
        print('assigning threads...', end='')
        for i,path in zip(range(nimgs), img_paths): 
            mcore.run(load_image, base_path + '/' + path, i, nimgs)
        print('done.') 
        print('waiting for threads to complete.')
        returns = mcore.returns()
        
    print()
    print('threads complete.')
    imgs = {item[0] : item[1] for item in returns}
    print()
    print('...image loading complete.')
    return imgs

def parse_core_name(path): 
    '''
    for use in register_core.py and evaluate_core_registration.py 
    
    path   str   ./.../unregistered_core={cluster_label}_round={round}_color={color_channel}.tif')
    '''
    name = path.split('/')[-1][:-4]
    (_status, (_, _core), (_, _round), (_,  _color)) = [x.split('=') for x in name.split('_')]
    return {'status':_status[0], 'core':_core, 'round':_round, 'color_channel':_color, 'path':path}


def parse_file_name(f): 
    '''
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

def myshow(img, title='', figsize=(7,7), ax=None):
    '''
    '''
    if ax is not None: 
        ax.imshow(sitk.GetArrayViewFromImage(img))
        ax.set_title(title)
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(False)
    else: 
        plt.figure(figsize=figsize)
        plt.imshow(sitk.GetArrayViewFromImage(img))
        plt.title(title)
        plt.axis('off')
        plt.show()
           
           
def load_config(path, verbose=True): 
    '''
    loads the config namespace into an object so that it's accessible 
    input
        path <str>     path to config object

    output 
        namespace
    '''
    sys.path.append(path)                     # temporarily append config path    
    import config                             # load namespace

    if verbose: print('loading config file from:', config.myloc)

    return config



           
           
           