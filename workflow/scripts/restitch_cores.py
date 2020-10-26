'''

See 
$ python restitch_cores.py --help 
for command line options 

example
$ python restitch_cores.py --results_path /home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/aggregated_results.csv --output /home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/S3/Scene-1/ --slide S3 --scene Scene-1 --qc ./manual_QC_example.json

Note, `manual_QC_example.json` is intended to be used with S3,Scene-1 and will remove all R0 cores in the first row, R1 cores in the second row, R2 cores in the third row. 

'''

import sys, os
import argparse

sys.path.append('../libs/')
import utils
import config
import segment 
import match 
import missingness 
import register 
import evaluate 
import qc 

import threading
import pandas as pd
import numpy as np
import json


if __name__ == '__main__': 
    print('starting `restitch_cores.py`...') 
    print('For command line options, see: `#python restich_cores.py --help`')
    
    parser = argparse.ArgumentParser(description='Restitching a set of registered cores given Round,Scene,Core IDs.')
    parser.add_argument('--results_path', 
                        dest='results', 
                        type=str, 
                        nargs=1, 
                        default='/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/aggregated_results.csv',
                        help='registration results csv path')
    
    parser.add_argument('--output', 
                        dest='output', 
                        type=str, 
                        nargs=1, 
                        default='/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/S3/Scene-1/',
                        help='output directory where the restitched images will be written to disk.')
    
    parser.add_argument('--slide', 
                        dest='slide', 
                        type=str, 
                        nargs=1,
                        default='S3',
                        help='slide name (identifier)')
    
    parser.add_argument('--scene', 
                        dest='scene', 
                        type=str, 
                        nargs=1,
                        default='Scene-1',
                        help='scene name (identifier)')
    
    parser.add_argument('--qc', 
                        dest='qc_method', 
                        type=str, 
                        nargs=1,
                        default='None',
                        help='qc method: Can be ["None", "Auto", "/path/to/json/file/with/core/ids/to/filter"]')
                        
    args = parser.parse_args()
    
    if args.qc_method[0] in ['None', 'none', 'NONE', None]: 
        print('No QC will be used') 
        qc_method = None 
        
    elif args.qc_method[0] in ['AUTO', 'Auto', 'auto']: 
        print('auto QC will be used')
        qc_method = 'auto'
        
    elif args.qc_method[0][-5:] == '.json': 
        print(f'manual QC will be used. loading file: {args.qc_method[0]}')
        # TODO: NEEDS TO BE TESTED 
        with open(args.qc_method[0]) as data_file:    
            qc_method = json.load(data_file)
            
    else: 
        print(f'unreconized qc method: {args.qc_method[0]}') 
        print('no qc will be done') 
        qc_method = None
    
    # Load aggregated_results.csv into mem 
    res = pd.read_csv(args.results[0])
    print(res.shape)

    # select only registered results -- keep R0 unregistered as this is the aligned reference 
    res = res[(res.status == 'registered') | (res['round'] == 'R0')]
    print(res.shape)
    
    # filter to specific slide/scene 
    res = res[(res.slide_name == args.slide[0]) & (res.scene == args.scene[0])]
    print(res.shape)
    print(args.slide[0])
    print(args.scene[0])
    
    # TODO - if passed a text file path for QC, need to parse it and make it a list to pass to the method below. 
    
    # run multithreading to speed this process up 
    print('assigning threads...')
    threads=[]
    for _round in np.sort(res['round'].unique()): 
        _temp = res[lambda x: (x['round'] == _round)]
        for _channel in np.sort(_temp['color_channel'].unique()): 
            print(f'\t\t\t\t {(_round, _channel)}')
            
            # parse the dictionary for manual qc. 
            if type(qc_method) == type({}): 
                if _round in qc_method.keys(): 
                    _qc_method = qc_method[_round]
                else: 
                    _qc_method=None
            else: 
                _qc_method = qc_method
            
            t = threading.Thread(target=qc.restitch_image, args = (res, _round, _channel, _qc_method, args.output[0], True, True))
            t.daemon = True
            t.start()
            threads.append(t)
    
    # prevent calls on the thread and wait for it to finish executing         
    for t in threads:
        t.join()

    print('...done')

    
    
    
    
    
    
    