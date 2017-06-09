import requests
from pandas import DataFrame, Series, to_datetime, date_range, Timestamp, to_timedelta
from time import sleep
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation

from math import pi
import bokeh.palettes as bp
from bokeh.document import Document
from bokeh.embed import file_html
from bokeh.resources import INLINE
from bokeh.util.browser import view
from bokeh.io import curstate
from bokeh.layouts import Column
from bokeh.models.widgets.markups import Div
from bokeh.models import Plot, ColumnDataSource
from bokeh.models.glyphs import Rect
from bokeh.models.axes import LinearAxis, CategoricalAxis
from bokeh.models.ranges import FactorRange, DataRange1d
from bokeh.models.widgets.tables import DataTable, TableColumn

API_KEY = '<INSERT VALID API KEY HERE>'
ARTICLE_URI = 'http://api.nytimes.com/svc/search/v2/articlesearch.json'
SHARED_URI = 'http://api.nytimes.com/svc/mostpopular/v2/mostshared/{section}/30.json'
EMAILED_URI = 'http://api.nytimes.com/svc/mostpopular/v2/mostemailed/{section}/30.json'
VIEWED_URI = 'http://api.nytimes.com/svc/mostpopular/v2/mostviewed/{section}/30.json'

curstate().autoadd = False

# set up metadata for API query
today = Timestamp.today().strftime('%Y%m%d')
today_minus_thirty = (Timestamp.today().date() - to_timedelta('30 days')).strftime('%Y%m%d')
page = 0

query_params = {
    'q': '"climate change"',
    'begin_date': today_minus_thirty,
    'end_date': today,
    'sort': 'newest',
    'hl': True,
    'page': page,
    'api-key': API_KEY
}

# pull all data for specified time period
# daily_limits = {k:v for k,v in request.headers.items() if k.startswith('X-RateLimit')}
request = requests.get(ARTICLE_URI, params=query_params)
data = request.json()

hit = 0
total_hits = data['response']['meta']['hits']
total_pages = total_hits / 10
colnames = data['response']['docs'][0].keys()
output_df = DataFrame(index=range(total_hits), columns=colnames)

while page <= total_pages:
    print total_pages - page,
    for doc in data['response']['docs']:
        output_df.loc[hit, :] = Series(doc)
        hit += 1
    page += 1
    sleep(1)
    query_params['page'] = page
    request = requests.get(ARTICLE_URI, params=query_params)
    data = request.json()

print ''

article_filter = output_df['document_type'].eq('article')
output_df = output_df[article_filter]

# keyword counts
number_keywords = output_df['keywords'].apply(lambda x: len(x))
keyword_count = output_df['keywords'].\
    apply(lambda l: [[v for k, v in d.items() if k == 'value'].pop() for d in l]).\
    apply(Series).\
    stack().\
    value_counts()

keyword_freq = keyword_count.value_counts()
kf_df = keyword_freq.sort_index().to_frame('height').reset_index().rename(columns={'index': 'width_midpoint'})
kf_df['height_midpoint'] = kf_df['height'].div(2.0)

kc_df = keyword_count[keyword_count.gt(2)].to_frame('height').reset_index().rename(columns={'index': 'x_labels'})
kc_df['height_midpoint'] = kc_df['height'].div(2.0)

# section counts
section_count = output_df.section_name.value_counts()
top_section, top_percent = (section_count / section_count.sum()).head(1).iteritems().next()
sc_df = section_count.to_frame('height').reset_index().rename(columns={'index': 'x_labels'})
sc_df['height_midpoint'] = sc_df['height'].div(2.0)

idx = date_range(today_minus_thirty, today)
daily_count = to_datetime(output_df.pub_date).\
    apply(lambda v: v.date()).\
    value_counts().\
    sort_index().\
    reindex(idx, fill_value=0)

dc_df = daily_count.to_frame('height').reset_index().rename(columns={'index': 'x_labels'})
dc_df['height_midpoint'] = dc_df['height'].div(2.0)
dc_df['bar_color'] = dc_df['x_labels'].apply(lambda d: 'black' if d.dayofweek == 6 else 'gray')
dc_df['week'] = dc_df['x_labels'].apply(lambda d: d.week)
dc_df['x_labels'] = dc_df['x_labels'].apply(lambda d: d.strftime('%Y-%m-%d'))
weekly_highpoints = dc_df.set_index('x_labels').groupby('week')['height'].\
    apply(lambda s: s.argmax()).to_frame('pub_date')
# article popularity
popularity_df = DataFrame()
section_counts = section_count.shape[0]
for section in section_count.index:
    print section_counts,
    shared = requests.get(SHARED_URI.format(section=section), params={'api-key': API_KEY})
    emailed = requests.get(EMAILED_URI.format(section=section), params={'api-key': API_KEY})
    viewed = requests.get(VIEWED_URI.format(section=section), params={'api-key': API_KEY})

    shared_df = DataFrame(shared.json()['results']).rename(columns={'total_shares': 'article_rank'})
    emailed_df = DataFrame(emailed.json()['results'])
    viewed_df = DataFrame(viewed.json()['results']).rename(columns={'views': 'article_rank'})

    emailed_df['article_rank'] = range(1, emailed_df.shape[0] + 1)
    shared_df['count_type'] = 'shares'
    emailed_df['count_type'] = 'emails'
    viewed_df['count_type'] = 'views'

    popularity_df = popularity_df.\
        append(shared_df, ignore_index=True).\
        append(emailed_df, ignore_index=True).\
        append(viewed_df, ignore_index=True)
    section_counts -= 1

output_df['web_url'] = output_df['web_url'].str.replace(r'^https?://', '')
popularity_df['url'] = popularity_df['url'].str.replace(r'^https?://', '')

is_popular_filter = output_df['web_url'].isin(popularity_df['url'])
output_popular_df = output_df[is_popular_filter]

popular_flagged_filter = popularity_df['url'].isin(output_popular_df['web_url'])
popularity = popularity_df[popular_flagged_filter].\
    set_index(['url', 'count_type'])['article_rank'].\
    unstack('count_type')
pop_order = popularity.fillna(21).mean(axis=1).sort_values()
popularity = popularity.fillna('--').rename(columns = lambda c: c + ' rank').reset_index()
popularity = popularity.merge(output_popular_df, left_on='url', right_on='web_url')
popularity = popularity.set_index('url').loc[pop_order.index].reset_index()
popularity['rank'] = range(1, popularity.shape[0] + 1)
col_order = ['rank', 'section_name', 'pub_date', 'headline', 'emails rank', 'shares rank', 'views rank']
popularity = popularity[col_order]
popularity['headline'] = popularity['headline'].apply(lambda v: v['main'])
popularity['pub_date'] = popularity['pub_date'].apply(lambda v: to_datetime(v).strftime('%Y-%m-%d'))

# topic modeling
output_df['headline_text'] = output_df['headline'].apply(lambda d: ' '.join(set([v for v in d.values() if len(v) > 0])))
output_df['text'] = output_df[['headline_text', 'snippet', 'lead_paragraph']].\
    fillna('').\
    apply(lambda r: ' '.join(r), axis=1)
output_df['text'] = output_df['text'].\
    str.replace(r'[<][/]?strong[>]', '').\
    str.replace(r'\b[0-9]+\b', '')

tf_vectorizer = CountVectorizer(
    max_df=0.95,
    min_df=2,
    max_features=1000,
    stop_words='english'
)

tf = tf_vectorizer.fit_transform(output_df['text'].tolist())

lda = LatentDirichletAllocation(
    n_topics=10,
    max_iter=5,
    learning_method='online',
    learning_offset=50.,
    random_state=0
).fit(tf)

lda_transform = lda.transform(tf)
tf_feature_names = tf_vectorizer.get_feature_names()
output_df['topic_number'] = lda_transform.argmax(axis=1) + 1
output_df['pub_date'] = to_datetime(output_df['pub_date']).apply(lambda d: d.strftime('%Y-%m-%d'))

tm_df = output_df.groupby(['pub_date', 'topic_number'])['_id'].count().to_frame('counts').reset_index()
color_dict = {k+1: v for k, v in dict(enumerate(bp.Blues9)).items()}
tm_df['color_mapping'] = tm_df['counts'].map(color_dict)
tm_df = tm_df.sort_values('counts')
tm_df['color_mapping'] = tm_df['color_mapping'].fillna(method='ffill')

components = DataFrame(lda.components_).div(DataFrame(lda.components_).sum(axis=1), axis=0).transpose()
components.index = tf_feature_names

topics_df = DataFrame(columns=['topic_number', 'feature_name', 'feature_score'], index=range(10 * 20))
ind = 0
for topic_number, topic in enumerate(lda.components_):
    for i in reversed(topic.argsort()[-20:]):
        topics_df.loc[ind, 'topic_number'] = topic_number + 1
        topics_df.loc[ind, 'feature_name'] = tf_feature_names[i]
        topics_df.loc[ind, 'feature_score'] = topic[i]
        ind += 1


# create the web page
axis_defaults = dict(
    axis_label_text_font_size='10pt',
    minor_tick_line_alpha=0.0,
    axis_line_alpha=0.0,
    major_tick_line_alpha=0.0,
    major_label_text_color='grey',
    major_label_text_font_size='9pt'
)

bk_page = Column(sizing_mode='scale_both')

bk_section0_text = '''
<h1>
New York Times API Exploration
</h1>

<p>
This page explores the topic of climate change as it appeared in The New York Times from <strong>{start_date}</strong>
to <strong>{end_date}</strong>. We used the New York Times APIs to search for the exact phrase "climate change",
including all types of material (news, op-eds, briefings, editorials, letters, obituaries, reviews, and corrections)
from all sources (The New York Times, International New York Times, AP, and Reuters).
</p>

<p>
First, we'll explore some of the context around the climate change coverage over the last month. Then we'll look at
measures of article reach/influence. Finally, we'll look at a topic structure for the coverage derived directly from the
text as opposed to the keyword structure provided by the New York Times itself.
</p>
'''.format(start_date=today_minus_thirty, end_date=today)

bk_section1_text1 = '''
<hr>
<h2>
Context
</h2>

<p>
The graphs below show counts of articles by keyword, section, and day.
</p>

<h3>
Keyword
</h3>

<p>
The first plot shows the number of keywords (the height of each bar) were used a given number of times (the horizontal
location of each bar across the plot).
'''

bk_section1_text2 = '''
As the plot shows, the grand majority of keywords ({kw_0count}) were used only one time, while {kw_maxcount} keyword
was used {kw_max} times. It's also worth noting that only {0:.2f} percent of {1} documents even had keywords.
</p>

<p>
The second plot shows the frequency of all keywords that occured more than twice.
</p>
'''.format(
    number_keywords.gt(0).mean(),
    output_df.shape[0],
    kw_0count=keyword_freq[1],
    kw_maxcount=keyword_freq[keyword_freq.index.max()],
    kw_max=keyword_freq.index.max()
)

bk_section1_text3 = '''
<h3>
Section
</h3>

<p>
The plot below shows how many articles appears in each section. The {top_section} alone accounted for {0:.2f} percent
of the total articles.
</p>
'''.format(top_percent, top_section=top_section)

bk_section1_text4 = '''
<h3>
Date
</h3>

<p>
The plot below shows shows the distribution of articles across the entire thirty-day period. Sundays are represented
by black bars in order to show weekly cycles.
</p>
'''

bk_section2_text1 = '''
<hr>
<h2>
Influence
</h2>

<p>
The only means of estimating the reach or influence of an article, using the New York Times APIs alone, is to pull the
"top 20" list for article shares, emails, and views for the most recent 30 days. The API doesn't list how many shares,
emails, or views each article had - only what order it was in the top 20. We pulled the top 20 for each section of the
New York Times and matched the URLs of those articles from the full list of articles on climate change. The results are
in the table below. Of the {total_articles} articles on climate change during the period we examined, only {total_pop_articles}
made it into the top 20 for emails, shares, or views for its given section.
</p>
'''.format(total_articles=output_df.shape[0], total_pop_articles=popularity.shape[0])

bk_section3_text1 = '''
<hr>
<h2>
Topic Structure
</h2>

<p>
All of the above gives us a sense of the landscape of the climate change discussion in the New York Times, but it gives
us little sense of the dynamics that influence that landscape. For example, more articles tended to be published on
climate change in the middle of each week. That is probably due in part to the news cycle as well as the political cycle
(the government tends to make fewer announcements and pass less legislation on weekends). That cycle itself tells us
little about what topics drove the increase in articles. We can't use keywords to understand that because the majority
of articles aren't tagged with keywords, and many of the keywords appear only once in the entire corpus of articles.
</p>

<p>In order to understand common themes among the climate change articles, we performed a "topic modeling" using a
method called Latent Diriclet Allocation, or LDA. LDA views documents such as news articles as being a mixture of
multiple topics. These topics are characterized by specific words. Therefore, if we take a matrix where each row
represents a document and each column represents a word, LDA finds which words tend to occur together, which allows us
to identify the content of each topic as well as understand which documents cover which topics.
</p>

<p>
For our analysis, we took the 1000 most common words from the corpus (after removing commonly-used, low-information
words such as "and" and "the") and identifed the 10 most prominent topics. We then assigned each article in the corpus
to the topic with with it was most closely aligned. Because of the limitations of the API, we were only able to include
the headline, lead paragraph of the article, and the snippet of text in which the phrase "climate change" occured.
</p>

<p>
For convenience sake, we've defined each topic in terms of the 20 words most strongly associated:
</p>
'''

bk_section3_text2 = '<ol>' + ' '.join(
    topics_df.groupby('topic_number')['feature_name'].
        apply(lambda s: '<li>' + ', '.join(s.tolist()) + '</li>').tolist()
    ) + '</ol>'

bk_section3_text3 = '''
<p>
While the topics are not immediately understandable, a brief perusal of each list gives a general sense of the topic.
We can then plot the frequency of each topic for each day. In the graph below, darker blue indicates more articles
published. The red borders indicate the high point of total article count for each calendar week.
</p>
'''

# must be done by hand
bk_section3_text4 = '''
<p>
As the graph shows, topics 6, 7, and 8 run almost constantly through the time period in question, although topic 6 is
a smaller element of the total conversation. Topics 1 and 2, on the other hand, are frequently important elements on the
weekly highpoints.
</p>
<hr>
'''


# keyword frequency plot
plot_kf = Plot(
    x_range=DataRange1d(),
    y_range=DataRange1d(start=0),
    plot_height=300,
    plot_width=600,
    toolbar_location=None,
    logo=None
)
glyph_kf = Rect(
    x='width_midpoint',
    y='height_midpoint',
    width=1,
    height='height'
)
plot_kf.add_glyph(ColumnDataSource(kf_df), glyph_kf)
plot_kf.add_layout(LinearAxis(axis_label='Number of keywords', **axis_defaults), 'left')
plot_kf.add_layout(LinearAxis(axis_label='Number of times used', **axis_defaults), 'below')

# keyword count plot
plot_kc = Plot(
    x_range=FactorRange(factors=kc_df['x_labels'].tolist()),
    y_range=DataRange1d(start=0),
    plot_height=600,
    plot_width=600,
    toolbar_location=None,
    logo=None
)
glyph_kc = Rect(
    x='x_labels',
    y='height_midpoint',
    width=1,
    height='height'
)
plot_kc.add_glyph(ColumnDataSource(kc_df), glyph_kc)
plot_kc.add_layout(LinearAxis(axis_label='Number of uses', **axis_defaults), 'left')
plot_kc.add_layout(CategoricalAxis(axis_label='Keyword', major_label_orientation=pi/2, **axis_defaults), 'below')

# section count plot
plot_sc = Plot(
    x_range=FactorRange(factors=sc_df['x_labels'].tolist()),
    y_range=DataRange1d(start=0),
    plot_height=600,
    plot_width=600,
    toolbar_location=None,
    logo=None
)
glyph_sc = Rect(
    x='x_labels',
    y='height_midpoint',
    width=1,
    height='height'
)
plot_sc.add_glyph(ColumnDataSource(sc_df), glyph_sc)
plot_sc.add_layout(LinearAxis(axis_label='Number of articles', **axis_defaults), 'left')
plot_sc.add_layout(CategoricalAxis(axis_label='Section', major_label_orientation=pi/2, **axis_defaults), 'below')

# daily count plot
plot_dc = Plot(
    x_range=FactorRange(factors=dc_df['x_labels'].tolist()),
    y_range=DataRange1d(start=0),
    plot_height=600,
    plot_width=600,
    toolbar_location=None,
    logo=None
)
glyph_dc = Rect(
    x='x_labels',
    y='height_midpoint',
    width=1,
    height='height',
    fill_color='bar_color'
)
plot_dc.add_glyph(ColumnDataSource(dc_df), glyph_dc)
plot_dc.add_layout(LinearAxis(axis_label='Number of articles', **axis_defaults), 'left')
plot_dc.add_layout(CategoricalAxis(axis_label='Date', major_label_orientation=pi/2, **axis_defaults), 'below')

# most popular table
pop_dt = DataTable(row_headers=False, selectable=False, sortable=True, sizing_mode='scale_both')
pop_dt.columns = [
    TableColumn(field='rank', title='Rank', sortable=True, width=50),
    TableColumn(field='section_name', title='Section', sortable=True, width=150),
    TableColumn(field='pub_date', title='Date', sortable=True, width=150),
    TableColumn(field='headline', title='Headline', sortable=True),
    TableColumn(field='emails rank', title='Email rank', sortable=True, width=125),
    TableColumn(field='shares rank', title='Share rank', sortable=True, width=125),
    TableColumn(field='views rank', title='View rank', sortable=True, width=125),
]
pop_dt.source = ColumnDataSource(popularity)

# topic-date heatmap
plot_tm = Plot(
    x_range=FactorRange(factors=[x.strftime('%Y-%m-%d') for x in idx.tolist()]),
    y_range=FactorRange(factors=tm_df['topic_number'].drop_duplicates().sort_values().tolist()),
    plot_height=300,
    plot_width=600,
    toolbar_location=None,
    logo=None
)
glyph_tm = Rect(
    x='pub_date',
    y='topic_number',
    width=1,
    height=1,
    fill_color='color_mapping',
    line_color=None
)
plot_tm.add_glyph(ColumnDataSource(tm_df), glyph_tm)

glyph_tm_weekly = Rect(
    x='pub_date',
    y=5.5,
    width=1,
    height=10,
    fill_color=None,
    line_color='red'
)
plot_tm.add_glyph(ColumnDataSource(weekly_highpoints), glyph_tm_weekly)

plot_tm.add_layout(CategoricalAxis(axis_label='Topic', **axis_defaults), 'left')
plot_tm.add_layout(CategoricalAxis(axis_label='Date', major_label_orientation=pi/2, **axis_defaults), 'below')

bk_page.children = [
    Div(text=bk_section0_text, sizing_mode='scale_both'),
    Div(text=bk_section1_text1, sizing_mode='scale_both'),
    plot_kf,
    Div(text=bk_section1_text2, sizing_mode='scale_both'),
    plot_kc,
    Div(text=bk_section1_text3, sizing_mode='scale_both'),
    plot_sc,
    Div(text=bk_section1_text4, sizing_mode='scale_both'),
    plot_dc,
    Div(text=bk_section2_text1, sizing_mode='scale_both'),
    pop_dt,
    Div(text=bk_section3_text1, sizing_mode='scale_both'),
    Div(text=bk_section3_text2, sizing_mode='scale_both'),
    Div(text=bk_section3_text3, sizing_mode='scale_both'),
    plot_tm,
    Div(text=bk_section3_text4, sizing_mode='scale_both'),
]

doc = Document()
doc.add_root(bk_page)
doc.validate()
filename = 'index.html'
with open(filename, "w") as f:
    f.write(file_html(doc, INLINE, "New York Times - Climate Change"))
view(filename)
