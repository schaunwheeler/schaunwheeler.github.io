from selenium.webdriver import PhantomJS
from pandas import DataFrame
from time import time
from re import sub

urls = [
    'https://www.greatschools.org/north-carolina/cary/1906-Cary-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1889-Davis-Drive-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1891-Weatherstone-Elementary-School/',
    'https://www.greatschools.org/north-carolina/cary/1892-Adams-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1900-Briarcliff-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1916-Farmington-Woods-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1926-Kingswood-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1938-Northwoods-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/1975-Penny-Road-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/2797-Reedy-Creek-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/2875-Green-Hope-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/3254-Turner-Creek-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/3359-Carpenter-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/3364-Highcroft-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/7673-Mills-Park-Elementary/',
    'https://www.greatschools.org/north-carolina/cary/7876-Alston-Ridge-Elementary-School/',
    'http://www.greatschools.org/north-carolina/apex/1893-Apex-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/1884-West-Lake-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/1898-Baucom-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/1982-Olive-Chapel-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/2876-Middle-Creek-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/2877-Salem-Elementary/',
    'http://www.greatschools.org/north-carolina/apex/7674-Laurel-Park-Elementary/',
    'http://www.greatschools.org/north-carolina/morrisville/1981-Morrisville-Elementary/',
    'http://www.greatschools.org/north-carolina/morrisville/3360-Cedar-Fork-Elementary/',
]

indicators = ['EquityRaceEthnicity', 'EquityLowIncome', 'EquityDisabilities']
wd = PhantomJS()

output_cols = [
    'school', 'url', 'students_per_grade', 'teachers_to_student', 'counselors_to_student', 'reading', 'math',
    'science'
]
output_df = DataFrame(columns=output_cols)
output_ind = 0

for url in urls:
    t1 = time()
    wd.get(url)
    school_name = wd.title.split(' -')[0]
    print school_name,

    school_info = wd.find_elements_by_class_name('school-info__item')
    for s in school_info:
        inner_html = sub(r'<.*?>|\n', ' ', s.get_attribute('innerHTML'))
        inner_html = sub(r'\s+', ' ', inner_html).strip()
        if 'grades' in inner_html.lower():
            min_grade, max_grade = inner_html.split(' ')[-1].split('-')
            if min_grade.lower() == 'pk':
                min_grade = -1
            elif min_grade.lower() == 'k':
                min_grade = 0
            n_grades = int(max_grade) - int(min_grade) + 1
        elif 'students' in inner_html.lower():
            n_students = int(sub(r'[^0-9]', '', inner_html.split(' ')[-1]))
    students_per_grade = float(n_students) / float(n_grades)

    staff_info = wd.find_element_by_id('TeachersStaff').find_elements_by_class_name('rating-container__score-item')
    teacher_info = sub(r'<.*?>|\n', ' ', staff_info[0].get_attribute('innerHTML'))
    teacher_info = sub(r'\s+', ' ', teacher_info).strip()
    counsel_info = sub(r'<.*?>|\n', ' ', staff_info[1].get_attribute('innerHTML'))
    counsel_info = sub(r'\s+', ' ', counsel_info).strip()
    t_to_s_school = int(sub(r'.*?(\d+) :1.*', r'\1', teacher_info))
    c_to_s_school = int(sub(r'.*?(\d+) :1.*', r'\1', counsel_info))

    columns = ['indicator', 'subject', 'category', 'school_score', 'state_average']
    df = DataFrame(columns=columns)
    ind = 0

    for indicator in indicators:
        elem = wd.find_element_by_id(indicator)
        buttons = elem.find_elements_by_class_name('sub-nav-item')
        for b in buttons:
            subject = b.text
            b.click()
            graphs = elem.find_elements_by_class_name('bar-graph-display')
            graphs = [r for r in graphs if r.find_element_by_xpath('..').get_attribute('class') != 'grades']
            for r in graphs:
                r_list = r.text.split('\n')
                extra_value = any(['% of students' in r for r in r_list])
                if r_list[0] in ('White', 'All students', 'Not low-income'):
                    continue
                df.loc[ind, 'indicator'] = indicator.replace('Equity', '')
                df.loc[ind, 'subject'] = subject
                df.loc[ind, 'category'] = r_list[0]
                df.loc[ind, 'school_score'] = r_list[1] if not extra_value else r_list[2]
                df.loc[ind, 'state_average'] = r_list[2] if not extra_value else r_list[3]
                ind += 1

    df['school_score'] = df['school_score'].str.replace(r'[^0-9]', '').astype('int')
    df['state_average'] = df['state_average'].str.replace(r'[^0-9]', '').astype('int')
    df['test_diff'] = df['school_score'] - df['state_average']
    subject_diffs = df.groupby('subject')['test_diff'].mean()

    output_df.loc[output_ind, 'school'] = school_name
    output_df.loc[output_ind, 'url'] = url
    output_df.loc[output_ind, 'students_per_grade'] = students_per_grade
    output_df.loc[output_ind, 'teachers_to_student'] = t_to_s_school
    output_df.loc[output_ind, 'counselors_to_student'] = c_to_s_school
    if 'Reading' in subject_diffs.index:
        output_df.loc[output_ind, 'reading'] = subject_diffs['Reading']
    if 'Math' in subject_diffs.index:
        output_df.loc[output_ind, 'math'] = subject_diffs['Math']
    if 'Science' in subject_diffs.index:
        output_df.loc[output_ind, 'science'] = subject_diffs['Science']
    output_ind += 1
    print time() - t1

wd.close()
