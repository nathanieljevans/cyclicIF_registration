import argparse
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
    print('starting `aggregate_results.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Aggregate all registration results for a given output directory.')
    parser.add_argument('--dir', metavar='in', type=str, nargs=1,
                        help='output directory')
    args = parser.parse_args()
    _all = []
    # traverse each slide name 
    for slide_name in [x for x in os.listdir(args.dir[0]) if os.path.isdir(args.dir[0] + '/' + x)]: 
        print(slide_name)
        # traverse each scene 
        for scene_name in [x for x in os.listdir(args.dir[0] + '/' + slide_name) if os.path.isdir(args.dir[0] + '/' + 
                                                                                                  slide_name + '/' + 
                                                                                                  x)]:
            print('\t' + scene_name)
            # traverse each core
            for core_name in [x for x in os.listdir(args.dir[0] + '/' + slide_name + '/' + scene_name) if os.path.isdir(args.dir[0] + 
                                                                                                                        '/' + slide_name +
                                                                                                                        '/' + scene_name + 
                                                                                                                       '/' + x)]:
                print('\t\t' + core_name, end='\r')
                
                try: 
                    # get all file names 
                    core_path = args.dir[0] + '/' + slide_name + '/' + scene_name + '/' + core_name + '/'
                    
                    parsed_names = pd.DataFrame([utils.parse_core_name(x) for x in os.listdir(core_path) if x[-4:]=='.tif'])

                    meta = pd.read_csv(core_path + 'core_meta.csv')
                    results = pd.read_csv(core_path + 'registration_eval.csv') 

                    dat = parsed_names.merge(meta, on=['round','color_channel'], how='left') 
                    
                    # need same data types
                    results.core == results.core.astype(int)
                    dat.core = dat.core.astype(int)
                    
                    dat = dat.merge(results, on=['round','color_channel', 'path', 'core', 'status'], how='left') 
                    
                    dat = dat.assign(registered_path=lambda x: core_path + '/' + x.path)

                    _all.append(dat)
                    
                except FileNotFoundError: 
                    print('\t\t' + core_name + ' - failed : FileNotFoundError') 
                    #raise
            print()
            
    _all = pd.concat(_all, axis=0, ignore_index=True) 
    _all.to_csv(args.dir[0] + '/aggregated_results.csv')
    print('completed results aggregation.')
            
            
            
                               
            
            
            
            
            
            