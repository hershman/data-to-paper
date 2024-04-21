
import pandas as pd

# Load the dataset
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write("Total Rows: " + str(df.shape[0]) + "\n")
    f.write("Total Columns: " + str(df.shape[1]) + "\n")

    # Summary Statistics
    f.write("\n# Summary Statistics\n")
    description = df.describe()
    f.write(description.to_string())
    
    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    for column in df.columns:
        if df[column].dtype == 'object':
            f.write(f"Column: {column}, Mode: {df[column].mode().values[0]}\n")
            
    # Missing Values
    f.write("\n# Missing Values\n")
    f.write("Missing Values:\n" + str(df.isnull().sum()) + "\n")

    # Unknown/ Undefined 
    f.write("\n# Unknown/ Undefined Values\n")
    for col in df.columns:
        if df[col].dtype == 'int64' or df[col].dtype == 'float64':
            count_less_than_zero = (df[col] < 0).sum()
            if count_less_than_zero > 0:
                f.write(f"Column: {col}, Unknown/Undefine Values Count: {count_less_than_zero}\n")
