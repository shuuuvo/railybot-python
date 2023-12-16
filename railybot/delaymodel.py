import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.neighbors import KNeighborsRegressor

df = pd.read_csv('WEY_WAT_2020_performance.csv')

# drop rows where train does not stop
df.drop(df[df.journeyLocationType == 'PP'].index, inplace=True)

# date extraction from 'rid' column
df['rid'] = df['rid'].astype(str)
df['date'] = df['rid'].str.extract(r'(\d{1,8})').squeeze().str.zfill(8)

# new dataframe for specific features
df2 = df.iloc[:,[3,16,17,38]]

# extraction of 'weekend' column from 'date'
df2['date'] = pd.to_datetime(df2['date'])
df2['weekend'] = df2['date'].dt.day_name().isin(['Saturday', 'Sunday']).astype(int)

# travel time from one station to another station
df2['dest'] = df2['tiploc'].shift(-1)
df2['dest_wta'] = df2['wta'].shift(-1)
df2['wtd'] = pd.to_datetime(df2['wtd'])
df2['dest_wta'] = pd.to_datetime(df2['dest_wta'])
df2['travel_time'] = (df2['dest_wta']-df2['wtd'])
df2['travel_time'] = pd.to_timedelta(df2['travel_time']).dt.total_seconds()

# waiting time at specific station
df2['wta'] = pd.to_datetime(df2['wta'])
df2['wait_time'] = (df2['wtd']-df2['wta'])
df2['wait_time'] = pd.to_timedelta(df2['wait_time']).dt.total_seconds()
df2['travel_time'] = df2['travel_time'].fillna(0)
df2['wait_time'] = df2['wait_time'].fillna(0)

# 'total_time' column from travel time and waiting time for any station
df2['total_time'] = df2['travel_time'] + df2['wait_time']

# arrival time extracted into hour, min, sec column
df2['ar_hour'] = df2.wta.dt.hour
df2['ar_min'] = df2.wta.dt.minute
df2['ar_sec'] = df2.wta.dt.second
df2['ar_hour'] = df2['ar_hour'].fillna(0)
df2['ar_min'] = df2['ar_min'].fillna(0)
df2['ar_sec'] = df2['ar_sec'].fillna(0)

# station name encoded into numeric data
df2['st_code'] = pd.factorize(df2['tiploc'])[0]

# peak hour column creation
def peak_hour(row):
    if 6 < row['ar_hour'] < 11:
        return 1
    elif 16 < row['ar_hour'] < 20:
        return 1
    else:
        return 0

df2['peak'] = df2.apply(peak_hour, axis=1)

# final dataframe and dataset
f_df = df2[['st_code', 'weekend', 'peak', 'ar_hour', 'ar_min', 'ar_sec', 'total_time']]
f_df = f_df.astype(np.int64)

# model training and creation
X = f_df[['st_code','weekend','peak','ar_hour','ar_min','ar_sec']]
Y = f_df[['total_time']]

Xtrain, Xtest, Ytrain, Ytest = train_test_split(X, Y, test_size=0.25, random_state=1)

knn = KNeighborsRegressor(n_neighbors=7)
knn.fit(Xtrain, Ytrain)

filename = 'model/_delay/finalized_model.sav'
pickle.dump(knn, open(filename, 'wb'))

# loaded_model = pickle.load(open(filename, 'rb'))
# sample = [[12,1,0,11,32,0]]
# result = loaded_model.predict(sample)
# print(result)

