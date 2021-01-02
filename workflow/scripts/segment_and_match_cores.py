'''


''' 
import argparse
import SimpleITK as sitk
import pandas as pd
import shutil
import numpy as np
from atpbar import atpbar

import sys, os
sys.path.append('../libs/')
import utils
import segment 
import match 
import register 
import evaluate 
import qc 

def mmkdir(path, remove=True): 
    '''
    my version of mkdir 
    '''
    if os.path.exists(path) and remove:
        shutil.rmtree(path)
        os.mkdir(path) 
    elif not os.path.exists(path): 
        os.mkdir(path) 
        
def main(inp, out, slide, scene, config_path): 
    '''
        inp      input directory 
        out      output directory 
        slide    slidename 
        scene           scene name 
        config_path     path to local config file 
    '''
    # make output directory 
    mmkdir(out, remove=False)
    
    # make dir for slide 
    _slide_dir = out + '/' + slide
    mmkdir(_slide_dir)
        
    # make dir for scene 
    _scene_dir = _slide_dir + '/' + scene
    mmkdir(_scene_dir) 
        
    # load in and parse all files in input directory 
    img_file_names = os.listdir(inp)
    parsed_names = pd.DataFrame([utils.parse_file_name(x) for x in img_file_names if x[-4:] == '.tif'])
    
    # filter to single experiment (eg slide_name, scene) 
    parsed_names = parsed_names[parsed_names.slide_name == slide]
    parsed_names = parsed_names[parsed_names.scene == scene]
    
    # load config namespace 
    config = utils.load_config(config_path)

    # multithreaded image loading 
    imgs = utils.load_imgs_mt(parsed_names.original.values, inp)
    
    # segment cores and get statistics 
    res, R0_dapi = match.get_all_rounds_core_statistics(parsed_names, imgs, config=config, verbose=False, return_R0_dapi=True)
    
    # create core id mapping 
    R0_dapi_stats = res[lambda x: x['round'] == 'R0']
    segment.generate_core_id_map(R0_dapi, R0_dapi_stats, config=config, plot=False) 
    
    # match across rounds + assign cluster labels to each component 
    cluster_labels = match.match_cores_across_rounds(res, config=config)
    res = res.assign(cluster = cluster_labels)
    
    # why are there so many cluster labels??? -- does changing it to unique cluster labels fix this? 
    # I think we were overwriting each folder multiple times
    for _cluster_label in atpbar(np.unique(cluster_labels), 'matching clusters'): 
        try:
            
            res_choice = res[res.cluster == _cluster_label]

            # check that R0 is included in the cluster - if not, we'll just skip the cluster since
            # TODO: use R1 as fixed choice... note - this is also relevant in register core - without R0, it'll fail as is
            if len(res_choice[lambda x: x['round'] == 'R0'])==0: 
                print(f'core cluster {_cluster_label} has no R0 image - skipping')
                continue

            # need to add check for >1 round being present. e.g., 2 Rounds of R8 ... in such cases remove the observation thats less similar
            ndups = utils.check_for_duplicates(res_choice, ['round'])

            if ndups > 0: 
                R0 = res_choice[lambda x: (x['round'] == 'R0')]
                # TODO what if R0 is a duplicate??? - currently, it fails
                R0x = R0.center_x.item()
                R0y = R0.center_y.item()
                bool_ind = res_choice.duplicated(subset=['round'], keep=False)
                dups = res_choice.loc[bool_ind]
                dups = dups.assign(dist_from_R0 = lambda x: ((x.center_x - R0x)**2 + (x.center_y - R0y)**2)**(0.5))
                dups = dups.sort_values('dist_from_R0') # ascending: smallest (best) val first
                Rx_inds_to_remove = dups.index[1:]
                res_choice = res_choice.drop(index=Rx_inds_to_remove)
                ndups = utils.check_for_duplicates(res_choice, ['round'])
                assert ndups == 0, f'there are {ndups} round duplicates in cluster {_cluster_label} (after trying to remove duplicates)'
            
            _core_dir = _scene_dir + f'/core-{"0"*(3-(len(str(_cluster_label))))}{_cluster_label}'
            mmkdir(_core_dir)
            
            # write metadata to disk 
            res_choice.to_csv(_core_dir + '/core_meta.csv')

            for i, row in parsed_names.sort_values(['round', 'color_channel']).reset_index(drop=True).iterrows(): 

                #print('\tprogress:', i, end='\r')
                temp = res_choice[(res_choice.cluster == _cluster_label) & (res_choice['round'] == row['round'])]
                
                # if there is a missing round, omit it
                if temp.shape[0] == 0: continue
                
                # select the proper bounding box for each matched core
                _core = segment.select_core(imgs[row.original], temp.component, temp, config=config, scale=config.downsample_proportion)
                
                # save image to file 
                sitk.WriteImage(_core, f'{_core_dir}/unregistered_core={_cluster_label}_round={row["round"]}_color={row.color_channel}.tif')
        except:
            print(f'core cluster {_cluster_label} failed - it will be excluded from downstream analysis')

if __name__ == '__main__': 
    print('starting `segment_and_match_cores.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Segmentation of cores & matching across rounds.')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='directory of input files (.tif slide scenes)')
    parser.add_argument('--output', metavar='out', type=str, nargs=1,
                        help='directory of output files (registered cores)')
    parser.add_argument('--slide', metavar='slide', type=str, nargs=1,
                        help='slide name (identifier)')
    parser.add_argument('--scene', 
                        metavar='scene', 
                        type=str, 
                        nargs=1,
                        help='scene name (identifier)',
                        default=['None']) # necessary if there is no scene name provided
    parser.add_argument('--config', 
                        metavar='config', 
                        type=str, 
                        nargs=1,
                        help='path to config file',
                        default=['None']) # necessary if there is no scene name provided                    
    args = parser.parse_args()

    print('scene:', args.scene[0])
    
    main(args.input[0], args.output[0], args.slide[0], args.scene[0], args.config[0])
    
    
            
            
    

    
    
    
    
    
    