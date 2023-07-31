from dataclasses import dataclass
from typing import Dict

import pandas as pd

from data_to_paper.latex.tables import create_threeparttable
from data_to_paper.utils import dedent_triple_quote_str

from .runtime_issues_collector import create_and_add_issue
from .types import CodeProblem, RunIssue


@dataclass
class RunUtilsError(Exception):
    issue: RunIssue


KNOWN_ABBREVIATIONS = ('std', 'BMI', 'P>|z|', 'P-value')


def is_name_an_unknown_abbreviated(name: str) -> bool:
    """
    Check if the name is abbreviated.
    """
    if not isinstance(name, str):
        return False
    if len(name) == 0:
        return False
    if name in KNOWN_ABBREVIATIONS:
        return False

    if not any(char.isalpha() for char in name):
        return False

    if len(name) == 1:
        return True

    if '.' in name or ':' in name or '_' in name:
        return True
    if name.islower() or name.istitle() or (name[0].isupper() and name[1:].islower()):
        return False
    return True


def to_latex_with_note(df: pd.DataFrame, filename: str, *args,
                       note: str = None,
                       legend: Dict[str, str] = None,
                       **kwargs):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f'Expected df to be a pandas.DataFrame, got {type(df)}')

    if not isinstance(filename, str):
        raise ValueError(f'Expected filename to be a string, got {type(filename)}')

    if not filename.endswith('.tex'):
        filename = filename + '.tex'

    latex = df.to_latex(*args, **kwargs)

    if note or legend:
        latex = create_threeparttable(latex, note, legend)

    _check_for_errors(latex, df, filename, *args, note=note, legend=legend, **kwargs)

    with open(filename, 'w') as f:
        f.write(latex)


def _check_for_errors(latex: str, df: pd.DataFrame, filename: str, *args,
                      note: str = None,
                      legend: Dict[str, str] = None,
                      **kwargs):
    caption = kwargs.get('caption', None)
    label = kwargs.get('label', None)
    index = kwargs.get('index', True)
    columns = kwargs.get('columns', None)
    columns = df.columns if columns is None else columns
    legend = {} if legend is None else legend

    # Check if the table is a df.describe() table
    description_headers = ('mean', 'std', 'min', '25%', '50%', '75%', 'max')
    if set(description_headers).issubset(columns) or set(description_headers).issubset(df.index):
        create_and_add_issue(category='Quantiles and min/max values should not be included in scientific tables',
                             code_problem=CodeProblem.OutputFileContentLevelA,
                             item=filename,
                             issue=f'The table includes mean, std, as well as quantiles and min/max values.',
                             instructions=dedent_triple_quote_str("""
            Note that in scientific tables, it is not customary to include quantiles, or min/max values, \
            especially if the mean and std are also included.
            Please revise the code so that the tables only include scientifically relevant statistics.
            """))

    # Check for repetitive values in a column
    for column_header in columns:
        data = df[column_header]
        if len(data.unique()) == 1 and len(data) > 5:
            data0 = data.iloc[0]
            # check if the value is a number
            if not isinstance(data0, (int, float)):
                pass
            elif round(data0) == data0 and data0 < 10:
                pass
            else:
                create_and_add_issue(category='Repetitive values in a column',
                                     code_problem=CodeProblem.OutputFileContentLevelB,
                                     item=filename,
                                     issue=f'The column "{column_header}" has the same unique value for all rows.',
                                     instructions=dedent_triple_quote_str("""
                    Please revise the code so that it:
                    * Finds the unique values of the column
                    * Asserts that the len of unique values == 1
                    * Create the table without this column
                    * Add the unique value in the table note (use `note=` in the function `to_latex_with_note`). 
                    """))

    # Check that the rows are labeled:
    if index is False and df.shape[0] > 1:
        create_and_add_issue(category='Unlabelled rows in a table',
                             code_problem=CodeProblem.OutputFileDesignLevelA,
                             item=filename,
                             issue=f'The table has more than one row, but the rows are not labeled.',
                             instructions=dedent_triple_quote_str("""
            Please revise the code making sure all tables are created with labeled rows.
            Use `index=True` in the function `to_latex_with_note`.
            """))

    # Check caption/label
    instructions = dedent_triple_quote_str("""
        Please revise the code making sure all tables are created with a caption and a label.
        Use the arguments `caption` and `label` of the function `to_latex_with_note`.
        Captions should be suitable for a table in a scientific paper.
        Labels should be in the format `table:<your table label here>`.
        """)
    if caption is None or label is None:
        missing = 'caption and label' if caption is None and label is None \
            else 'caption' if caption is None else 'label'
        create_and_add_issue(category='Problem with table caption/label',
                             code_problem=CodeProblem.OutputFileDesignLevelA,
                             item=filename,
                             issue=f'The table does not have a {missing}',
                             instructions=instructions)

    if label is not None and not label.startswith('table:'):
        create_and_add_issue(category='Problem with table caption/label',
                             code_problem=CodeProblem.OutputFileDesignLevelA,
                             item=filename,
                             issue='The label of the table is not in the format `table:<your table label here>`',
                             instructions=instructions)

    # check if the caption starts with "Table <number>"
    if caption is not None and caption.lower().startswith('table'):
        create_and_add_issue(category='Problem with table caption/label',
                             code_problem=CodeProblem.OutputFileDesignLevelA,
                             item=filename,
                             issue='The caption of the table should not start with "Table ..."',
                             instructions=instructions)

    # Check that any abbreviated row/column labels are explained in the legend
    if index:
        headers = [name for name in df.index]
    else:
        headers = []
    headers += [name for name in columns]
    abbr_names = [name for name in headers if is_name_an_unknown_abbreviated(name)]
    un_mentioned_abbr_names = [name for name in abbr_names if name not in legend]
    if un_mentioned_abbr_names:
        instructions = dedent_triple_quote_str("""
            Please revise the code making sure all abbreviated names are explained in their table legend.
            Add the missing abbreviations and their explanations as keys and values in the `legend` argument of the \
            function `to_latex_with_note`.
            """)
        if legend:
            create_and_add_issue(category='Some abbreviated names are not explained in the table legend',
                                 code_problem=CodeProblem.OutputFileDesignLevelB,
                                 item=filename,
                                 issue=f'The legend of the table needs to include also the following abbreviated names:\n'
                                       f'{un_mentioned_abbr_names}', instructions=instructions)
        else:
            create_and_add_issue(category='Some abbreviated names are not explained in the table legend',
                                 code_problem=CodeProblem.OutputFileDesignLevelB,
                                 item=filename,
                                 issue=f'The table needs a legend explaining the following abbreviated names:\n'
                                       f'{un_mentioned_abbr_names}', instructions=instructions)
