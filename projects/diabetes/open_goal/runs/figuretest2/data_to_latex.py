
# IMPORT
import pandas as pd
from my_utils import to_latex_with_note, to_figure_with_note, is_str_in_df, split_mapping, AbbrToNameDef
import matplotlib
matplotlib.use('Agg')  # Switch to a non-interactive backend suitable for scripts without GUI.

# PREPARATION FOR ALL TABLES AND FIGURES
shared_mapping: AbbrToNameDef = {
    'BMI': ('BMI', 'Body Mass Index'),
    'PhysActivity': ('P. Act.', 'Physical Activity in the past 30 days (0=no, 1=yes)'),
    'Diabetes_binary': ('Diabetes', 'Diabetes(0=no, 1=yes)'),
    'Age': ('Age C.', 'Age in 13-level age category with intervals of 5 years (1= 18 - 24, 2= 25 - 29, ..., 12= 75 - 79, 13 = 80 or older)'),
}

# DF 1: "Logistic regression analysis of the moderation effect of physical activity on the association between BMI and Diabetes, controlling for age"
df1 = pd.read_pickle('df_1.pkl')

# Format values:
# Not Applicable

# Rename rows and columns:
mapping1 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df1, k)) 
mapping1 |= {
    '0': ('Lower', None),
    '1': ('Higher', None),
    'OR': ('O.R.', 'Odds Ratio of diabetes obtained from logistic regression model.'),
    'BMI:PhysActivity': ('BMI*P.Act.', 'Interaction term between BMI and Physical Activity')
}
abbrs_to_names1, glossary1 = split_mapping(mapping1)
df1 = df1.rename(columns=abbrs_to_names1, index=abbrs_to_names1)

# Create latex table:
to_latex_with_note(
    df1, 'df_1.tex',
    caption="Logistic regression effect of physical activity on BMI and Diabetes, with age control", 
    label='table:df_1',
    note="O.R.=Odds Ratio in logistic regression model.",
    glossary=glossary1)

# DF 2: "Difference in mean BMI between individuals with diabetes and those without diabetes, stratified by age group and diabetes"
df2 = pd.read_pickle('df_2.pkl')

# Format values:
# Not Applicable

# Rename rows and columns:
mapping2 = dict((k, v) for k, v in shared_mapping.items() if is_str_in_df(df2, k)) 
mapping2 |= {
    '0': ('No', None),
    '1': ('Yes', None),
    'Mean BMI': ('Avg. BMI', 'Average Body Mass Index'),
    'STD BMI': ('STD BMI', 'Standard Deviation of Body Mass Index'),
    '95% CI': ('95% CI', '95% Confidence Interval'),
}
abbrs_to_names2, glossary2 = split_mapping(mapping2)
df2 = df2.rename(columns=abbrs_to_names2, index=abbrs_to_names2)

# Create latex figure:
to_figure_with_note(
    df2, 'df_2.tex',
    caption="Difference in mean BMI between individuals with diabetes and those without diabetes, stratified by age group and diabetes.", 
    label='figure:df_2',
    note="Bars indicate standard deviation (STD).",
    glossary=glossary2,
    kind='bar',
    y='Avg. BMI',
    yerr='STD BMI',  
)
