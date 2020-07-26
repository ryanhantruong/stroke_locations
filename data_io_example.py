from pathlib import Path
import tools
import pandas as pd

_stroke_dir = Path('Path to directory that contain outputs of stroke_analysis/preprocessing')
DTN_PATH  = _stroke_dir / 'processed_data'
HOSPITAL_ADDY = DTN_PATH / 'hospital_address_NE_for_stroke_locations.csv'
HOSP_KEY_PATH = DTN_PATH /'hospital_keys_master_v2.csv'

def get_hosp_keys(hospital_key=HOSP_KEY_PATH):
    keys = pd.read_csv(hospital_key).set_index('HOSP_ID')
    keys_dict = tools.smart_dict()
    keys_dict.update(keys['HOSP_KEY'].to_dict())
    return keys_dict

def get_hosp_keys_in_str():
    keys = get_hosp_keys()
    keys_out = {str(k): str(v) for k, v in keys.items()}
    return keys_out
