from zipfile import ZipFile
from pandas import read_csv, to_datetime, Series
from os import listdir
from os.path import join
from scipy.sparse import csr_matrix, hstack, vstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import SGDRegressor, SGDClassifier
from time import time
from numpy import log, exp

BASE_DIR = '/Users/swheeler/Downloads/flights/'
TEST_PCT = 0.1
all_files = [f for f in listdir(BASE_DIR) if f.endswith('.zip')]
drop_cols = [
    'CANCELLATION_CODE', 'CARRIER_DELAY', 'WEATHER_DELAY', 'NAS_DELAY', 'SECURITY_DELAY', 'LATE_AIRCRAFT_DELAY',
    'CANCELLED', 'DIVERTED', 'DEP_TIME', 'FLIGHTS', 'AIRLINE_ID', 'UNIQUE_CARRIER', 'ORIGIN_AIRPORT_SEQ_ID',
    'DEST_AIRPORT_SEQ_ID', 'CARRIER', 'FL_NUM', 'FL_DATE', 'CRS_DEP_TIME'
]
hashing_cols = [
    'TAIL_NUM', 'ORIGIN_AIRPORT_ID', 'ORIGIN_CITY_MARKET_ID', 'DEST_AIRPORT_ID', 'DEST_CITY_MARKET_ID', 'FLIGHT',
    'FL_MONTH', 'FL_WEEK', 'FL_DAY', 'FL_DAYOFWEEK', 'FL_HOUR', 'FL_MINUTE'
]

tf_vectorizer = HashingVectorizer(
    analyzer='word',
    n_features=1048576,
    binary=False,
    norm='l1',
    non_negative=False
)

sgdr = SGDClassifier(
    loss='huber',
    penalty='elasticnet',
    alpha=0.0001,
    l1_ratio=0.5,
    fit_intercept=True,
    n_iter=50,
    shuffle=True,
    verbose=0,
    epsilon=0.1,
    random_state=42,
    learning_rate='optimal',
    warm_start=False,
    average=False,
)

test_x_list = []
test_y_all = Series()
for filename in all_files:
    t1 = time()
    print filename,
    with open(join(BASE_DIR, filename), 'r') as f:
        zipfile = ZipFile(f)
        file_name = [f.filename for f in zipfile.filelist if f.filename.endswith('.csv')].pop()
        df = read_csv(zipfile.open(file_name), low_memory=False)
    df = df[df['CANCELLED'].eq(0.0)]
    df['FLIGHT'] = df['UNIQUE_CARRIER'] + df['FL_NUM'].astype('str')
    df['FL_TIMESTAMP'] = df['FL_DATE'] + \
        df['CRS_DEP_TIME'].astype('str').apply(lambda v: v.zfill(4)).str.replace(r'(\d{2})(\d{2})', r' \1:\2')
    drop_cols += [c for c in df.columns if c.startswith('Unnamed')]
    df = df.drop(drop_cols, axis=1)
    df['FL_TIMESTAMP'] = to_datetime(df['FL_TIMESTAMP'])
    df['FL_MONTH'] = df['FL_TIMESTAMP'].apply(lambda v: v.month)
    df['FL_WEEK'] = df['FL_TIMESTAMP'].apply(lambda v: v.week)
    df['FL_DAY'] = df['FL_TIMESTAMP'].apply(lambda v: v.day)
    df['FL_DAYOFWEEK'] = df['FL_TIMESTAMP'].apply(lambda v: v.dayofweek)
    df['FL_HOUR'] = df['FL_TIMESTAMP'].apply(lambda v: v.hour)
    df['FL_MINUTE'] = df['FL_TIMESTAMP'].apply(lambda v: v.minute)
    df = df.sort_values(['FL_TIMESTAMP'])
    df['n_flights_1h'] = df.groupby('ORIGIN_AIRPORT_ID').apply(
        lambda df2: df2.rolling('1h', on='FL_TIMESTAMP').count()['FL_MINUTE']).reset_index(0, drop=True)
    df['n_flights_2h'] = df.groupby('ORIGIN_AIRPORT_ID').apply(
        lambda df2: df2.rolling('2h', on='FL_TIMESTAMP').count()['FL_MINUTE']).reset_index(0, drop=True)
    df['n_flights_3h'] = df.groupby('ORIGIN_AIRPORT_ID').apply(
        lambda df2: df2.rolling('3h', on='FL_TIMESTAMP').count()['FL_MINUTE']).reset_index(0, drop=True)
    df = df.drop(['FL_TIMESTAMP'], axis=1)

    text = ''
    for c in hashing_cols:
        text += (' ' + c + '__' + df[c].astype('str'))

    outcome = df['DEP_DELAY'].copy()
    outcome.loc[outcome.lt(0)] = 0.0
    outcome.loc[outcome.gt(0)] = 1.0

    df = df.drop(hashing_cols + ['DEP_DELAY'], axis=1)

    train_idx, test_idx = train_test_split(outcome, test_size=TEST_PCT)

    train_y = outcome.iloc[train_idx]
    test_y = outcome.iloc[test_idx]
    train_x_t = text.iloc[train_idx]
    test_x_t = text.iloc[test_idx]
    train_x_v = df.iloc[train_idx, :]
    test_x_v = df.iloc[test_idx, :]

    tf = tf_vectorizer.fit_transform(train_x_t.tolist())
    train_x = hstack([csr_matrix(train_x_v), tf], format='csr')

    tf = tf_vectorizer.fit_transform(test_x_t.tolist())
    test_x = hstack([csr_matrix(test_x_v), tf], format='csr')

    test_x_list.append(test_x)
    test_y_all = test_y_all.append(test_y, ignore_index=True)

    _ = sgdr.partial_fit(train_x, train_y, classes=[0.0, 1.0])

    print time() - t1

test_x = vstack(test_x_list, format='csr')
test_y = test_y_all.to_frame('original')
test_y['predicted'] = sgdr.predict_proba(test_x)[1]



mad = (test_y['original'] - test_y['predicted']).abs().median()
type_s = (test_y['original'].gt(0.0) == test_y['predicted'].gt(0.0)).mean()
fn = (test_y['original'].gt(0.0) & test_y['predicted'].le(0.0)).mean()
fp = (test_y['original'].le(0.0) & test_y['predicted'].gt(0.0)).mean()


import seaborn as sns
sns.distplot(test_y['original'])