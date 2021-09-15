#!/bin/bash

# for this script we're just going to register one slide name and scene 
# in the future we can parse which slides/scenes are available and run them all

# NOTE! make sure conda environment is active (cycIF_reg)
# DNC = DO NOT CHANGE

myloc=$(pwd)	# DNC
data_dir=/mnt/z/Marilyne/Axioscan/6-Dhivya/split/No_Scene/ 									 # unregistered image path
script_dir=/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/scripts/	 # github repo paths, DNC 
output_dir=/mnt/e/CycIF_analysis/registration_outputs/registered_cores/						 # github repo paths, DNC 
slide_name=D1	   # 
scene_name=None    # use None (no quotes) to specify no scene name is given - cap sensitive 

prereg_out=/mnt/e/CycIF_analysis/registration_outputs/pre-registered_imgs/  # where to save pre-registered images
restitched_out=/mnt/e/CycIF_analysis/registration_outputs/registered_imgs/	# where to save re-stitched & regstered images
qc_path=/mnt/e/CycIF_analysis/registration_outputs/QC_file.json				# path to QC file

echo '###########################################################################################'
echo '###########################################################################################'

echo 'using data directory:' 
echo $data_dir

echo 'using output directory:' 
echo $output_dir

echo 'using script directory:'
echo $script_dir 

echo 'processing slide name:' 
echo $slide_name 

echo 'processing scene name:' 
echo $scene_name 

echo '###########################################################################################'
echo '###########################################################################################'

# becacuse python calls are wrapped in run_registration... 
cd $script_dir

echo 'slide pre-registration'
date
python slide_registration.py --input $data_dir --output $prereg_out --slide $slide_name --scene $scene_name

echo 'segmenting and matching cores'
date
python segment_and_match_cores.py --input $data_dir --output $output_dir --slide $slide_name --scene $scene_name --config $myloc

echo 'registering and evaluating cores'
date
scene_dir=$output_dir/$slide_name/$scene_name
for core_dir in $scene_dir/*/
do
    echo "registering $core_dir dir..."
    python register_core.py --input $core_dir --config $myloc
    python evaluate_core_registration.py --input $core_dir
done

echo 'aggregating results'
date
python aggregate_results.py --dir $output_dir

echo 'generate QC file' 
date 
python generate_QC_file.py --results $output_dir/aggregated_results.csv --output $qc_path --config $myloc --slide $slide_name --scene $scene_name

echo 'restitiching cores'
date
python restitch_cores.py --results_path $output_dir/aggregated_results.csv --slide $slide_name --scene $scene_name --qc $qc_path --config $myloc --output $restitched_out

echo 'registration pipeline complete'
date
