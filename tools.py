import pandas as pd
from pathlib import Path
import numpy as np
import json

HOSP_KEY_PATH = Path('E:\\stroke_data\\') / 'hospital_keys.csv'

MAPBOX_TOKEN = json.loads(open('config/mapbox.json').readline())['token']

CENTER_GEO = {
    'Boston': {
        'lat': 42.361145,
        'lon': -71.057083
    },
    'NYC': {
        'lat': 40.730610,
        'lon': -73.935242
    }
}


class smart_dict(dict):
    # to suppport mapping of AHA_ID to HOSP_KEY
    def __missing__(self, key):
        return key


def get_hosp_keys(hospital_key=HOSP_KEY_PATH):
    keys = pd.read_csv(hospital_key).set_index('HOSP_ID')
    keys_dict = smart_dict()
    keys_dict.update(keys['HOSP_KEY'].to_dict())
    return keys_dict


def get_hosp_keys_in_str():
    keys = get_hosp_keys()
    keys_out = {str(k): str(v) for k, v in keys.items()}
    return keys_out


def cast_to_int_then_str(x):
    if pd.isnull(x):
        return np.nan
    elif isinstance(x, str):
        return x
    else:
        return str(int(x))
