"""Script for Get Your Guide data task

This code is meant to accompany the writeup.
"""

from pandas import read_csv, to_datetime, DataFrame, get_dummies, MultiIndex
from numpy import log, exp
from os.path import join
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import KFold

CSV_SOURCE_DIR = '/Users/swheeler/Downloads/ds_ana_assessment/'
TRAIN_FILE = 'train.csv'
TEST_FILE = 'prediction.csv'

train_path = join(CSV_SOURCE_DIR, TRAIN_FILE)
test_path = join(CSV_SOURCE_DIR, TEST_FILE)


def remove_unprofitable_groups(df, cols, outcome_col, verbose=True):
    """Remove all rows associated with features that lack non-zero outcomes in the data set.

    This function takes any arbiraty set of columns of categorical variables, and sums
    and outcome column for each category. All categories with sums of zero are removed.

    Args:
        df (pandas.DataFrame): The data set to filter.
        cols (list): Column names associated with categorical variables.
        outcome_col (str): The name of the column to be summed for each catgory.
        verbose (bool): A flag indicating whether to print the the number of rows removed
            for each `col`.

    Returns:
        pandas.DataFrame: The input data frame, with rows removed.

    """

    drop_rows = df[outcome_col].isnull()
    for col in cols:
        zero_rev = df.groupby(col)[outcome_col].sum().eq(0)
        zero_rev_filt = df[col].isin(zero_rev[zero_rev].index)
        if verbose:
            print col, zero_rev_filt.sum()
        drop_rows = drop_rows | zero_rev_filt
    return df[~drop_rows]


def rough_cut(df, outcome_col, cols, count_gt=400, std_weight=1.0, remove_nulls=None):
    """Remove all rows that fail to meet a sample size or distributional cutoff.

    This function takes any arbiraty set of columns of categorical variables, and sums
    and outcome column for each category. All categories with sums of zero are removed.

    Args:
        df (pandas.DataFrame): The data set to filter.
        outcome_col (str): The name of the column to be summed for each catgory.
        cols (list): Column names associated with categorical variables.
        count_gt (int): The minimum number of rows for which a category must be represented.
        std_weights (float): The differnce in means in `outcome_col` will be calcualted for each
            category, and only those with a difference greater than `std_weight` * the standard deviation
            of all differences in means across categories will be kept.
        remove_nulls (list): A list of columns on which to do additional filtering. After categories have
            been filtered out from each of `cols`, if any given row is null for all values of
            `remove_nulls`, it will be removed from the data set.

    Returns:
        pandas.DataFrame: The input data frame, with columns filtered and rows removed.

    """

    keep_values = {}
    for c in cols:
        in_sum = df.groupby(c)[outcome_col].sum()
        in_count = df.groupby(c)[outcome_col].count()
        all_sum = train[outcome_col].sum()
        all_count = train[outcome_col].count()
        diff_means = (in_sum / in_count) - ((all_sum - in_sum) / (all_count - in_count))
        diff_means = diff_means[in_count.gt(count_gt)]
        diff_means_std = diff_means.std() * std_weight
        keep_values[c] = diff_means[diff_means.gt(diff_means_std)]

    for k, v in keep_values.items():
        df[k] = df[k].where(df[k].isin(v.index))

    if remove_nulls is not None:
        df = df[df[remove_nulls].notnull().any(axis=1)]

    return df

# column designations that will be used repeatedly
candidate_cols = ['keyword_id', 'ad_group_id', 'campaign_id', 'account_id']
additional_cols = ['device_id', 'match_type_id', 'day_of_week']
outcome_cols = ['revenue', 'clicks', 'conversions', 'revenue_per_click', 'log_revenue_per_click']

# read in data set and create needed variables
train = read_csv(train_path)
train.columns = [c.lower() for c in train.columns]
train['revenue_per_click'] = train['revenue'] / train['clicks']
train['day_of_week'] = to_datetime(train['date']).apply(lambda d: d.strftime('%w'))
train['log_revenue_per_click'] = log(train['revenue_per_click'] + 1)

train = remove_unprofitable_groups(train, cols=reversed(candidate_cols), outcome_col='revenue')

train = rough_cut(
    df=train,
    outcome_col='log_revenue_per_click',
    cols=candidate_cols,
    count_gt=400,
    std_weight=0,
    remove_nulls=['keyword_id', 'ad_group_id']
)

# one-hot encode variables
train_d = get_dummies(train[candidate_cols + additional_cols].astype('object'), sparse=True, prefix_sep='__')
train_d_midx = MultiIndex.from_tuples(
    [(v[0], int(float(v[1]))) for v in [c.split('__') for c in train_d.columns]],
    names=['variable', 'value']
)
train_d.columns = train_d_midx

# set up regressor to make an even compromise between l1 and l2 regularization.
sgdr = SGDRegressor(
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
    average=False
)

total_clicks = train['clicks'].sum()
k = 2                                                       # number of folds for validaton
cwsd = 0                                                    # placeholder for click-weighted squared distance
coefs = DataFrame(index=train_d.columns, columns=range(k))  # container for coefficient results from folds
n = 0
kf = KFold(n_splits=k, random_state=42, shuffle=True)
for train_index, test_index in kf.split(train_d):
    print n + 1,
    y_train, y_test = train[outcome_cols].iloc[train_index], train[outcome_cols].iloc[test_index]
    x_train, x_test = train_d.iloc[train_index, :], train_d.iloc[test_index, :]

    # do partial_fit to accomodate a large data set
    for i in xrange(0, x_train.shape[0], 100000):
        end = i + 100000 if (i + 100000) < x_train.shape[0] else x_train.shape[0]
        # print x_train.shape[0] - end
        sgdr.partial_fit(x_train.iloc[i:end, :], train['log_revenue_per_click'].iloc[i:end])

    coefs.loc[:, n] = sgdr.coef_
    # click weighted squared distance
    cwsd += ((y_test['revenue_per_click'] - exp(sgdr.predict(x_test) - 1)).pow(2) * y_test['clicks']).sum()
    n += 1

# divide click-weighted squared distance by total clicks to get average
acwsd = cwsd / float(total_clicks)
