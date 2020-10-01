'''
general utility functions 
'''

import SimpleITK as sitk
from matplotlib import pyplot as plt 

import time

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
    multiscene = 'Scene' in f
    
    f2 = f.split('_')
    
    R, protein, slide = f2[:3]
    
    date = '-'.join(f2[3:6])
    
    scene=None
    if multiscene: 
        scan, scene = f2[7].split('-', 1)
    else: 
        scan = f2[7]
        
    color = f2[8]
    note, ftype = f2[9].split('.')
    
    names = "round,protein,slide_name,date,scan_id,scene,color_channel,note,file_type,original".split(',')
    res = {n:v for n,v in zip(names, [R,protein,slide,date,scan,scene,color,note, ftype,f])}
    return res

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
           
           
           
           
           
           