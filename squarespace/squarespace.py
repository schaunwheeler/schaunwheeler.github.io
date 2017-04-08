"""Script for Squarespace data challenge

This script contains a complete workflow for generating a series of metrics and plots
to fit and evaluate a model of trial cohort conversion rates.
"""


from pandas import read_csv, to_datetime, get_dummies, DataFrame, concat
from numpy import NaN, arange
from sklearn.linear_model import SGDClassifier, LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold
from sklearn.metrics import f1_score
from bokeh.plotting import figure, output_file, show, gridplot

DATASET_FILEPATH = '/Users/swheeler/Downloads/Strategy_Data_Set.csv'


def prepare_data(filename, reference_date, index_cols=None, country_rate=0.001):
    """Clean and format the raw data to prepare for modeling.

    This function reads in a dataset from CSV, formats dates appropriately,
    and splits the raw data into a set of one-hot encoded user attributes, an
    outcome variable, and a date filter.

    Args:
        filename (str): The complete path to the file containing the data
            for the challenge.
        reference_date (str): The date to be used at as "completion date":
            the date at which the function assumes all users who are going
            to convert have converted. Parsed by `pandas.to_datetime`, which
            can accept a variety of formats. '%Y-%m-%d' works for certain.
        index_cols (list): strings indicating columns names that will make
            up the index of all DataFrames and Series used in the analysis.
            Adding to the index will not drop the columns from the DataFrame.
        country_rate (float): a percentage to determine which countries will
            be grouped into an "other" category. Any countries representing
            less than `country_rate` percent of the total countries will
            be grouped together.

    Returns:
        pandas.DataFrame: the user attributes that make up most of the predictors
            for the model.
        pandas.Series: a Series of 1s and 0s, where 1 means a user converted
        pandas.Series: a Series of trial lengths, used to filter the predictor
            dataset and outcome variable.

    """

    final_date = to_datetime(reference_date).date()
    df = read_csv(filename).drop_duplicates()

    # convert date columns to datetime
    df['trial_date'] = to_datetime(df['trial_date']).apply(lambda v: v.date())
    df['subscription_date'] = to_datetime(df['subscription_date']).apply(lambda v: v.date())

    if index_cols is not None:
        df = df.set_index(index_cols, drop=False)

    # consolidate countries that make up less than `country_rate` of total countries into "other" category
    df['trial_country_lumped'] = df['trial_country'].copy()
    country_counts = df['trial_country'].value_counts(normalize=True)
    country_counts = country_counts[country_counts.ge(country_rate)]
    df.loc[~df['trial_country_lumped'].isin(country_counts.index), 'trial_country_lumped'] = 'Other'

    # one-hot encode country and day of week
    trial_country_df = get_dummies(df['trial_country_lumped'], prefix='trial_country', prefix_sep='__')
    day_of_week_df = get_dummies(df['day_of_week'], prefix='day_of_week', prefix_sep='__')

    # calculate trial length and conversion
    df['trial_length'] = (df['subscription_date'] - df['trial_date'])
    df.loc[df['trial_length'].isnull(), 'trial_length'] = final_date - df.loc[df['trial_length'].isnull(), 'trial_date']
    df['trial_length'] = df['trial_length'].apply(lambda v: v.days)
    df['converted'] = df['subscription_date'].notnull().astype('int')

    data = day_of_week_df.join(trial_country_df)

    return data, df['converted'], df['trial_length']


def estimate_cohort_rates(outcome, attributes, data_filter, regressor, horizon=28, folds=3, verbose=False):
    """Fit a regressor to predict cohort conversion rates.

    This function takes the outputs of `prepare_data`, constructs a data set
    for each time horizon, and evaluates the model through k-fold validation.

    Args:
        outcome (pandas.Series): The indicator Series from `prepare_data` indicating
            whether a user converted or not.
        attributes (pandas.DataFrame): The one-hot encoded user attributes output
            from `prepare_data`.
        data_filter (pandas.Series): The Series of trial lengths output from
            `prepare_data`, used to filter the rest of the data for different
            time horizons.
        regressor: Any class that has a `fit` and `predict` method.
        horizon (int): the number of days out to fit the model. A separate model
            will be fit and evaluated for range(0, horizon + 1).
        folds (float): The number of folds for which to do k-fold cross validation.
        verbose (bool): A flag indicating whether to print the time horizon for each
            fold. Used to keep track of function progress.

    Returns:
        pandas.DataFrame: A DataFrame where each row indicates a cohort (represented by
            date) and each column indicates a fold and time horizon (so total number of
            columns will equal (`folds` * `horizon`) + 1, with the extra column showing
            total number of users in each cohort. Values in every column except that extra
            one will be the absolute difference between the predited rate and the actual
            rate.

    """

    # create a dataframe from all data to ensure every date is represented in each fold.
    cohorts = outcome.groupby(level=['trial_date']).count().to_frame(('cohort_size', 0))

    # k-fold cross validation
    k = 1
    kf = KFold(n_splits=folds, random_state=42, shuffle=True)
    for train_index, test_index in kf.split(outcome):
        y_train, y_test = outcome.iloc[train_index], outcome.iloc[test_index]
        y_train_cohort_size = y_train.groupby(level=['trial_date']).count()
        y_test_cohort_size = y_test.groupby(level=['trial_date']).count()
        y_train_final_rate = y_train.groupby(level=['trial_date']).mean()
        y_test_final_rate = y_test.groupby(level=['trial_date']).mean()
        attributes_train = attributes.iloc[train_index].groupby(level=['trial_date']).mean()
        attributes_test = attributes.iloc[test_index].groupby(level=['trial_date']).mean()

        # one loop for each time horizon
        for l in range(0, horizon + 1):
            if verbose:
                print l,
            y_train_present_count = y_train.loc[data_filter.iloc[train_index].lt(l)].groupby(level=['trial_date']).sum()
            y_test_present_count = y_test.loc[data_filter.iloc[test_index].lt(l)].groupby(level=['trial_date']).sum()
            y_train_present_rate = y_train_present_count / y_train_cohort_size
            y_test_present_rate = y_test_present_count / y_test_cohort_size

            X_train = y_train_cohort_size.to_frame('size').\
                join(y_train_present_rate.to_frame('present'), how='outer').\
                join(attributes_train, how='outer').\
                reindex(cohorts.index).\
                fillna(0.0)

            X_test = y_test_cohort_size.to_frame('size').\
                join(y_test_present_rate.to_frame('present'), how='outer'). \
                join(attributes_test, how='outer'). \
                reindex(cohorts.index).\
                fillna(0.0)

            _ = regressor.fit(X_train, y_train_final_rate)
            abs_diff = (y_test_final_rate - regressor.predict(X_test)).abs()
            cohorts[('fold_' + str(k), l)] = abs_diff

        if verbose:
            print ''
        k += 1

    return cohorts


def plot_errors(filepath, pred_errors, baseline_errors, show_plot=True):
    """Create a plot to evaluate the model against the baseline.

    This function uses the Bokeh plotting library to create an html document
    comparing model performance to baseline for each cohort.

    Args:
        filepath (string): The file and path of the html document.
        pred_errors (pandas.DataFrame): The model outputs from `estimate_cohort_rates`.
        baseline_errors (pandas.Series): The absolute difference between the actual
            conversion rates for each cohort and a global conversionrate (across all
            cohorts).
        show_plot (bool): If True, open the html document in the browser. If False,
            just output the Bokeh plot object.

    Returns:
        bokeh.plotting.figure.Figure: If show_plot is False, return the plot object.
        Otherwise, return nothing.

    """

    if show_plot:
        output_file(filepath)

    # create one plot for each cohort group (defined by trial date)
    grid_list = []
    for trial_date in pred_errors.index:
        baseline = baseline_errors[trial_date]
        days = pred_errors['fold_1'].columns.tolist()
        baselines = [baseline for d in days]

        plot = figure(
            plot_width=250,
            plot_height=200,
            x_axis_label='day from ' + trial_date.strftime('%Y-%m-%d'),
            y_axis_label='error',
            y_range=[0.0, 0.075],
            toolbar_location=None
        )

        # plot one gray line for each fold of the model validation
        for fold in [l for l in pred_errors.columns.get_level_values(0).unique() if 'fold' in l]:
            plot.line(days, pred_errors.loc[trial_date, fold].tolist(), line_width=1, line_color='grey')

        # add a black line for the baseline
        plot.line(days, baselines, line_width=1, line_color='black')
        grid_list.append(plot)

    gp = gridplot(grid_list, ncols=3, toolbar_location=None)

    if show_plot:
        show(gp)
    else:
        return gp


# process the data for modeling
p, o, d = prepare_data(
    DATASET_FILEPATH,
    reference_date='2013-10-15',
    index_cols=['id', 'trial_date'],
    country_rate=0.01
)

# instantiate a regressor
rf = RandomForestRegressor(oob_score=True, n_estimators=100)


global_rate = o.mean()                                  # single rate across all cohorts
cohort_rates = o.groupby(level=['trial_date']).mean()   # rate for each cohort
baseline_error = (cohort_rates - global_rate).abs()     # absolute difference between global and cohort rates

cohort_rate_description = cohort_rates.describe()       # descriptive statistics for cohort rates

# percent of users who converted at different time horizons
time_to_conversion = d[o.eq(1)].value_counts(normalize=True).sort_index().cumsum()

# fit the model and create error estimates
predictions = estimate_cohort_rates(o, p, d, regressor=rf, horizon=28,  folds=10, verbose=True)

# correlation between average error and time horizon
kendall_avg = predictions.iloc[:, 1:].stack(0).mean().reset_index().corr(method='kendall').iloc[0, 1]

# correlation between each fold/cohort and time horizon
kendall_all = predictions.iloc[:, 1:].stack(0).transpose().reset_index().\
    corr(method='kendall').loc[:, 'index'].drop(['index'])

# matrix of boolean values indicating whether the model beat the baseline
model_beats_baseline = predictions.drop(['cohort_size'], axis=1).sub(baseline_error, axis=0).lt(0)

# total percentage of times the model beat the baseline
model_beats_baseline_pct = model_beats_baseline.stack().stack().mean()

# correlation between average percentage of time model beats baseline and time horizon
kendall_avg_folds_beat_with_day = model_beats_baseline.stack(0).mean().reset_index().corr(method='kendall').iloc[0, 1]

# correlation between average model error and baseline error per cohort
kendall_baseline_error_with_avg_folds_beat = model_beats_baseline.mean(axis=1).corr(baseline_error, method='kendall')

# create the diagonostic plot
plot_errors(
    filepath="/Users/swheeler/Desktop/squarespace.html",
    pred_errors=predictions,
    baseline_errors=baseline_error,
    show_plot=True
)

