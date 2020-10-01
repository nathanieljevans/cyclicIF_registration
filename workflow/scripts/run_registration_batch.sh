#!/bin/sh

data_dir=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/data
out_dir=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output
slide_name=S3
scene=Scene-1

echo 'segmenting and matching cores...' 
time {
python segment_and_match_cores.py --input $data_dir --output $out_dir --slide $slide_name --scene $scene
}
echo 'core segmentation and matching is complete.'

scene_dir=$out_dir/$slide_name/$scene
for core_dir in $scene_dir/*
do
    echo $core_dir
    sbatch process_core_sbatch.sh $core_dir
done

echo 'sbatch core assignment complete. After the jobs have completed, run `aggregate_results.py`' 

