#!/bin/bash
#SBATCH --partition exacloud
#SBATCH --account MillsLab
#SBATCH --cpus-per-task 1
#SBATCH --mem 2GB
#SBATCH --time 0:05:00
#SBATCH --job-name core-reg-evans
#SBATCH --output=/dev/null

core_dir=$1
log=$core_dir/batch_log_file.log
touch $log

echo "registering $core_dir dir..." > $log
python register_core.py --input $core_dir >> $log
echo "evaluating registration success in $core_dir..." >> $log
python evaluate_core_registration.py --input $core_dir >> $log