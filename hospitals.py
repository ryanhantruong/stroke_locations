'''Load, manipulate, and write hospital location files'''
import os
import pandas as pd


HOSPITAL_DIR = os.path.join('data', 'hospitals')
if not os.path.isdir(HOSPITAL_DIR):
    os.makedirs(HOSPITAL_DIR)


def load_hospitals(hospital_file):
    '''
    Read in the given relative filepath as a table of hospital information
    '''
    return pd.read_csv(hospital_file, sep='|').set_index('CenterID')
