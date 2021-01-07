#!/bin/bash

###########################################################################
# Initialize local folder to store processed results & project config.py  #
#                                                                         #
# usage                                                                   #
# ./init_project.sh /path/to/experiment/folder                            #
# warning: this will erase the contents of the folder if it exists        #
###########################################################################


out=$1 

echo '##########################################################################'
echo 'initializing new cyclicIF folder'

rm -r $out 

mkdir $out

cp ../libs/_config.py $out/config.py 

cp ../../tutorial.ipynb $out/tutorial.ipynb

cp ../../results.ipynb $out/results.ipynb

cp ../../full_slide_registration_evaluation.ipynb $out/full_slide_registration_evaluation.ipynb

cp ../../QC_plots.ipynb $out/QC_plots.ipynb

cp ../../dedusting_eval.ipynb $out/dedusting_eval.ipynb

cp run_experiment_registration.sh $out/run_experiment_registration.sh

mkdir $out/dedusted_imgs
mkdir $out/pre-registered_imgs
mkdir $out/registered_cores
mkdir $out/registered_imgs

echo 'project initialization complete, navigate to:'
echo "$out"
echo '##########################################################################'