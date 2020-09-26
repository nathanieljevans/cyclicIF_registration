'''
general utility functions 
'''

import SimpleITK as sitk
from matplotlib import pyplot as plt 

import time

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

def myshow(img, title='', figsize=(7,7)):
    '''
    '''
    plt.figure(figsize=figsize)
    plt.imshow(sitk.GetArrayViewFromImage(img))
    plt.title(title)
    plt.axis('off')
    plt.show()
           
           
           
           
           
           