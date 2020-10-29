'''


''' 
import argparse
import SimpleITK as sitk
import pandas as pd
import shutil

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

def mmkdir(path, remove=True): 
    '''
    my version of mkdir 
    '''
    if os.path.exists(path) and remove:
        shutil.rmtree(path)
        os.mkdir(path) 
    elif not os.path.exists(path): 
        os.mkdir(path) 
        
def main(inp, out, slide, scene): 
    '''
        inp     input directory 
        out      output directory 
        slide     slidename 
        scene    scene name 
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
    
    # load images into memory 
    imgs = {}
    for i,path in enumerate(parsed_names.original.values): 
        print(f'loading images... progress: {i}/{parsed_names.original.values.shape[0]}', end='\r')
        imgs[path] = sitk.ReadImage(inp + '/' + path)
    
    # segment cores and get statistics 
    res, R0_dapi = match.get_all_rounds_core_statistics(parsed_names, imgs, verbose=True, return_R0_dapi=True)
    
    # create core id mapping 
    R0_dapi_stats = res[lambda x: x['round'] == 'R0']
    segment.generate_core_id_map(R0_dapi, R0_dapi_stats, plot=False, out=_scene_dir) 
    
    # match across rounds + assign cluster labels to each component 
    cluster_labels = match.match_cores_across_rounds(res)
    res = res.assign(cluster = cluster_labels)
    
    for i,_cluster_label in enumerate(cluster_labels): 
        print(f'core {i}/{len(cluster_labels)} | label: {_cluster_label}')
        
        res_choice = res[res.cluster == _cluster_label]
        
        _core_dir = _scene_dir + f'/core-{"0"*(3-(len(str(_cluster_label))))}{_cluster_label}'
        mmkdir(_core_dir)
        
        # write metadata to disk 
        res_choice.to_csv(_core_dir + '/core_meta.csv')

        for i, row in parsed_names.sort_values(['round', 'color_channel']).reset_index(drop=True).iterrows(): 

            print('\tprogress:', i, end='\r')
            temp = res_choice[(res_choice.cluster == _cluster_label) & (res_choice['round'] == row['round'])]
            
            # if there is a missing round, omit it
            if temp.shape[0] == 0: continue
            
            # select the proper bounding box for each matched core
            _core = segment.select_core(imgs[row.original], temp.component, temp, scale=config.downsample_proportion)
            
            # save image to file 
            sitk.WriteImage(_core, f'{_core_dir}/unregistered_core={_cluster_label}_round={row["round"]}_color={row.color_channel}.tif')
    
    
    
        
if __name__ == '__main__': 
    print('starting `segment_and_match_cores.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Segmentation of cores & matching across rounds.')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='directory of input files (.tif slide scenes)')
    parser.add_argument('--output', metavar='out', type=str, nargs=1,
                        help='directory of output files (registered cores)')
    parser.add_argument('--slide', metavar='slide', type=str, nargs=1,
                        help='slide name (identifier)')
    parser.add_argument('--scene', metavar='scene', type=str, nargs=1,
                        help='scene name (identifier)')
    args = parser.parse_args()
    
    main(args.input[0], args.output[0], args.slide[0], args.scene[0])
    
    
            
            
    

    
    
    
    
    
    