#!/bin/sh

data_dir=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/data
out_dir=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output
slide_name=S3
scene=Scene-1

echo 'segmenting and matching cores...' 
time {
python segment_and_match_cores.py --input $data_dir --output $out_dir --slide $slide_name --scene $scene
}
echo 'complete.'

scene_dir=$out_dir/$slide_name/$scene
for core_dir in $scene_dir/*
do
    time {
    echo "registering $core_dir dir..."
    python register_core.py --input $core_dir
    python evaluate_core_registration.py --input $core_dir
    }
    ls $core_dir | grep -P "unregistered_.*_round=R[1-9].*" | xargs -d"\n" rm
done

