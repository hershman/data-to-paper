from typing import Optional, List

import pandas as pd

from data_to_paper.llm_coding_utils.df_to_figure import df_to_figure
from data_to_paper.research_types.hypothesis_testing.coding.analysis.check_df_of_table import \
    check_output_df_for_content_issues
from data_to_paper.research_types.hypothesis_testing.coding.utils import convert_filename_to_label
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import ListInfoDataFrame
from data_to_paper.run_gpt_code.overrides.pvalue import is_containing_p_value, is_only_p_values

from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from data_to_paper.run_gpt_code.run_issues import RunIssue, CodeProblem


def _df_to_figure(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_figure to be used by LLM-writen code.
    """
    label = convert_filename_to_label(filename)

    issue_collector = IssueCollector.get_runtime_instance()
    issues = []
    issues.extend(check_output_df_for_content_issues(df, label, is_figure=True))
    issues.extend(_check_for_p_values_in_figure(df, label, **kwargs))
    issue_collector.issues.extend(issues)
    df_to_figure(df, filename, label=label, raise_formatting_errors=False, **kwargs)

    # save df to pickle with the func and kwargs
    df = ListInfoDataFrame.from_prior_df(df, ('df_to_figure', df, label, kwargs))
    pickle_filename = label + '.pkl'
    df.to_pickle(pickle_filename)


def _check_for_p_values_in_figure(df: pd.DataFrame, filename: str,
                                  x_p_value: Optional[str] = None,
                                  y_p_value: Optional[str] = None,
                                  **kwargs) -> List[RunIssue]:
    """
    If the df has p-values, they must be plotted using the argument `x_p_value` or `y_p_value`.
    """
    if not is_containing_p_value(df):
        return []
    msgs = []
    # df must have exactly one column with p-values
    p_value_columns = [col for col in df.columns if is_only_p_values(df[col])]
    if len(p_value_columns) != 1:
        msgs.append(f'Expecting exactly one column with p-values.')
    else:
        p_value_column = p_value_columns[0]
        # check that the p-values are plotted with x_p_value or y_p_value:
        if x_p_value is None and y_p_value is None:
            msgs.append(f'The df has p-values in column `{p_value_column}`, but they are not being plotted.')
        elif x_p_value is not None:
            if x_p_value != p_value_column:
                msgs.append(f'Column `{x_p_value}` is not the column with the p-values, which is `{p_value_column}`.')

        elif y_p_value is not None:
            if y_p_value != p_value_column:
                msgs.append(f'Column `{y_p_value}` is not the column with the p-values, which is `{p_value_column}`.')
    return [RunIssue(
        category='Plotting P-values',
        issue=msg,
        item=filename,
        instructions='To plot p-values with `df_to_figure`, the df must have exactly one column with p-values, '
                     'and its name must be provided in the `x_p_value` or `y_p_value` argument.',
        code_problem=CodeProblem.OutputFileContentLevelA,
    ) for msg in msgs]
