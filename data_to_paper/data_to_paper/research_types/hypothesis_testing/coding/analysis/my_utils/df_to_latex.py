from typing import Dict, List, Optional

import pandas as pd

from data_to_paper.llm_coding_utils.df_to_latex import df_to_latex
from data_to_paper.research_types.hypothesis_testing.coding.analysis.check_df_of_table import \
    check_output_df_for_content_issues
from data_to_paper.research_types.hypothesis_testing.coding.utils import convert_filename_to_label
from data_to_paper.run_gpt_code.overrides.dataframes.df_with_attrs import ListInfoDataFrame

from data_to_paper.run_gpt_code.run_contexts import IssueCollector
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types


def _df_to_latex(df: pd.DataFrame, filename: str, **kwargs):
    """
    Replacement of df_to_latex to be used by LLM-writen code.
    Same as df_to_latex, but also checks for issues.
    """
    label = convert_filename_to_label(filename)

    issue_collector = IssueCollector.get_runtime_instance()
    issues = check_output_df_for_content_issues(df, label)
    issue_collector.issues.extend(issues)
    df_to_latex(df, filename, label=label, **kwargs)

    # save df to pickle with the func and kwargs
    df = ListInfoDataFrame.from_prior_df(df, ('df_to_latex', df, label, {}))
    pickle_filename = label + '.pkl'
    df.to_pickle(pickle_filename)
