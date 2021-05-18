import argparse
import SimpleITK as sitk
import pandas as pd

import sys, os
sys.path.append('../libs/')
import utils
import segment 
import match 
import register 
import evaluate 
import qc


if __name__ == '__main__': 
    print('starting `evaluate_core_registration.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Evaluating a registration of an individual core across rounds + channels.')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='core directory (.tif core images)')
    args = parser.parse_args()
    
    # read in meta data 
    parsed_names = pd.DataFrame([utils.parse_core_name(x) for x in os.listdir(args.input[0]) if x[-4:]=='.tif'])

    # select DAPI round 0 info 
    fixed_name = parsed_names[lambda x: (x['round']=='R0') & (x.color_channel=='c1')]
    fixed = utils.myload(args.input[0] + '/' + fixed_name.path.item())
    
    # remove R0 from rest of data
    parsed_names = parsed_names[lambda x: ~((x['round']=='R0') )]
    
    # remove any images that havent already been registered AND select only dapi rounds
    parsed_names = parsed_names[lambda x: (x.color_channel == 'c1')]
    
    _res = []
    print('evaluating results of registered cores...')
    for i,row in parsed_names[lambda x: (x.color_channel=='c1') & (x.status == 'registered')].iterrows(): 
        #print('generating registration success metrics:', row['round'])
        moving = utils.myload(args.input[0] + '/' + row.path)
        df = evaluate.eval_registration(fixed, moving, row.path, plot=False)
        _res.append(df)
    
    print('evaluating results of unregistered cores...')
    for i,row in parsed_names[lambda x: (x.color_channel=='c1') & (x.status == 'unregistered')].iterrows(): 
        #print('generating registration success metrics:', row['round'])
        moving = utils.myload(args.input[0] + '/' + row.path)
        moving = sitk.Resample(moving, fixed)
        df = evaluate.eval_registration(fixed, moving, row.path, plot=False)
        _res.append(df)
        
    res = pd.DataFrame(_res)
    res = res.merge(parsed_names, left_on='name',right_on='path', how='left')
    res.to_csv(args.input[0] + '/registration_eval.csv', index=False, mode='w')
        
    print('eval complete.')