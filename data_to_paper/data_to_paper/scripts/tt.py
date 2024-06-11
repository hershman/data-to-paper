import pandas as pd
import matplotlib.pyplot as plt

from data_to_paper.llm_coding_utils.df_plot_with_pvalue import df_plot_with_pvalue

# Creating a DataFrame with data and error columns
data = {
    'apples': [3, 2, 5, 7, 2],
    'oranges': [1, 5, 3, 8, 6],
    'bananas': [3, 4, 2, 1, 5],
    'apples_err': [0.5, 4.3, 0.6, 0.2, 0.4],
    'oranges_err': [(0.3, 0.5), (0.4, 0.6), (0.5, 0.2), (0.1, 0.3), (0.3, 0.4)],
    'bananas_err': [0.2, 0.3, 0.1, 0.5, 0.4],
    'apples_ci': [(2.5, 3.5), (1.7, 2.3), (4.4, 5.6), (6.8, 7.2), (1.6, 2.4)],
    'oranges_ci': [(0.8, 1.2), (4.4, 5.6), (2.8, 3.2), (7.7, 8.3), (5.6, 6.4)],
    'bananas_ci': [(2.8, 3.2), (3.8, 4.2), (1.8, 2.2), (0.7, 1.3), (4.6, 5.4)],
    'apples_p_value': [0.1, 0.002, 0.3, 0.4, 0.5],
    'oranges_p_value': [0.1, 0.2, 0.001, 0.4, 0.5],
    'bananas_p_value': [0.1, 0.2, 0.3, 0.00001, 0.5]
}
df = pd.DataFrame(data)

# Plotting with error bars using DataFrame structure
ax = df_plot_with_pvalue(df, kind='bar', y=['apples', 'oranges', 'bananas'],
                         yerr=['apples_err', 'oranges_err', 'bananas_err'],
                            y_p_value=['apples_p_value', 'oranges_p_value', 'bananas_p_value'])
# ax = df_plot_with_pvalue(df, y=['apples', 'oranges', 'bananas'], y_ci=['apples_ci', 'oranges_ci', 'bananas_ci'])
plt.show()

