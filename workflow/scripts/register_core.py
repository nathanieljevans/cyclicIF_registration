import argparse
import SimpleITK as sitk
import pandas as pd
from mantichora import mantichora
from atpbar import atpbar

import sys, os
sys.path.append('../libs/')
import utils
import segment 
import match 
import register 
import evaluate 
import qc


if __name__ == '__main__': 
    print('starting `register_core.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Registration of an individual core across rounds + channels.')
    parser.add_argument('--input', metavar='input', type=str, nargs=1,
                        help='core directory (.tif core images)')
    parser.add_argument('--config', metavar='config', type=str, nargs=1,
                        help='path to directory with config object')
    args = parser.parse_args()
    
    # read in meta data 
    parsed_names = pd.DataFrame([utils.parse_core_name(x) for x in os.listdir(args.input[0]) if x[-4:]=='.tif'])

    # select DAPI round 0 info 
    fixed_name = parsed_names[lambda x: (x['round']=='R0') & (x.color_channel=='c1')]

    assert fixed_name.shape[0] > 0, f'No R0 core to use as fixed image in: {args.input[0]}'

    fixed = sitk.ReadImage(args.input[0] + '/' + fixed_name.path.item(), sitk.sitkUInt16)
    
    # remove dapi round 0 from rest of data
    parsed_names = parsed_names[lambda x: ~((x['round']=='R0') & (x.color_channel))]
    
    # remove any images that have already been registered 
    parsed_names = parsed_names[lambda x: x.status == 'unregistered']

    # load config namespace 
    config = utils.load_config(args.config[0])

    def _reg_(parsed_names, row, pbar): 
        '''for multithreading'''
        moving = sitk.ReadImage(args.input[0] + '/' + row.path)
        Tx = register.get_registration_transform(fixed, moving, verbose=False, config=config)
        for i, crow in parsed_names[lambda x: x['round']==row['round']].iterrows():
            cmoving = sitk.ReadImage(args.input[0] + '/' + crow.path, sitk.sitkUInt16) 
            reg_cmoving = register.preform_transformation(fixed, moving,Tx)
            sitk.Cast(sitk.RescaleIntensity(reg_cmoving), sitk.sitkUInt16)
            sitk.WriteImage(reg_cmoving, f'{args.input[0]}/registered_core={crow.core}_round={crow["round"]}_color={crow.color_channel}.tif')
        next(pbar)

    coreid = args.input[0][-9:-1]
    pbar = iter(atpbar(range(parsed_names[lambda x: x.color_channel=='c1'].shape[0]+1), coreid))
    with mantichora(mode='threading', nworkers=12) as mcore: 
        next(pbar)
        for i, row in parsed_names[lambda x: x.color_channel=='c1'].iterrows(): 
            mcore.run(_reg_, parsed_names, row, pbar)
        returns = mcore.returns()
    for i in pbar:
        print() 
        print(i)
        