from pandas import read_csv, to_datetime, get_dummies, DataFrame, Series, qcut
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from time import time


def cv_results(x, y, model, nfolds=10, nparts=10, verbose=False):
    """
    Fit and evaluate a classification model using k-fold cross-validation then summarize the accuracy of the
     classification by partitioning the predicted probabilities into quantiles and calculating the positives rate.

    :param x: a Pandas DataFrame containig all predictors
    :param y: a Pandas Series continaing the outcome values (0s and 1s)
    :param model: any classification model that has a `fit` and `predict_proba` class.
    :param nfolds: number of folds for cross-validation
    :param nparts: number of quantiles in which to partition the probabilities
    :param verbose: boolean indicating whether to track progress through folds

    :return: a Pandas DataFrame showing the percent 1s in each quantile.
    """

    results = DataFrame()
    n = 1
    for train_ind, test_ind in KFold(n_splits=nfolds).split(x):
        t1 = time()
        if verbose:
            print n,
        x_train = x.iloc[train_ind, :]
        y_train = y.iloc[train_ind]
        x_test = x.iloc[test_ind, :]
        y_test = y.iloc[test_ind].to_frame('actual')

        _ = model.fit(x_train, y_train)
        y_test['prob'] = rf.predict_proba(x_test)[:, 1]
        results = results.append(y_test)
        t2 = time()
        if verbose:
            print t2 - t1
        n += 1

    evaluation = results.groupby(qcut(results['quantile'], nparts, labels=False))['actual'].mean().\
        to_frame('renewed_pct').reset_index()
    return evaluation

# read in data and create outcome variable
data = read_csv('/Users/swheeler/Downloads/take-home-exercise-data.csv')
outcome = data['EndingState'].isin(['Renewed', 'Changed']).astype('int')

# convert date columns to datetimes
data['StartDate'] = to_datetime(data['StartDate'], format='%m/%d/%y')
data['EndDate'] = to_datetime(data['EndDate'], format='%m/%d/%y')
data['AccountCreatedDate'] = to_datetime(data['AccountCreatedDate'], format='%m/%d/%y')
data['AccountCreatedDateOrdinal'] = data['AccountCreatedDate'].apply(lambda d: d.toordinal())

drop_cols = ['SubscriberKey', 'AccountCreatedDate', 'StartDate', 'EndDate', 'EndingState']
category_cols = [
    'CoursePillar', 'CountryCode', 'Channel', 'Company', 'EmailDomain', 'ProductType', 'BeginningState', 'AutoRenewOn'
]

data_text = data[category_cols].copy()

# convert to string, fill in missing values, and remove categories represented
# by fewer than 10 rows, then one-hot encode
for col in category_cols:
    datas = data[col].astype('str').copy()
    datas = datas.fillna('Unknown')
    vc = datas.value_counts()
    if vc.le(10).sum() > 0:
        nullify = vc[vc.le(10)].index.values
        datas[datas.isin(nullify)] = None

    datad = get_dummies(datas, prefix=col, prefix_sep='__')
    data[datad.columns] = datad

# drop non-predictor columns and fill in missing values with means
data = data.drop(drop_cols + category_cols, axis=1)
data = data.fillna(data.mean())

rf = RandomForestClassifier(
    n_estimators=1000,
    oob_score=True,
    random_state=42,
    class_weight='balanced_subsample',
    verbose=False,
    n_jobs=-1
)

# model using all variables
evals = cv_results(x=data, y=outcome, model=rf, nfolds=10, nparts=20, verbose=True)

# get importances and keep only those variables at least one-tenth as important as the most important variable
_ = rf.fit(data, outcome)
importance = Series(rf.feature_importances_, index=data.columns).sort_values(ascending=False)
importance2 = importance / importance.max()
most_important = importance[importance2.gt(0.1)]

# model using only most important variables
evals2 = cv_results(x=data.loc[:, most_important.index], y=outcome, model=rf, nfolds=10, nparts=20, verbose=True)

# compare both models
eval_df = evals.merge(evals2, left_on='prob', right_on='prob', suffixes=['_full', '_imp'])
eval_df['renewed_pct_diff'] = eval_df['renewed_pct_full'] - eval_df['renewed_pct_imp']