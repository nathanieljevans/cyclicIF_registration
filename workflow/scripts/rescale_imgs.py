'''
This script was developed in response to a bug (1/24/22): Images that should be 16-bit are read into memory with pixel intensity values of less than 256. 

One potential fix to this is rescaling the problematic images to 16-bit. This assumes the images are saved with 8-bit intensities in a 16-bit format. 

Further work should be done to understand this better. 


example

```bash 

(cycIF_reg) $ python rescale_imgs.py --input /path/to/images/dir
```

This script will create a new directory with rescaled images. Images will only be rescaled if they have pixel intensity values less than 256. 
'''


import argparse
import SimpleITK as sitk
import pandas as pd
from mantichora import mantichora
from atpbar import atpbar
import numpy as np

import sys, os
sys.path.append('../libs/')
import utils
import segment 
import match 
import register 
import evaluate 
import qc


if __name__ == '__main__': 
    print('starting...')
    parser = argparse.ArgumentParser(description='Rescale low intensity 16-bit images.')
    parser.add_argument('--input', metavar='input', type=str, nargs=1,
                        help='core directory (.tif core images)')

    args = parser.parse_args()
    
    for i,fname in enumerate(os.listdir(args.input[0])): 
        print(f'image # {i}:', fname, end=' ')
        img = utils.myload(args.input[0] + '/' + fname)
        #max_val_est = np.random.choice(sitk.GetArrayFromImage(img).ravel(), size=100000).max()
        max_val = sitk.GetArrayFromImage(img).max()
        print('|| max pixel value:', max_val)
        print('---')