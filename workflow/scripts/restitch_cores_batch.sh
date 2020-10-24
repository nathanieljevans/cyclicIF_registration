#!/bin/bash
#SBATCH --partition exacloud
#SBATCH --account MillsLab
#SBATCH --cpus-per-task 15
#SBATCH --mem 16GB
#SBATCH --time 2:00:00
#SBATCH --job-name restitch-evans
#SBATCH --output=./restitch_output.log

# for some reason by conda doesn't seem to be initialized right 
#source ~/.bashrc

conda activate cycIF_reg

results_path=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/aggregated_results.csv
output_dir=/home/exacloud/lustre1/NGSdev/evansna/cyclicIF/output/S3/Scene-1/
slide_name=S3
scene_name=Scene-1
QC=None # can be None or a file path 

python restitch_cores.py --results_path $results_path --output $output_dir --slide $slide_name --scene $scene_name --qc $QC
