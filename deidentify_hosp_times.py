import pandas as pd
from pathlib import Path
import xlwings as xw
import tools


E_DRIVE = Path('E:\\stroke_data\\')

# load KORI_GRANT, excel will popup and ask for password
sheet = xw.Book(str(E_DRIVE/'KORI_GRANT.xlsx') ).sheets[0]
time_df = sheet['A27:AD311'].options(convert=pd.DataFrame,index=False,header=True).value

time_df.drop_duplicates(inplace=True)
time_df.set_index('AHA_ID',inplace=True)
time_df.head()
out = time_df[time_df.columns[1:13]]
out.index=out.index.map(tools.get_hosp_keys())
out.index.name='HOSP_KEY'
out.reset_index(inplace=True)
out.to_excel(E_DRIVE/'deidentified_DTN.xlsx',index=False)
