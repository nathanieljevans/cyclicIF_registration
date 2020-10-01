import argparse
import pandas as pd

import sys, os
sys.path.append('../libs/')
import utils
import config
import segment 
import match 
import missingness 
import register 
import evaluate 
import qc


if __name__ == '__main__': 
    print('starting `aggregate_results.py`...') 
    
    parser = argparse.ArgumentParser(description='CyclicIF registration pipeline. Aggregate all registration results for a given directory.')
    parser.add_argument('--input', metavar='in', type=str, nargs=1,
                        help='output directory')
    args = parser.parse_args()
    
    