import pandas as pd
from pathlib import Path
import xlwings as xw
import numpy as np


file_path = Path('E:\\stroke_data\\')

# load KORI_GRANT, excel will popup and ask for password
sheet = xw.Book(str(file_path/'KORI_GRANT.xlsx') ).sheets[0]
time_df = sheet['A27:AD311'].options(convert=pd.DataFrame,index=False,header=True).value
time_df.drop_duplicates(inplace=True)
# figure out center type
prim_center_filter = time_df['ARTPUNC_N'].isna() | time_df['ARTPUNC_P75'].isna() | time_df['ARTPUNC_P25'].isna() | time_df['ARTPUNC_MEDIAN'].isna()
time_df['CENTER_TYPE'] = 'Comprehensive'
time_df.loc[prim_center_filter,'CENTER_TYPE'] = 'Primary'
# KORI_GRANT said 36 CSC but only 34 seems to ARTPUNCH time

# AHA_ID and hospital adddress look up
aha_address = pd.read_excel(file_path/'AHA 2012 ID codes.xlsx',header=None,names=['AHA_ID','Name','Street','City',
'Postal_Code','State'])

# cross-list data in both spreadsheets
merge = aha_address.merge(time_df[['AHA_ID','SITE_ID','CENTER_TYPE']],on='AHA_ID',how='inner')
merge['Failed_Lookup'] = False
merge['Latitude'] = np.nan
merge['Longitude'] = np.nan


# rename columns so that it'll be similar to Patrick's input
# purpose: so file is compatible with hospitals.update_locations_han()
merge.columns = ['AHA_ID','OrganizationName','Street','City','PostalCode','State','SITE_ID','CenterType'
'Failed_Lookup','Latitude','Longitude']
merge.to_csv(file_path/'inner_join_siteID.csv',index=False)

# review output
df = pd.read_csv(file_path/'inner_join_siteID.csv',sep='|')
df.head()
