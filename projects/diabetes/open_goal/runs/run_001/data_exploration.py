
import pandas as pd

# Load the data
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Open the output file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write('# Data Size\n')
    f.write('Number of rows: {}\n'.format(data.shape[0]))
    f.write('Number of columns: {}\n'.format(data.shape[1]))
    f.write('\n')

    # Summary Statistics
    f.write('# Summary Statistics\n')
    f.write(str(data.describe()))
    f.write('\n\n')

    # Categorical Variables
    f.write('# Categorical Variables\n')
    categorical_cols = data.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        f.write('Column Name: {}\n'.format(col))
        f.write('Most Common Value: {}\n'.format(data[col].mode()[0]))
    if categorical_cols.size == 0:
        f.write('Not Applicable\n')
    f.write('\n')

    # Missing Values
    f.write('# Missing Values\n')
    missing_values = data.isnull().sum()
    n_missing_values = missing_values.sum()
    if n_missing_values == 0:
        f.write('No missing values')
    else:
        f.write(str(missing_values))
    f.write('\n\n')
