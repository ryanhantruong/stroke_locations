import pandas as pd
from pathlib import Path
import xlwings as xw

file_path = Path('E:\\stroke_data\\')

# load KORI_GRANT, excel will popup and ask for password
sheet = xw.Book(str(file_path/'KORI_GRANT.xlsx') ).sheets[0]
time_df = sheet['A27:AD311'].options(convert=pd.DataFrame,index=False,header=True).value
time_df.drop_duplicates(inplace=True)
time_df.head()
time_df.reset_index(inplace=True)
time_df[['index','AHA_ID','SITE_ID']].to_csv('hospital_keys.csv')
