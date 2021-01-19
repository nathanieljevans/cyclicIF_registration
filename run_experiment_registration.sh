#!/bin/bash

# for this script we're just going to register one slide name and scene 
# in the future we can parse which slides/scenes are available and run them all

# NOTE! make sure conda environment is active (cycIF_reg)

myloc=$(pwd)
data_dir=/mnt/z/Marilyne/Axioscan/5_Pejovic/Tiffs/Registration/
script_dir=/mnt/c/Users/Public/cyclicIF_processing/cyclicIF_registration/workflow/scripts/

slide_name=S3
scene_name=Scene-1    # use None (no quotes) to specify no scene name is given - cap sensitive 

#dedust_out=/mnt/d/cyclicIF_outputs/5_Pejovic/S3/test_de-dusted/
prereg_out=/mnt/d/cyclicIF_outputs/5_Pejovic/S3/pre-registered_imgs/
output_dir=/mnt/d/cyclicIF_outputs/5_Pejovic/S3/registered_cores/
restitched_out=/mnt/d/cyclicIF_outputs/5_Pejovic/S3/registered_imgs/
qc_path=/mnt/e/CycIF_analysis/registration_outputs/QC_file.json

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

# dedust the dapi images 
# python dedust_dapi_images.py --input /mnt/z/Marilyne/Axioscan/6-Dhivya/split/No_Scene/ --output /mnt/e/CycIF_analysis/registration_outputs/test_de-dusted/ --slide D1 --scene None
#echo 'de-dusting images'
#date
#python dedust_dapi_images.py --input $data_dir --output $dedust_out --slide $slide_name --scene $scene_name --config $myloc

# pre register TMAs 
# python slide_registration.py --input /mnt/e/CycIF_analysis/registration_outputs/test_de-dusted/ --output /mnt/e/CycIF_analysis/registration_outputs/test --slide D1 --scene None
echo 'slide pre-registration'
date
python slide_registration.py --input $data_dir --output $prereg_out --slide $slide_name --scene $scene_name

# split cores and match across rounds
# python segment_and_match_cores.py --input /mnt/z/Marilyne/Axioscan/6-Dhivya/split/No_Scene/ --output /mnt/e/CycIF_analysis/registration_outputs/test_core_reg --slide D1 --scene None --config /mnt/e/CycIF_analysis/registration_outputs/6-Dhivya/D4
echo 'segmenting and matching cores'
date
python segment_and_match_cores.py --input $prereg_out --output $output_dir --slide $slide_name --scene $scene_name --config $myloc

# register each core 
echo 'registering and evaluating cores'
date
scene_dir=$output_dir/$slide_name/$scene_name
for core_dir in $scene_dir/*/
do
    echo "registering $core_dir dir..."
    python register_core.py --input $core_dir --config $myloc
    python evaluate_core_registration.py --input $core_dir
    #ls $core_dir | grep -P "unregistered_.*_round=R[1-9].*" | xargs -d"\n" rm   # TODO - delete unregistered cores 
done

# aggregate results 
echo 'aggregating results'
date
python aggregate_results.py --dir $output_dir

echo 'generate QC file' 
#python generate_QC_file.py --results /mnt/e/CycIF_analysis/registration_outputs/test_core_reg/aggregated_results.csv --output /mnt/e/CycIF_analysis/registration_outputs/QC_file.json --slide D1 --scene None --config /mnt/e/CycIF_analysis/registration_outputs/6-Dhivya/D4
date 
python generate_QC_file.py --results $output_dir/aggregated_results.csv --output $qc_path --config $myloc --slide $slide_name --scene $scene_name

## restitch the cores 
#### NOTE: qc is None 
echo 'restitiching cores'
date
python restitch_cores.py --results_path $output_dir/aggregated_results.csv --slide $slide_name --scene $scene_name --qc None --config $myloc --output $restitched_out

echo 'registration pipeline complete'
date
