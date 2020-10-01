import argparse
import SimpleITK as sitk
import pandas as pd

import sys, os
sys.path.append('../libs/')
import utils
import config
import segment 
import match 
import missingness 
import register 
import evaluate 
import qc


if __name__ == '__main__': 
    print('starting `register_core.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Registration of an individual core across rounds + channels.')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='core directory (.tif core images)')
    args = parser.parse_args()
    
    # read in meta data 
    #meta = pd.read_csv(args.input[0] + '/core_meta.csv')
    parsed_names = pd.DataFrame([utils.parse_core_name(x) for x in os.listdir(args.input[0]) if x[-4:]=='.tif'])

    # select DAPI round 0 info 
    fixed_name = parsed_names[lambda x: (x['round']=='R0') & (x.color_channel=='c1')]

    fixed = sitk.ReadImage(args.input[0] + '/' + fixed_name.path.item())
    
    # remove dapi round 0 from rest of data
    parsed_names = parsed_names[lambda x: ~((x['round']=='R0') & (x.color_channel))]
    
    # remove any images that have already been registered 
    parsed_names = parsed_names[lambda x: x.status == 'unregistered']
    
    for i,row in parsed_names[lambda x: x.color_channel=='c1'].iterrows(): 
        print('generating registration transformation:', row['round'])
        moving = sitk.ReadImage(args.input[0] + '/' + row.path)
        Tx = register.get_registration_transform(fixed, moving, verbose=False)
        
        for i, crow in parsed_names[lambda x: x['round']==row['round']].iterrows():
            print('\tregistering:', crow.color_channel)
            # trasformed each channel using the dapi registration 
            cmoving = sitk.ReadImage(args.input[0] + '/' + crow.path) 
            reg_cmoving = register.preform_transformation(fixed,moving,Tx)
            sitk.WriteImage(reg_cmoving, f'{args.input[0]}/registered_core={crow.core}_round={crow["round"]}_color={crow.color_channel}.tif')

        