
# Import required packages
import pandas as pd

# Load the data file
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Key Variables for summary
key_numerical_variables = ['BMI', 'GenHlth', 'MentHlth', 'PhysHlth', 'Age', 'Education', 'Income']
key_categorical_variables = ['Diabetes_binary', 'HighBP', 'HighChol', 'Smoker', 'Stroke', 'HeartDiseaseorAttack', 'Sex']

# Open the output file
with open('data_exploration.txt', 'w') as f:
    # Data Size
    f.write('# Data Size\n')
    f.write('Number of rows: {}\n'.format(df.shape[0]))
    f.write('Number of columns: {}\n\n'.format(df.shape[1]))

    # Summary Statistics (Numerical Variables only)
    f.write('# Summary Statistics (Numerical Variables)\n')
    f.write(str(df[key_numerical_variables].describe()))
    f.write('\n\n')

    # Categorical Variables Analysis
    f.write('# Categorical Variables\n')
    for var in key_categorical_variables:
        f.write('Variable "{}": Most common value: {}\n'.format(var, df[var].mode().values[0]))
    f.write('\n')

    # Missing Values
    f.write('# Missing Values\n')
    f.write('Missing, unknown, or undefined values: {}\n'.format(df.isnull().sum().sum()))
    
    # Assuming '9' as code for unknown/undefined in some columns like 'GenHlth'
    f.write("Count of '9' in 'GenHlth' (represents unknown/undefined): {}\n\n".format(df[df['GenHlth'] == 9].shape[0]))

    # Any other summary : Here, I used unique value counts for key categorical variables
    f.write('# Unique Values Count (for key categorical variables)\n')
    for var in key_categorical_variables:
        f.write("Unique value counts for '{}': \n{}\n".format(var, df[var].value_counts()))
    f.write('\n')
