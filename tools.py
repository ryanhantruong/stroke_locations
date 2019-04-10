import pandas as pd
from pathlib import Path

HOSP_KEY_PATH = Path('E:\\stroke_data\\')/'hospital_keys.csv'

class smart_dict(dict):
    # to suppport mapping of AHA_ID to HOSP_KEY
    def __missing__(self, key):
        return key

def get_hosp_keys():
  keys = pd.read_csv(HOSP_KEY_PATH).set_index('AHA_ID')
  keys_dict = smart_dict()
  keys_dict.update(keys['Key'].to_dict())
  return keys_dict

def get_hosp_keys_in_str():
  keys = get_hosp_keys()
  keys_out = {str(k):str(v) for k,v in keys.items()}
  return keys_out
