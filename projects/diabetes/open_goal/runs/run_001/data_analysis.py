

# IMPORT
from my_utils import df_to_latex, df_to_figure
import numpy as np
import pandas as pd
from statsmodels.formula.api import logit
import pickle

# LOAD DATA
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## No descriptive statistics table is needed because the summary provided by the output of the Data Exploration Code is sufficient for this analysis.

## Figure df_param_dist:
caption = "Histogram of Key Features"
df_param_dist = df[['Diabetes_binary','HighBP','HighChol','Stroke']]
df_to_figure(df_param_dist, 'df_param_dist', kind='hist', y=df_param_dist.columns, caption=caption)

# PREPROCESSING
# No preprocessing is needed, because our data is already in the format suitable for analysis.

# ANALYSIS

## Figure df_log_reg_diabetes_highBP:
caption = "Logistic regression of Diabetes_binary on HighBP, adjusting for Age, BMI, and Sex"
# Perform logistic regression with confounding variables
logit_model_highBP = logit('Diabetes_binary ~ HighBP + Age + BMI + Sex', data=df).fit()
# Create dataframe and save to LaTeX figure
df_log_reg_diabetes_highBP = pd.DataFrame({'coef': logit_model_highBP.params, 
                                           'std err': logit_model_highBP.bse, 
                                           'z': logit_model_highBP.tvalues, 
                                           'p>|z|': logit_model_highBP.pvalues, 
                                           '[0.025': logit_model_highBP.conf_int()[0], '0.975]': logit_model_highBP.conf_int()[1]})
df_to_figure(df_log_reg_diabetes_highBP, 'df_log_reg_diabetes_highBP', kind='bar', y='coef', yerr='std err', y_p_value='p>|z|', caption=caption)

## Figure df_log_reg_diabetes_HighChol:
caption = "Logistic regression of Diabetes_binary on HighChol, adjusting for Age, BMI, and Sex"
# Perform logistic regression with confounding variables
logit_model_highChol = logit('Diabetes_binary ~ HighChol + Age + BMI + Sex', data=df).fit()
# Create dataframe and save to LaTeX figure
df_log_reg_diabetes_HighChol = pd.DataFrame({'coef': logit_model_highChol.params, 
                                           'std err': logit_model_highChol.bse, 
                                           'z': logit_model_highChol.tvalues, 
                                           'p>|z|': logit_model_highChol.pvalues, 
                                           '[0.025': logit_model_highChol.conf_int()[0], '0.975]': logit_model_highChol.conf_int()[1]})
df_to_figure(df_log_reg_diabetes_HighChol, 'df_log_reg_diabetes_HighChol', kind='bar', y='coef', yerr='std err', y_p_value='p>|z|', caption=caption)


## Figure df_log_reg_diabetes_Stroke:
caption = "Logistic regression of Diabetes_binary on Stroke, adjusting for Age, BMI, and Sex"
# Perform logistic regression with confounding variables
logit_model_Stroke = logit('Diabetes_binary ~ Stroke + Age + BMI + Sex', data=df).fit()
# Create dataframe and save to LaTeX figure
df_log_reg_diabetes_Stroke = pd.DataFrame({'coef': logit_model_Stroke.params, 
                                           'std err': logit_model_Stroke.bse, 
                                           'z': logit_model_Stroke.tvalues, 
                                           'p>|z|': logit_model_Stroke.pvalues, 
                                           '[0.025': logit_model_Stroke.conf_int()[0], '0.975]': logit_model_Stroke.conf_int()[1]})
df_to_figure(df_log_reg_diabetes_Stroke, 'df_log_reg_diabetes_Stroke', kind='bar', y='coef', yerr='std err', y_p_value='p>|z|', caption=caption)

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),         
    'accuracy of logistic model for HighBP': logit_model_highBP.prsquared,
    'accuracy of logistic model for HighChol': logit_model_highChol.prsquared,
    'accuracy of logistic model for Stroke': logit_model_Stroke.prsquared
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)

