
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, is_str_in_df, split_mapping, AbbrToNameDef

# PREPARATION FOR ALL TABLES
shared_mapping: AbbrToNameDef = {
    'Coef.': ('Coeff.', 'Logistic regression coefficient'),
    'Std.Err.': ('Std. Err.', 'Standard error of the coefficient'),
    'z': ('z', 'Wald test statistic'),
    'P>|z|': ('p-val', 'The p-value of the Wald test'),
    '[0.025': ('Low 95%', 'Lower bound of the 95% confidence interval'),
    '0.975]': ('Upp 95%', 'Upper bound of the 95% confidence interval'),
}

# TABLE 1
df1 = pd.read_pickle('table_1.pkl')

# RENAME COLUMNS AND ROWS
mapping1: AbbrToNameDef = {k: v for k, v in shared_mapping.items() if is_str_in_df(df1, k)} 
mapping1 |= {
    'Intercept': ('Intrcpt', 'Baseline log-odds of having diabetes'),
    'BMI': ('BMI', None),
    'Smoker': ('Smoker', '1: Yes, 0: No'),
    'PhysActivity': ('PhysAct', '1: Yes, 0: No'),
    'Fruits': ('Fruits', '1: Yes, 0: No'),
    'Veggies': ('Veggies', '1: Yes, 0: No'),
    'HighBP': ('HighBP', '1: Yes, 0: No'),
    'HighChol': ('HighChol', '1: Yes, 0: No'),
}
abbrs_to_names1, legend1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# SAVE AS LATEX
to_latex_with_note(
    df1, 'table_1.tex',
    caption="Odds Ratios from Logistic Regression Model Predicting Diabetes Presence", 
    label='table:logistic_regression',
    legend=legend1)

# TABLE 2
df2 = pd.read_pickle('table_2.pkl')

# RENAME COLUMNS AND ROWS
mapping2: AbbrToNameDef = {k: v for k, v in shared_mapping.items() if is_str_in_df(df2, k)} 
mapping2 |= {
    'Intercept': ('Intrcpt', 'Baseline log-odds of having diabetes'),
    'BMI': ('BMI', None),
    'Smoker': ('Smoker', '1: Yes, 0: No'),
    'PhysActivity': ('PhysAct', '1: Yes, 0: No'),
    'Fruits': ('Fruits', '1: Yes, 0: No'),
    'Veggies': ('Veggies', '1: Yes, 0: No'),
    'HighBP': ('HighBP', '1: Yes, 0: No'),
    'HighChol': ('HighChol', '1: Yes, 0: No'),
}
abbrs_to_names2, legend2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# SAVE AS LATEX
to_latex_with_note(
    df2, 'table_2.tex',
    caption="Odds Ratios for Individual Risk Factors Predicting Diabetes Presence", 
    label='table:individual_risk_factors',
    legend=legend2)
