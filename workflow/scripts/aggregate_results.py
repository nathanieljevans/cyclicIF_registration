'''
This script is meant to be run as a command line operation. Given a directory to an output folder, it will traverse the directory structure and aggregate all result/meta data and place them in a single csv. 

use
$ python aggregate_results.py --help 
to see command line options 

example use: 
$ python aggregate_results.py --dir /home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output

Note: the registration results are only available for c1 (dapi) channel, however, in this step we map them across all channels (keyed by round) so that it can  be used for QC and later steps. 

Note: the meta data (original image meta data + segmentation metrics) is split and segmentation metrics (calculated from round dapi channel) is propagated to each channel. 

'''

import argparse
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
        scene_dir = args.dir[0] + '/' + slide_name
        for scene_name in [x for x in os.listdir(scene_dir) if os.path.isdir(scene_dir + '/' + x)]:
            print('\t' + scene_name)
            # traverse each core
            core_dir = scene_dir + '/' + scene_name
            for core_name in sorted([x for x in os.listdir(core_dir) if os.path.isdir(core_dir + '/' + x)]):
                print('\t\t' + core_name, end='\r')

                try: 
                    # get all file names 
                    core_path = args.dir[0] + '/' + slide_name + '/' + scene_name + '/' + core_name + '/'

                    ## parsed_names contains all file names - but none of the original information or registration metrics 
                    parsed_names = pd.DataFrame([utils.parse_core_name(x) for x in os.listdir(core_path) if x[-4:]=='.tif'])

                    # meta contains the original data 
                    meta = pd.read_csv(core_path + 'core_meta.csv')

                    # check for duplicates in results
                    ndups = utils.check_for_duplicates(meta, ['round', 'color_channel'])
                    assert ndups == 0, f'there are {ndups} duplicates in `core_meta.csv` of {core_name}'

                    # break meta into two parts, one with original slide name - which shouldn't be propagated to other channels 
                    # this should be propagated only to dapi rounds - keyed by round, channel
                    meta1 = meta[['round','color_channel','img_name', 'protein']]

                    # the other with the dapi-c1 core segmentation metrics, scene/slide name etc 
                    # this should be propagated to all channels, keyed by round
                    meta2 = meta[['round','center_x','center_y', 'width', 'height', 'Volume (nm^3)',\
                                  'Elongation','Flatness', 'Oriented Bounding Box Minimum Size(nm)',\
                                  'Oriented Bounding Box Maximum Size(nm)', 'Intensity Mean',\
                                  'Intensity Standard Deviation', 'Intensity Skewness', 'component',\
                                 'slide_name', 'date', 'scan_id', 'scene', 'note']]

                    # results contain registration metrics for dapi channels (c1) + some redundant info with parsed_names 
                    results = pd.read_csv(core_path + 'registration_eval.csv') 

                    # check for duplicates in results
                    ndups = utils.check_for_duplicates(results, ['path'])
                    assert ndups == 0, f'there are {ndups} duplicates in `registration_eval.csv` of {core_name}'

                    # slide_name and scene are not included - because we've already navigated into the file structure - has to be same scene/slide_name
                    dat = parsed_names.merge(meta1, on=['round', 'color_channel'], how='left') 

                    # check for duplicates in results
                    ndups = utils.check_for_duplicates(dat, ['status', 'round', 'color_channel'])
                    assert ndups == 0, f'there are {ndups} duplicates after meta1 merge of {core_name}'

                    # keyed by round only - propagate dapi channel core segmentation features to the other channels - also includes slide_name, scene (which we need later)
                    dat = dat.merge(meta2, on=['round'], how='left')

                    # check for duplicates in results
                    ndups = utils.check_for_duplicates(dat, ['status', 'round', 'color_channel'])
                    assert ndups == 0, f'there are {ndups} duplicates after meta2 merge of {core_name}'

                    # need same data types
                    results.core == results.core.astype(int)
                    dat.core = dat.core.astype(int)

                    # assign registration status for merge on
                    results = results.assign(status=[x.split('_')[0] for x in results.path.values])
                    #print('results\n', print(results[['path', 'status']].head()))

                    # we really only need the registration metrics and round - other data in results is redundant and causes merge issues
                    results = results[['round', 'status', 'jacaard_coef','dice_coef','volume_similarity','false_pos_err','false_neg_err','hausdorff_dist']]

                    # note color channel not included here: we want to propagate registration results to all channels 
                    dat = dat.merge(results, on=['round', 'status'], how='left') 

                    dat = dat.assign(registered_path=lambda x: core_path + '/' + x.path)

                    # check for duplicates in results
                    ndups = utils.check_for_duplicates(dat, ['path'])
                    assert ndups == 0, f'there are {ndups} duplicates in merged reg. eval. results of {core_name}'

                    _all.append(dat)

                except FileNotFoundError: 
                    print('\t\t' + core_name + ' - failed : FileNotFoundError') 
                    #raise
            print()

    _all = pd.concat(_all, axis=0, ignore_index=True) 

    # check for duplicates in results
    ndups = utils.check_for_duplicates(_all, ['path'])
    assert ndups == 0, f'there are {ndups} duplicates in `aggregated_results.csv`'

    _all.to_csv(args.dir[0] + '/aggregated_results.csv', index=False, mode='w')
    print('completed results aggregation.')
            
            
            
                               
            
            
            
            
            
            