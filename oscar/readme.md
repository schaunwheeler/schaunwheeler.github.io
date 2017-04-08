**Oscar Health Case Study**

Prepared by Schaun Wheeler, 8 April 2017

**Overview**

The first task was to define the health status of all 100,000 members in the given dataset. I did this through the following process:

1. Consolidate the four levels of the CCS hierarchy into a single set of labels

2. Determine a window within which each label would remain "active" - meaning the label still could be thought to convey something meaningful about the current state of a member’s health.

3. Compile labels for each member within each window in a way that conveys as much information as possible with as few labels as possible

The second task was to describe how I would go about predicting one or more the health statuses based on prescription drug data. 

**Consolidate labels**

At each level of the category ontology after ccs_1, for most parent categories, there exists an 'other' category that gives no new information beyond the fact of the parent category. For example, one of the level-2 categories under the "Congenital anomalies" parent category is “Other congenital anomalies” Those labels can be considered null.

This is the number of null labels in each category before and after nullifying the 'other' labels:

<table>
  <tr>
    <td>CCS data field</td>
    <td>% null with "other" labels</td>
    <td>% null without “other” labels</td>
  </tr>
  <tr>
    <td>ccs_2_desc</td>
    <td>1.8%</td>
    <td>16.8%</td>
  </tr>
  <tr>
    <td>ccs_3_desc</td>
    <td>24.8%</td>
    <td>51.0%</td>
  </tr>
  <tr>
    <td>ccs_4_desc</td>
    <td>78.8%</td>
    <td>88.9%</td>
  </tr>
</table>


After nullifying "other" labels, we can combine all of the ccs descriptions into a single field by starting with the level-4 labels, filling in missing values with level-3 labels, then filling in remaining missing values with level-2 labels, and then filling in the last missing values with level-1 labels.

We can take one more consolidating step by recognizing that certain labels have less to do with health status and more to do with health maintenance activities such as routine visits ('Medical examination/evaluation', 'Administrative/social admission'), preventative care ('Other screening for suspected conditions', 'Immunizations and screening for infectious disease'), or symptoms not necessarily indicative of a more permanent health condition ('Abdominal pain', 'Fever').

These records, as well as those that have no diagnosis code, can be consolidated into a general 'Preventative or preliminary care' label, which actually accounts for over 20% of all the claims in the dataset.

Of the 100000 members in the data set, over 75,000 have at least one claim falling into this preventative or preliminary care category, yet over 97,000 also claim not falling into this category. This suggests that, for the majority of claimants, this category often constitutes background noise for other, underlying conditions.

Applying these substitutions ultimately results in 527 distinct labels if all four levels of the CCS hierarchy are used, 385 labels if only the first three levels are used, 129 if the first two are used, and 17 labels if only the top level is used. For the discussion below, I used all four level of the hierarchy, and therefore deal with 527 distinct label possibilities per claim.

**Define an active window**

Once we have our list of valid labels, we need to decide which claims represent current health status rather than simply being a part of the a member’s medical history. Do do this, I calculated the number of days between recurrences of level-1 CCS labels. For each of those labels, 95% of all recurrences happened within the window specified below.

<table>
  <tr>
    <td>Level-1 Label</td>
    <td>Window</td>
  </tr>
  <tr>
    <td>Diseases of the skin and subcutaneous tissue</td>
    <td>392</td>
  </tr>
  <tr>
    <td>Preventative or preliminary care</td>
    <td>371</td>
  </tr>
  <tr>
    <td>Infectious and parasitic diseases</td>
    <td>363</td>
  </tr>
  <tr>
    <td>Diseases of the respiratory system</td>
    <td>345</td>
  </tr>
  <tr>
    <td>Diseases of the circulatory system</td>
    <td>344</td>
  </tr>
  <tr>
    <td>Diseases of the nervous system and sense organs</td>
    <td>339</td>
  </tr>
  <tr>
    <td>Diseases of the digestive system</td>
    <td>335</td>
  </tr>
  <tr>
    <td>Diseases of the genitourinary system</td>
    <td>329</td>
  </tr>
  <tr>
    <td>Endocrine; nutritional; and metabolic diseases and immunity disorders</td>
    <td>303</td>
  </tr>
  <tr>
    <td>Neoplasms</td>
    <td>249</td>
  </tr>
  <tr>
    <td>Diseases of the blood and blood-forming organs</td>
    <td>226</td>
  </tr>
  <tr>
    <td>Injury and poisoning</td>
    <td>220</td>
  </tr>
  <tr>
    <td>Unspecified</td>
    <td>192</td>
  </tr>
  <tr>
    <td>Congenital anomalies</td>
    <td>154</td>
  </tr>
  <tr>
    <td>Diseases of the musculoskeletal system and connective tissue</td>
    <td>143</td>
  </tr>
  <tr>
    <td>Complications of pregnancy; childbirth; and the puerperium</td>
    <td>106</td>
  </tr>
  <tr>
    <td>Mental Illness</td>
    <td>105</td>
  </tr>
  <tr>
    <td>Certain conditions originating in the perinatal period</td>
    <td>45</td>
  </tr>
</table>


Therefore, we could consider any claim occurring within the active window as having a high chance of re-occuring. 

**Compile health status for each member**

The final part of the task was to consolidate each member’s recent claim history into a current status. For each member, I followed the following procedures:

1. If the member has no claims within any active window, they are given a status of "No current diagnoses or symptoms" - in other words, as far as we know, this member is healthy.

2. If the only claims the member has within any active window falling under the "Preventative or preliminary care" label, the member is given that label as  status.

3. In all other cases, all "Preventative or preliminary care" labels are dropped from the member’s history under the assumption that those labels are incidental to the more specific diagnoses that make up the rest of the member’s recent history. Remaining record are then further consolidated by finding all cases where a subcategory label is occurs in the same history as one of its parents. In those cases, the most granular label is used. For example, “Tuberculosis” is a level-3 category under the level-1 category of “Infectious and parasitic diseases”. If both of those appeared in the same member’s recent history, only “Tuberculosis” would be used.

The above process results in 60163 members having a health status of "No current diagnoses or symptoms", 4337 members having a health status of simply “Preventative or preliminary care”, and 11068 members having a health status comprised of a single diagnosis. The remaining 24% of the members in the dataset had some combination of diagnoses - sometimes as many as 12, but usually between 2 and 4.

**Predict labels**

In the dataset provided, there were 17 drug categories, 90 drug groups, and 424 drug classes. We need this data in a format that matches the format of the categories we are trying to predict (one row per member). I would approach the task of predicting, say, the "No current diagnoses or symptoms" label, or those members with multiple labels, through the following process:

1. Engineer a large set of features

    1. Aggregate the number of times a member filed a claim for a category, group, or class within different time spans. I would probably start with monthly aggregation, and if I couldn’t get satisfactory results from that, I would try windows of one week and two months to see if I could improve model performance.

    2. Given that this would produce a very large number of variables, I would also generate some new features using random projections or some other dimensionality-reduction procedure to capture any variation in drug claims that persists across time.

    3. I would likely start with only a few months of data - say the six most recent months - and only expand if I eventually needed to improve the predictive ability of the model.

    4. Depending on what model I used as a ranking algorithm (see step 2, below), I would calculate at least second-order interactions between variables.

2. Rank each individual feature in terms of its usefulness for predicting member health status

    5. I tend to use a forest model (random or gradient boosting) for this process since it is relatively robust to overfitting and implicitly handles interactions. However, given both the large number of potential predictors as well as the size of the data set, I would probably lean towards something more scalable like stochastic gradient boosting fit with L1 regularization to do online feature selection. This would shrink the coefficients of many of the predictors to zero, and leave the rest rankable by the absolute value of the coefficient.

3. Cross-validate increasingly simpler models until increased simplicity results in substantially lower accuracy

    6. I would pick a cost function. A plain error rate could work, but depending on the business needs that prompted the need to predict the category, I might use a combination of false positive rate and false negative rate, each weighted by how costly that specific type of error was to the business.

    7. I would start with a model that included all variables that weren’t excluded from step 2 above. I would fit a model using 2-fold cross validation and calculate the cost function based on predictions to each fold. I would then repeat the above process for each variable, each time dropping out the lowest-ranked variable.

    8. The above process would result in a plottable cost curve that could be used to select the appropriate trade-off between accuracy and simplicity.

Once I had the final set of selected variables, I would fit the model through cross-validation, this time using more folds (something like 10) so the predictions would more accurately simulate the performance of using the entire data set. I would use, at the very least, the same cost function that I used in the feature selection step, possibly including other metrics if they were necessary for the business to make decisions about how to use, or how much to trust, the model results.

