
# IMPORT
import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.formula.api import logit
import pickle

# LOAD DATA
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed.

# ANALYSIS

## DF 1: "Logistic regression analysis of the moderation effect of physical activity on the association between BMI and Diabetes, controlling for age"
model = logit("Diabetes_binary ~ BMI * PhysActivity + Age", data=df).fit()
params = np.exp(model.params)
conf= np.exp(model.conf_int())
conf['OR'] = params
p_values = model.pvalues
conf['p-value'] = p_values
df1 = conf
df1.to_pickle('df_1.pkl')  

## DF 2: "Difference in mean BMI between individuals with diabetes and those without diabetes, stratified by age group and diabetes"
bins = [1, 5, 9, df['Age'].max()]
labels = ['Young', 'Middle-aged', 'Old']
df['AgeGroup'] = pd.cut(df['Age'], bins=bins, labels = labels, include_lowest=True)

df2 = df.groupby(['AgeGroup', 'Diabetes_binary'])['BMI'].agg(['mean', 'std', lambda x: stats.norm.interval(0.95, loc=np.mean(x), scale=stats.sem(x))])
df2.columns = ['Mean BMI', 'STD BMI', '95% CI']
df2.index.names = ['AgeGroup', 'Diabetes_binary']
df2.to_pickle('df_2.pkl')  

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': df.shape[0]
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
