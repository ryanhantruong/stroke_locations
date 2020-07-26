import pandas as pd
from pathlib import Path
import numpy as np
import json

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

def cast_to_int_then_str(x):
    if pd.isnull(x):
        return np.nan
    elif isinstance(x, str):
        return x
    else:
        return str(int(x))
