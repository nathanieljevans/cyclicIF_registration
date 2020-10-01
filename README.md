# Cyclic Immunofluorescence Registration Pipeline




--- 

## Pipeline 

To run the registration pipeline for a single experiment: 

```$ ./run_registration.sh --input /path/to/images/directory --output /path/to/output/directory --slide S1 --scene Scene-1```

To run this pipeline in parrallel, use: 

```$ ./run_registration_batch.sh --input /path/to/images/directory --output /path/to/output/directory --slide S1 --scene Scene-1```
 
For specific pipeline steps, see `tutorial.ipynb` 

## Output Structure

```
output
│  └ registration_results.csv 
│       
│
└───<slide_name_01>
│   │
│   │       
│   └───<scene_name_01>
│   │     │
│   │     │
│   │     └──<core_label_01>
│   │     │      └ batch_log_file.log
│   │     │      └ core_meta.csv
│   │     │      └ registration_eval.csv
│   │     │      └ registered_core=1_round=R1_color=c1.tif
│   │     │      └ ...
│   │     │      └ unregistered_core=1_round=R1_color=c1.tif
│   │     │      └ ...
│   │     │
       
```

> batch_log_file.log:                         log file for the sbatch command 
> core_meta.csv:                              meta data for core, includes shape statistics for the dapi segmentations 
> registration_eval.csv:                      registration eval metrics
> registered_core=1_round=R1_color=c1.tif     registered image: round, color channel
> unregistered_core=1_round=R1_color=c1.tif   unregistered image: round, color channel (**note:** R0, c1 is the DAPI fixed channel that all others are registered too. 
> registration_results.csv                    aggregated results from all experiments/cores. 

## Results 

To interact with the results (especially if you're working on a remote file system), it's easiest to use the `results.ipynb` notebook. This allows the user to visualize experiment segmentations and registered images. Additionally, registration metrics can be evaluated to identify outliers. 

## Quality Control 

...
 
