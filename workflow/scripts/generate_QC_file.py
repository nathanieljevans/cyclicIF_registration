'''

'''
import argparse

import pandas as pd

import numpy as np

import json

import sys, os
sys.path.append('../libs/')
import utils
import segment 
import match 
import register 
import evaluate 
import qc 


if __name__ == '__main__':     
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. QC file generation.')
    parser.add_argument('--results', metavar='results', type=str, nargs=1,
                        help='path to aggregtated results')
    parser.add_argument('--output', metavar='out', type=str, nargs=1,
                        help='path name to save QC file')
    parser.add_argument('--config', 
                        metavar='config', 
                        type=str, 
                        nargs=1,
                        help='directory to config.py',
                        default=['None']) # necessary if there is no scene name provided  
    parser.add_argument('--slide', metavar='slide', type=str, nargs=1,
                        help='slide name (identifier)')
    parser.add_argument('--scene', 
                        metavar='scene', 
                        type=str, 
                        nargs=1,
                        help='scene name (identifier)',
                        default=['None']) # necessary if there is no scene name provided                  
    args = parser.parse_args()

    # load config namespace 
    config = utils.load_config(args.config[0])

    # load results 
    res = pd.read_csv(args.results[0])

    # filter to desired slide and scene 
    res = res[lambda x: (x.slide_name==args.slide[0]) & (x.scene==args.scene[0])]

    # filter to registered dapi observations
    res = res[lambda x: (x.status=='registered') & (x.color_channel=='c1')]

    # select cores to remove 
    toremove = res[lambda x: (x.dice_coef < config.QC_dice_coef)]

    # organize into dict 
    myqc = {}
    for _round in toremove['round'].sort_values().unique(): 
        temp = toremove[lambda x: x['round'] == _round]
        assert temp.core.unique().tolist()==temp.core.values.tolist(), 'duplicate dapi cores to be removed'
        myqc[_round] = temp.core.values.tolist()

    with open(args.output[0], 'w') as fp:
        json.dump(myqc, fp)

