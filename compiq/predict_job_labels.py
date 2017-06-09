import argparse
from json import loads
from re import sub
from pandas import Series
from numpy.random import choice
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.naive_bayes import MultinomialNB
from time import time

parser = argparse.ArgumentParser()
parser.add_argument("input")
args = parser.parse_args()


def xstr(s):
    return '' if s is None else str(s)

outfile = open("evaluation_output2.txt", "w")

industry_dict = {}
with open(args.input, "r") as f:
    for record in f.readlines():
        record = loads(record)
        industry = record['industry0']
        if industry in industry_dict.keys():
            industry_dict[industry] += 1
        else:
            industry_dict[industry] = 1

total_records = sum(industry_dict.values())
holdout_percent = 150000. / total_records
x_train = []
y_train = []
x_test = []
y_test = []
size = 0

tf_vectorizer = HashingVectorizer(
    analyzer='word',
    n_features=1048576,
    binary=False,
    norm='l1',
    non_negative=True,
    stop_words='english'
)

nb = MultinomialNB(
    alpha=1.0,
    fit_prior=True,
    class_prior=None
)

outfile.write('Total number of records: {}\n'.format(total_records))
outfile.write('Probability of record being chosen for training set: {:0.1f}\n\n'.format(holdout_percent))
outfile.write('==Training model now==\n')
outfile.write('Feature extraction settings: {}\n'.format(str(tf_vectorizer)))
outfile.write('Model settings: {}\n'.format(str(nb)))

t2 = time()
with open(args.input, "r") as f:
    for record in f.readlines():
        size += 1
        record = loads(record)
        indu = record['industry0']
        text = ' '.join([xstr(v) for k, v in record.items() if k in ('city', 'company', 'title', 'description')])
        text = sub(r'<.*?>', ' ', text)
        text = sub(r'[^A-Za-z0-9 ]', ' ', text)
        text = text.lower()

        for_test = choice([True, False], size=1, p=[holdout_percent, 1 - holdout_percent])[0]

        if for_test:
            x_test.append(text)
            y_test.append(indu)
        else:
            x_train.append(text)
            y_train.append(indu)

        if (size % 200000 == 0) or (size == total_records):
            t1 = time()
            outfile.write('Number of records evaluated: {}.\n'.format(size))
            outfile.write('    Time to pull and clean records: {} seconds.\n'.format(t1 - t2))
            tf = tf_vectorizer.fit_transform(x_train)
            nb.partial_fit(tf, y_train, classes=industry_dict.keys(), sample_weight=None)
            x_train = []
            y_train = []
            t2 = time()
            outfile.write('    Time to fit records: {} seconds.\n'.format(t2 - t1))

tf_test = tf_vectorizer.fit_transform(x_test)
probs = nb.predict_proba(tf_test)
probs_cat = probs.argmax(axis=1)
probs_s = Series([nb.classes_[i] for i in probs_cat])
actua_s = Series(y_test)

accuracy = (probs_s == actua_s).mean()


outfile.write('\nNumber of records randomly selected for test set: {}\n'.format(probs.shape[0]))
outfile.write('Number of features in test set: {}\n'.format(tf_test.sum(axis=0).__gt__(0.0).sum()))
outfile.write('Classification accuracy: {:0.1f}%\n'.format(accuracy * 100))
outfile.write('Number of unique categories: {}\n'.format(len(industry_dict)))
outfile.write('Number of unique predicted categories: {}\n\n'.format(probs_s.nunique()))
outfile.write('Test set category breakdown: \n{}\n\n'.format(actua_s.value_counts().to_string()))
outfile.write('Predicted category breakdown: \n{}\n\n'.format(probs_s.value_counts().to_string()))
outfile.close()


