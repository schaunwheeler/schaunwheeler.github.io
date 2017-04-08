"""Script for Oscar Health case study

This script contains a complete workflow for structuring a list of valid diagnosis labels, appling those labels
to claims data, and then selecting which claims to use to characterize a member's current health status.
"""

from pandas import read_csv, to_datetime
from os.path import join

CSV_SOURCE_DIR = '~/'
PRESCRIPTION_FILE = 'prescription_drugs.csv'
CLAIMS_FILE = 'claim_lines.csv'
CCS_FILE = 'ccs.csv'

claims_path = join(CSV_SOURCE_DIR, CLAIMS_FILE)
prescr_path = join(CSV_SOURCE_DIR, PRESCRIPTION_FILE)
ccs_path = join(CSV_SOURCE_DIR, CCS_FILE)


def structure_ccs_table(filepath, use_levels=4, replacements=None, new_label='Preventative or preliminary care'):
    """Choose a single string to characterize each diagnosis code

    This function reads in the CCS definition file, processes the fields, then chooses a single label for each
    diagnosis code from the processed fields.

    Args:
        filename (str): The complete path to the file containing the css data.
        use_levels (int): The number of CCS levels to use. A lower number will
            result in a smaller number of candiate labels.
        replacements (dict): A dictonary where keys indicate a column and the values
            are a list of strings that will be replaced with the value fed to `new_label`.
        new_label (str): The catch-all name to be used to replace any diagnosis codes that
            indicate something other than the diagnosis of definite medical condition.

    Returns:
        pandas.DataFrame: A processed table mapping diagnosis codes to the new labels.
        pandas.DataFrame: A simplified reference table where each label is represented only once.

    """

    desc_cols = ['ccs_1_desc', 'ccs_2_desc', 'ccs_3_desc', 'ccs_4_desc']

    ccs_df = read_csv(filepath)
    ccs_df['description'] = None
    ccs_df['level'] = 0

    # clean diag column
    ccs_df['diag'] = ccs_df['diag'].str.replace(r'[^0-9A-Za-z]', '')

    # nullify any labels that begin with "Other"
    for col in desc_cols[1:]:
        ccs_df.loc[ccs_df[col].str.startswith('Other').fillna(False), col] = None

    for col in reversed([x for x in desc_cols if int(x.split('_')[1]) in range(1, use_levels + 1)]):
        needs_to_be_filled = ccs_df['description'].isnull()
        ccs_df.loc[needs_to_be_filled, 'description'] = ccs_df.loc[needs_to_be_filled, col]
        ccs_df.loc[needs_to_be_filled, 'level'] = int(col.split('_')[1])

    if replacements is not None:
        for k, v, in replacements.items():
            ccs_df.loc[ccs_df[k].isin(v), 'description'] = new_label
            ccs_df.loc[ccs_df[k].isin(v), 'ccs_1_desc'] = new_label

    ref = ccs_df.drop_duplicates(subset=['description'])

    return ccs_df, ref


def structure_claims_data(filepath, ccs_lookup, gap_pct=0.95, diagnostics=False):
    """Map diagnosis labels to each claim and determine which labels are part of a patient's current health status.

    This function reads in the claims file and aligns it with the output of `structure_ccs_table`. The function
    determines which labels are still "active" by calculating how many days pass between claims for each first-level
    category label for each member. The function takes certain percentile of all of this gaps data and uses that as
    the window within which a label is considered part of a member's current health status.

    Args:
        filename (str): The complete path to the file containing the claims data.
        ccs_lookup (pandas.DataFrame): The first output of the `structure_ccs_table`, mapping diagnosis codes
            to lables.
        gap_pct (float): A number between 0.0 and 1.0 indicating what percentile of gap lengths should determine the
            window within which a label should be considered active.
        diagnostics (bool): If True, output the window length for each level-1 category label instead of outputting
            the labelled claims data.

    Returns:
        pandas.DataFrame: Either the labelled claims data or a diagnostic report.

    """

    claims = read_csv(filepath)

    # format claims dataset
    claims['description'] = claims['diag1'].map(ccs_lookup.set_index('diag')['description']).fillna('Unspecified')
    claims['ccs_1_desc'] = claims['diag1'].map(ccs_lookup.set_index('diag')['ccs_1_desc']).fillna('Unspecified')
    claims['date_svc'] = to_datetime(claims['date_svc']).apply(lambda v: v.date())

    reference_date = claims['date_svc'].max()
    # member_date_count = claims.groupby(['member_id', 'date_svc'])['record_id'].count().to_frame('count').reset_index()
    member_date_desc_count = claims.groupby(['member_id', 'date_svc', 'ccs_1_desc'])['record_id'].count().\
        to_frame('count').reset_index().sort_values(['member_id', 'ccs_1_desc'])

    group_cols = ['member_id', 'ccs_1_desc', 'description']
    member_df = claims.groupby(group_cols)['date_svc'].last().to_frame('latest_claim').reset_index()
    member_df['days_since_last_claim'] = (reference_date - member_df['latest_claim']).apply(lambda v: v.days)

    member_date_desc_count['gap_length'] = member_date_desc_count['date_svc'].diff()
    drop_inds = member_date_desc_count.groupby(['member_id', 'ccs_1_desc']).head(1).index
    member_date_desc_count = member_date_desc_count.drop(drop_inds)
    gap_limit = member_date_desc_count.groupby('ccs_1_desc')['gap_length'].quantile(gap_pct).apply(lambda v: v.days)

    if diagnostics:
        return gap_limit

    member_df['gap_limit'] = member_df['ccs_1_desc'].map(gap_limit.to_dict())
    member_df['is_recent'] = member_df['days_since_last_claim'].lt(member_df['gap_limit'])
    member_df['pct_within_gap'] = 1.0 - (member_df['days_since_last_claim'] / member_df['gap_limit'])

    return member_df


def get_member_status(df, label='No current diagnoses or symptoms', prelim_label='Preventative or preliminary care'):
    """Determine each member's current health status

    If a member has no claims within any active window, they are given a status of `label` If the only claims the member
    has within any active window falling under the `prelim_label` label, the member is given that label as  status.
    In all other cases, all `prelim_label` labels are dropped from the member's history under the assumption that those
    labels are incidental to the more specific diagnoses that make up the rest of the member's recent history.
    Remaining record are then further consolidated by finding all cases where a subcategory label is occurs in the same
    history as one of its parents. In those cases, the most granular label is used.

    Args:
        df (pandas.DataFrame): labelled claims data.
        label (str): The label to indicate a "healthy" current status.
        prelim_label (bool): The label indicating a claim has to do with treatment of symptoms rather than any
            definite underlying condition

    Returns:
        str: a list of pipe-separated labels characterizing member's current health status

    """

    desc_cols = ['ccs_1_desc', 'ccs_2_desc', 'ccs_3_desc', 'ccs_4_desc']
    if ~df['is_recent'].any():
        return label
    elif df.loc[df['is_recent'], 'description'].eq(prelim_label).all():
        return prelim_label
    else:
        not_just_symptoms = df['description'].ne(prelim_label)
        diag_list = df.loc[df['is_recent'] & not_just_symptoms, 'description'].sort_values().tolist()
        ccs_check = ccs_ref[ccs_ref['description'].isin(diag_list)]
        for l in sorted(ccs_check['level'].unique()):
            descs = ccs_check.loc[ccs_check['level'].eq(l), 'description']
            checks = ccs_check.loc[ccs_check['level'].gt(l), desc_cols].stack().tolist()
            for ind, d in descs.iteritems():
                if d in checks:
                    _ = diag_list.pop(diag_list.index(d))

        return ' | '.join(diag_list)

# each key must be a valid column name, and each value must be a list of strings to replace with the new label
replace_dict = {
    'ccs_1_desc': [
        'Symptoms; signs; and ill-defined conditions and factors influencing health status',
        'Undefined',
        'Residual codes; unclassified; all E codes'
    ],
    'ccs_2_desc': [
        'Immunizations and screening for infectious disease'
    ]
}

ccs, ccs_ref = structure_ccs_table(ccs_path, use_levels=1, replacements=replace_dict)
mem_df = structure_claims_data(claims_path, ccs, gap_pct=0.95, diagnostics=False)
member_status = mem_df.groupby('member_id').apply(get_member_status).to_frame('status_detail')
general_labels = ['No current diagnoses or symptoms', 'Preventative or preliminary care']
member_status['status_summary'] = member_status['status_detail'].\
    where(member_status['status_detail'].isin(general_labels))
single_status = member_status['status_detail'].str.count('[|]').eq(0)
member_status.loc[member_status['status_summary'].isnull() & single_status] = 'Single diagnoisis'
member_status['status_summary'] = member_status['status_summary'].fillna('Multiple diagnoses')

# prescr = read_csv(prescr_path)