#!/bin/sh
### DEPRECATED

# the order of elements passed to the script will define these inputs below. 
data_dir=$1 #/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/data
out_dir=$2 #/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output
slide_name=$3 #S3
scene=$4 #Scene-1
config_path=$5 # #/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/config.py

echo 'segmenting and matching cores...' 

python segment_and_match_cores.py --input $data_dir --output $out_dir --slide $slide_name --scene $scene --config $config_path

echo 'complete.'

scene_dir=$out_dir/$slide_name/$scene
for core_dir in $scene_dir/*/
do
    echo "registering $core_dir dir..."
    python register_core.py --input $core_dir --config $config_path
    python evaluate_core_registration.py --input $core_dir
    #ls $core_dir | grep -P "unregistered_.*_round=R[1-9].*" | xargs -d"\n" rm
done

