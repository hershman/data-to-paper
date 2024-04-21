
# IMPORT
import pandas as pd
import statsmodels.formula.api as smf
import pickle

# LOAD DATA
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
# No descriptive statistics table is needed.

# PREPROCESSING
# No preprocessing is needed, because our data values are already in a suitable format for analysis. All the values are binary and do not require any special transformations.

# ANALYSIS

## Table 1: "Odds Ratios from logistic regression model predicting Diabetes presence"
# fit the model
model1 = smf.logit(formula = "Diabetes_binary ~ BMI + Smoker + PhysActivity + Fruits + Veggies + HighBP + HighChol", data = df)
result1 = model1.fit()

# Create a dataframe for Table 1
df1 = pd.DataFrame(result1.summary2().tables[1]) 

# Save Table 1
df1.to_pickle('table_1.pkl')

## Table 2: "Odds Ratios for individual risk factors predicting Diabetes presence"

# fit separate models for each factor
results_dict = {}
for factor in ['HighBP', 'HighChol', 'PhysActivity', 'Fruits', 'Veggies', 'BMI', 'Smoker']:
    model = smf.logit(formula = f"Diabetes_binary ~ {factor}", data = df)
    result = model.fit()
    results_dict[factor] = pd.DataFrame(result.summary2().tables[1])

# Create a dataframe for Table 2
df2 = pd.concat(results_dict, axis=0)

# Save Table 2
df2.to_pickle('table_2.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
    'Total number of observations': len(df),
}
with open('additional_results.pkl', 'wb') as f:
    pickle.dump(additional_results, f)
