import inspect
import re
from typing import Optional, Dict

import pandas as pd

from data_to_paper.latex.clean_latex import process_latex_text_and_math
from data_to_paper.llm_coding_utils.df_to_labeled_latex import df_to_numerically_labeled_latex
from data_to_paper.llm_coding_utils.note_and_legend import convert_note_and_glossary_to_latex_table_caption, \
    convert_note_and_glossary_to_html
from data_to_paper.run_gpt_code.overrides.dataframes.utils import to_html_with_value_format
from data_to_paper.run_gpt_code.overrides.pvalue import OnStr, OnStrPValue
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator

THREEPARTTABLE = r"""\begin{table}[htbp]
\centering
\begin{threeparttable}
<caption>
<label>
<tabular>
\begin{tablenotes}
<note_and_glossary>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""

THREEPARTTABLE_WIDE = r"""\begin{table}[h]
<caption>
<label>
\begin{threeparttable}
\renewcommand{\TPTminimum}{\linewidth}
\makebox[\linewidth]{%
<tabular>}
\begin{tablenotes}
\footnotesize
<note_and_glossary>
\end{tablenotes}
\end{threeparttable}
\end{table}
"""


HTML_TABLE_WITH_LABEL_AND_CAPTION = r"""
<b>{caption}</b>
{table}
{note_and_glossary}
"""


@raise_on_wrong_func_argument_types_decorator
def df_to_latex(df: pd.DataFrame, filename: Optional[str], caption: str = None, label: str = None,
                note: str = None,
                glossary: Dict[str, str] = None,
                is_wide: bool = True,
                pvalue_on_str: Optional[OnStr] = None,
                **kwargs):
    """
    Create a latex table with a note.
    Same as df.to_latex, but with a note and glossary.
    """

    regular_latex_table = df_to_numerically_labeled_latex(df, pvalue_on_str=pvalue_on_str)

    pvalue_on_str_html = OnStr.SMALLER_THAN if pvalue_on_str == OnStr.LATEX_SMALLER_THAN else pvalue_on_str
    with OnStrPValue(pvalue_on_str_html):
        regular_html_table = to_html_with_value_format(df, border=0, justify='left')

    tabular_part = get_tabular_block(regular_latex_table)
    latex_caption = r'\caption{' + process_latex_text_and_math(caption) + '}\n' if caption else ''
    html_caption = caption if caption else ''
    label = r'\label{' + label + '}\n' if label else ''

    index = kwargs.get('index', True)
    note_and_glossary = convert_note_and_glossary_to_latex_table_caption(df, note, glossary, index)
    note_and_glossary_html = convert_note_and_glossary_to_html(df, note, glossary, index)

    template = THREEPARTTABLE if not is_wide else THREEPARTTABLE_WIDE
    latex = template.replace('<tabular>', tabular_part) \
        .replace('<caption>\n', latex_caption) \
        .replace('<label>\n', label) \
        .replace('<note_and_glossary>', note_and_glossary)

    html = HTML_TABLE_WITH_LABEL_AND_CAPTION.replace('{caption}', html_caption) \
        .replace('{table}', regular_html_table) \
        .replace('{note_and_glossary}', note_and_glossary_html)
    return latex


def get_tabular_block(latex_table: str) -> str:
    """
    Extract the tabular block of the table.
    """
    return re.search(pattern=r'\\begin{tabular}.*\n(.*)\\end{tabular}', string=latex_table, flags=re.DOTALL).group(0)
